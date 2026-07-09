import logging
import time
import re
import google.generativeai as genai
from app.config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
        self.system_instruction = (
            "You are a Retrieval-Augmented Generation (RAG) assistant. "
            "Answer questions using only the provided context. Never use outside knowledge. "
            "If the answer cannot be found in the context, respond exactly with \"I don't know.\""
        )
        
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_CHAT_MODEL,
            system_instruction=self.system_instruction
        )
        
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

    def generate_response(self, context: str, question: str) -> str:
        """
        Sends the compiled context and user question to the Gemini model and returns the response.
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")
            
        prompt = (
            f"Here is the context retrieved from documents:\n"
            f"---------------------\n"
            f"{context}\n"
            f"---------------------\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )
        
        response = self._execute_with_retry(self.model.generate_content, prompt)
        return response.text.strip()

