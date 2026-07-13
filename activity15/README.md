# Week 5 Project: ReAct Loop & Native Tool Calling

This project is a modular, production-ready implementation of a Reasoning and Acting (ReAct) Agent loop using the Google Gemini API with native function calling, safe mathematical execution, and automatic RAG Triad evaluation with self-correction feedback.

---

## Folder Structure

```text
activity13/
│
├── config.py                  # Client configuration, model parameters, and rate-limit retries
├── tools.py                   # Factual search tool, safe math evaluator, and clarify tool
├── project_react_loop.py      # Core ReAct loop logic and transcript logger
├── routing_test_suite.py      # Test runner validating tool routing accuracy across 10 scenarios
├── evaluation_integration.py  # RAG Triad judge and self-correction runner
├── routing_report_week5.md    # Analysis of results, failure modes, and architectural reflection
├── README.md                  # System description and execution documentation
└── requirements.txt           # Project dependencies
```

---

## Installation & Setup

### 1. Set Up a Virtual Environment
From the workspace root directory, activate the pre-existing virtual environment:
```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat
```

### 2. Install Dependencies
Run the following command to install the required Python packages:
```bash
pip install -r activity13/requirements.txt
```

### 3. Configure the Gemini API Key
Ensure you have a `.env` file in either the workspace root or the `activity13` directory containing your Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## Running the Project

All scripts should be executed from the workspace root directory (`c:\Users\STUDENT\Documents\agentic-ai`) using python's module run option to ensure proper path resolutions.

### 1. Run the Routing Test Suite
This validates that the agent correctly routes user queries to the expected tools:
```bash
python -m activity13.routing_test_suite
```

### 2. Run the Evaluation and Self-Correction Loop
This runs a sample multi-turn query, grades the response on Context Relevance, Groundedness, and Answer Relevance, and triggers self-correction if scores fall below `0.7`:
```bash
python -m activity13.evaluation_integration
```

### 3. Run the ReAct Loop Demos
This executes a set of example queries demonstrating facts search, math evaluation, and clarification requests:
```bash
python -m activity13.project_react_loop
```

---

## Expected Outputs

### Tool Routing Suite Results
```text
==========================================================================================
                                ROUTING TEST SUITE RESULTS                                
==========================================================================================
No.  | Category               | Expected Tool      | Actual Tool        | Correct 
------------------------------------------------------------------------------------------
1    | Factual Questions      | search_documents   | search_documents   | YES     
2    | Factual Questions      | search_documents   | search_documents   | YES     
3    | Factual Questions      | search_documents   | search_documents   | YES     
4    | Math Questions         | calculate          | calculate          | YES     
5    | Math Questions         | calculate          | calculate          | YES     
6    | Math Questions         | calculate          | calculate          | YES     
7    | Greetings              | clarify            | clarify            | YES     
8    | Ambiguous Questions    | clarify            | clarify            | YES     
9    | Ambiguous Questions    | clarify            | clarify            | YES     
10   | Multi-step Questions   | search_documents   | search_documents   | YES     
------------------------------------------------------------------------------------------
Total Test Cases: 10
Correct Routings: 10
Target Accuracy:  80.0%
Actual Accuracy:  100.0%
==========================================================================================
```

### RAG Triad Evaluator Results
```text
==================================================
EVALUATION & SELF-CORRECTION TEST RUN
==================================================
Question:         What is Qdrant and what are dense embeddings?
Answer:           Qdrant is a production-ready vector database designed for fast similarity search and semantic retrieval of high-dimensional vectors. Dense embeddings are real-valued vector representations of text where semantically similar words or sentences are positioned closer in vector space.
Context Rel:      1.0
Groundedness:     1.0
Answer Rel:       1.0
Passed:           True
Was Corrected:    False
==================================================
```
