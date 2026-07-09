"""
Routing Test Suite module for the Week 5 Project.
Defines 10 test cases across multiple categories and runs them to measure 
Gemini tool routing accuracy (target >= 80%).
"""

import sys
from typing import List, Dict, Any, Tuple
from activity13.project_react_loop import react_loop

# Test cases defining query, category, and expected tool.
TEST_CASES = [
    {
        "query": "What is chunking in RAG?",
        "category": "Factual Questions",
        "expected_tool": "search_documents"
    },
    {
        "query": "Can you explain what overlap means in document processing?",
        "category": "Factual Questions",
        "expected_tool": "search_documents"
    },
    {
        "query": "What are dense embeddings?",
        "category": "Factual Questions",
        "expected_tool": "search_documents"
    },
    {
        "query": "Calculate 15% of 200",
        "category": "Math Questions",
        "expected_tool": "calculate"
    },
    {
        "query": "What is 100 + (25 * 4)?",
        "category": "Math Questions",
        "expected_tool": "calculate"
    },
    {
        "query": "Compute 5 ** 3",
        "category": "Math Questions",
        "expected_tool": "calculate"
    },
    {
        "query": "Hello! Good morning.",
        "category": "Greetings",
        "expected_tool": "clarify"
    },
    {
        "query": "What is the status of that task?",
        "category": "Ambiguous Questions",
        "expected_tool": "clarify"
    },
    {
        "query": "How do I do that thing we talked about?",
        "category": "Ambiguous Questions",
        "expected_tool": "clarify"
    },
    {
        "query": "Tell me what Qdrant is and then calculate 20 * 5.",
        "category": "Multi-step Questions",
        "expected_tool": "search_documents"  # Expected to start with document search
    }
]

def run_routing_tests() -> Tuple[float, List[Dict[str, Any]]]:
    """
    Runs all defined test cases, determines actual tool calls,
    compares them to expectations, and returns the results.
    """
    results = []
    correct_count = 0
    
    print("\nStarting Routing Test Suite...")
    print("-" * 70)
    
    for idx, case in enumerate(TEST_CASES, 1):
        query = case["query"]
        category = case["category"]
        expected = case["expected_tool"]
        
        print(f"Running Test {idx}/10: [{category}] '{query}'")
        
        # Execute the ReAct loop
        _, transcript = react_loop(query)
        
        # Find the first tool call action in the transcript
        actual_tool = "None"
        for label, content in transcript:
            if label == "ACTION":
                # Action logs look like: "Tool: search_documents\nArguments: ..."
                first_line = content.split("\n")[0]
                if "Tool: " in first_line:
                    actual_tool = first_line.replace("Tool: ", "").strip()
                    break
        
        # Multi-step queries might call multiple tools; we verify if the expected one is present
        is_correct = (actual_tool == expected)
        if is_correct:
            correct_count += 1
            
        results.append({
            "idx": idx,
            "query": query,
            "category": category,
            "expected": expected,
            "actual": actual_tool,
            "correct": is_correct
        })
        
    accuracy = (correct_count / len(TEST_CASES)) * 100.0
    return accuracy, results


def display_results(accuracy: float, results: List[Dict[str, Any]]) -> None:
    """Print results table and accuracy summary."""
    print("\n" + "=" * 90)
    print(f"{'ROUTING TEST SUITE RESULTS':^90}")
    print("=" * 90)
    print(f"{'No.':<4} | {'Category':<22} | {'Expected Tool':<18} | {'Actual Tool':<18} | {'Correct':<8}")
    print("-" * 90)
    
    for r in results:
        correct_str = "YES" if r["correct"] else "NO"
        print(f"{r['idx']:<4} | {r['category']:<22} | {r['expected']:<18} | {r['actual']:<18} | {correct_str:<8}")
        
    print("-" * 90)
    print(f"Total Test Cases: {len(results)}")
    print(f"Correct Routings: {sum(1 for r in results if r['correct'])}")
    print(f"Target Accuracy:  80.0%")
    print(f"Actual Accuracy:  {accuracy:.1f}%")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    accuracy, results = run_routing_tests()
    display_results(accuracy, results)
    
    # Exit with code 0 if accuracy meets target, otherwise 1
    if accuracy >= 80.0:
        sys.exit(0)
    else:
        sys.exit(1)
