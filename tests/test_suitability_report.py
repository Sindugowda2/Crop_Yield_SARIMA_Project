import os
import pandas as pd
from src.suitability_report import build_action_plan


def test_build_action_plan(tmp_path):
    proc = tmp_path / "processed"
    proc.mkdir()

    # fake dataset_suitability.csv
    suit = pd.DataFrame(
        [
            {
                "state_name": "odisha",
                "crop": "rice",
                "year_count": 2,
                "usable_for_sarima": False,
            },
            {
                "state_name": "andhra pradesh",
                "crop": "rice",
                "year_count": 6,
                "usable_for_sarima": True,
            },
        ]
    )
    suit.to_csv(proc / "dataset_suitability.csv", index=False)

    # fake missing counts
    miss = pd.DataFrame([{"state_name": "odisha", "count": 6244}])
    miss.to_csv(proc / "missing_year_state_counts.csv", index=False)

    # copy into project structure location
    base = os.path.abspath(os.getcwd())
    target_proc = os.path.join(base, "data", "processed")
    os.makedirs(target_proc, exist_ok=True)
    suit.to_csv(os.path.join(target_proc, "dataset_suitability.csv"), index=False)
    miss.to_csv(os.path.join(target_proc, "missing_year_state_counts.csv"), index=False)

    out = build_action_plan()
    assert out is not None
    assert os.path.exists(out)
    df = pd.read_csv(out)
    assert "action" in df.columns
    # cleanup
    os.remove(os.path.join(target_proc, "dataset_suitability.csv"))
    os.remove(os.path.join(target_proc, "missing_year_state_counts.csv"))
    os.remove(out)
