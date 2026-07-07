import json
import logging
import re
import random
import time
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from app.config import Config

logger = logging.getLogger(__name__)

class EvaluationService:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_CHAT_MODEL
        )

    def _execute_with_retry(self, func, *args, max_retries=5, initial_backoff=2, max_backoff=30, **kwargs):
        backoff = initial_backoff
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_msg = str(e).lower()
                is_hard_quota = "exceeded your current quota" in err_msg or "billing details" in err_msg
                if is_hard_quota:
                    logger.error(f"Hard Gemini API quota limit encountered in evaluation. Error: {e}")
                    raise e
                    
                is_rate_limit = "429" in err_msg or "quota" in err_msg or "rate limit" in err_msg or "resource_exhausted" in err_msg
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = None
                    match_in = re.search(r"retry in ([\d\.]+)\s*s", err_msg)
                    if match_in:
                        try:
                            sleep_time = float(match_in.group(1)) + 1.0
                        except ValueError:
                            pass
                    if not sleep_time:
                        match_delay = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_msg)
                        if match_delay:
                            try:
                                sleep_time = float(match_delay.group(1)) + 1.0
                            except ValueError:
                                pass
                    if not sleep_time:
                        sleep_time = random.uniform(0.5, min(max_backoff, backoff))
                        backoff = min(max_backoff, backoff * 2)
                        
                    logger.warning(
                        f"Gemini API rate limit in evaluation. Retrying in {sleep_time:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries}). Error: {e}"
                    )
                    time.sleep(sleep_time)
                else:
                    raise e

    def evaluate_context_relevance(self, query: str, context: str) -> dict:
        prompt = (
            f"You are an expert evaluator. Evaluate the relevance of the retrieved context to the user query.\n\n"
            f"User Query: {query}\n"
            f"Retrieved Context:\n{context}\n\n"
            f"Rate the context relevance on a scale of 0.0 to 1.0, where:\n"
            f"- 0.0: The context is completely irrelevant to the user query.\n"
            f"- 0.5: The context is partially relevant or contains some information but lacks detail to fully answer.\n"
            f"- 1.0: The context is highly relevant and contains all necessary information to fully answer the user query.\n\n"
            f"Respond strictly in JSON format with two fields:\n"
            f"- \"score\": a floating-point number between 0.0 and 1.0 representing the relevance.\n"
            f"- \"reason\": a brief, single-sentence explanation for the score.\n"
        )
        try:
            response = self._execute_with_retry(
                self.model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            return {"score": float(data.get("score", 0.0)), "reason": str(data.get("reason", ""))}
        except Exception as e:
            logger.error(f"Error evaluating context relevance: {e}")
            return {"score": 0.0, "reason": f"Evaluation failed: {str(e)}"}

    def evaluate_groundedness(self, response_text: str, context: str) -> dict:
        prompt = (
            f"You are an expert evaluator. Evaluate the groundedness (faithfulness) of the response based on the retrieved context. "
            f"Identify if there are any claims, facts, or details in the response that are not directly supported by the context.\n\n"
            f"Retrieved Context:\n{context}\n"
            f"Response:\n{response_text}\n\n"
            f"Rate the groundedness on a scale of 0.0 to 1.0, where:\n"
            f"- 0.0: The response is completely ungrounded, hallucinated, or contradicts the context.\n"
            f"- 0.5: The response is partially grounded but contains some unsupported details, extrapolations, or assumptions.\n"
            f"- 1.0: The response is entirely faithful and every single statement is directly supported by the context.\n\n"
            f"Respond strictly in JSON format with two fields:\n"
            f"- \"score\": a floating-point number between 0.0 and 1.0 representing the groundedness.\n"
            f"- \"reason\": a brief, single-sentence explanation for the score.\n"
        )
        try:
            response = self._execute_with_retry(
                self.model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            return {"score": float(data.get("score", 0.0)), "reason": str(data.get("reason", ""))}
        except Exception as e:
            logger.error(f"Error evaluating groundedness: {e}")
            return {"score": 0.0, "reason": f"Evaluation failed: {str(e)}"}

    def evaluate_answer_relevance(self, query: str, response_text: str) -> dict:
        prompt = (
            f"You are an expert evaluator. Evaluate how relevant the generated response is to the user's query. "
            f"Does it directly address the query without going off-topic or being incomplete?\n\n"
            f"User Query: {query}\n"
            f"Response:\n{response_text}\n\n"
            f"Rate the answer relevance on a scale of 0.0 to 1.0, where:\n"
            f"- 0.0: The response does not answer or address the user's query at all.\n"
            f"- 0.5: The response is partially relevant but misses the main point or is off-topic.\n"
            f"- 1.0: The response directly, clearly, and completely answers the user's query.\n\n"
            f"Respond strictly in JSON format with two fields:\n"
            f"- \"score\": a floating-point number between 0.0 and 1.0 representing the relevance.\n"
            f"- \"reason\": a brief, single-sentence explanation for the score.\n"
        )
        try:
            response = self._execute_with_retry(
                self.model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text.strip())
            return {"score": float(data.get("score", 0.0)), "reason": str(data.get("reason", ""))}
        except Exception as e:
            logger.error(f"Error evaluating answer relevance: {e}")
            return {"score": 0.0, "reason": f"Evaluation failed: {str(e)}"}

    def evaluate_triad(self, query: str, context: str, response_text: str) -> dict:
        """
        Runs all three evaluations in parallel using a ThreadPoolExecutor.
        """
        logger.info("Starting RAG Triad evaluation in parallel...")
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_context = executor.submit(self.evaluate_context_relevance, query, context)
                future_groundedness = executor.submit(self.evaluate_groundedness, response_text, context)
                future_relevance = executor.submit(self.evaluate_answer_relevance, query, response_text)
                
                context_res = future_context.result()
                groundedness_res = future_groundedness.result()
                relevance_res = future_relevance.result()
                
            logger.info("Parallel RAG Triad evaluation completed successfully.")
            return {
                "context_relevance": context_res,
                "groundedness": groundedness_res,
                "answer_relevance": relevance_res
            }
        except Exception as e:
            logger.error(f"Error during parallel triad evaluation: {e}")
            return {
                "context_relevance": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"},
                "groundedness": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"},
                "answer_relevance": {"score": 0.0, "reason": f"Evaluation crashed: {str(e)}"}
            }
