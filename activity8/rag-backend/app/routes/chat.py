import logging
from flask import Blueprint, request, jsonify
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)
rag_service = RagService()

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    RAG chat endpoint. Searches relevant chunks from indexed documents,
    verifies similarity score threshold, and generates responses.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        answer = rag_service.answer_question(message)
        return jsonify({
            "response": answer
        }), 200
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
