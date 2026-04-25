import logging
import requests

from config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class LLMService:
    """Service to interact with the local Ollama API for text generation."""
    def __init__(self):
        self._url   = OLLAMA_URL
        self._model = OLLAMA_MODEL

    def chat(self, system: str, user_message: str, timeout: int = 120) -> str:
        """Sends a structured chat request to the LLM and returns the response text."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system}, # Sets behavior/context for the AI
                {"role": "user",   "content": user_message}, # The actual question or prompt
            ],
            "stream": False, # Disables streaming to get the full response in one JSON object
        }
        try:
            resp = requests.post(
                f"{self._url}/api/chat",
                json=payload,
                timeout=timeout, # High timeout because LLM inference can be slow on CPUs
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Ollama is not reachable. Make sure the ollama service is running.")
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out. The model may still be loading.")
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            raise RuntimeError(f"LLM error: {exc}") from exc

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self._url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


llm_service = LLMService()
