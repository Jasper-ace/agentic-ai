import logging
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify

# Add the workspace root and activity13 directory to sys.path so we can import modules
workspace_path = Path(__file__).resolve().parents[4]
activity13_path = Path(__file__).resolve().parents[3]

if str(workspace_path) not in sys.path:
    sys.path.append(str(workspace_path))
if str(activity13_path) not in sys.path:
    sys.path.append(str(activity13_path))

from evaluation_integration import run_with_evaluation

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    RAG chat endpoint. Runs the user message through the ReAct loop and
    evaluates the result with the self-correcting RAG Triad.
    Returns both the answer and the detailed execution transcript.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    chat_history = data.get('history', [])

    try:
        # Run the complete ReAct loop with self-correcting evaluation (passing session history)
        eval_result = run_with_evaluation(message, chat_history=chat_history)
        
        # Build a beautiful, rich Markdown response containing the answer.
        # Hide transcript and evaluation details for clarification requests.
        markdown_response = []
        
        answer_text = eval_result["answer"]
        is_clarification = answer_text.startswith("[Clarify]")
        
        markdown_response.append(answer_text)
        
        if not is_clarification:
            markdown_response.append("\n\n---\n### 🛠️ Agent Execution Transcript")
            markdown_response.append("The ReAct (Reasoning & Action) loop executed the following trace:\n")
            
            for label, content in eval_result["transcript"]:
                # Format transcript sections nicely
                if label == "USER":
                    markdown_response.append(f"- **[USER]** `{content}`")
                elif label == "ACTION":
                    markdown_response.append(f"- **[ACTION]** {content.replace(chr(10), ' ')}")
                elif label == "OBSERVE":
                    markdown_response.append(f"- **[OBSERVE]** *{content}*")
                elif label == "ANSWER":
                    markdown_response.append(f"- **[ANSWER]** {content}")
                elif label == "SYSTEM":
                    markdown_response.append(f"- **[SYSTEM]** ⚠️ *{content}*")
                    
            markdown_response.append("\n---\n### 📊 RAG Triad Evaluation Scores")
            markdown_response.append(f"- **Context Relevance**: `{eval_result['context_relevance']:.2f} / 1.00`")
            markdown_response.append(f"- **Groundedness**: `{eval_result['groundedness']:.2f} / 1.00`")
            markdown_response.append(f"- **Answer Relevance**: `{eval_result['answer_relevance']:.2f} / 1.00`")
            
            status = "✅ PASSED" if eval_result["passed"] else "❌ FAILED"
            markdown_response.append(f"- **Evaluation Status**: **{status}**")
            markdown_response.append(f"- **Self-Correction Triggered**: **{'Yes' if eval_result['was_corrected'] else 'No'}**")

        full_reply = "\n".join(markdown_response)
        
        return jsonify({
            "response": full_reply
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
