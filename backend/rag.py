# backend/rag.py
# ─────────────────────────────────────────────
# RAG Module — Retrieval Augmented Generation
#
# What it does:
#   1. Loads 70 documents from documents/ folder
#   2. Splits them into chunks of 512 tokens
#   3. Embeds each chunk using sentence-transformers
#   4. Stores embeddings in ChromaDB
#   5. When user asks question — finds top 3 relevant chunks
#   6. Returns chunks to conversation manager to inject into prompt
#
# WHY RAG:
#   LLM only knows what it was trained on.
#   RAG gives it access to our specific university documents.
#   This makes answers more accurate and grounded.
# ─────────────────────────────────────────────

import os
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

# ── CONFIG ────────────────────────────────────
DOCUMENTS_DIR  = "../documents"        # where our 70 docs live
VECTORSTORE_DIR = "../vectorstore"     # where ChromaDB stores embeddings
COLLECTION_NAME = "university_docs"   # name of our collection
CHUNK_SIZE      = 512                  # characters per chunk
CHUNK_OVERLAP   = 50                   # overlap between chunks
TOP_K           = 3                    # number of chunks to retrieve

# ── EMBEDDING MODEL ───────────────────────────
# all-MiniLM-L6-v2 is small (80MB) and fast on CPU
# Converts text into 384-dimensional vectors
# Similar text → similar vectors → easy to find related content
print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded ✅")

# ── CHROMADB SETUP ────────────────────────────
# ChromaDB is a local vector database
# Stores embeddings and lets us search by similarity
client     = chromadb.PersistentClient(path=VECTORSTORE_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}  # cosine similarity for text
)


# ── DOCUMENT CHUNKING ─────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Splits a long document into smaller overlapping chunks.

    WHY CHUNKS:
    LLMs have context window limits. A 512-character chunk
    fits comfortably in the prompt alongside conversation history.

    WHY OVERLAP:
    Overlap ensures important information at chunk boundaries
    is not lost. If a sentence spans two chunks, overlap
    captures it in both.

    Example:
    Text: "ABCDEFGHIJ" with size=4, overlap=1
    Chunks: ["ABCD", "DEFG", "GHIJ"]
    """
    chunks = []
    start  = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():  # skip empty chunks
            chunks.append(chunk.strip())
        start = end - overlap  # move forward with overlap

    return chunks


# ── INDEXING PIPELINE ─────────────────────────

def index_documents() -> int:
    """
    Processes all documents in the documents/ folder:
    1. Reads each .txt file
    2. Splits into chunks
    3. Embeds each chunk
    4. Stores in ChromaDB

    Returns: number of chunks indexed
    WHY RE-RUNNABLE: If documents change, run again to update index.
    """
    docs_path = Path(DOCUMENTS_DIR)

    if not docs_path.exists():
        print(f"Documents folder not found: {DOCUMENTS_DIR}")
        return 0

    # Check if already indexed
    existing = collection.count()
    if existing > 0:
        print(f"Vector store already has {existing} chunks — skipping indexing")
        print("Delete vectorstore/ folder to reindex")
        return existing

    print(f"Indexing documents from {DOCUMENTS_DIR}...")

    all_chunks    = []
    all_ids       = []
    all_metadatas = []
    chunk_id      = 0

    # Process each .txt file
    for doc_path in sorted(docs_path.glob("*.txt")):
        try:
            text = doc_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)

            for chunk in chunks:
                all_chunks.append(chunk)
                all_ids.append(f"chunk_{chunk_id}")
                all_metadatas.append({
                    "source":   doc_path.name,
                    "category": doc_path.stem.split("_")[0]  # e.g. "course", "exam"
                })
                chunk_id += 1

            print(f"  Processed: {doc_path.name} → {len(chunks)} chunks")

        except Exception as e:
            print(f"  Error processing {doc_path.name}: {e}")

    if not all_chunks:
        print("No chunks found!")
        return 0

    # Embed all chunks at once (batch is faster)
    print(f"\nEmbedding {len(all_chunks)} chunks...")
    embeddings = embedder.encode(
        all_chunks,
        show_progress_bar=True,
        batch_size=32
    ).tolist()

    # Store in ChromaDB in batches of 100
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents  = all_chunks[i:i+batch_size],
            embeddings = embeddings[i:i+batch_size],
            ids        = all_ids[i:i+batch_size],
            metadatas  = all_metadatas[i:i+batch_size]
        )

    print(f"\nIndexing complete! {len(all_chunks)} chunks stored in ChromaDB ✅")
    return len(all_chunks)


# ── RETRIEVAL ─────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Finds the most relevant document chunks for a query.

    Steps:
    1. Embed the query using the same model
    2. Search ChromaDB for similar embeddings
    3. Return top_k most similar chunks

    WHY COSINE SIMILARITY:
    Measures the angle between two vectors.
    Similar meaning → small angle → high similarity score.
    Works well for semantic search regardless of text length.

    Returns list of dicts with:
    - text: the chunk content
    - source: which document it came from
    - score: similarity score (0-1, higher is better)
    """
    if collection.count() == 0:
        print("Vector store is empty — run index_documents() first")
        return []

    # Embed the query
    query_embedding = embedder.encode(query).tolist()

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    chunks = []
    for i in range(len(results["documents"][0])):
        distance = results["distances"][0][i]
        score    = 1 - distance  # convert distance to similarity

        chunks.append({
            "text":   results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", "unknown"),
            "score":  round(score, 3)
        })

    return chunks


def format_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a clean context string
    to inject into the LLM prompt.

    WHY FORMATTING MATTERS:
    The LLM needs clear structure to distinguish
    retrieved context from conversation history.
    """
    if not chunks:
        return ""

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']}]\n{chunk['text']}"
        )

    return "\n\n".join(context_parts)


# ── AUTO INDEX ON IMPORT ──────────────────────
# When rag.py is imported, automatically index
# documents if not already done.
print("Checking vector store...")
index_documents()