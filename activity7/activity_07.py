import os
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

COLLECTION_NAME = "activity7_memory"
VECTOR_SIZE = 8

SOURCE_TEXT = """
Qdrant is a vector database designed for similarity search and retrieval.

Chunking is the process of dividing a document into smaller pieces before embedding.
If a chunk is too large, it may contain too much unrelated information.
If a chunk is too small, it may lose the surrounding context needed for the answer.

Overlap helps preserve meaning when a sentence or idea crosses a boundary.
Metadata such as source, section, and strategy makes debugging easier.
"""


# -----------------------------
# Fixed-size Chunking
# -----------------------------
def fixed_size_chunk(text: str, chunk_size: int = 140, overlap: int = 30) -> list[str]:
    """Split text into overlapping character windows."""
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # stop when we've reached the end
        if end == len(text):
            break

        start = end - overlap

    return chunks


# -----------------------------
# Paragraph Chunking
# -----------------------------
def paragraph_chunk(text: str) -> list[str]:
    """Split text on blank lines."""
    regex_pattern = r"\n\s*\n"

    paragraphs = [
        p.strip()
        for p in re.split(regex_pattern, text)
        if p.strip()
    ]

    return paragraphs


# -----------------------------
# Embedding Generator
# -----------------------------
def embed_text(text: str) -> list[float]:
    vocab = [
        "qdrant",
        "chunking",
        "embedding",
        "overlap",
        "metadata",
        "retrieval",
        "context",
        "vector",
    ]

    lowered = text.lower()

    vector = [
        float(lowered.count(word))
        for word in vocab
    ]

    norm = sum(v * v for v in vector) ** 0.5

    if norm == 0:
        return [0.0] * len(vector)

    return [v / norm for v in vector]


# -----------------------------
# Store Chunks
# -----------------------------
def store_chunks(client, collection_name, chunks, strategy, start_id):
    points = []

    for index, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=start_id + index,
                vector=embed_text(chunk),
                payload={
                    "text": chunk,
                    "strategy": strategy,
                    "chunk_index": index,
                    "source": "sample_doc",
                },
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points,
    )


# -----------------------------
# Query
# -----------------------------
def retrieve_best_match(client, collection_name, query_vector):
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=1,
        with_payload=True,
        with_vectors=False,
    )

    if result.points:
        return result.points[0]

    return None


# -----------------------------
# Main
# -----------------------------
def main():

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333")
    )

    # Delete old collection
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        client.delete_collection(collection_name=COLLECTION_NAME)

    # Create collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    fixed_chunks = fixed_size_chunk(SOURCE_TEXT)
    paragraph_chunks = paragraph_chunk(SOURCE_TEXT)

    print("----- Fixed-size Chunks -----")
    for i, chunk in enumerate(fixed_chunks):
        print(f"{i}:")
        print(chunk)
        print()

    print("----- Paragraph Chunks -----")
    for i, chunk in enumerate(paragraph_chunks):
        print(f"{i}:")
        print(chunk)
        print()

    # Integer IDs
    store_chunks(
        client,
        COLLECTION_NAME,
        fixed_chunks,
        "fixed_size",
        start_id=0,
    )

    store_chunks(
        client,
        COLLECTION_NAME,
        paragraph_chunks,
        "paragraph",
        start_id=100,
    )

    query_text = "Why does overlap help when chunking a document?"
    query_vector = embed_text(query_text)

    match = retrieve_best_match(
        client,
        COLLECTION_NAME,
        query_vector,
    )

    print("\nQuery:")
    print(query_text)

    if match:
        payload = match.payload

        print("\nBest Match Strategy:")
        print(payload["strategy"])

        print("Chunk Index:")
        print(payload["chunk_index"])

        print("\nRetrieved Text:")
        print(payload["text"])
    else:
        print("No matching chunk found.")


if __name__ == "__main__":
    main()