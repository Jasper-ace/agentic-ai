import logging
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.gemini_service import GeminiService
from app.services.evaluation_service import EvaluationService
from app.utils.chunker import split_text
from app.config import Config

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.gemini_service = GeminiService()
        self.evaluation_service = EvaluationService()

    def process_and_index_document(self, filename: str, content: str) -> int:
        """
        Takes raw document content, splits into overlapping chunks,
        generates embeddings, and stores them in the vector database.
        """
        logger.info(f"Indexing document '{filename}'...")
        
        # Chunk text
        chunks = split_text(content, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
        if not chunks:
            logger.warning(f"No text chunks generated for file '{filename}'.")
            return 0
            
        logger.info(f"Generated {len(chunks)} chunks for '{filename}'.")
        
        # Generate embeddings
        embeddings = self.embedding_service.get_embeddings(chunks)
        
        # Save to Qdrant
        upserted_count = self.qdrant_service.upsert_chunks(
            chunks=chunks,
            embeddings=embeddings,
            filename=filename
        )
        return upserted_count

    def answer_question(self, question: str) -> dict:
        """
        Answers a user question by searching relevant chunks, applying a
        similarity threshold, building context, querying the LLM, and evaluating the RAG Triad.
        """
        logger.info(f"Answering query: '{question}'")
        
        # 1. Embed query
        query_vector = self.embedding_service.get_query_embedding(question)
        
        # 2. Search Qdrant
        search_hits = self.qdrant_service.search_relevant_chunks(query_vector, limit=5)
        
        # 3. Filter by similarity threshold
        relevant_hits = [hit for hit in search_hits if hit["score"] >= Config.SIMILARITY_THRESHOLD]
        
        if not relevant_hits:
            logger.info("No documents met the similarity threshold. Returning 'I don't know.'")
            response = "I don't know."
            evaluation = {
                "context_relevance": {"score": 0.0, "reason": "No retrieved context met the similarity threshold."},
                "groundedness": {"score": 1.0, "reason": "The response 'I don't know.' is grounded because no context is available."},
                "answer_relevance": {"score": 1.0, "reason": "Answering 'I don't know.' is appropriate when no information is found in documents."}
            }
            return {
                "response": response,
                "evaluation": evaluation
            }
            
        # 4. Construct context
        context_parts = []
        for hit in relevant_hits:
            logger.info(f"Retrieved chunk from '{hit['filename']}' with similarity score {hit['score']:.4f}")
            context_parts.append(f"Source: {hit['filename']}\n{hit['text']}")
            
        context = "\n\n=== Context Block ===\n".join(context_parts)
        
        # 5. Call LLM
        response = self.gemini_service.generate_response(context, question)
        
        # 6. Evaluate RAG Triad
        try:
            evaluation = self.evaluation_service.evaluate_triad(question, context, response)
        except Exception as e:
            logger.error(f"Error evaluating RAG triad: {e}")
            evaluation = {
                "context_relevance": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"},
                "groundedness": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"},
                "answer_relevance": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"}
            }
            
        return {
            "response": response,
            "evaluation": evaluation
        }

    def list_documents(self) -> list[dict]:
        return self.qdrant_service.list_indexed_files()

    def delete_all_documents(self):
        self.qdrant_service.delete_all_documents()

    def delete_document(self, filename: str):
        self.qdrant_service.delete_document_by_filename(filename)
