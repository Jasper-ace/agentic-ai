"""
Search Comparison module for Activity 14.
Ingests a fact-based document dataset into Qdrant collection 'course_memory',
runs a 10-query comparison suite, and prints the performance metrics of Baseline Search vs Improved Search.
"""

import os
import uuid
import re
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Import search pipeline configurations and tools
from activity14.bridging_search_tool import (
    gemini_client,
    qdrant_client,
    COLLECTION_NAME,
    search_documents,
    call_gemini_with_retry,
)
import activity14.bridging_search_tool as bst

# Factual dataset to index in Qdrant
DOCUMENTS_DATASET = [
    {
        "filename": "qdrant_info.txt",
        "text": "Qdrant is a production-ready vector database designed for fast similarity search and semantic retrieval of high-dimensional vectors."
    },
    {
        "filename": "chunking_strategies.txt",
        "text": "Chunking is the process of splitting large documents into smaller, cohesive segments before generating embeddings. Standard strategies include fixed-size sliding windows and paragraph-based chunking."
    },
    {
        "filename": "overlap_details.txt",
        "text": "Overlap refers to the shared content between consecutive chunks. It ensures that context and semantics are preserved across chunk boundaries."
    },
    {
        "filename": "embeddings_concept.txt",
        "text": "Embeddings are dense, real-valued vector representations of text where semantically similar words or sentences are positioned closer in vector space."
    },
    {
        "filename": "rag_triad_evaluation.txt",
        "text": "The RAG Triad is an evaluation framework consisting of three core metrics: Context Relevance (is retrieved context relevant to the query?), Groundedness (is the response supported by the retrieved context?), and Answer Relevance (does the response directly address the user's question?)."
    },
    {
        "filename": "react_loop_architecture.txt",
        "text": "The ReAct (Reasoning and Acting) loop is an agent architecture where an LLM cycles through generating Thoughts (reasoning), selecting Actions (tool calls), processing Observations (tool execution), and producing final Answers."
    },
    {
        "filename": "hybrid_search_info.txt",
        "text": "Hybrid Search combines Dense Similarity search with Keyword Overlap search to improve the relevance of retrieved documents by blending semantic meaning and exact keyword matches."
    },
    {
        "filename": "query_expansion_info.txt",
        "text": "Query Expansion is a technique where short user queries are rewritten or expanded into a richer, more detailed document-style paragraph before generating embeddings, which helps in retrieving documents that do not share exact terms with the query."
    },
    {
        "filename": "llm_reranking_info.txt",
        "text": "LLM Re-ranking uses a powerful language model to assess the relevance of the top-N retrieved documents and re-order them, returning the best document chunk to the user."
    },
    {
        "filename": "gemini_structured_outputs.txt",
        "text": "Structured outputs in Gemini are implemented using Pydantic or JSON schema validation, ensuring that the model output strictly conforms to a specified JSON structure."
    }
]

# 10 test queries and their expected answers
TEST_CASES = [
    {
        "query": "What is Qdrant?",
        "expected_answer": "Qdrant is a production-ready vector database designed for fast similarity search and semantic retrieval."
    },
    {
        "query": "Explain chunking strategies.",
        "expected_answer": "Chunking splits large documents into smaller segments using strategies like sliding windows or paragraphs."
    },
    {
        "query": "How does overlap help in document chunking?",
        "expected_answer": "Overlap preserves context and semantics across chunk boundaries."
    },
    {
        "query": "What are dense embeddings?",
        "expected_answer": "Embeddings are dense vector representations of text where semantically similar items are positioned closer."
    },
    {
        "query": "What is the RAG Triad?",
        "expected_answer": "The RAG Triad evaluates Context Relevance, Groundedness, and Answer Relevance."
    },
    {
        "query": "How does a ReAct loop work?",
        "expected_answer": "A ReAct loop cycles through Thoughts, Actions, Observations, and producing final Answers."
    },
    {
        "query": "What is hybrid search?",
        "expected_answer": "Hybrid Search combines Dense Similarity search with Keyword Overlap search."
    },
    {
        "query": "Explain query expansion.",
        "expected_answer": "Query Expansion rewrites short queries into richer paragraphs before embedding."
    },
    {
        "query": "What is LLM re-ranking?",
        "expected_answer": "LLM Re-ranking uses an LLM to assess and re-order the top retrieved documents."
    },
    {
        "query": "How do you enforce structured outputs in Gemini?",
        "expected_answer": "Structured outputs are enforced using Pydantic or JSON schema validation."
    }
]


def setup_and_index_qdrant() -> None:
    """
    Creates the 'course_memory' Qdrant collection if it does not exist,
    generates embeddings for the dataset, and upserts the points.
    """
    print("\n[SETUP] Checking Qdrant collection 'course_memory'...")
    try:
        collections = qdrant_client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        
        # If collection exists, we can delete and recreate to ensure clean data
        if exists:
            print(f"[SETUP] Collection '{COLLECTION_NAME}' exists. Recreating to ensure clean dataset...")
            qdrant_client.delete_collection(COLLECTION_NAME)
            
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        print(f"[SETUP] Created collection '{COLLECTION_NAME}' successfully.")
        
        # Index the dataset
        points = []
        for idx, doc in enumerate(DOCUMENTS_DATASET):
            print(f"[SETUP] Generating embedding for chunk {idx+1}/{len(DOCUMENTS_DATASET)}: '{doc['filename']}'")
            
            # Generate embedding using gemini-embedding-2
            response = call_gemini_with_retry(
                gemini_client.models.embed_content,
                model="gemini-embedding-2",
                contents=doc["text"],
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            embedding = response.embeddings[0].values
            
            # Add to points list
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "filename": doc["filename"],
                    "chunk_index": idx,
                    "text": doc["text"]
                }
            ))
            
        # Upsert all points
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"[SETUP] Indexed {len(points)} document chunks into '{COLLECTION_NAME}' successfully.\n")
        
    except Exception as e:
        print(f"[SETUP ERROR] Failed to set up Qdrant: {str(e)}")
        raise e


def evaluate_hit_relevance(query: str, expected_answer: str, retrieved_hit: str) -> str:
    """
    Uses gemini-3.1-flash-lite to judge if the retrieved search hit satisfies the expected answer.
    Returns 'YES' or 'NO'.
    """
    if "Error" in retrieved_hit or "Not found" in retrieved_hit:
        return "NO"

    # Clean retrieved hit prefix
    retrieved_content = retrieved_hit.replace("[Found]", "").strip()

    prompt = (
        "You are a strict, objective evaluation judge.\n"
        "Your task is to determine if the retrieved document chunk contains the key information "
        "necessary to satisfy or support the expected answer for the given query.\n\n"
        f"[User Query]: {query}\n"
        f"[Expected Answer]: {expected_answer}\n"
        f"[Retrieved Chunk]: {retrieved_content}\n\n"
        "Instructions:\n"
        "- Reply YES if the retrieved chunk contains the concepts described in the expected answer.\n"
        "- Reply NO if it does not contain the key concepts or is unrelated.\n"
        "- Output ONLY 'YES' or 'NO' and nothing else. Do not provide reasoning."
    )

    try:
        response = call_gemini_with_retry(
            gemini_client.models.generate_content,
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        judgment = response.text.strip().upper()
        if "YES" in judgment:
            return "YES"
    except Exception as e:
        print(f"[EVAL WARNING] Judge LLM call failed: {str(e)}")
        
    return "NO"


def run_comparison() -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Runs the 10 test queries against both Baseline Search and Improved Search.
    Returns baseline accuracy, improved accuracy, and detailed results list.
    """
    results = []
    baseline_correct = 0
    improved_correct = 0

    print("======================================================================")
    print("                    RUNNING SEARCH COMPARISON SUITE                   ")
    print("======================================================================")

    for idx, case in enumerate(TEST_CASES, 1):
        query = case["query"]
        expected = case["expected_answer"]
        print(f"\nQuery {idx}: '{query}'")

        # 1. Run Baseline Search (All improvements disabled)
        bst.USE_QUERY_EXPANSION = False
        bst.USE_HYBRID_SEARCH = False
        bst.USE_LLM_RERANK = False
        
        try:
            baseline_hit = search_documents(query)
        except Exception as e:
            baseline_hit = f"[Error] {str(e)}"
            
        baseline_result = evaluate_hit_relevance(query, expected, baseline_hit)
        if baseline_result == "YES":
            baseline_correct += 1

        # 2. Run Improved Search (Query Expansion, Hybrid Search, and LLM Re-ranking enabled)
        bst.USE_QUERY_EXPANSION = True
        bst.USE_HYBRID_SEARCH = True
        bst.USE_LLM_RERANK = True
        
        try:
            improved_hit = search_documents(query)
        except Exception as e:
            improved_hit = f"[Error] {str(e)}"

        improved_result = evaluate_hit_relevance(query, expected, improved_hit)
        if improved_result == "YES":
            improved_correct += 1

        print(f"  -> Baseline Result: {baseline_result} | Hit: {baseline_hit[:60]}...")
        print(f"  -> Improved Result: {improved_result} | Hit: {improved_hit[:60]}...")

        results.append({
            "idx": idx,
            "query": query,
            "expected": expected,
            "baseline_hit": baseline_hit,
            "improved_hit": improved_hit,
            "baseline_result": baseline_result,
            "improved_result": improved_result
        })

    baseline_accuracy = (baseline_correct / len(TEST_CASES)) * 100.0
    improved_accuracy = (improved_correct / len(TEST_CASES)) * 100.0

    return baseline_accuracy, improved_accuracy, results


def display_comparison_table(
    baseline_acc: float, 
    improved_acc: float, 
    results: List[Dict[str, Any]]
) -> None:
    """Prints a formatted ASCII markdown table of the comparison results."""
    print("\n" + "=" * 100)
    print(f"{'SEARCH COMPARISON RESULTS TABLE':^100}")
    print("=" * 100)
    print(f"{'No.':<3} | {'Query':<35} | {'Baseline Hit?':<15} | {'Improved Hit?':<15}")
    print("-" * 100)
    for r in results:
        # Truncate queries for readability
        q_trunc = r["query"] if len(r["query"]) <= 33 else r["query"][:30] + "..."
        print(f"{r['idx']:<3} | {q_trunc:<35} | {r['baseline_result']:<15} | {r['improved_result']:<15}")
    print("-" * 100)
    print(f"Baseline Search Accuracy: {baseline_acc:.1f}%")
    print(f"Improved Search Accuracy: {improved_acc:.1f}%")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    # Setup database
    setup_and_index_qdrant()
    
    # Run evaluations
    baseline_acc, improved_acc, results = run_comparison()
    
    # Display summary
    display_comparison_table(baseline_acc, improved_acc, results)
