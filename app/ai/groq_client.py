"""
Groq AI client — async, drop-in replacement for the old Anthropic/Claude client.
Uses AsyncGroq so FastAPI's event loop is never blocked.
Default model: llama-3.3-70b-versatile (fast, capable, free-tier friendly).
"""

import time
from typing import Any, Optional

from app.ai.cache import ai_cache
from app.core.config import get_settings

settings = get_settings()


class GroqClient:
    def __init__(self) -> None:
        self._client: Optional[Any] = None

    @property
    def client(self):
        """Lazily initialise the AsyncGroq client."""
        if self._client is None and settings.GROQ_API_KEY:
            from groq import AsyncGroq

            # 60 s is plenty — Groq is fast but network latency varies
            self._client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=60.0)
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        # Try cache first
        if use_cache:
            cached = await ai_cache.get_response(prompt)
            if cached:
                cached["cached"] = True
                return cached

        start = time.perf_counter()

        if not self.client:
            # No API key configured — return a mock response
            response_text = self._mock_response(prompt)
            tokens = len(prompt.split()) + len(response_text.split())
            confidence = 0.75
            model_label = "Mock (GROQ_API_KEY not set)"
        else:
            messages: list[dict[str, str]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            completion = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            response_text = completion.choices[0].message.content or ""
            usage = completion.usage
            tokens = (usage.prompt_tokens + usage.completion_tokens) if usage else 0
            confidence = 0.93
            model_label = f"Groq/{settings.GROQ_MODEL}"

        elapsed_ms = (time.perf_counter() - start) * 1000
        payload: dict[str, Any] = {
            "response": response_text,
            "confidence_score": confidence,
            "model_used": model_label,
            "response_time_ms": round(elapsed_ms, 2),
            "tokens_used": tokens,
            "cached": False,
        }

        if use_cache:
            await ai_cache.set_response(prompt, payload)

        return payload

    @staticmethod
    def _mock_response(prompt: str) -> str:
        lp = prompt.lower()
        if "quiz" in lp:
            return (
                '{"questions":[{"question":"What is the primary function of mitochondria?",'
                '"options":["Energy production","Protein synthesis","Cell division","Waste removal"],'
                '"answer":"Energy production",'
                '"explanation":"Mitochondria produce ATP through cellular respiration."}]}'
            )
        if "flashcard" in lp:
            return '{"cards":[{"front":"Mitochondria","back":"Organelle that produces ATP — the powerhouse of the cell."}]}'
        if "moderate" in lp or "toxic" in lp:
            return '{"is_safe":true,"confidence_score":0.96,"reason":"Content is appropriate for an educational platform."}'
        if "study plan" in lp:
            return '{"plan":[{"day":1,"topics":["Introduction"],"activities":["Read overview","Take notes"],"hours":2}]}'
        return (
            "I'm EduConnect AI. Add your GROQ_API_KEY to backend/.env to enable full AI capabilities. "
            "Get a free key at https://console.groq.com"
        )


groq_client = GroqClient()
