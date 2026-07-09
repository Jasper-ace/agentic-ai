"""
Evaluation Integration module for the Week 5 Project.
Implements the RAG Triad evaluation using Gemini structured outputs,
and a self-correction feedback loop when evaluation scores fail validation.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from google.genai import types

from activity13.config import client, DEFAULT_MODEL, EVAL_SCORE_THRESHOLD, call_with_retry
from activity13.project_react_loop import react_loop, print_transcript

# Pydantic schema to enforce structured evaluation output from Gemini
class TriadScores(BaseModel):
    context_relevance: float = Field(
        ..., 
        description="Is the retrieved context relevant to the user question? Score 0.0 (irrelevant) to 1.0 (fully relevant)."
    )
    groundedness: float = Field(
        ..., 
        description="Is the answer fully supported by and grounded ONLY in the retrieved context? Score 0.0 (completely ungrounded/hallucinated) to 1.0 (fully grounded)."
    )
    answer_relevance: float = Field(
        ..., 
        description="Does the answer directly address the user's question? Score 0.0 (irrelevant/off-topic) to 1.0 (perfectly addresses)."
    )
    reasoning: str = Field(
        ..., 
        description="Brief justification for each of the scores."
    )


def score_rag_triad(question: str, context: str, answer: str) -> TriadScores:
    """
    Evaluates the RAG Triad scores using Gemini with structured JSON output.
    
    Args:
        question: The user query.
        context: The context retrieved during tool calls.
        answer: The final generated answer.
        
    Returns:
        A TriadScores object containing the scores and reasoning.
    """
    prompt = f"""
    Evaluate the following RAG interaction:
    
    [Question]: {question}
    [Retrieved Context]: {context}
    [Generated Answer]: {answer}
    
    Evaluate the three RAG Triad metrics:
    1. Context Relevance: How relevant is the context to the question?
    2. Groundedness: Is the answer supported by the context without extra facts?
    3. Answer Relevance: Does the answer directly answer the question?
    """
    
    try:
        response = call_with_retry(
            client.models.generate_content,
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriadScores,
                temperature=0.0,
                system_instruction="You are a strict, objective AI evaluation judge grading RAG performance."
            )
        )
        # Parse the JSON response directly into Pydantic model
        result_json = json.loads(response.text)
        return TriadScores(**result_json)
    except Exception as e:
        # Fallback in case of API failure
        return TriadScores(
            context_relevance=1.0 if context else 0.0,
            groundedness=0.5,
            answer_relevance=0.5,
            reasoning=f"Fallback scoring due to evaluation error: {str(e)}"
        )


def run_with_evaluation(question: str, chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Runs the ReAct loop, evaluates the result, and performs self-correction 
    if the Groundedness or Answer Relevance scores fall below the threshold.
    
    Args:
        question: The user query.
        chat_history: List of previous messages from the frontend session.
        
    Returns:
        A dictionary with evaluation results and correction metadata.
    """
    # 1. Run initial ReAct loop (passing frontend chat history)
    answer, transcript = react_loop(question, chat_history=chat_history)
    
    # Extract retrieved contexts from the transcript OBSERVE blocks
    contexts = []
    for label, content in transcript:
        if label == "OBSERVE" and "[Found]" in content:
            contexts.append(content)
            
    context_str = "\n".join(contexts) if contexts else "No context retrieved."
    
    # 2. Score the initial answer
    scores = score_rag_triad(question, context_str, answer)
    
    # 3. Check for failures (Groundedness or Answer Relevance < Threshold)
    passed = (scores.groundedness >= EVAL_SCORE_THRESHOLD and 
              scores.answer_relevance >= EVAL_SCORE_THRESHOLD)
              
    corrected_answer = None
    was_corrected = False
    final_scores = scores
    
    # If the answer triggered a clarification prompt, bypass correction and return it directly
    if answer.startswith("[Clarify]"):
        passed = True
        
    if not passed:
        was_corrected = True
        # Construct correction prompt with feedback
        feedback = (
            f"The previous answer failed the RAG evaluation.\n"
            f"Groundedness score: {scores.groundedness}/1.0\n"
            f"Answer Relevance score: {scores.answer_relevance}/1.0\n"
            f"Reasoning: {scores.reasoning}\n\n"
            f"Please search for the correct information again, "
            f"and formulate an answer that is completely grounded in the retrieved documents "
            f"and directly answers the user query."
        )
        
        # Re-run ReAct loop with self-correction feedback
        corrected_answer, corrected_transcript = react_loop(
            question, 
            chat_history=chat_history, 
            feedback_prompt=feedback
        )
        transcript.extend(corrected_transcript)
        
        # Re-evaluate the corrected answer
        final_scores = score_rag_triad(question, context_str, corrected_answer)
        passed = (final_scores.groundedness >= EVAL_SCORE_THRESHOLD and 
                  final_scores.answer_relevance >= EVAL_SCORE_THRESHOLD)
                  
        answer_to_return = corrected_answer
    else:
        answer_to_return = answer
        
    return {
        "question": question,
        "answer": answer_to_return,
        "transcript": transcript,
        "context_relevance": final_scores.context_relevance,
        "groundedness": final_scores.groundedness,
        "answer_relevance": final_scores.answer_relevance,
        "passed": passed,
        "corrected_answer": corrected_answer,
        "was_corrected": was_corrected
    }


if __name__ == "__main__":
    q = "What is Qdrant and what are dense embeddings?"
    result = run_with_evaluation(q)
    
    print("\n" + "=" * 50)
    print("EVALUATION & SELF-CORRECTION TEST RUN")
    print("=" * 50)
    print(f"Question:         {result['question']}")
    print(f"Answer:           {result['answer']}")
    print(f"Context Rel:      {result['context_relevance']}")
    print(f"Groundedness:     {result['groundedness']}")
    print(f"Answer Rel:       {result['answer_relevance']}")
    print(f"Passed:           {result['passed']}")
    print(f"Was Corrected:    {result['was_corrected']}")
    if result['was_corrected']:
        print(f"Corrected Ans:    {result['corrected_answer']}")
    print("=" * 50)
    
    print("\nFull Transcript:")
    print_transcript(result["transcript"])
