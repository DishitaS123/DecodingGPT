from nist_chatgpt_eval.criteria import VALID_LABELS, criteria_summary


def build_analysis_prompt(conversation: str) -> str:
    labels = ", ".join(VALID_LABELS)
    return f"""You are evaluating a conversation between a developer and ChatGPT.

Use the following NIST-inspired criteria:
{criteria_summary()}

Return a single label from: {labels}
Also provide a short rationale.

Conversation:
{conversation}
"""
