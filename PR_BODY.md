# PR: chore: auto-update manual mapping & suitability action plan

**Short summary:** Conservative automated mapping suggestions + a prioritized suitability action plan to make state/crop combos SARIMA-ready with minimal manual review.

## Summary ✅
This PR applies conservative automated suggestions to `data/processed/manual_state_to_subdivision.csv` and adds an updated `data/processed/suitability_action_plan.csv` that prioritizes (state, crop) combinations for SARIMA readiness.

## What changed 🔧
- **Added/updated** `data/processed/manual_state_to_subdivision.csv` (auto-suggested mappings). Backups are created before any write (timestamped `.bak.*`).
- **Added** `data/processed/suitability_action_plan.csv` — merged suitability + missing-year counts with a recommended `action` column.
- **Added** workflow: `.github/workflows/auto_manual_map_pr.yml` — runs `src/manual_map_updater`, applies suggestions, and opens a draft PR automatically (on dispatch or schedule).
- **New scripts:** `src/manual_map_updater.py`, `src/suitability_report.py` (with unit tests).

## Why 🎯
Automates conservative mapping fixes and surfaces a prioritized action plan so you can focus on validating the small set of changes that improve SARIMA coverage and data quality.

## How to test locally 🔁
1. Generate merged dataset & suitability:
   ```bash
   python -m src.merge_datasets
   ```
2. Build action plan:
   ```bash
   python -m src.suitability_report
   ```
3. Dry-run mapping suggestions:
   ```bash
   python -m src.manual_map_updater
   ```
4. (Optional) Apply suggestions locally (creates backups):
   ```bash
   python -m src.manual_map_updater --apply
   ```
5. Run tests:
   ```powershell
   & "venv/Scripts/python.exe" -m pytest -q
   ```

## Review checklist ✅
- [ ] Confirm new mappings in `manual_state_to_subdivision.csv` are correct and conservative.
- [ ] Verify `suitability_action_plan.csv` recommendations align with expectations.
- [ ] Backups exist for any overwritten manual mapping files (timestamped `.bak.*`).
- [ ] Ensure CI (lint/test) passes and scheduled cadence is acceptable.

## Suggested branch & commit message
- Branch: `auto/manual-mapping-<YYYYMMDD-HHMMSS>` (workflow will create timestamped branch automatically)
- Commit message: `chore(ci): add automated manual mapping PR workflow, updater, and action plan`

---

*If you want, I can also change the workflow to run on push for this branch or create a GitHub Issue instead of a PR for lower friction — tell me what you prefer.*
