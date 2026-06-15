import chromadb
from sentence_transformers import SentenceTransformer
from ingest import ingest

# ── Config ────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "ucla_transfer_guide"
CHROMA_PATH = "./chroma_db"
TOP_K = 5

# ── Setup ─────────────────────────────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

print("Setting up ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Delete existing collection if re-running to avoid duplicates
try:
    client.delete_collection(COLLECTION_NAME)
    print("Cleared existing collection.")
except:
    pass

collection = client.create_collection(COLLECTION_NAME)

# ── Embed and store ───────────────────────────────────────────────────────────
print("Running ingestion pipeline...")
chunks = ingest()
print(f"Embedding {len(chunks)} chunks...")

texts = [c["text"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

# Store in ChromaDB with metadata
collection.add(
    ids=[f"{c['source']}_{c['chunk_index']}" for c in chunks],
    embeddings=embeddings.tolist(),
    documents=texts,
    metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]
)

print(f"\nStored {collection.count()} chunks in ChromaDB.")


# ── Retrieval function ────────────────────────────────────────────────────────
def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Retrieve the top-k most relevant chunks for a query."""
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )
    chunks_out = []
    for i in range(len(results["documents"][0])):
        chunks_out.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i]
        })
    return chunks_out


# ── Test retrieval ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        "What is the housing lottery process for transfer students?",
        "Which dining hall do students recommend at UCLA?",
        "What do students say about enrollment appointments for transfers?",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        results = retrieve(query)
        for i, r in enumerate(results):
            print(f"\n[Result {i+1}] Source: {r['source']} | Distance: {r['distance']:.3f}")
            print(r["text"][:300])
