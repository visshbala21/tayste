import hashlib
import json
import logging
from typing import Optional, Type
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_input(data: dict) -> str:
    """Deterministic hash of input data for caching."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


class LLMClient:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            if not self.available:
                raise RuntimeError("OPENAI_API_KEY not configured")
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_model: Type[BaseModel],
        temperature: float = 0.3,
    ) -> Optional[BaseModel]:
        """Generate structured JSON output from OpenAI, validated via Pydantic."""
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            parsed = json.loads(text)
            return output_model.model_validate(parsed)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def generate_safe(
        self,
        system_prompt: str,
        user_prompt: str,
        output_model: Type[BaseModel],
        fallback: Optional[BaseModel] = None,
        temperature: float = 0.3,
    ) -> Optional[BaseModel]:
        """Generate with safe fallback if LLM unavailable or fails."""
        if not self.available:
            logger.warning("LLM unavailable, returning fallback")
            return fallback
        try:
            return self.generate_structured(system_prompt, user_prompt, output_model, temperature)
        except Exception as e:
            logger.error(f"LLM call failed after retries: {e}")
            return fallback


llm_client = LLMClient()
