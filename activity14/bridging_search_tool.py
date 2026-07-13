"""
Bridging Search Tool module for Activity 14.
Implements enhanced document retrieval from the Qdrant vector database using Google Gemini.
Features configurable Query Expansion, Hybrid Search, and LLM Re-ranking.
"""

import os
import re
import time
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from pydantic import BaseModel, Field

# Define and load environment variables
load_dotenv()
from pathlib import Path
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    parent_env_path = Path(__file__).resolve().parent.parent / ".env"
    if parent_env_path.exists():
        load_dotenv(parent_env_path)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found in environment variables.")

# Initialize Google Gemini SDK Client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Resolve Qdrant Host and Port
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
if QDRANT_HOST == "qdrant":
    import socket
    try:
        socket.gethostbyname("qdrant")
    except socket.gaierror:
        QDRANT_HOST = "localhost"

QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "course_memory"

# Initialize Qdrant Client
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Search Pipeline Configurable Flags
USE_QUERY_EXPANSION: bool = True
USE_HYBRID_SEARCH: bool = True
USE_LLM_RERANK: bool = False


def call_gemini_with_retry(api_func, *args, **kwargs):
    """
    Executes a Gemini API function, automatically retrying with exponential backoff
    if rate limit (429 RESOURCE_EXHAUSTED) is encountered.
    """
    max_retries = 6
    backoff = 22.0  # Free tier allows 5 RPM, so we wait 22 seconds between retries/requests
    
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"\n[SYSTEM] Rate limit hit (429). Retrying in {backoff:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(backoff)
                backoff *= 1.5
            else:
                raise e
    raise RuntimeError("Max retries exceeded for Gemini API call due to rate limits.")


def expand_query(query: str) -> str:
    """
    Rewrites a query into a document-style paragraph using gemini-3.1-flash-lite
    only if the query is shorter than 20 tokens.
    
    Args:
        query: The user query string.
        
    Returns:
        The expanded document-style paragraph or the original query.
    """
    query_clean = query.strip()
    if not query_clean:
        return ""

    # Count tokens of the input query
    try:
        token_count = gemini_client.models.count_tokens(
            model="gemini-3.1-flash-lite",
            contents=query_clean
        ).total_tokens
    except Exception as e:
        # Fallback to word splitting count if API fails
        token_count = len(query_clean.split())

    # Skip expansion for longer queries (20 tokens or more)
    if token_count >= 20:
        return query_clean

    # Formulate expansion instruction
    prompt = (
        "You are an expert search assistant. Rewrite the following short query into a single, cohesive, "
        "document-style paragraph containing fact-filled context and descriptive terms that directly answer the query. "
        "Do not write conversational filler, greetings, or introductions. Output only the informative paragraph.\n\n"
        f"Query: {query_clean}"
    )

    try:
        response = call_gemini_with_retry(
            gemini_client.models.generate_content,
            model="gemini-3.1-flash-lite",
            contents=prompt
        )
        expanded_text = response.text.strip()
        if expanded_text:
            return expanded_text
    except Exception as e:
        print(f"[SYSTEM WARNING] Query expansion failed: {str(e)}. Using original query.")
        
    return query_clean


def hybrid_search(query: str, chunks: List[Dict[str, Any]], alpha: float = 0.7) -> Dict[str, Any]:
    """
    Combines dense similarity score and keyword overlap score to rank chunks.
    Formula: Hybrid Score = alpha * dense_score + (1-alpha) * keyword_score
    
    Args:
        query: The user's original query.
        chunks: List of retrieved chunk dictionaries containing "text" and "score".
        alpha: Weight given to dense similarity score (0.0 to 1.0).
        
    Returns:
        The chunk dictionary with the highest hybrid score.
    """
    if not chunks:
        raise ValueError("Cannot perform hybrid search on an empty chunk list.")

    # Lowercase and clean query tokens
    query_clean = query.lower()
    query_words = set(re.findall(r'\b\w+\b', query_clean))

    scored_chunks = []
    for chunk in chunks:
        dense_score = chunk.get("score", 0.0)
        
        # Calculate Keyword Overlap Score (Jaccard similarity style intersection)
        chunk_text = chunk.get("text", "").lower()
        chunk_words = set(re.findall(r'\b\w+\b', chunk_text))
        
        if not query_words:
            keyword_score = 0.0
        else:
            intersection = query_words.intersection(chunk_words)
            keyword_score = len(intersection) / len(query_words)

        hybrid_score = alpha * dense_score + (1.0 - alpha) * keyword_score
        
        scored_chunk = chunk.copy()
        scored_chunk["hybrid_score"] = hybrid_score
        scored_chunk["keyword_score"] = keyword_score
        scored_chunks.append(scored_chunk)

    # Sort chunks in descending order of hybrid score
    scored_chunks.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored_chunks[0]


class BestChunkSelection(BaseModel):
    best_chunk_index: int = Field(
        ..., 
        description="The 0-based index of the chunk that is most relevant to the query."
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this chunk is the most relevant."
    )


def rerank_with_llm(query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses gemini-3.1-flash-lite to re-rank chunks and return the best one.
    Uses structured JSON output matching the BestChunkSelection schema.
    
    Args:
        query: The user's original query.
        chunks: List of retrieved chunk dictionaries containing "text".
        
    Returns:
        The best chunk dictionary selected by the LLM.
    """
    if not chunks:
        raise ValueError("Cannot perform LLM re-ranking on an empty chunk list.")
    
    # Prompt formulation
    prompt = (
        "You are an expert search ranker. Your task is to rank the retrieved document chunks "
        "by their relevance to the user's query and select the best one.\n\n"
        f"[User Query]\n{query}\n\n"
        "[Retrieved Chunks]\n"
    )
    for idx, chunk in enumerate(chunks):
        prompt += f"--- Chunk {idx} ---\n{chunk.get('text', '')}\n\n"

    try:
        response = call_gemini_with_retry(
            gemini_client.models.generate_content,
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BestChunkSelection,
                temperature=0.0,
                system_instruction="You are a strict, objective search re-ranking judge."
            )
        )
        
        result = json.loads(response.text)
        best_idx = result.get("best_chunk_index", 0)
        
        # Guard against index out of bounds
        if 0 <= best_idx < len(chunks):
            return chunks[best_idx]
    except Exception as e:
        print(f"[SYSTEM WARNING] LLM re-ranking failed: {str(e)}. Falling back to top vector search result.")
        
    return chunks[0]


def search_documents(query: str) -> str:
    """
    Search documents for information matching the query using Qdrant vector database.
    Applies configurable query expansion, hybrid search, and LLM re-ranking.
    
    Args:
        query: The search term or topic.
        
    Returns:
        A string formatted as [Found] ... or [Not found] ... or [Error] ...
    """
    # 1. Handle empty query
    query_clean = query.strip()
    if not query_clean:
        return "[Error] Query is empty."

    # 2. Query Expansion (only expand if enabled and short query)
    search_query = query_clean
    if USE_QUERY_EXPANSION:
        search_query = expand_query(query_clean)

    # 3. Generate query embedding using gemini-embedding-2
    try:
        response = call_gemini_with_retry(
            gemini_client.models.embed_content,
            model="gemini-embedding-2",
            contents=search_query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        query_vector = response.embeddings[0].values
    except Exception as e:
        return f"[Error] Embedding generation failed: {str(e)}"

    # 4. Search Qdrant collection 'course_memory'
    try:
        response = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=10,
            with_payload=True
        )
        search_hits = response.points
    except Exception as e:
        return f"[Error] Qdrant connection/search failed: {str(e)}"

    if not search_hits:
        return f"[Not found] No documents matching '{query_clean}' were found in the database."

    # 5. Extract payloads and validate text content
    valid_chunks = []
    for hit in search_hits:
        if not hit.payload:
            continue
        text_segment = hit.payload.get("text")
        if not text_segment:
            continue
        valid_chunks.append({
            "text": text_segment,
            "score": hit.score,
            "filename": hit.payload.get("filename", "Unknown"),
            "chunk_index": hit.payload.get("chunk_index", 0)
        })

    if not valid_chunks:
        return "[Error] Search results are missing text payloads."

    # 6. Apply improvements based on configuration flags
    best_chunk = None
    if USE_LLM_RERANK:
        best_chunk = rerank_with_llm(query_clean, valid_chunks)
    elif USE_HYBRID_SEARCH:
        best_chunk = hybrid_search(query_clean, valid_chunks, alpha=0.7)
    else:
        # Baseline Search: Top dense match
        best_chunk = valid_chunks[0]

    if not best_chunk:
        return f"[Not found] No matching chunks resolved for '{query_clean}'."

    # Return only the text payload of the best chunk, prefixed with [Found] for ReAct loop compatibility
    return f"[Found] {best_chunk['text']}"
