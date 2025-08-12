import requests

def test_api():
    """
    Test the /chat endpoint of the FastAPI application.
    Sends a sample question and prints the response.
    """
    response = requests.post(
        "http://localhost:8000/chat",
        json={"session_id": "test-session-1",
              "message": "Can you tell me about my order PSO1121?"}  # Example question
    )
    # print(response)
    # print("response was successful:", response.status_code == 200)

    if response.status_code == 200:
        essentials = response.json()
        # print("raw response:", essentials)
        print("Answer:", essentials.get("answer"))
        # if isinstance(essentials.get("source_documents"), list):
            # print("Source Documents:")
            # for doc in essentials["source_documents"]:
                # print(f" - {doc.get('relevant_doc')}, Metadata: {doc}")

if __name__ == "__main__":
    test_api()