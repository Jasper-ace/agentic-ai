import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import Config

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        # Connect to Qdrant server
        self.client = QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
        self.collection_name = Config.QDRANT_COLLECTION

    def _ensure_collection_exists(self, vector_size: int):
        """
        Creates the Qdrant collection if it doesn't already exist.
        Recreates it if there is a vector size mismatch (self-healing).
        Uses cosine distance for Gemini embeddings.
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating collection '{self.collection_name}' with {vector_size} dimensions (Cosine).")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
            else:
                # Check vector size mismatch
                info = self.client.get_collection(self.collection_name)
                current_size = info.config.params.vectors.size
                if current_size != vector_size:
                    logger.warning(f"Vector size mismatch! Collection has {current_size} dims, but new vector has {vector_size} dims. Recreating collection...")
                    self.client.delete_collection(self.collection_name)
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                    )
                else:
                    logger.info(f"Collection '{self.collection_name}' exists and matches dimension size {vector_size}.")
        except Exception as e:
            logger.error(f"Failed to check/create Qdrant collection: {e}")
            raise e

    def upsert_chunks(self, chunks: list[str], embeddings: list[list[float]], filename: str) -> int:
        """
        Stores chunks and their vector embeddings in Qdrant with metadata.
        """
        if not chunks or not embeddings:
            return 0
            
        vector_size = len(embeddings[0])
        self._ensure_collection_exists(vector_size)
        
        points = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "filename": filename,
                    "chunk_index": idx,
                    "text": chunk_text
                }
            ))
            
        logger.info(f"Upserting {len(points)} points for '{filename}' to Qdrant.")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)

    def search_relevant_chunks(self, query_embedding: list[float], limit: int = 5) -> list[dict]:
        """
        Searches Qdrant for similar vector chunks.
        Tries calling .query_points and falls back to .search if the server doesn't support it or if it fails.
        """
        vector_size = len(query_embedding)
        self._ensure_collection_exists(vector_size)
        
        results = None
        
        # Try the unified query_points API first
        if hasattr(self.client, "query_points"):
            try:
                logger.info("Querying Qdrant using unified query_points API...")
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=limit,
                    with_payload=True
                )
                results = response.points
            except Exception as e:
                logger.warning(f"Unified query_points API failed ({e}). Falling back to search API...")
        
        # Fall back to .search API if query_points was not successful/supported
        if results is None:
            if hasattr(self.client, "search"):
                logger.info("Querying Qdrant using search API...")
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    with_payload=True
                )
            else:
                raise AttributeError("QdrantClient has neither 'query_points' nor 'search' method.")
        
        return [
            {
                "score": hit.score,
                "filename": hit.payload.get("filename"),
                "chunk_index": hit.payload.get("chunk_index"),
                "text": hit.payload.get("text")
            }
            for hit in results
        ]

    def list_indexed_files(self) -> list[dict]:
        """
        Retrieves a list of all distinct files that have been indexed in Qdrant.
        """
        offset = None
        unique_files = {}
        
        while True:
            # Scroll points page by page
            response, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            
            for point in response:
                filename = point.payload.get("filename")
                if filename:
                    if filename not in unique_files:
                        unique_files[filename] = {
                            "filename": filename,
                            "chunks": 0
                        }
                    unique_files[filename]["chunks"] += 1
                    
            offset = next_offset
            if offset is None or len(response) == 0:
                break
                
        return list(unique_files.values())

    def delete_all_documents(self):
        """
        Wipes the entire collection and recreates it.
        """
        logger.info(f"Deleting collection '{self.collection_name}'.")
        vector_size = 3072
        try:
            info = self.client.get_collection(self.collection_name)
            vector_size = info.config.params.vectors.size
        except Exception as e:
            logger.warning(f"Could not retrieve existing collection size for recreate ({e}). Defaulting to 3072.")
        
        self.client.delete_collection(self.collection_name)
        self._ensure_collection_exists(vector_size)

    def delete_document_by_filename(self, filename: str):
        """
        Deletes all chunks belonging to a specific file from Qdrant.
        """
        logger.info(f"Deleting documents with filename '{filename}' from Qdrant.")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=filename)
                    )
                ]
            )
        )
