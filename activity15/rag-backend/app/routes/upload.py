import os
import logging
from flask import Blueprint, request, jsonify
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)
rag_service = RagService()

@upload_bp.route('/upload', methods=['POST'])
def upload_documents():
    """
    Accepts multiple .txt files, chunks them, embeds them,
    and indexes them in Qdrant.
    """
    # Check if files part exists
    if 'files' not in request.files:
        # Check if they sent a single file as 'file'
        files = request.files.getlist('file')
        if not files:
            return jsonify({"error": "No file part in the request under 'files' or 'file'"}), 400
    else:
        files = request.files.getlist('files')

    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No selected files"}), 400

    files_uploaded = 0
    total_chunks = 0

    for file in files:
        if file.filename == '':
            continue
            
        # Optional: Validate file type
        ext = os.path.splitext(file.filename)[1].lower()
        if ext != '.txt':
            logger.warning(f"File '{file.filename}' rejected: only .txt files are supported.")
            continue
            
        try:
            # Read and decode contents
            content = file.read().decode('utf-8', errors='ignore')
            
            # Process and index
            chunks_created = rag_service.process_and_index_document(file.filename, content)
            
            if chunks_created > 0:
                files_uploaded += 1
                total_chunks += chunks_created
                
        except Exception as e:
            logger.error(f"Error processing file '{file.filename}': {e}")
            return jsonify({"error": f"Failed to process file '{file.filename}': {str(e)}"}), 500

    if files_uploaded == 0:
        return jsonify({"error": "No valid .txt files were successfully indexed"}), 400

    return jsonify({
        "success": True,
        "files_uploaded": files_uploaded,
        "chunks_created": total_chunks
    }), 200
