# backend/data/vectordb.py
"""
Vector DB — uses the full CRM knowledge base (crm_knowledge.json) 
instead of the old 12-entry synthetic list.
"""
import json
import os
# pyrefly: ignore [missing-import]
import chromadb
import numpy as np

class MockSentenceTransformer:
    def __init__(self, name=None):
        pass
    def encode(self, text: str):
        # Generate deterministic mock unit embedding based on text hash
        val = sum(ord(c) for c in text)
        np.random.seed(val % 10000)
        vector = np.random.uniform(-1, 1, 384)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

JSON_PATH = os.path.join(os.path.dirname(__file__), "crm_knowledge.json")

# 1. Load the embedding model (mocked to run with 0MB RAM)
model = MockSentenceTransformer('all-MiniLM-L6-v2')

# 2. Create an in-memory Chroma DB
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="crm_knowledge",
    metadata={"hnsw:space": "cosine"}
)

# 3. Load the knowledge base
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        KNOWLEDGE = json.load(f)
else:
    # Fallback to old synthetic data if JSON not generated yet
    KNOWLEDGE = [
        {"type": "decision", "id": i+1, "text": d} for i, d in enumerate([
            "Decision: Expanded to second location in 2024. Outcome: Failed. Reason: Logistics capacity insufficient.",
            "Decision: Hired 10 sales reps in Q1 2025. Outcome: Success. Reason: Revenue increased by 18%.",
            "Decision: Cut prices by 10%. Outcome: Mixed. Reason: Volume up, margins down.",
            "Decision: Invested in warehouse automation. Outcome: Success. Reason: 15% overhead reduction.",
            "Decision: Outsourced logistics. Outcome: Failed. Reason: SLA breaches, complaints up 40%.",
            "Decision: Launched premium product line. Outcome: Success. Reason: High margins, brand differentiation.",
        ])
    ]
    print("⚠️  crm_knowledge.json not found. Run: python data/seed_db.py")

# 4. Add all knowledge entries to Chroma
for entry in KNOWLEDGE:
    uid = f"{entry['type']}_{entry['id']}"
    embedding = model.encode(entry["text"]).tolist()
    collection.upsert(
        ids=[uid],
        embeddings=[embedding],
        metadatas=[{"text": entry["text"], "type": entry["type"]}]
    )

print(f"[OK] Vector DB loaded with {len(KNOWLEDGE)} CRM knowledge entries.")


def retrieve_memory(query_text: str, top_k: int = 3) -> tuple:
    """
    Queries the vector DB and returns the best matching CRM knowledge entries
    along with the average cosine similarity score.
    Returns: (combined_text, avg_similarity_score)
    """
    query_embedding = model.encode(query_text).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "distances"]
    )

    if results["metadatas"] and len(results["metadatas"][0]) > 0:
        texts = []
        scores = []
        for i, meta in enumerate(results["metadatas"][0]):
            distance = results["distances"][0][i]
            similarity = round(1 - distance, 4)
            scores.append(similarity)
            texts.append(meta["text"])

        combined_text = " | ".join(texts)
        avg_score = round(sum(scores) / len(scores), 4)
        return combined_text, avg_score

    return "No relevant past memory found.", 0.0