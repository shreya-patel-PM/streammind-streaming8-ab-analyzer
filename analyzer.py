"""
analyzer.py — Claude API call logic for Streaming Agent #8.

Wraps the Anthropic SDK call, handles markdown fence stripping
(defensive — Claude occasionally wraps responses despite prompt
instructions), and returns parsed JSON.
"""

import json
import re
from anthropic import Anthropic

from prompt import SYSTEM_PROMPT, build_user_message


# Model used by both Make and Streamlit implementations.
# Match this to whatever the Make HTTP module uses.
CLAUDE_MODEL = "claude-sonnet-4-5"

# Maximum tokens for the response. The schema produces ~600-900 tokens
# in practice; 4096 leaves ample headroom.
MAX_TOKENS = 4096

# Temperature. Lower = more consistent calibration. 0.2 worked well in
# Make.com testing across all 8 archetypes.
TEMPERATURE = 0.2


class AnalyzerError(Exception):
    """Raised when analysis fails for any reason."""
    pass


def _strip_markdown_fences(text):
    """
    Remove ```json ... ``` or ``` ... ``` wrappers from a string.

    Claude occasionally wraps JSON responses in markdown fences despite
    explicit prompt instructions not to. This strips them defensively.

    Returns the cleaned string.
    """
    # Remove opening ```json or ``` (with optional whitespace)
    text = re.sub(r'^\s*```(?:json)?\s*\n?', '', text)
    # Remove closing ``` (with optional whitespace)
    text = re.sub(r'\n?\s*```\s*$', '', text)
    return text.strip()


def analyze_experiment(experiment, api_key):
    """
    Send an experiment to Claude and return the parsed analysis.

    Args:
        experiment: dict with the experiment fields (test_name,
            hypothesis, variant_a, variant_b, primary_metric, a_value,
            b_value, sample_size, duration_days,
            statistical_significance, guardrail_notes, segment_notes,
            context_notes).
        api_key: Anthropic API key string.

    Returns:
        dict with the parsed memo:
            {
                "tldr": str,
                "interpretation": {
                    "primary_signal": str,
                    "confidence": "High" | "Medium" | "Low",
                    "confidence_reasoning": str
                },
                "recommendation": {
                    "action": "Ship" | "Kill" | "Iterate" | "Extend",
                    "reasoning": str
                },
                "open_questions": [str, ...],
                "watchouts": [str, ...]
            }

    Raises:
        AnalyzerError: if the API call fails or JSON parsing fails.
    """
    if not api_key:
        raise AnalyzerError(
            "No API key provided. Set ANTHROPIC_API_KEY in "
            ".streamlit/secrets.toml or as an environment variable."
        )

    client = Anthropic(api_key=api_key)

    user_message = build_user_message(experiment)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
    except Exception as e:
        raise AnalyzerError(f"API call failed: {str(e)}")

    # Extract the text content from the response
    if not response.content or len(response.content) == 0:
        raise AnalyzerError(
            f"Claude returned an empty response. "
            f"stop_reason: {response.stop_reason}"
        )

    raw_text = response.content[0].text

    # Strip markdown fences defensively
    cleaned_text = _strip_markdown_fences(raw_text)

    # Parse JSON
    try:
        memo = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise AnalyzerError(
            f"Failed to parse Claude response as JSON: {str(e)}. "
            f"Raw response: {cleaned_text[:300]}..."
        )

    # Validate basic schema structure
    required_keys = {
        "tldr", "interpretation", "recommendation",
        "open_questions", "watchouts"
    }
    missing_keys = required_keys - set(memo.keys())
    if missing_keys:
        raise AnalyzerError(
            f"Claude response missing required keys: {missing_keys}"
        )

    return memo