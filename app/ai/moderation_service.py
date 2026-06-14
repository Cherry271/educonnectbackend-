import json

from app.ai.groq_client import groq_client as claude_client
from app.schemas.common import ModerationResult


class ModerationService:
    async def moderate(self, content: str) -> ModerationResult:
        prompt = (
            f"Moderate this educational platform content for toxicity, spam, harassment, "
            f"and inappropriate language. Return JSON only: "
            f'{{"is_safe": bool, "confidence_score": float, "reason": str}}\n\n'
            f"Content: {content[:2000]}"
        )
        result = await claude_client.generate(
            prompt, system="You are a content moderation AI.", use_cache=False
        )

        try:
            data = json.loads(result["response"])
            return ModerationResult(**data)
        except (json.JSONDecodeError, ValueError):
            lower = content.lower()
            toxic_words = ["hate", "kill", "spam", "scam"]
            is_safe = not any(w in lower for w in toxic_words)
            return ModerationResult(
                is_safe=is_safe,
                confidence_score=0.85 if is_safe else 0.7,
                reason="Rule-based fallback check"
                if is_safe
                else "Potentially inappropriate content detected",
            )


moderation_service = ModerationService()
