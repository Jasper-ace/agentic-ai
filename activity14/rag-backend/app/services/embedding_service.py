import logging
import time
import re
import google.generativeai as genai
from app.config import Config

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # Configure Gemini API client
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
        
        self.model_name = Config.GEMINI_EMBEDDING_MODEL
        self._validate_and_fallback_model()
        
    def _execute_with_retry(self, func, *args, max_retries=10, initial_backoff=5, **kwargs):
        """
        Executes a Gemini API call and retries on 429 / rate limits / quota exceeded errors.
        Extracts recommended retry delay from the exception message if available.
        Fails fast without retrying if a hard quota limit (e.g. daily quota exceeded) is detected.
        """
        backoff = initial_backoff
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = str(e).lower()
                
                # Check for hard/daily quota limits where retrying is futile and will only block workers
                is_hard_quota = "exceeded your current quota" in err_msg or "billing details" in err_msg
                if is_hard_quota:
                    logger.error(f"Hard Gemini API quota limit encountered. Failing fast. Error: {e}")
                    raise e
                    
                is_rate_limit = "429" in err_msg or "quota" in err_msg or "rate limit" in err_msg or "resource_exhausted" in err_msg
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = None
                    
                    # Look for "retry in X.Y s" or similar
                    match_in = re.search(r"retry in ([\d\.]+)\s*s", err_msg)
                    if match_in:
                        try:
                            sleep_time = float(match_in.group(1)) + 1.0
                        except ValueError:
                            pass
                            
                    # Or look for "retry_delay { seconds: X }"
                    if not sleep_time:
                        match_delay = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_msg)
                        if match_delay:
                            try:
                                sleep_time = float(match_delay.group(1)) + 1.0
                            except ValueError:
                                pass
                                
                    if not sleep_time:
                        sleep_time = backoff
                        backoff *= 2
                        
                    logger.warning(
                        f"Gemini API rate limit encountered. Retrying in {sleep_time:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries}). Error: {e}"
                    )
                    time.sleep(sleep_time)
                else:
                    raise e
        
    def _validate_and_fallback_model(self):
        """
        Queries Google AI to check if the configured model is supported.
        If not, falls back to an available embedding model on the account.
        """
        if not Config.GEMINI_API_KEY:
            return
            
        try:
            available_models = [m.name for m in genai.list_models()]
            
            # Check if model name has 'models/' prefix
            tgt_model = self.model_name
            if not tgt_model.startswith("models/"):
                tgt_model = f"models/{tgt_model}"
                
            if tgt_model not in available_models:
                # Find available embedding models
                emb_models = [m for m in available_models if "embed" in m.lower()]
                if emb_models:
                    old_model = self.model_name
                    # Use the first available model (e.g. models/gemini-embedding-001)
                    self.model_name = emb_models[0]
                    logger.warning(f"Embedding model '{old_model}' not available. Falling back to '{self.model_name}'.")
                else:
                    logger.warning(f"Configured embedding model '{self.model_name}' not listed in available models.")
            else:
                self.model_name = tgt_model
                logger.info(f"Using embedding model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not validate embedding model via list_models: {e}. Defaulting to '{self.model_name}'.")

    def get_embedding(self, text: str) -> list[float]:
        """
        Generates embedding for a single string content.
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")
        
        response = self._execute_with_retry(
            genai.embed_content,
            model=self.model_name,
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a batch of texts with batching and retry logic.
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")
        if not texts:
            return []
            
        batch_size = 50
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self._execute_with_retry(
                genai.embed_content,
                model=self.model_name,
                content=batch,
                task_type="retrieval_document"
            )
            all_embeddings.extend(response['embedding'])
            
        return all_embeddings

    def get_query_embedding(self, query: str) -> list[float]:
        """
        Generates embedding for a search query.
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")
            
        response = self._execute_with_retry(
            genai.embed_content,
            model=self.model_name,
            content=query,
            task_type="retrieval_query"
        )
        return response['embedding']

