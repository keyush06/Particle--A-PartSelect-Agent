from fastapi import FastAPI
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
from backend.core import build_chain
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from typing import Dict, Optional
from backend.utils import extract_part_number, extract_model_number, norm, resolve_entities, get_order_status, cancel_order, initiate_return, route_intent, format_order_answer

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

        user_intent = route_intent(message)
        # ======Metadata filter===========
        print("====++++&&&===this is our entities=======++++&&&", part_number, model_number, order_id)

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
            if order_id:
                metadata_filter["order_id_norm"] = {"$eq": norm(order_id)}
            elif part_number:
                metadata_filter["item_part_numbers_norm"] = {"$in": [norm(part_number)]}

        elif user_intent == "transactions_order":
            if not order_id:
                return ChatResponse(session_id=session_id, answer="To help with your order, please provide your Order ID (e.g., PSO1234).")
            msg = message.lower()
            if "status" in msg or "track" in msg or "tracking" in msg:
                res = get_order_status(order_id)
            elif "cancel" in msg:
                res = cancel_order(order_id)
            elif "return" in msg or "refund" in msg or "exchange" in msg:
                res = initiate_return(order_id, part_number=part_number)
            else:
                res = get_order_status(order_id)

            if res.get("ok"):
                ans = format_order_answer(res, message)
                return ChatResponse(session_id=session_id, answer=ans)
            else:
                return ChatResponse(session_id=session_id, answer=res.get("error") or res.get("message", "Unable to process the request."))
            
        


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
        
        chain = chat_sessions[session_id][namespace]

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

        ## Here we get the response
        response = chain.invoke({"question": message})
        # response = chain({"question": message})

        ## printing contexts - remove later
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

        # Namespace stats (optional, converted to plain dict)
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