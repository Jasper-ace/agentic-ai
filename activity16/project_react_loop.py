"""
ReAct Loop module for the Week 5 Project.
Implements the core ReAct loop, Gemini function calling integration,
transcript recording/printing, and demo query capability.
Supports multi-turn conversational clarification queries.
"""

from typing import List, Dict, Any, Tuple
from google.genai import types
from activity14.config import client, DEFAULT_MODEL, MAX_ITERATIONS, call_with_retry
from activity14.tools import AVAILABLE_FUNCTIONS, search_documents, calculate, clarify

# System instruction to guide Gemini to act as a ReAct agent using the tools
SYSTEM_INSTRUCTION = """
You are a expert assistant with access to tools. Your task is to resolve user queries using the reasoning-loop (ReAct) pattern.
Always use the search_documents tool if factual info is requested.
Always use the calculate tool for mathematical expressions.
Always use the clarify tool if a query is ambiguous, greeting, or incomplete.

Follow these rules:
1. Perform reasoning step-by-step.
2. If you need information from a tool, call the tool.
3. Once you have all the information needed, provide a concise, direct, and complete final answer.
"""

def print_transcript(transcript: List[Tuple[str, str]]) -> None:
    """
    Print the ReAct loop transcript in the requested university grading format.
    
    Args:
        transcript: A list of (label, content) tuples.
    """
    print("====================================================")
    for label, content in transcript:
        print(f"[{label}]")
        print(f"{content}\n")
    print("====================================================")


def parse_chat_history(chat_history: List[Dict[str, Any]]) -> List[types.Content]:
    """
    Translates React-side frontend chat history into a list of Gemini Content objects.
    Correctly maps clarifying AI queries and subsequent user replies to FunctionCalls and FunctionResponses.
    """
    history: List[types.Content] = []
    if not chat_history:
        return history
        
    i = 0
    while i < len(chat_history):
        msg = chat_history[i]
        sender = msg.get("sender")
        text = msg.get("text", "")
        
        if sender == "user":
            # Check if this user message is answering a previous clarifying question
            is_clarification_response = False
            if i > 0:
                prev_msg = chat_history[i-1]
                prev_text = prev_msg.get("text", "")
                
                # Check if the previous message was a Clarify prompt
                if prev_msg.get("sender") == "ai" and prev_text.startswith("[Clarify]"):
                    is_clarification_response = True
                    clarify_question = prev_text.replace("[Clarify]", "").strip()
            
            if is_clarification_response:
                # 1. Append the model's clarify function call first
                history.append(
                    types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="clarify",
                                    args={"question": clarify_question}
                                )
                            )
                        ]
                    )
                )
                # 2. Append the user's input as the function response
                history.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name="clarify",
                                response={"result": text}
                            )
                        ]
                    )
                )
            else:
                # Standard user query
                history.append(types.Content(role="user", parts=[types.Part.from_text(text=text)]))
                
        elif sender == "ai":
            # If the AI message was a clarify prompt, we skip appending it as text,
            # because we handle it as part of the user's response above.
            if not text.startswith("[Clarify]"):
                history.append(types.Content(role="model", parts=[types.Part.from_text(text=text)]))
                
        i += 1
        
    return history


def react_loop(
    question: str, 
    chat_history: List[Dict[str, Any]] = None, 
    feedback_prompt: str = None
) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Executes the ReAct loop for a given question.
    
    Args:
        question: The user query.
        chat_history: List of previous messages from the frontend session.
        feedback_prompt: Optional correction feedback for self-correction.
        
    Returns:
        A tuple of (final_answer, transcript).
    """
    transcript: List[Tuple[str, str]] = []
    
    # Log the initial user query
    transcript.append(("USER", question))
    if feedback_prompt:
        transcript.append(("SYSTEM", f"Self-Correction Triggered:\n{feedback_prompt}"))
        
    # Reconstruct history from previous chat history if available
    history = parse_chat_history(chat_history)
    
    # Append the current query to the history
    current_query_text = question
    if feedback_prompt:
        current_query_text += f"\n\n[SYSTEM FEEDBACK]: {feedback_prompt}"
        
    history.append(types.Content(role="user", parts=[types.Part.from_text(text=current_query_text)]))
    
    tools_list = [search_documents, calculate, clarify]
    
    # Configure GenerateContentConfig and explicitly DISABLE Automatic Function Calling (AFC)
    config = types.GenerateContentConfig(
        tools=tools_list,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    
    iteration = 0
    final_answer = ""
    
    while iteration < MAX_ITERATIONS:
        iteration += 1
        
        try:
            # Generate next step from the model using the rate-limit-aware retry wrapper
            response = call_with_retry(
                client.models.generate_content,
                model=DEFAULT_MODEL,
                contents=history,
                config=config
            )
            
            # Check if the model wants to call functions
            if response.function_calls:
                model_parts = response.candidates[0].content.parts
                history.append(types.Content(role="model", parts=model_parts))
                
                tool_responses = []
                has_clarified = False
                
                for call in response.function_calls:
                    tool_name = call.name
                    tool_args = call.args
                    
                    # Log Action
                    action_msg = f"Tool: {tool_name}\nArguments: {tool_args}"
                    transcript.append(("ACTION", action_msg))
                    
                    # Execute tool
                    if tool_name in AVAILABLE_FUNCTIONS:
                        try:
                            # Extract argument correctly
                            arg_value = list(tool_args.values())[0] if tool_args else ""
                            observe_result = AVAILABLE_FUNCTIONS[tool_name](arg_value)
                        except Exception as e:
                            observe_result = f"Error executing tool: {str(e)}"
                    else:
                        observe_result = f"Error: Tool '{tool_name}' not found."
                        
                    # Log Observation
                    transcript.append(("OBSERVE", observe_result))
                    
                    if tool_name == "clarify":
                        has_clarified = True
                        final_answer = observe_result
                    
                    # Create the function response part
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": observe_result}
                        )
                    )
                
                # If the clarify tool was triggered, stop execution immediately and wait for user reply
                if has_clarified:
                    transcript.append(("ANSWER", final_answer))
                    break
                    
                # Append tool responses as user input for the next loop iteration
                history.append(types.Content(role="user", parts=tool_responses))
                
            else:
                # No function calls, the model gave a final answer
                final_answer = response.text or ""
                transcript.append(("ANSWER", final_answer))
                break
                
        except Exception as e:
            err_msg = f"Error in ReAct loop: {str(e)}"
            transcript.append(("SYSTEM", err_msg))
            final_answer = err_msg
            break
            
    if iteration >= MAX_ITERATIONS and not final_answer:
        final_answer = "Error: ReAct loop exceeded maximum iterations without a final answer."
        transcript.append(("ANSWER", final_answer))
        
    return final_answer, transcript


def demo_query(question: str) -> None:
    """Runs a demo query and prints the transcript."""
    print(f"\n--- Running Demo Query: '{question}' ---")
    _, transcript = react_loop(question)
    print_transcript(transcript)


if __name__ == "__main__":
    demo_query("What is Qdrant?")
    demo_query("Compute 45% of 350 + (12 * 8)")
    demo_query("Hello there!")
