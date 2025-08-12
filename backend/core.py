from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import yaml

load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = "partselect-parts"
pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(index_name)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def load_prompt():
    with open("backend/prompt.yaml", "r") as file:
        return yaml.safe_load(file)

def build_chain(memory = None, filter = None, namespace = "products"):
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = "partselect-parts"
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(index_name)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # retrieving our vector store
    # vector_store = PineconeVectorStore(index=index, 
    #                                    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    #                                    namespace=namespace)

    vector_store = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
        namespace=namespace,
    )

    ## filtering
    print("vector_store.namespace:", getattr(vector_store, "namespace", None))
    # print("FILTER", filter)

    retriever_kwargs = {"k": 10, "namespace": namespace} # added namespace here
    if filter:
        retriever_kwargs["filter"] = filter
    # define the retriever, we can change the method as we want
    retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = retriever_kwargs
    )
    print("The arguments to retriever", retriever_kwargs, "/n")


    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0.0,
        max_tokens=None
    )

    llm_not_to_be_used = ChatOpenAI(
        model="gpt-4",
        temperature=0.0
    )

    # getting the system prompt here that is defined in th UDF above
    system_prompt = load_prompt()["system_prompt"]

    # """We will combine the prompt. There will also be a document prompt that will help in putting filters."""
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=system_prompt
    )

    ## debug
    # doc_prompt = PromptTemplate(
    # input_variables=["page_content"],
    # template="{page_content}"
    # )

    prod_doc_prompt = PromptTemplate(
    input_variables=[
        "page_content",
        "part_number", 
        "name",
        "manufacturer", 
        "manufacturer_part_number", 
        "category",
        "price",
        "installation_guide", 
        "troubleshooting",
        "compatible_models"
    ],
    template=(
        "Content: {page_content}\n"
        "Part Number: {part_number}\n"
        "Name: {name}\n"
        "Manufacturer: {manufacturer}\n"
        "Manufacturer Part Number: {manufacturer_part_number}\n"
        "Category: {category}\n"
        "Price: {price}\n"
        "Installation Guide: {installation_guide}\n"
        "Troubleshooting: {troubleshooting}\n"
        "Compatible Models: {compatible_models}"
        )
    )

    transaction_doc_prompt = PromptTemplate(
    input_variables=[
        "page_content",
        "order_id",
        "customer_id",
        "created_id",
        "status",
        "carrier",
        "item_part_numbers_norm",
        "address_city"
    ],
    template=(
        "Content: {page_content}\n"
        "Order ID: {order_id}\n"
        "Customer ID: {customer_id}\n"
        "Created Date: {created_id}\n"
        "Status: {status}\n"
        "Carrier: {carrier}\n"
        "Items: {item_part_numbers_norm}\n"
        "Address City: {address_city}"
        )
    )

    CONDENSE_PROMPT = PromptTemplate(
    input_variables=["chat_history", "question"],
    template=(
        "Rewrite the user’s follow-up as a standalone query.\n"
        "If the user says things like 'this part' or 'does this', resolve them using the most recently mentioned part number "
        "or model in the chat history. Include those IDs explicitly.\n\n"
        "Chat history:\n{chat_history}\n\n"
        "Follow-up: {question}\n\n"
        "Standalone query:"
    )
)

    # Set up conversation memory if not provided.
    if memory is None:
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            output_key="answer"
        )

    print("done before retreival chain")
    ## here is everything chained
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm_not_to_be_used,
        retriever=retriever,
        memory=memory,
        condense_question_prompt=CONDENSE_PROMPT,
        return_source_documents=True,
        combine_docs_chain_kwargs={
            "prompt": prompt,
            "document_prompt": prod_doc_prompt if namespace == "products" else transaction_doc_prompt
        }
    )
    return conv_chain

    
"""
Code is for the transactions index
"""

def transactions_search_order(order_id: str):
    """
    Search for a specific order in the transactions index.
    """
    
    
    result = index.query(
        vector=[0.0] * 1536,
        top_k=1,
        namespace = "transactions",
        include_metadata=True,
        filter={
            "order_id_norm": {"$eq": order_id.lower()}
        }

    )
    matches = result.get("matches", [])
    if matches and matches[0].get("metadata"):
        return matches[0]["metadata"]
    return None