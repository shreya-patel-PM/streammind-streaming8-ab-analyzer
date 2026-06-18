"""
app.py — StreamMind A/B Analyzer (Streaming Agent #8 Streamlit twin).

Two-tab interface:
- Tab 1: pick from 8 pre-loaded experiments
- Tab 2: enter your own experiment (added in Stage 7)
"""

import json
import os
import streamlit as st

from analyzer import analyze_experiment, AnalyzerError


# ─────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="StreamMind — A/B Analyzer",
    page_icon="🧪",
    layout="wide"
)


# ─────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────

@st.cache_data
def load_experiments():
    """Load the 8 sample experiments from data/sample_experiments.json."""
    with open("data/sample_experiments.json") as f:
        data = json.load(f)
    return data["experiments"]


def get_api_key():
    """Get the Anthropic API key from secrets or environment."""
    # Streamlit Cloud and local .streamlit/secrets.toml
    if "ANTHROPIC_API_KEY" in st.secrets:
        return st.secrets["ANTHROPIC_API_KEY"]
    # Fallback to environment variable
    return os.environ.get("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────

def render_experiment_details(experiment):
    """Show the experiment data being analyzed."""
    st.markdown("#### Experiment data")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Variant A (Control):** {experiment['variant_a']}")
        st.markdown(f"**Variant A result:** {experiment['a_value']}")
        st.markdown(f"**Sample size per arm:** {experiment['sample_size']}")
    with col2:
        st.markdown(f"**Variant B (Treatment):** {experiment['variant_b']}")
        st.markdown(f"**Variant B result:** {experiment['b_value']}")
        st.markdown(f"**Statistical significance:** {experiment['statistical_significance']}")

    st.markdown(f"**Primary Metric:** {experiment['primary_metric']}")
    st.markdown(f"**Hypothesis:** {experiment['hypothesis']}")

    if experiment.get("guardrail_notes"):
        st.markdown(f"**Guardrail metrics:** {experiment['guardrail_notes']}")
    if experiment.get("segment_notes"):
        st.markdown(f"**Segment breakdown:** {experiment['segment_notes']}")
    if experiment.get("context_notes"):
        st.markdown(f"**Additional context:** {experiment['context_notes']}")


def render_memo(memo):
    """Render the parsed analysis memo."""
    # Top-line verdict cards
    col1, col2 = st.columns(2)
    with col1:
        action = memo["recommendation"]["action"]
        st.metric("Recommendation", action)
    with col2:
        confidence = memo["interpretation"]["confidence"]
        st.metric("Confidence", confidence)

    st.markdown("---")

    # TL;DR
    st.markdown("#### TL;DR")
    st.info(memo["tldr"])

    # Interpretation
    st.markdown("#### Primary signal")
    st.markdown(memo["interpretation"]["primary_signal"])

    st.markdown("#### Confidence reasoning")
    st.markdown(memo["interpretation"]["confidence_reasoning"])

    # Recommendation
    st.markdown("#### Recommendation reasoning")
    st.markdown(memo["recommendation"]["reasoning"])

    # Open questions
    st.markdown("#### Open questions")
    for q in memo["open_questions"]:
        st.markdown(f"- {q}")

    # Watchouts
    st.markdown("#### Watchouts")
    for w in memo["watchouts"]:
        st.markdown(f"- {w}")


# ─────────────────────────────────────────────────────────────────
# Main app
# ─────────────────────────────────────────────────────────────────

def main():
    st.title("StreamMind — A/B Analyzer")
    st.caption(
        "Structured ship / kill / iterate / extend recommendations for "
        "streaming A/B tests. Powered by Claude Sonnet."
    )

    api_key = get_api_key()
    if not api_key:
        st.error(
            "No ANTHROPIC_API_KEY found. Add it to "
            ".streamlit/secrets.toml or as an environment variable."
        )
        st.stop()

    experiments = load_experiments()

    # ─────────────────────────────────────────────────────────────
    # Tab 1: pick a sample experiment
    # ─────────────────────────────────────────────────────────────

    tab1, tab2 = st.tabs(
        ["Try a sample experiment", "Analyze your own"]
    )

    with tab1:
        st.markdown(
            "Pick one of 8 pre-loaded experiments spanning the major "
            "analytical archetypes — clear winners, mixed signals, "
            "underpowered tests, segment conflicts, and more."
        )

        # Build the dropdown options: "EXP-001: <test_name> (<archetype>)"
        options = [
            f"{exp['id']}: {exp['test_name']} ({exp['archetype']})"
            for exp in experiments
        ]

        selected_label = st.selectbox(
            "Choose an experiment",
            options,
            index=0,
            key="sample_selector"
        )

        # Resolve the label back to the experiment dict
        selected_index = options.index(selected_label)
        selected_experiment = experiments[selected_index]

        # Show the experiment details
        with st.expander("View experiment data", expanded=False):
            render_experiment_details(selected_experiment)

        # Analyze button
        if st.button(
            "Analyze with Claude",
            type="primary",
            key="sample_analyze_btn"
        ):
            with st.spinner(
                "Claude is analyzing the experiment "
                "(~15-25 seconds)..."
            ):
                try:
                    memo = analyze_experiment(
                        selected_experiment, api_key
                    )
                    st.session_state["sample_memo"] = memo
                    st.session_state["sample_memo_id"] = (
                        selected_experiment["id"]
                    )
                except AnalyzerError as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.session_state.pop("sample_memo", None)

        # Render the most recent analysis (if any)
        if "sample_memo" in st.session_state:
            st.markdown("---")
            st.markdown(
                f"### Analysis for "
                f"{st.session_state['sample_memo_id']}"
            )
            render_memo(st.session_state["sample_memo"])

    with tab2:
        st.markdown(
            "Custom experiment entry form coming in Stage 7."
        )


if __name__ == "__main__":
    main()