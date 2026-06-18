"""
app.py — StreamMind A/B Analyzer (Streaming Agent #8 Streamlit twin).

Two-tab interface:
- Tab 1: pick from 8 pre-loaded experiments
- Tab 2: enter your own experiment data
"""

import json
import os
import toml
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
    if "ANTHROPIC_API_KEY" in st.secrets:
        return st.secrets["ANTHROPIC_API_KEY"]
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
    col1, col2 = st.columns(2)
    with col1:
        action = memo["recommendation"]["action"]
        st.metric("Recommendation", action)
    with col2:
        confidence = memo["interpretation"]["confidence"]
        st.metric("Confidence", confidence)

    st.markdown("---")

    st.markdown("#### TL;DR")
    st.info(memo["tldr"])

    st.markdown("#### Primary signal")
    st.markdown(memo["interpretation"]["primary_signal"])

    st.markdown("#### Confidence reasoning")
    st.markdown(memo["interpretation"]["confidence_reasoning"])

    st.markdown("#### Recommendation reasoning")
    st.markdown(memo["recommendation"]["reasoning"])

    st.markdown("#### Open questions")
    for q in memo["open_questions"]:
        st.markdown(f"- {q}")

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

    tab1, tab2 = st.tabs(
        ["Try a sample experiment", "Analyze your own"]
    )

    # ─────────────────────────────────────────────────────────────
    # Tab 1: sample experiment selector
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.markdown(
            "Pick one of 8 pre-loaded experiments spanning the major "
            "analytical archetypes — clear winners, mixed signals, "
            "underpowered tests, segment conflicts, and more."
        )

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

        selected_index = options.index(selected_label)
        selected_experiment = experiments[selected_index]

        with st.expander("View experiment data", expanded=False):
            render_experiment_details(selected_experiment)

        if st.button(
            "Analyze with Claude",
            type="primary",
            key="sample_analyze_btn"
        ):
            with st.spinner(
                "Claude is analyzing the experiment (~15-25 seconds)..."
            ):
                try:
                    memo = analyze_experiment(selected_experiment, api_key)
                    st.session_state["sample_memo"] = memo
                    st.session_state["sample_memo_id"] = selected_experiment["id"]
                except AnalyzerError as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.session_state.pop("sample_memo", None)

        if "sample_memo" in st.session_state:
            st.markdown("---")
            st.markdown(
                f"### Analysis for {st.session_state['sample_memo_id']}"
            )
            render_memo(st.session_state["sample_memo"])

    # ─────────────────────────────────────────────────────────────
    # Tab 2: custom experiment entry
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.markdown(
            "Enter your own experiment data below. All fields except "
            "Guardrail / Segment / Context Notes are required."
        )

        with st.form("custom_experiment_form", clear_on_submit=False):
            test_name = st.text_input(
                "Test name",
                placeholder="e.g., Homepage CTA color — blue vs. green",
                key="custom_test_name"
            )

            hypothesis = st.text_area(
                "Hypothesis",
                placeholder="We believe [change] will result in [outcome] because [reason].",
                height=80,
                key="custom_hypothesis"
            )

            col1, col2 = st.columns(2)
            with col1:
                variant_a = st.text_input(
                    "Variant A (Control)",
                    placeholder="Description of the control",
                    key="custom_variant_a"
                )
            with col2:
                variant_b = st.text_input(
                    "Variant B (Treatment)",
                    placeholder="Description of the treatment",
                    key="custom_variant_b"
                )

            primary_metric = st.text_input(
                "Primary metric",
                placeholder="e.g., Click-through rate, Day-7 retention",
                key="custom_primary_metric"
            )

            col3, col4 = st.columns(2)
            with col3:
                a_value = st.text_input(
                    "Variant A result",
                    placeholder="e.g., 3.21 or 18.2%",
                    key="custom_a_value"
                )
            with col4:
                b_value = st.text_input(
                    "Variant B result",
                    placeholder="e.g., 3.68 or 19.4%",
                    key="custom_b_value"
                )

            col5, col6 = st.columns(2)
            with col5:
                sample_size = st.text_input(
                    "Sample size per arm",
                    placeholder="e.g., 48500",
                    key="custom_sample_size"
                )
            with col6:
                duration_days = st.text_input(
                    "Test duration (days)",
                    placeholder="e.g., 14",
                    key="custom_duration"
                )

            statistical_significance = st.text_input(
                "Statistical significance",
                placeholder="e.g., p < 0.001 (99.9%) or p = 0.14 (86%)",
                key="custom_significance"
            )

            st.markdown("---")
            st.markdown(
                "**Optional context** — provide when relevant for richer analysis."
            )

            guardrail_notes = st.text_area(
                "Guardrail metrics (optional)",
                placeholder="Movement on metrics other than the primary (e.g., 'Time-on-page decreased 11% in Variant B')",
                height=70,
                key="custom_guardrail"
            )

            segment_notes = st.text_area(
                "Segment breakdown (optional)",
                placeholder="Performance by user segment (e.g., 'Mobile users: A 71%, B 58%')",
                height=70,
                key="custom_segment"
            )

            context_notes = st.text_area(
                "Additional context (optional)",
                placeholder="External events, secondary metrics, or other context Claude should consider",
                height=70,
                key="custom_context"
            )

            submitted = st.form_submit_button(
                "Analyze with Claude",
                type="primary"
            )

        if submitted:
            required_fields = {
                "Test name": test_name,
                "Hypothesis": hypothesis,
                "Variant A": variant_a,
                "Variant B": variant_b,
                "Primary metric": primary_metric,
                "Variant A result": a_value,
                "Variant B result": b_value,
                "Sample size": sample_size,
                "Duration": duration_days,
                "Statistical significance": statistical_significance,
            }
            missing = [
                name for name, val in required_fields.items()
                if not val.strip()
            ]

            if missing:
                st.error(
                    "Please fill in these required fields: "
                    + ", ".join(missing)
                )
            else:
                custom_experiment = {
                    "test_name": test_name,
                    "hypothesis": hypothesis,
                    "variant_a": variant_a,
                    "variant_b": variant_b,
                    "primary_metric": primary_metric,
                    "a_value": a_value,
                    "b_value": b_value,
                    "sample_size": sample_size,
                    "duration_days": duration_days,
                    "statistical_significance": statistical_significance,
                    "guardrail_notes": guardrail_notes,
                    "segment_notes": segment_notes,
                    "context_notes": context_notes,
                }

                with st.spinner(
                    "Claude is analyzing your experiment (~15-25 seconds)..."
                ):
                    try:
                        memo = analyze_experiment(custom_experiment, api_key)
                        st.session_state["custom_memo"] = memo
                        st.session_state["custom_test_name_display"] = test_name
                    except AnalyzerError as e:
                        st.error(f"Analysis failed: {str(e)}")
                        st.session_state.pop("custom_memo", None)

        if "custom_memo" in st.session_state:
            st.markdown("---")
            st.markdown(
                f"### Analysis for {st.session_state['custom_test_name_display']}"
            )
            render_memo(st.session_state["custom_memo"])


if __name__ == "__main__":
    main()