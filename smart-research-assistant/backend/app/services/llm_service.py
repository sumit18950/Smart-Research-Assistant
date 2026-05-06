"""
LLM service abstraction supporting OpenAI and Anthropic.
Handles token tracking for cost optimization.
"""

import re
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.logging import logger
from app.core.prompts import SYSTEM_PROMPT


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.provider = settings.llm_provider
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        if self.provider == "anthropic":
            self.llm = ChatAnthropic(
                model=settings.anthropic_model,
                anthropic_api_key=settings.anthropic_api_key,
                temperature=0.1,
                max_tokens=2048,
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                openai_api_key=settings.openai_api_key,
                temperature=0.1,
                max_tokens=2048,
            )

    async def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> dict:
        """Generate a response from the LLM with token tracking."""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content

        # Track tokens from response metadata (handle both OpenAI and Anthropic)
        metadata = getattr(response, "response_metadata", {})
        if self.provider == "anthropic":
            usage = metadata.get("usage", {})
            self.token_usage["prompt_tokens"] += usage.get("input_tokens", 0)
            self.token_usage["completion_tokens"] += usage.get("output_tokens", 0)
            self.token_usage["total_tokens"] += (
                usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            )
        else:
            usage = metadata.get("token_usage", {})
            if usage:
                self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                self.token_usage["total_tokens"] += usage.get("total_tokens", 0)

        # Extract confidence score from response
        confidence = self._extract_confidence(content)

        # Clean the confidence line from the answer
        answer = re.sub(r"\n*CONFIDENCE:\s*[\d.]+\s*$", "", content).strip()

        return {
            "answer": answer,
            "confidence": confidence,
            "token_usage": dict(self.token_usage),
        }

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from LLM response."""
        match = re.search(r"CONFIDENCE:\s*([\d.]+)", text)
        if match:
            try:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))
            except ValueError:
                pass
        return 0.5  # Default moderate confidence

    def get_token_usage(self) -> dict:
        return dict(self.token_usage)

    def reset_token_usage(self):
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
