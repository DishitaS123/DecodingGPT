from __future__ import annotations

from dataclasses import dataclass

from nist_chatgpt_eval.prompting import build_analysis_prompt


@dataclass(slots=True)
class AnalysisResult:
    label: str
    confidence: float
    rationale: str


class BaseLLMClient:
    def analyze(self, conversation: str) -> AnalysisResult:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """Offline heuristic client so the starter works without API access."""

    def analyze(self, conversation: str) -> AnalysisResult:
        text = conversation.lower()

        risky_terms = [
            "password",
            "api key",
            "token",
            "disable ssl",
            "hardcode",
            "bypass auth",
            "ignore validation",
        ]
        safe_terms = [
            "environment variable",
            "sanitize",
            "least privilege",
            "redact",
            "secret manager",
            "privacy",
            "secure",
        ]

        risky_hits = sum(term in text for term in risky_terms)
        safe_hits = sum(term in text for term in safe_terms)

        if risky_hits >= 2:
            return AnalysisResult(
                label="non_compliant",
                confidence=0.86,
                rationale="Conversation includes multiple indicators of insecure or sensitive handling.",
            )
        if risky_hits == 1:
            return AnalysisResult(
                label="needs_review",
                confidence=0.68,
                rationale="Conversation includes a potential security or privacy concern that should be reviewed.",
            )
        if safe_hits >= 1:
            return AnalysisResult(
                label="compliant",
                confidence=0.73,
                rationale="Conversation appears to encourage safer handling of code or data.",
            )
        return AnalysisResult(
            label="needs_review",
            confidence=0.55,
            rationale="Conversation does not clearly show either strong compliance or clear non-compliance.",
        )


class PromptOnlyClient(BaseLLMClient):
    """Stub showing where a real API-backed client would go."""

    def analyze(self, conversation: str) -> AnalysisResult:
        prompt = build_analysis_prompt(conversation)
        raise NotImplementedError(
            "Replace PromptOnlyClient with your API-backed implementation. "
            f"Prompt preview:\n\n{prompt}"
        )
