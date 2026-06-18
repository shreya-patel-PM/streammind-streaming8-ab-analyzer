# StreamMind — A/B Test Analyzer

A Streamlit-based AI agent that turns raw A/B test data into structured PM-grade analysis memos: ship/kill/iterate/extend recommendations with calibrated confidence, open questions, and watchouts.

This is the **Streamlit twin** of Streaming Agent #8. A Make.com version of the same agent exists in parallel — see *"Twin implementation"* below.

---

## What it does

Reads an A/B test result and produces a structured analysis memo via Claude Sonnet:

- **TL;DR** — one-sentence verdict
- **Primary signal** — what the data shows with magnitude
- **Confidence** — High / Medium / Low, with reasoning
- **Recommendation** — Ship / Kill / Iterate / Extend, with operational detail
- **Open questions** — specific follow-ups the test raises
- **Watchouts** — concrete risks of acting on the recommendation

The agent is calibrated against 6 explicit rules covering common failure modes: underpowered tests, segment conflicts, guardrail violations, external-event confounds, and secondary-metric surprises.

---

## The 8 analytical archetypes

The agent ships with 8 pre-loaded experiments covering the major analytical archetypes a streaming PM encounters:

| ID | Archetype | Expected verdict |
|---|---|---|
| EXP-001 | Clear winner | Ship / High |
| EXP-002 | Clear loser | Kill / High |
| EXP-003 | No significant difference | Kill / High |
| EXP-004 | Guardrail violation | Iterate / Medium |
| EXP-005 | Sample size too small (calibration test) | Extend / Low |
| EXP-006 | Surprising secondary metric | Iterate / Medium |
| EXP-007 | Test invalidated by external event | Extend / Low |
| EXP-008 | Conflicting segments | Iterate / High |

---

## Twin implementation

This agent ships in two implementations sharing the same Claude prompt and schema:

- **Make.com version** — production-style workflow with scheduled triggers, Google Sheets as data source, and Notion as the memo destination. Handles 7 of 8 archetypes; EXP-008 requires manual handling in v1 due to a Make-specific JSON escape inconsistency with multi-quote source fields.
- **Streamlit version** (this repo) — interactive demo with two input modes (sample selector and custom-entry form). Handles all 8 archetypes including EXP-008 because Python's `json.dumps` resolves the escape limitation natively.

---

## Stack

- **Streamlit** — UI framework
- **Anthropic SDK** — Claude API access
- **Python 3.13+** — language runtime
- **Claude Sonnet 4.5** — analytical model

---

## Run locally

### Prerequisites
- Python 3.13 or 3.14
- An Anthropic API key

### Setup

```bash
# Clone and enter the project
git clone https://github.com/shreya-patel-PM/streammind-streaming8-ab-analyzer.git
cd streammind-streaming8-ab-analyzer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set the API key
mkdir -p .streamlit
echo 'ANTHROPIC_API_KEY = "sk-ant-..."' > .streamlit/secrets.toml

# Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Architecture

data/sample_experiments.json   → 8 pre-loaded experiments

prompt.py                       → System prompt + user message builder

analyzer.py                     → Claude API call + JSON parsing

app.py                          → Streamlit UI (two tabs)

Each Claude call:
1. Builds a structured user message from the experiment dict
2. Sends with the calibrated system prompt (6 calibration rules + 5 quality rules)
3. Strips defensive markdown fences from the response
4. Parses JSON
5. Validates the schema before returning

---

## The calibration rules

The prompt includes 6 calibration rules that prevent common analytical failures:

1. **Underpowered tests** — when significance < 95% AND sample size < 5,000, confidence MUST be Low and action MUST be Extend
2. **Ship requires High confidence** — never Ship without High; Medium confidence positive results recommend Iterate instead
3. **Segment vs. aggregate** — when segments conflict, the aggregate is misleading; recommend Iterate with cohort-specific follow-up
4. **External events** — mid-test confounds make data unreliable; recommend Extend with clean rerun
5. **Secondary metric surprises** — flat primary + moving secondary means the wrong metric was chosen; recommend Iterate with redesign
6. **Guardrail violations** — never Ship if a guardrail metric degraded, even if primary won

EXP-005 specifically tests Rule 1 — its small sample (1,850) and low significance (86%) MUST produce Extend / Low. EXP-008 specifically tests Rule 3 — its aggregate "loss" hides device-segment wins.

---

## What I built and what I learned

Built as part of the StreamMind portfolio — 24 agents in 22 weeks, targeting streaming PM roles.

Key learnings from this build:

- **Twin implementations expose tooling tradeoffs.** Make.com and Streamlit both work, but their failure modes are different. Documenting where each shines is the real portfolio output.
- **Calibration rules need explicit examples.** The "confidence defaults to Medium" failure mode is real; preventing it requires showing Claude what wrong looks like, not just describing what right looks like.
- **Markdown fence stripping is mandatory.** Despite explicit prompt instructions, ~5-15% of Claude responses include ` ```json ` fences. Always strip defensively before parsing.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

Built by [Shreya Patel](https://www.linkedin.com/in/shreeaipatel/) 

Part of the **StreamMind** portfolio (27 AI agents across streaming, PM, and pharma domains).