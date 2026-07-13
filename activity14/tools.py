"""
Tools module for the Week 5 ReAct Loop & Tool Calling Project.
Defines the mock knowledge base, safe math evaluator, clarify tool,
and the registry of available functions for the Gemini API.
Includes dynamic integration with Qdrant Vector Database if available.
"""

import ast
import operator
import re
import sys
from pathlib import Path
from typing import Dict, Any, Callable

# Part 1: Mock Knowledge Base Dictionary
MOCK_KNOWLEDGE_BASE: Dict[str, str] = {
    "qdrant": (
        "Qdrant is a production-ready vector database designed for fast "
        "similarity search and semantic retrieval of high-dimensional vectors."
    ),
    "chunking": (
        "Chunking is the process of splitting large documents into smaller, cohesive "
        "segments before generating embeddings. Standard strategies include fixed-size "
        "sliding windows and paragraph-based chunking."
    ),
    "overlap": (
        "Overlap refers to the shared content between consecutive chunks. It ensures "
        "that context and semantics are preserved across chunk boundaries."
    ),
    "embeddings": (
        "Embeddings are dense, real-valued vector representations of text where "
        "semantically similar words or sentences are positioned closer in vector space."
    ),
    "rag triad": (
        "The RAG Triad is an evaluation framework consisting of three core metrics: "
        "Context Relevance (is retrieved context relevant to the query?), "
        "Groundedness (is the response supported by the retrieved context?), and "
        "Answer Relevance (does the response directly address the user's question?)."
    ),
    "react loop": (
        "The ReAct (Reasoning and Acting) loop is an agent architecture where an LLM "
        "cycles through generating Thoughts (reasoning), selecting Actions (tool calls), "
        "processing Observations (tool execution), and producing final Answers."
    )
}

# 1. Search Documents Tool
def search_documents(query: str) -> str:
    """
    Search the Qdrant vector database for documents relevant to the user query.
    Supports advanced features including query expansion, hybrid vector/keyword search,
    and LLM re-ranking to retrieve the most semantically relevant text chunk.
    
    Args:
        query: The user search query or question.
        
    Returns:
        A string formatted as [Found] ... containing the best matching text chunk,
        or [Not found] ... if no relevant documents are found.
    """
    from activity14.bridging_search_tool import search_documents as qdrant_search_documents
    return qdrant_search_documents(query)


# 2. Safe Calculate Tool
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: lambda x: x
}

def safe_eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return safe_eval_ast(node.body)
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise TypeError(f"Unsupported binary operator: {op_type.__name__}")
        return ALLOWED_OPERATORS[op_type](safe_eval_ast(node.left), safe_eval_ast(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
        return ALLOWED_OPERATORS[op_type](safe_eval_ast(node.operand))
    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise TypeError(f"Unsupported constant type: {type(node.value).__name__}")
        return float(node.value)
    elif isinstance(node, ast.Num):
        return float(node.n)
    else:
        raise TypeError(f"Unsupported AST node: {type(node).__name__}")

def calculate(expression: str) -> str:
    """
    Safely evaluate an arithmetic expression.
    Supports basic arithmetic (+, -, *, /), modulo (%), brackets (), exponentiation (**), and percentages.
    
    Args:
        expression: The mathematical expression string.
        
    Returns:
        The evaluated result as a string, or an error message.
    """
    try:
        processed_expr = re.sub(r"(\d+(?:\.\d+)?)%", r"(\1 / 100.0)", expression)
        processed_expr = processed_expr.strip()
        
        if not processed_expr:
            return "Error: Empty expression."
            
        tree = ast.parse(processed_expr, mode='eval')
        result = safe_eval_ast(tree)
        return str(result)
        
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        return f"Error: Invalid expression. Details: {str(e)}"


# 3. Clarify Tool
def clarify(question: str) -> str:
    """
    Ask for clarification when a user request is ambiguous, incomplete, or requires extra details.
    
    Args:
        question: The clarifying question to return to the user.
        
    Returns:
        A string formatted as [Clarify] ...
    """
    return f"[Clarify] {question}"


# Dispatcher dictionary for execution during the ReAct loop
AVAILABLE_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "search_documents": search_documents,
    "calculate": calculate,
    "clarify": clarify
}
