"""Produce a prioritized action plan for dataset suitability.

Reads:
- data/processed/dataset_suitability.csv (produced by merge_datasets.generate_suitability_report)
- data/processed/missing_year_state_counts.csv (counts of rows that previously had missing year)

Writes:
- data/processed/suitability_action_plan.csv

"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"

SUIT_FILE = PROC / "dataset_suitability.csv"
MISSING_FILE = PROC / "missing_year_state_counts.csv"
OUT_FILE = PROC / "suitability_action_plan.csv"


def build_action_plan(min_years=5):
    if not SUIT_FILE.exists():
        print(f"Suitability file not found: {SUIT_FILE}. Try running merge_datasets.merge_all_datasets() to generate it.")
        return None

    suit = pd.read_csv(SUIT_FILE)
    miss = pd.read_csv(MISSING_FILE) if MISSING_FILE.exists() else pd.DataFrame(columns=["state_name","count"]) 

    miss = miss.rename(columns={"state_name":"state_name","count":"missing_rows"})

    out = suit.merge(miss, on="state_name", how="left")
    out["missing_rows"] = out["missing_rows"].fillna(0).astype(int)

    def recommend(r):
        if r["usable_for_sarima"]:
            return "OK"
        if r["missing_rows"] > 0:
            return "Check manual state->subdivision mapping / fill missing years"
        return "Needs historical data"

    out["action"] = out.apply(recommend, axis=1)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)
    print(f"Suitability action plan written to: {OUT_FILE}")
    # summary
    summary = out.groupby("action").size().reset_index(name="count")
    print(summary.to_string(index=False))
    return OUT_FILE


if __name__ == "__main__":
    build_action_plan()
