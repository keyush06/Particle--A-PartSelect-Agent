import os
import json
from dotenv import load_dotenv
from uuid import uuid4
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
# from ..backend.utils import norm

load_dotenv()

class VectorStore:
    def __init__(self):
        self.index_name = "partselect-parts"
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.setup_index()
        self.index = self.pc.Index(self.index_name)
        self.vc = PineconeVectorStore(index=self.index, embedding=self.embeddings)

    def setup_index(self):
        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  #dims
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

    ## adding normalized fields for better retrieval
    def norm(self, text):
        return text.lower().replace("-","").replace(" ","")

    def prepare_product_docs(self):
        docs = []
        with open('./data/parts_data.json') as f:
            data = json.load(f)
        for part in data:
            text = f"""
            Part Number: {part['part_number']}
            Name: {part['name']}
            Category: {part['category']}
            Manufacturer: {part['manufacturer']}
            Manufacturer Part Number: {part['manufacturer_part_number']}
            Price: {part['price']}
            Description: {part['description']}
            Installation Guide: {part['installation_guide']}
            Troubleshooting: {part['troubleshooting']}
            Compatible Models: {', '.join(part['compatible_models'])}
            Compatible Brands: {', '.join(part['compatible_brands'])}
            """
            metadata = {
                "part_number": part["part_number"],
                "part_number_norm": self.norm(part["part_number"]),
                "name": part["name"],
                "category": part["category"],
                "price": part["price"],
                "manufacturer": part["manufacturer"],
                "manufacturer_part_number": part["manufacturer_part_number"],
                "manufacturer_part_number_norm": self.norm(part["manufacturer_part_number"]),
                "troubleshooting": part["troubleshooting"],
                "installation_guide": part["installation_guide"],
                "compatible_models": part["compatible_models"],
                "compatible_models_norm": [self.norm(model) for model in part["compatible_models"]]
            }
            # print("Ingesting metadata keys:", list(metadata.keys()))
            docs.append(Document(page_content=text, metadata=metadata))
        return docs
    
    def prepare_transaction_docs(self):
        docs = []
        with open('./data/transactions_data.json') as f:
            data = json.load(f)
        for txn in data:
            items_str = "; ".join(
                [f"{item['qty']}x {item['part_number']} @ ${item['price']}" for item in txn["items"]]
            )
            text = f"""
            Order ID: {txn['order_id']}
            Customer ID: {txn['customer_id']}
            Created Date: {txn['created_id']}
            Status: {txn['status']}
            Carrier: {txn['carrier']}
            Items: {items_str}
            Address City: {txn['address_city']}
            """
            metadata = {
                "order_id": txn["order_id"],
                "order_id_norm": self.norm(txn["order_id"]),
                "customer_id": txn["customer_id"],
                "customer_id_norm": self.norm(txn["customer_id"]),
                "created_id": txn["created_id"],
                "status": txn["status"],
                "carrier": txn["carrier"],
                "address_city": txn["address_city"],
                "category": "transaction",  # for filtering if needed
                "item_part_numbers_norm": [self.norm(item["part_number"]) for item in txn["items"]]
                # "items": [
                #     {
                #         "part_number": item["part_number"],
                #         "part_number_norm": self.norm(item["part_number"]),
                #         "qty": item["qty"],
                #         "price": item["price"]
                #     }
                #     for item in txn["items"]
                # ]
            }
            docs.append(Document(page_content=text, metadata=metadata))
        return docs

    # def ingest_documents(self):
    #     docs = self.prepare_docs()
    #     uuids = [str(uuid4()) for _ in range(len(docs))]
    #     self.vc.add_documents(
    #         documents=docs,
    #         ids=uuids
    #     )

    def ingest_documents(self):
        # Ingest products
        product_docs = self.prepare_product_docs()
        product_uuids = [str(uuid4()) for _ in range(len(product_docs))]
        self.vc.add_documents(
            documents=product_docs,
            ids=product_uuids,
            namespace="products"
        )
        print(f"Ingested {len(product_docs)} product docs to namespace 'products'.")

        # Ingest transactions
        transaction_docs = self.prepare_transaction_docs()
        txn_uuids = [str(uuid4()) for _ in range(len(transaction_docs))]
        self.vc.add_documents(
            documents=transaction_docs,
            ids=txn_uuids,
            namespace="transactions"
        )
        print(f"Ingested {len(transaction_docs)} transaction docs to namespace 'transactions'.")
 

    def get_vectorstore(self):
        return PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings
        )

if __name__ == "__main__":
    vector_store = VectorStore()
    vector_store.ingest_documents()
    print("Documents ingested successfully.")