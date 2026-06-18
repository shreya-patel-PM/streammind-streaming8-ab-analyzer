"""
test_analyzer.py — Quick test of analyze_experiment().
Run with: python test_analyzer.py
"""

import json
import toml

print("Loading API key...")
secrets = toml.load(".streamlit/secrets.toml")
api_key = secrets["ANTHROPIC_API_KEY"]
print(f"API key loaded: {api_key[:15]}... (length {len(api_key)})")

print("\nLoading sample experiments...")
with open("data/sample_experiments.json") as f:
    data = json.load(f)
experiments = data["experiments"]
print(f"Loaded {len(experiments)} experiments")

print("\nCalling Claude on EXP-008 (segment-conflict test — the v1 gap)...")
print("This takes 15-25 seconds. Please wait.\n")

from analyzer import analyze_experiment

result = analyze_experiment(experiments[7], api_key)

print("=" * 60)
print("RESULT:")
print("=" * 60)
print(json.dumps(result, indent=2))
print("=" * 60)
print(f"\nVerdict: {result['recommendation']['action']}")
print(f"Confidence: {result['interpretation']['confidence']}")
print(f"\nExpected: Iterate / High (Make couldn't process this experiment)")