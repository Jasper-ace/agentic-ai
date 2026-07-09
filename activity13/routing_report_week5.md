# Week 5 Project Routing & Evaluation Report

**Course**: Advanced Agentic Systems & Software Architecture  
**Topic**: ReAct Loop, Native Tool Routing, & Self-Correcting RAG Triad Evaluators  
**Date**: July 2026  

---

## 1. Executive Summary

This report documents the design, implementation, and evaluation of the Week 5 Project. The project implements a robust, state-of-the-art **Reasoning and Acting (ReAct) loop** integrated with native Google Gemini Function Calling, a safe arithmetic evaluator, a vector-database-ready mock retrieval mechanism, and an automated **RAG Triad evaluation pipeline** featuring autonomous self-correction.

During evaluation on our 10-case routing test suite, the agent achieved **100% routing accuracy**, successfully identifying when to search documents, evaluate mathematics, or seek clarification. Furthermore, the RAG Triad evaluation system successfully validated answers and ran corrective loops when needed, achieving high scores in Context Relevance, Groundedness, and Answer Relevance.

---

## 2. Tool Routing Results Table

The following table details the routing test suite results:

| Test No. | Category | Query | Expected Tool | Actual Tool | Correct |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Factual Questions | "What is chunking in RAG?" | `search_documents` | `search_documents` | **YES** |
| **2** | Factual Questions | "Can you explain what overlap means in document processing?" | `search_documents` | `search_documents` | **YES** |
| **3** | Factual Questions | "What are dense embeddings?" | `search_documents` | `search_documents` | **YES** |
| **4** | Math Questions | "Calculate 15% of 200" | `calculate` | `calculate` | **YES** |
| **5** | Math Questions | "What is 100 + (25 * 4)?" | `calculate` | `calculate` | **YES** |
| **6** | Math Questions | "Compute 5 ** 3" | `calculate` | `calculate` | **YES** |
| **7** | Greetings | "Hello! Good morning." | `clarify` | `clarify` | **YES** |
| **8** | Ambiguous Questions | "What is the status of that task?" | `clarify` | `clarify` | **YES** |
| **9** | Ambiguous Questions | "How do I do that thing we talked about?" | `clarify` | `clarify` | **YES** |
| **10** | Multi-step Questions | "Tell me what Qdrant is and then calculate 20 * 5." | `search_documents` | `search_documents` | **YES** |

### Summary Statistics:
- **Total Test Cases**: 10
- **Successful Routings**: 10
- **Target Routing Accuracy**: 80.0%
- **Actual Routing Accuracy**: **100.0%**

---

## 3. Failure Analysis & Mitigation

While the final routing accuracy reached 100%, several critical design considerations and potential failure modes were addressed during implementation:

1. **Free-Tier Rate Limits (429 RESOURCE_EXHAUSTED)**
   - *Problem*: The Gemini API free tier restricts traffic to 5 Requests Per Minute (RPM). Running the test suite sequentially triggered rate limit exceptions instantly.
   - *Mitigation*: Implemented a robust wrapper `call_with_retry` in `config.py`. It uses exponential backoff and sleeps (22 seconds default) to guarantee rate limit compliance and prevent crash-outs.

2. **Under-routing & Over-routing in Multi-step Queries**
   - *Problem*: In multi-step queries like *"Tell me what Qdrant is and then calculate 20 * 5"*, the model may decide to answer using internal knowledge rather than calling the tool.
   - *Mitigation*: Formulated clean, directive docstrings in `tools.py` and set a precise `SYSTEM_INSTRUCTION` in `project_react_loop.py` to enforce step-by-step tool utilization.

3. **Safe Evaluation vs. Arbitrary Code Execution**
   - *Problem*: Using Python's built-in `eval()` opens the door to severe code injection vulnerabilities.
   - *Mitigation*: Built a strict AST-based evaluator (`safe_eval_ast`) inside `tools.py`. It explicitly parses expressions into an Abstract Syntax Tree and recursively evaluates only allowed math nodes (`ast.BinOp`, `ast.Constant`, etc.), rejecting any malicious functions or identifiers.

---

## 4. Architectural Reflection & Next Steps

The project's modular design decouples the API configurations, tools, loop runner, and testing suites. This ensures high maintainability:
- **Mock DB Decoupling**: The mock database is structured as a dictionary in `tools.py`. Upgrading this to a vector index (e.g., Qdrant) only requires swapping the internals of `search_documents` without altering the ReAct loop logic or evaluation configurations.
- **Structured RAG Evaluation**: The RAG Triad judge utilizes Gemini's native structured JSON formatting with a Pydantic model (`TriadScores`), guaranteeing type-safe evaluations.
- **Autonomous Feedback Loop**: Implementing a self-correcting prompt allows the agent to self-heal when answers fall short of relevance or groundedness, mirroring production RAG guardrails.
