# Reflection

## Checkpoint 1: Visualizing Boundaries

If a document is exactly **200 characters** long, with a **chunk size of 100** and an **overlap of 20**:

* **First chunk:** **[0, 100]**
* **Second chunk:** **[80, 180]**

The second chunk starts at character **80** because it overlaps the previous chunk by **20 characters**.

---

## Final Critical Reflection Checkpoints

### 1. Which chunking strategy returned the most relevant text for your query? Did it capture the entire sentence context or was it cut off?

The query returned a **Fixed-Size** chunk as the best match because it contained the keyword **"overlap."** However, the retrieved text was **cut off** at the end of the sentence, ending with *"Overlap helps preserve meaning when a sent"*. Although it matched the query, it did not capture the complete sentence, showing one disadvantage of fixed-size chunking.

### 2. What happened to the text structure in Fixed-Size Chunk #2 vs. Paragraph Chunk #2? Identify how boundaries changed word availability.

In **Fixed-Size Chunk #2**, the text was split based only on character count, causing words and sentences to be cut in the middle. This resulted in incomplete information and reduced readability. In contrast, **Paragraph Chunk #2** preserved the complete paragraph, keeping all related sentences together. This maintained the original structure of the document and provided better context for retrieval.

### 3. Hypothetical Application: Imagine you are building a production AI system for a company's internal HR manual handbook. Why might relying exclusively on Fixed-Size character chunking create bad answers for employees?

Using only fixed-size chunking could cause important policies or procedures to be split across multiple chunks. As a result, the AI might retrieve only part of a policy, leading to incomplete or misleading answers. Employees could receive incorrect guidance if essential details are missing because the sentence or paragraph was divided in the middle. Using paragraph-based or semantic chunking would preserve context and improve the accuracy of responses.

### 4. The Metadata Payload: Why do we spend computing effort storing things like `chunk_index` and `strategy` inside the database alongside raw vectors? Why can't we just store the text string alone?

Metadata provides important information about each stored chunk. The `chunk_index` identifies the original position of the chunk in the document, while the `strategy` records how it was created. This information makes it easier to debug retrieval results, compare different chunking methods, trace the source of retrieved content, and reconstruct the original document if necessary. If only the text string were stored, it would be much harder to understand where the information came from or analyze why a particular chunk was retrieved.

