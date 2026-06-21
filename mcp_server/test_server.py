import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# Test semantic search
results = index.search(
    namespace="deals",
    query={
        "inputs": {"text": "technology sector antitrust merger risks"},
        "top_k": 3
    }
)

hits = results.get("result", {}).get("hits", [])
print(f"Found {len(hits)} results:\n")
for hit in hits:
    fields = hit.get("fields", {})
    print(f"Score: {hit.get('_score'):.3f}")
    print(f"Text: {fields.get('text', '')[:100]}...")
    print()