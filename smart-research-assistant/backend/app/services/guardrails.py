"""
Safety guardrails for the RAG system:
- Prompt injection detection
- Hallucination checking
- Low-confidence rejection
- Input sanitization
"""

import re
from app.core.config import get_settings
from app.core.logging import logger
from app.core.prompts import HALLUCINATION_CHECK_PROMPT
from app.models.schemas import QueryResponse


# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"override\s+(all\s+)?instructions",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if",
    r"<\s*/?system\s*>",
    r"\[\s*INST\s*\]",
]


class Guardrails:
    def __init__(self):
        self.settings = get_settings()
        self.confidence_threshold = self.settings.confidence_threshold
        self._injection_re = re.compile(
            "|".join(INJECTION_PATTERNS), re.IGNORECASE
        )

    def check_prompt_injection(self, query: str) -> tuple[bool, str]:
        """
        Detect potential prompt injection in user input.
        Returns (is_safe, reason).
        """
        if self._injection_re.search(query):
            logger.warning(f"Prompt injection detected in query: {query[:100]}")
            return False, "Query contains patterns that may be attempting prompt injection."

        # Check for excessive special characters (potential encoding attacks)
        special_ratio = sum(1 for c in query if not c.isalnum() and c not in " .,?!'-()") / max(len(query), 1)
        if special_ratio > 0.4:
            logger.warning(f"Suspicious character ratio in query: {special_ratio:.2f}")
            return False, "Query contains an unusual proportion of special characters."

        return True, ""

    def check_confidence(self, response: QueryResponse) -> QueryResponse:
        """
        If confidence is below threshold, add a warning to the response.
        """
        if response.confidence_score < self.confidence_threshold:
            logger.info(
                f"Low confidence response: {response.confidence_score:.2f} "
                f"(threshold: {self.confidence_threshold})"
            )
            response.answer = (
                f"**Low Confidence Warning** (score: {response.confidence_score:.2f}): "
                f"The following answer may not be fully supported by the available sources. "
                f"Please verify independently.\n\n{response.answer}"
            )
        return response

    def sanitize_input(self, text: str) -> str:
        """Basic input sanitization."""
        # Remove null bytes
        text = text.replace("\x00", "")
        # Limit length
        text = text[:2000]
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    async def verify_grounding(
        self, answer: str, context: str, llm_service
    ) -> dict:
        """
        Use the LLM to verify the answer is grounded in the context.
        Returns verification result with any unsupported claims.
        """
        prompt = HALLUCINATION_CHECK_PROMPT.format(
            context=context, answer=answer
        )
        result = await llm_service.generate(prompt)

        verified = "VERIFIED: true" in result["answer"].lower()
        unsupported = []

        claims_match = re.search(
            r"UNSUPPORTED_CLAIMS:\s*\[(.+?)\]", result["answer"], re.DOTALL
        )
        if claims_match:
            claims_text = claims_match.group(1)
            unsupported = [c.strip().strip("'\"") for c in claims_text.split(",")]

        return {
            "verified": verified,
            "unsupported_claims": unsupported,
            "raw_check": result["answer"],
        }
