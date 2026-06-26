from flask import Blueprint, jsonify
from app.services.rag_service import RagService

documents_bp = Blueprint('documents', __name__)
rag_service = RagService()

@documents_bp.route('/documents', methods=['GET'])
def list_documents():
    """
    Lists distinct filenames currently indexed in Qdrant with chunk counts.
    """
    try:
        files = rag_service.list_documents()
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"error": f"Failed to list documents: {str(e)}"}), 500

@documents_bp.route('/documents', methods=['DELETE'])
def delete_all_documents():
    """
    Deletes all document vectors from Qdrant.
    """
    try:
        rag_service.delete_all_documents()
        return jsonify({"success": True, "message": "All indexed vectors successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete all documents: {str(e)}"}), 500

@documents_bp.route('/documents/<path:filename>', methods=['DELETE'])
def delete_document(filename):
    """
    Deletes all chunks belonging to a specific filename from Qdrant.
    """
    try:
        rag_service.delete_document(filename)
        return jsonify({"success": True, "message": f"Document '{filename}' successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete document '{filename}': {str(e)}"}), 500
