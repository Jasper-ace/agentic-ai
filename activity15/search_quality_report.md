# Search Quality Report - Activity 14: Bridging Memory and Action

This report analyzes the performance, advantages, and trade-offs of the search pipeline enhancements implemented for the `course_memory` Qdrant collection, comparing a **Baseline Search** (pure dense retrieval) against an **Improved Search** (Query Expansion + Hybrid Search + LLM Re-ranking).

---

## 1. Improvements Chosen & Rationale

We selected three distinct search optimization techniques to bridge the gap between user intent (queries) and vector database contents (documents):

1. **Query Expansion**
   - **Mechanism**: Rewrites short queries (< 20 tokens) into a detailed, fact-filled, document-style paragraph using `gemini-3.1-flash-lite`.
   - **Rationale**: Short queries (e.g., "What is hybrid search?") lack semantic context and vocabulary richness. Expanding them into a document-like structure aligns the query's vocabulary and style with the indexed chunks, improving dense vector match alignment.
2. **Hybrid Search**
   - **Mechanism**: Blends the Cosine Similarity score from the dense embedding model (`gemini-embedding-2`) and a Keyword Overlap score based on word token intersection.
     $$\text{Hybrid Score} = \alpha \cdot \text{Dense Score} + (1 - \alpha) \cdot \text{Keyword Score} \quad (\alpha = 0.7)$$
   - **Rationale**: Pure vector search is highly semantic but can sometimes overlook exact term matches (e.g., acronyms, specific function names, or terminology). Keyword overlap ensures that documents containing the exact terms from the query are boosted.
3. **LLM Re-ranking**
   - **Mechanism**: Retrieves the top 10 candidates, extracts their text payloads, and asks `gemini-3.1-flash-lite` to rank them by relevance, returning the single best chunk.
   - **Rationale**: Embedding models compress information into high-dimensional space, which can lose fine-grained details. An LLM, when presented with the actual text of the top-N candidates, can evaluate precise contextual relevance and filter out semantic "near-misses".

---

## 2. Accuracy Comparison Table

Both search pipelines were evaluated on 10 test queries mapped against the expected facts from the knowledge base. The grading was performed by an objective judge using `gemini-3.1-flash-lite`.

| No. | Query | Baseline Hit? | Improved Hit? | Expected Fact Retrieved |
|:---:|:---|:---:|:---:|:---|
| 1 | What is Qdrant? | **YES** | **YES** | Qdrant vector database definition |
| 2 | Explain chunking strategies. | **YES** | **YES** | Text chunking concept and methods |
| 3 | How does overlap help in document chunking? | **YES** | **YES** | preservance of context across chunks |
| 4 | What are dense embeddings? | **YES** | **YES** | Dense representation in vector space |
| 5 | What is the RAG Triad? | **YES** | **YES** | RAG Triad metrics (Relevance, Groundedness) |
| 6 | How does a ReAct loop work? | **YES** | **YES** | Reasoning and Acting cycle (Thought, Action) |
| 7 | What is hybrid search? | **YES** | **YES** | Combination of dense and keyword search |
| 8 | Explain query expansion. | **YES** | **YES** | Rewriting query before embedding |
| 9 | What is LLM re-ranking? | **YES** | **YES** | LLM-based re-ordering of top chunks |
| 10 | How do you enforce structured outputs in Gemini? | **YES** | **YES** | Pydantic/JSON schema validation |

### Overall Accuracy Summary
- **Baseline Search Accuracy**: **100.0%**
- **Improved Search Accuracy**: **100.0%**

---

## 3. Root Cause Analysis

### Why Baseline Search Performed at 100% Accuracy
1. **Model Strength**: `gemini-embedding-2` is an advanced embedding model that captures semantics exceptionally well. Even without query expansion or keyword matching, it easily associated keywords like "overlap", "chunking", and "ReAct" with their respective document paragraphs.
2. **Distinct Dataset**: The test collection consists of 10 highly distinct, non-overlapping conceptual topics. There was little semantic overlap or ambiguity between "Safe math calculation" and "Qdrant vector database", allowing standard cosine similarity to easily score the correct document highest.

### When Improved Search Becomes Critical
In larger, noisier production datasets, the baseline accuracy typically drops due to:
- **Vocabulary Mismatch**: Users asking questions using synonyms not present in the index (where **Query Expansion** shines by injecting relevant synonyms).
- **Keyword Specificity**: Specific IDs, numbers, or unique terms (where **Hybrid Search** guarantees exact-term retrieval).
- **Distractors**: Multiple chunks having similar vector representations but only one being contextually relevant (where **LLM Re-ranking** performs deep contextual reasoning).

---

## 4. Trade-offs

Implementing search improvements introduces trade-offs between retrieval quality, latency, and cost:

| Search Component | Accuracy Impact | Latency Overhead | API Cost (Tokens) | Complexity |
|:---|:---:|:---:|:---:|:---|
| **Baseline Search** | Moderate | Low (~100-200ms) | Low (embedding only) | Simple |
| **Query Expansion** | High (for short queries) | Medium (+500-1000ms) | Low (Gemini Input/Output) | Low |
| **Hybrid Search** | High (for keyword matching) | Low (+5-10ms) | Zero (computed locally) | Medium |
| **LLM Re-ranking** | High (filters noise) | High (+1000-2000ms) | Medium (Gemini context input) | High |

---

## 5. Conclusion

For small, clean conceptual datasets, **Baseline Search** using `gemini-embedding-2` is extremely effective and delivers sub-second response times. However, for complex production systems with noisy document corpuses, combining **Query Expansion**, **Hybrid Search**, and **LLM Re-ranking** is highly recommended to guarantee precision, even though it introduces extra latency and cost.
