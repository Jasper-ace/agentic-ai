"""
Activity 16 LangGraph Implementation.
Migrates the Week 5 ReAct chatbot into a LangGraph StateGraph architecture.
Features:
- Structured AgentState TypedDict
- generate_node, evaluate_node, rewrite_node
- Reusable judge_metric function using Pydantic BaseModel for structured validation
- Fast port check for Qdrant and fallback to Mock Knowledge Base
- Extensive diagnostic logging for all iterations
"""

import os
import sys
import json
import socket
from typing import TypedDict, List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

# Ensure root workspace is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

# Import existing tools and configurations
from activity16.tools import calculate, clarify, search_documents, MOCK_KNOWLEDGE_BASE
from activity16.config import client, call_with_retry

# Check model support dynamically at startup
def get_supported_model() -> str:
    """
    Checks if gemini-2.0-flash is available and has quota.
    If not, falls back to gemini-3.1-flash-lite.
    """
    load_dotenv()
    try:
        # A minimal call to verify availability
        client.models.generate_content(
            model="gemini-2.0-flash",
            contents="health check",
            config=types.GenerateContentConfig(max_output_tokens=1)
        )
        return "gemini-2.0-flash"
    except Exception:
        # If it raises quota/other issues, return the fallback
        return "gemini-3.1-flash-lite"

# Use gemini-2.0-flash as specified, with fallback to gemini-3.1-flash-lite
MODEL_NAME = get_supported_model()
print(f"[SYSTEM] Using active model: {MODEL_NAME}")


# Define the TypedDict AgentState
class AgentState(TypedDict):
    """
    State representing the agent's memory during execution.
    """
    question: str
    original_question: str
    retrieved_chunk: str
    answer: str
    context_relevance: float
    groundedness: float
    answer_relevance: float
    iteration: int
    log: List[Dict[str, Any]]
    route_decision: str


# Pydantic schema for judge evaluations
class JudgeScore(BaseModel):
    """
    Structured model to enforce schema for LLM judges.
    """
    score: float = Field(
        ...,
        description="The evaluation score between 0.0 (completely failing/irrelevant) and 1.0 (perfect/complete)."
    )
    reasoning: str = Field(
        ...,
        description="Detailed explanation of the rating and why this score was assigned."
    )


def is_qdrant_running() -> bool:
    """
    Checks if a local Qdrant server is running on localhost:6333.
    """
    try:
        with socket.create_connection(("localhost", 6333), timeout=0.2):
            return True
    except Exception:
        return False


def retrieve_context(query: str) -> str:
    """
    Attempts to retrieve context using Qdrant search if it is online.
    If Qdrant is down or no documents are found, falls back to a keyword-matching
    mechanism over the local MOCK_KNOWLEDGE_BASE to ensure the demo is functional.
    
    Args:
        query: The search query.
        
    Returns:
        The retrieved text context or a not found message.
    """
    if is_qdrant_running():
        try:
            result = search_documents(query)
            if result.startswith("[Found]"):
                return result
        except Exception as e:
            result = f"[Error] Qdrant search failed: {e}"
    else:
        result = "[Error] Qdrant is offline."
        
    # Fallback to keyword-based retrieval from MOCK_KNOWLEDGE_BASE
    query_lower = query.lower()
    for key, text in MOCK_KNOWLEDGE_BASE.items():
        # Check if the mock key is in the query, or if any word matches
        if key in query_lower or any(word in query_lower for word in key.split() if len(word) > 3):
            print(f"[SYSTEM FALLBACK] Qdrant is offline or returned error. Matching keyword '{key}' in Mock KB.")
            return f"[Found] {text}"
            
    return result


def judge_metric(metric_name: str, prompt: str) -> JudgeScore:
    """
    Evaluates a specific metric using Gemini 2.0 Flash with structured output.
    
    Args:
        metric_name: The name of the metric being evaluated.
        prompt: The evaluation prompt containing inputs.
        
    Returns:
        A JudgeScore containing the score and reasoning.
    """
    system_instruction = (
        f"You are a strict, objective AI evaluation judge grading the '{metric_name}' metric. "
        "Provide a score between 0.0 and 1.0, and a concise reason."
    )
    
    try:
        response = call_with_retry(
            client.models.generate_content,
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JudgeScore,
                temperature=0.0,
                system_instruction=system_instruction
            )
        )
        data = json.loads(response.text)
        return JudgeScore(**data)
    except Exception as e:
        print(f"[SYSTEM WARNING] Judge for '{metric_name}' failed: {e}. Using fallback score 0.0.")
        return JudgeScore(score=0.0, reasoning=f"Judge failed: {str(e)}")


def generate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that retrieves context and generates an initial/updated answer.
    
    Args:
        state: The current AgentState.
        
    Returns:
        Updates for AgentState.
    """
    query = state["question"]
    print(f"\n--- [NODE] generate_node (Iteration {state.get('iteration', 0) + 1}) ---")
    print(f"Retrieving context for query: '{query}'")
    
    # Retrieve context
    retrieved = retrieve_context(query)
    
    # Generate answer using Gemini 2.0 Flash
    prompt = f"""You are a helpful assistant. Answer the user's question using the retrieved context.
If the context is irrelevant, not found, or contains errors, answer to the best of your ability but state that it was not found in the context.

Question: {query}
Retrieved Context: {retrieved}

Answer:"""
    
    response = call_with_retry(
        client.models.generate_content,
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0
        )
    )
    answer = response.text or ""
    
    print(f"Generated Answer Preview: '{answer[:80]}...'")
    
    return {
        "retrieved_chunk": retrieved,
        "answer": answer,
        "iteration": state.get("iteration", 0) + 1
    }


def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that evaluates context relevance, groundedness, and answer relevance.
    Updates the routing decision and logs.
    
    Args:
        state: The current AgentState.
        
    Returns:
        Updates for AgentState.
    """
    print(f"\n--- [NODE] evaluate_node (Iteration {state['iteration']}) ---")
    question = state["question"]
    context = state["retrieved_chunk"]
    answer = state["answer"]
    iteration = state["iteration"]
    
    # 1. Context Relevance
    context_rel_prompt = f"""Evaluate the relevance of the retrieved context to the user's question.
Question: {question}
Retrieved Context: {context}

Rate how relevant the context is for answering the question.
- High score (0.8 - 1.0) if the context is directly relevant.
- Low score (0.0 - 0.3) if the context is completely off-topic or says 'not found'.
"""
    context_rel = judge_metric("Context Relevance", context_rel_prompt)
    
    # 2. Groundedness
    groundedness_prompt = f"""Evaluate the groundedness of the generated answer.
Retrieved Context: {context}
Generated Answer: {answer}

Rate whether the generated answer is supported ONLY by the retrieved context.
- High score (0.8 - 1.0) if the answer is completely supported.
- Low score (0.0 - 0.3) if the answer is hallucinated or context was not found.
"""
    groundedness = judge_metric("Groundedness", groundedness_prompt)
    
    # 3. Answer Relevance
    answer_rel_prompt = f"""Evaluate the relevance of the generated answer to the user's question.
Question: {question}
Generated Answer: {answer}

Rate whether the answer directly addresses the question.
- High score (0.8 - 1.0) if the question is fully answered.
- Low score (0.0 - 0.3) if the answer is generic, off-topic, or an error/missing message.
"""
    answer_rel = judge_metric("Answer Relevance", answer_rel_prompt)
    
    # Determine routing decision
    THRESHOLD = 0.7
    MAX_ITERATIONS = 3
    
    scores_ok = (context_rel.score >= THRESHOLD and 
                 groundedness.score >= THRESHOLD and 
                 answer_rel.score >= THRESHOLD)
                 
    if iteration >= MAX_ITERATIONS:
        route_decision = "accept_maxed"
    elif scores_ok:
        route_decision = "accept"
    else:
        route_decision = "rewrite"
        
    judge_reasons_str = f"Context Rel: {context_rel.reasoning} | Groundedness: {groundedness.reasoning} | Answer Rel: {answer_rel.reasoning}"
    
    print(f"Scores -> Context Rel: {context_rel.score:.2f}, Groundedness: {groundedness.score:.2f}, Answer Rel: {answer_rel.score:.2f}")
    print(f"Decision: {route_decision}")
    
    # Create log entry
    log_entry = {
        "iteration": iteration,
        "question": question,
        "chunk_preview": context[:120] + "..." if len(context) > 120 else context,
        "answer_preview": answer[:120] + "..." if len(answer) > 120 else answer,
        "context_relevance": context_rel.score,
        "groundedness": groundedness.score,
        "answer_relevance": answer_rel.score,
        "judge_reasons": judge_reasons_str,
        "route_decision": route_decision
    }
    
    new_log = list(state.get("log", []))
    new_log.append(log_entry)
    
    return {
        "context_relevance": context_rel.score,
        "groundedness": groundedness.score,
        "answer_relevance": answer_rel.score,
        "route_decision": route_decision,
        "log": new_log
    }


def rewrite_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that rewrites the user query to make it more specific and search-friendly.
    
    Args:
        state: The current AgentState.
        
    Returns:
        Updates for AgentState.
    """
    print(f"\n--- [NODE] rewrite_node ---")
    original_question = state["original_question"]
    current_question = state["question"]
    last_log = state["log"][-1] if state.get("log") else {}
    judge_reasons = last_log.get("judge_reasons", "")
    
    prompt = f"""You are an expert search query optimizer. The user's original query was: '{original_question}'.
The previous search query was: '{current_question}'.
The retrieved documents did not satisfy the evaluation criteria.
Judges feedback: {judge_reasons}

Rewrite the query to be more specific, descriptive, and fact-filled, so it retrieves more relevant documents from a vector database.
Focus on specific search terms, nouns, or concepts.
Only output the rewritten query. Do not include any explanations, greetings, or introductory text.

Rewritten Query:"""
    
    response = call_with_retry(
        client.models.generate_content,
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7
        )
    )
    rewritten_query = response.text.strip()
    rewritten_query = rewritten_query.strip('"\'')
    
    print(f"Rewrote query from '{current_question}' to '{rewritten_query}'")
    
    return {
        "question": rewritten_query
    }


def should_retry(state: AgentState) -> str:
    """
    Conditional routing function that reads the route decision.
    
    Args:
        state: The current AgentState.
        
    Returns:
        The next node name or action ("end" or "rewrite").
    """
    decision = state["route_decision"]
    if decision in ("accept", "accept_maxed"):
        return "end"
    else:
        return "rewrite"


def run_agent(question: str) -> Dict[str, Any]:
    """
    Assembles, compiles, and invokes the LangGraph agent for a question.
    
    Args:
        question: The user query.
        
    Returns:
        The final AgentState.
    """
    # 1. Build the graph
    workflow = StateGraph(AgentState)
    
    # 2. Add nodes
    workflow.add_node("generate", generate_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("rewrite", rewrite_node)
    
    # 3. Define edges
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "evaluate")
    
    workflow.add_conditional_edges(
        "evaluate",
        should_retry,
        {
            "end": END,
            "rewrite": "rewrite"
        }
    )
    
    workflow.add_edge("rewrite", "generate")
    
    # 4. Compile graph
    app = workflow.compile()
    
    # 5. Initialize state
    initial_state: AgentState = {
        "question": question,
        "original_question": question,
        "retrieved_chunk": "",
        "answer": "",
        "context_relevance": 0.0,
        "groundedness": 0.0,
        "answer_relevance": 0.0,
        "iteration": 0,
        "log": [],
        "route_decision": ""
    }
    
    # 6. Invoke the graph with recursion_limit = 10
    final_state = app.invoke(initial_state, config={"recursion_limit": 10})
    
    return final_state


def print_result(result: Dict[str, Any]) -> None:
    """
    Prints a formatted report of the run.
    """
    print("\n" + "="*80)
    print(f"Original Question: {result['original_question']}")
    print(f"Iterations Used:   {result['iteration']}")
    print(f"Route Decision:    {result['route_decision']}")
    print("Scores:")
    print(f"  - Context Relevance: {result['context_relevance']:.2f}")
    print(f"  - Groundedness:      {result['groundedness']:.2f}")
    print(f"  - Answer Relevance:  {result['answer_relevance']:.2f}")
    print("-"*80)
    print("Final Answer:")
    print(result['answer'])
    print("-"*80)
    print("Complete Iteration Log:")
    for log_entry in result['log']:
        print(f"\n  [Iteration {log_entry['iteration']}]")
        print(f"  Question:         {log_entry['question']}")
        print(f"  Chunk Preview:    {log_entry['chunk_preview']}")
        print(f"  Answer Preview:   {log_entry['answer_preview']}")
        print(f"  Scores:           Context Rel: {log_entry['context_relevance']:.2f}, "
              f"Groundedness: {log_entry['groundedness']:.2f}, "
              f"Answer Rel: {log_entry['answer_relevance']:.2f}")
        print(f"  Judge Reasons:    {log_entry['judge_reasons']}")
        print(f"  Route Decision:   {log_entry['route_decision']}")
    print("="*80 + "\n")


def main() -> None:
    """
    Main function executing standard and vague questions.
    """
    load_dotenv()
    
    normal_questions = [
        "What is ReAct?",
        "What is the travel budget?",
        "What did we learn about chunking?"
    ]
    
    vague_questions = [
        "Tell me about that thing from class",
        "What did the course say?",
        "Do the stuff"
    ]
    
    print("======================================================================")
    print("                     STARTING LANGGRAPH AGENT TEST RUN                ")
    print("======================================================================")
    
    results = []
    
    print("\n>>> RUNNING NORMAL QUESTIONS <<<\n")
    for q in normal_questions:
        try:
            res = run_agent(q)
            results.append(res)
            print_result(res)
        except Exception as e:
            print(f"Error running agent on '{q}': {e}", file=sys.stderr)
            
    print("\n>>> RUNNING VAGUE QUESTIONS <<<\n")
    for q in vague_questions:
        try:
            res = run_agent(q)
            results.append(res)
            print_result(res)
        except Exception as e:
            print(f"Error running agent on '{q}': {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
