# Architecture Comparison: ReAct Chatbot vs. LangGraph StateGraph

This document provides a comparative analysis of the Week 5 ReAct chatbot architecture and the Week 6 LangGraph implementation.

---

## 1. ASCII Architecture Diagrams

### Week 5 ReAct Loop Architecture

The ReAct (Reasoning and Acting) loop cycles sequentially through Thought, Action, and Observation within a single LLM context window until a final answer or max iterations is reached.

```
       +---------------------------------------------+
       |                  User Query                 |
       +---------------------------------------------+
                              |
                              v
                +---------------------------+
                |    LLM Reasoning Step     | <-----+
                +---------------------------+       |
                 /                         \        |
                / (No Tool Call)            \       | (Observation)
               v                             v      |
       +--------------+               +-----------+ |
       | Final Answer |               | Tool Call | |
       +--------------+               +-----------+ |
                                             |      |
                                             v      |
                                      +-----------+ |
                                      | Tool Exec |-+
                                      +-----------+
```

---

### Week 6 LangGraph StateGraph Architecture

The LangGraph architecture separates reasoning, evaluation, and query refinement into discrete state nodes. It implements a structured feedback loop driven by external LLM judges and conditional routing.

```
                  +---------------------------+
                  |         User Query        |
                  +---------------------------+
                                |
                                v
                  +---------------------------+
                  |       generate_node       | <---------------+
                  +---------------------------+                 |
                                |                               |
                                v                               |
                  +---------------------------+                 |
                  |       evaluate_node       |                 |
                  |    (3 RAG Triad Judges)   |                 |
                  +---------------------------+                 |
                                |                               |
                                v                               |
                  +---------------------------+                 |
                  |       should_retry()      | (rewrite)       |
                  |    (Conditional Router)   |-----------> +-----------+
                  +---------------------------+             |  rewrite  |
                                |                           |   node    |
                                | (accept /                 +-----------+
                                |  accept_maxed)
                                v
                             [ END ]
```

---

## 2. ReAct vs. LangGraph Comparison Table

| Dimension | ReAct Chatbot (Week 5) | LangGraph StateGraph (Week 6) |
| :--- | :--- | :--- |
| **State Management** | Implicitly kept in the LLM's conversational text history / prompt transcript. | Explicitly defined in a typed schema (`AgentState`), decoupled from the prompt context. |
| **Control Flow** | Dynamic and autonomous; the LLM determines when to call tools and when to exit. | Deterministic graph-based flow; routing is controlled by code logic (`should_retry`). |
| **Self-Correction** | Prompt-driven self-correction. If evaluations fail, feedback is appended as user messages. | Edge-driven loop; failures steer execution to a query-rewriting node before restarting retrieval. |
| **Tool Execution** | Directly invoked during the loop whenever the LLM outputs a function call. | Integrated either as independent nodes or encapsulated within nodes (e.g., retrieval in `generate_node`). |
| **Debugging** | Harder; requires parsing unstructured text transcripts to find thoughts, actions, and observations. | Highly structured; execution path can be logged, visualized as a graph, and inspected state-by-state. |

---

## 3. Five-Question Trace Comparison

Here is an analysis of how both architectures handle five representative queries:

### Question 1: "What is ReAct?" (Direct Match)
*   **ReAct Loop**: 
    1. Thought: Needs definition of ReAct loop. Calls `search_documents("What is ReAct?")`.
    2. Observation: `[Found] The ReAct (Reasoning and Acting) loop is an agent architecture...`
    3. Thought: Has info. Formulates final answer.
*   **LangGraph**:
    1. `generate_node`: Search returns correct context. Gemini generates definition.
    2. `evaluate_node`: Scores context relevance (1.0), groundedness (1.0), and answer relevance (1.0).
    3. `should_retry`: All scores >= 0.7. Route decision is `"accept"`. Graph ends.

### Question 2: "What is the travel budget?" (No Data Available)
*   **ReAct Loop**:
    1. Thought: Needs travel budget. Calls `search_documents("What is the travel budget?")`.
    2. Observation: `[Not Found] ...`
    3. Thought: No info available. Formulates final answer noting lack of info.
*   **LangGraph**:
    1. `generate_node`: Search returns `[Not Found]`. Gemini answers stating no budget is found.
    2. `evaluate_node`: Context relevance is 0.0 (empty context). Groundedness is 1.0 (truthful to empty context). Answer relevance is 1.0.
    3. `should_retry`: Context relevance < 0.7. Route decision is `"rewrite"`.
    4. `rewrite_node`: Rewrites to "travel budget details course data".
    5. `generate_node` (Iter 2): Search still fails.
    6. `evaluate_node` (Iter 2): Scores fail threshold. Decision is `"rewrite"`.
    7. `rewrite_node` (Iter 2): Rewrites again.
    8. `generate_node` (Iter 3): Search fails.
    9. `evaluate_node` (Iter 3): Max iterations reached. Decision is `"accept_maxed"`. Graph ends.

### Question 3: "What did we learn about chunking?" (Direct Match)
*   **ReAct Loop**:
    1. Thought: Calls `search_documents("What did we learn about chunking?")`.
    2. Observation: `[Found] Chunking is the process of splitting large documents...`
    3. Thought: Formulates answer and terminates.
*   **LangGraph**:
    1. `generate_node`: Search retrieves chunking definition. Gemini generates final answer.
    2. `evaluate_node`: Scores: context relevance (1.0), groundedness (1.0), answer relevance (1.0).
    3. `should_retry`: Decision is `"accept"`. Graph ends.

### Question 4: "Tell me about that thing from class" (Vague Query)
*   **ReAct Loop**:
    1. Thought: Query is vague. Calls `clarify("Could you please specify which topic from class you mean?")`.
    2. Observation: `[Clarify] ...`
    3. Loop terminates or waits for user reply.
*   **LangGraph**:
    1. `generate_node`: Search retrieves `[Not Found]` because query is vague. Gemini gives a vague/generic answer.
    2. `evaluate_node`: Judges score context relevance low (~0.1).
    3. `should_retry`: Route decision is `"rewrite"`.
    4. `rewrite_node`: Gemini rewrites to a more search-friendly query (e.g. "RAG agent architecture course details").
    5. `generate_node` (Iter 2): Search tries with rewritten query. Might find "react loop" or "qdrant" if rewritten contains them.
    6. `evaluate_node`: Re-evaluates. If scores pass, terminates; otherwise continues to max iterations (3) and exits with `"accept_maxed"`.

### Question 5: "Do the stuff" (Extremely Vague Query)
*   **ReAct Loop**:
    1. Thought: Query is nonsensical. Calls `clarify("Could you please specify what action or task you want me to perform?")`.
    2. Observation: `[Clarify] ...`
    3. Agent pauses.
*   **LangGraph**:
    1. `generate_node`: Retrieval fails. Gemini generates a polite error message.
    2. `evaluate_node`: Evaluators score context relevance as 0.0.
    3. `should_retry`: Route decision is `"rewrite"`.
    4. `rewrite_node`: Attempts to expand/rewrite query to something class-related.
    5. Loops up to 3 times, fails to find relevant text, and terminates on the 3rd iteration with `"accept_maxed"`.

---

## 4. Failure Analysis

*   **Vague Queries in LangGraph**: LangGraph does not naturally handle interactive user clarification unless a `clarify` node is specifically wired to wait for user input (interrupts). Without interrupts, the rewrite node tries to guess the user's intent, leading to a loop of 3 iterations that eventually outputs a fallback answer.
*   **State Bloat**: In LangGraph, if state contains raw document chunks and entire histories, memory usage grows over multiple turns. However, it keeps the prompt window clean by separating logs from the generation prompt.
*   **Judges Inconsistencies**: LLM judges can sometimes be overly strict or lenient. For example, a grounded answer might receive a `0.6` groundedness score due to minor phrasing differences, triggering an unnecessary query rewrite.

---

## 5. Advantages & Disadvantages

### ReAct Chatbot (Week 5)
*   **Advantages**:
    *   Highly flexible; can decide on-the-fly to clarify, compute, or search.
    *   Natural multi-turn conversation support with minimal setup.
*   **Disadvantages**:
    *   Prone to getting stuck in loops (e.g., calling the same tool repeatedly).
    *   Prompt context window gets filled with internal reasoning, inflating token usage and cost.

### LangGraph StateGraph (Week 6)
*   **Advantages**:
    *   Highly structured and predictable execution flow.
    *   Robust quality assurance using LLM judges.
    *   Saves token costs by excluding internal reasoning from the conversational history.
*   **Disadvantages**:
    *   Higher latency due to multiple sequential LLM calls (generation + 3 judges + rewrite per iteration).
    *   Less conversational flexibility; requires explicit graph configurations to handle interrupts or tool switches.
