from fastapi import FastAPI
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from backend.core import build_chain, transactions_search_order
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from typing import Dict, Optional
from backend.utils import norm, resolve_entities, route_intent, static_policies #get_order_status, cancel_order, initiate_return, route_intent, format_order_answer

app = FastAPI(title="PartSelect Chat Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PartSelect Chat Agent Backend Running!"}

chat_sessions: Dict[str, any] = dict()
chat_memories: Dict[str, ConversationBufferMemory] = dict()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str

## Creating the endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print("entered chatpoint")
    try:
        print("try first")
        session_id = request.session_id or str(uuid.uuid4())
        message = request.message

        print(f"Received question: {message}")

        # ======ENTITY EXTRACTION AND INTENT========
        # part_number = extract_part_number(message)
        # model_number = extract_model_number(message)
        part_number, model_number, order_id, ctx = resolve_entities(session_id, message)
        print("@@@@@@The session is this:", ctx)
        # Reuse session context for follow-ups if the current turn has no explicit entities
        if not order_id and ctx and ctx.get("active_order"):
            order_id = ctx["active_order"]
        if not part_number and ctx and ctx.get("active_part"):
            part_number = ctx["active_part"]
        if not model_number and ctx and ctx.get("active_model"):
            model_number = ctx["active_model"]

        print("====++++&&&===this is our entities=======++++&&&", part_number, model_number, order_id)


        user_intent = route_intent(message, session_id)

        # ======Metadata filter===========
        
        ## Building namespaces
        metadata_filter = {}
        if user_intent == "products":
            namespace = "products"
            if part_number:
                metadata_filter["part_number_norm"] = {"$eq": norm(part_number)}
            # elif manufacturer_part_number:
            #     metadata_filter["manufacturer_part_number_norm"] = {"$eq": norm(manufacturer_part_number)}
            elif model_number:
                metadata_filter["compatible_models_norm"] = {"$in": [norm(model_number)]}

        elif user_intent == "transactions_policy":
            namespace = "transactions"
            policies = static_policies()
            for key, value in policies.items():
                if key in message.lower():
                    return ChatResponse(session_id=session_id, answer=value)

        elif user_intent == "transactions_order":
            order_id = order_id or (ctx.get("active_order") if ctx else None)
            if not order_id:
                return ChatResponse(session_id=session_id, answer="I might need an Order number here. To help with your order, please provide your Order ID (e.g., PSO1234).")
            msg = message.lower()
            if any(k in msg for k in ["status", "track", "tracking"]):
                # Use Pinecone for status
                meta = transactions_search_order(order_id)
                if meta:
                    status = meta.get("status", "unknown")
                    carrier = meta.get("carrier", "the carrier")
                    city = meta.get("address_city", "your address")
                    return ChatResponse(session_id=session_id, answer=f"Your order {order_id} is currently {status} with {carrier}, shipping to {city}.")
                else:
                    return ChatResponse(session_id=session_id, answer="Order not found.")
                
            elif "cancel" in msg:
                meta = transactions_search_order(order_id)
                if meta and meta.get("status") == "order_placed":
                    return ChatResponse(session_id=session_id, answer=f"Order {order_id} cancellation request submitted.")
                elif meta:
                    return ChatResponse(session_id=session_id, answer=f"Order {order_id} cannot be cancelled because status is '{meta.get('status')}'.")
                else:
                    return ChatResponse(session_id=session_id, answer="Order not found.")
                
            elif any(k in msg for k in ["return", "refund", "exchange"]):
                meta = transactions_search_order(order_id)
                if meta:
                    return ChatResponse(session_id=session_id, answer=f"Return initiated for order {order_id}.")
                else:
                    return ChatResponse(session_id=session_id, answer="Order not found.")

            ## For all other queries, tool calling is not sufficient hence we use an LLM
            meta = transactions_search_order(order_id)
            if not meta:
                return ChatResponse(session_id=session_id, answer="Order not found.")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant for order queries. Use the provided order metadata to answer the user's question as accurately as possible. If a field is missing, say so."),
                ("user", "User question: {question}\nOrder metadata: {metadata}")
            ])

            llm = ChatOpenAI(model="gpt-4", temperature=0.2)
            answer = llm.invoke(prompt.format_prompt(question=message, metadata=meta).to_string()).content
            return ChatResponse(session_id=session_id, answer=answer)
        

        print("====++++&&&===this is our metadata filters=======++++&&&", metadata_filter)

        ## session ID check
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {}
            print("^^^^ New session^^^^^")
            if namespace not in chat_sessions[session_id]:
                memory_new = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True,
                    output_key="answer"
                )
                chat_memories[session_id] = memory_new
                chat_sessions[session_id][namespace] = build_chain(memory=memory_new, filter=metadata_filter, namespace=namespace)  
        else:
            chain = chat_sessions[session_id][namespace]
            chain.retriever.search_kwargs.update({
                                                    "namespace": namespace,
                                                    "k": 10,
                                                    "filter": metadata_filter or {}
        })
        
        # Building the chain
        chain = chat_sessions[session_id][namespace]


        # ==========================================================================================
        ## Debugging
        # probe_docs = chain.retriever.get_relevant_documents(message)
        # print(f"[probe] docs returned: {len(probe_docs)}")
        # for i, d in enumerate(probe_docs[:3]):
        #     print(f"[probe] {i} meta keys:", list(d.metadata.keys()))
        #     print(f"[probe] {i} part_number_norm:", d.metadata.get("part_number_norm"))
        #     print(f"[probe] {i} order_id_norm:", d.metadata.get("order_id_norm"))

        # # If nothing comes back, optionally relax filter or try a simpler query
        # if not probe_docs:
        #     # Try a neutral probe with same filter
        #     try:
        #         vs = chain.retriever.vectorstore
        #         probe2 = vs.similarity_search(
        #             "installation", k=5, filter=metadata_filter
        #         )
        #         print(f"[probe2] docs with neutral query: {len(probe2)}")
        #         for i, d in enumerate(probe2[:3]):
        #             print(f"[probe2] {i} part_number_norm:", d.metadata.get("part_number_norm"))
        #     except Exception as ex:
        #         print("[probe2] vectorstore check failed:", ex)

        # ==========================================================================================


        ## Here we get the response
        response = chain.invoke({"question": message})
        # response = chain({"question": message})
        if "source_documents" in response:
            print("=== RETRIEVED DOCUMENTS ===")
            for doc in response["source_documents"]:
                print("Page content:", doc.page_content)
                print("Metadata:", doc.metadata)
                print("-----")

        answer = response["answer"]
        source_docs = [{"relevant_documents": doc.page_content, **doc.metadata} for doc in response["source_documents"]]

        if not answer:
            return {"error": "No answer found for the question."}
        
        return ChatResponse(session_id=session_id, answer=answer)

    except Exception as e:
        print("direct here")
        return ChatResponse(
            session_id=request.session_id or "error",
            answer=f"Internal server error: {str(e)}"
        )


"""It is important to serialize all the responses otherwise got recursive errors"""
def _to_serializable(obj):
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, dict):
            return {str(k): _to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_serializable(v) for v in obj]
        return str(obj)

"""
Call this endpoint to see if you are able to fetch the records directly from the pinecone database.
Since I am using Langchain, that has its own abstractions, it is important to view the raw output and 
what goes into the retriever.
"""
@app.get("/_debug/pinecone")
def debug_pinecone(
    q: str = "installation",
    ns: str = "products",
    key: str = "part_number_norm",
    value: str = "ps8694830",
    top_k: int = 5,
    nofilter: bool = False,
    include_stats: bool = False,
):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = "partselect-parts"
        index = pc.Index(index_name)

        stats = None
        if include_stats:
            raw = index.describe_index_stats(namespace=ns)
            stats = _to_serializable(raw)

        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        vec = emb.embed_query(q)
        filter_arg = None if nofilter else {key: {"$eq": value}}

        res = index.query(
            vector=vec,
            top_k=top_k,
            include_metadata=True,
            namespace=ns,
            filter=filter_arg,
        )
        matches = res.get("matches", []) or []
        hits = [
            {
                "score": m.get("score"),
                "id": m.get("id"),
                "part_number": (m.get("metadata") or {}).get("part_number"),
                "part_number_norm": (m.get("metadata") or {}).get("part_number_norm"),
                "order_id": (m.get("metadata") or {}).get("order_id"),
                "order_id_norm": (m.get("metadata") or {}).get("order_id_norm"),
            }
            for m in matches
        ]

        payload = {
            "ok": True,
            "index": index_name,
            "namespace": ns,
            "q": q,
            "filter": filter_arg,
            "count_hits": len(hits),
            "hits": hits,
        }
        if include_stats:
            payload["stats"] = stats

        # Ensure fully JSON-serializable
        payload = _to_serializable(payload)
        return JSONResponse(content=payload)

    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500,
        )