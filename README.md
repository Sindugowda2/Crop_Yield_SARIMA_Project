[![CI](https://github.com/<your-repo-owner>/<your-repo-name>/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-repo-owner>/<your-repo-name>/actions)

# Crop Yield Prediction using SARIMA

This project predicts future crop yield using SARIMA time-series model
based on rainfall, fertilizer, pesticide, and soil-related factors.

## Technologies
- Python
- Pandas
- SARIMA
- Streamlit

## Dataset
Government Open Data (India)

## Output
State-wise best crop recommendation

---

## Run the Streamlit UI (AgroDash) 🔧

1. Install requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the app from project root:

   ```bash
   streamlit run ui/app.py
   ```

3. The app will open at http://localhost:8501. Place custom images in `ui/assets/` (e.g., `logo.svg`, `hero.svg`) and the app will load them automatically.

Notes:
- The UI includes Dashboard, Crop Management, Weather, Market Prices, Settings and About pages.
- Some features use project modules (SARIMA training, dataset loading); if those modules are unavailable the app will show placeholders.

---

## Adding YEAR & seasonal rainfall to crop data

If your pipeline raises errors about a missing `YEAR` column (required by the time-series/SARIMA code), you can generate a merged dataset with YEAR and seasonal rainfall (kharif/rabi/whole_year) from the rainfall data by running:

```bash
python -m src.add_year_month
```

Notes:
- The script reads `data/processed/cleaned_crop_data.csv` and `data/raw/rainfall_validation.csv` and writes `data/processed/cleaned_crop_data_with_year.csv`.
- It performs exact matches, a small set of manual mappings for known mismatches (e.g. `odisha -> ORISSA`, `manipur/nagaland/mizoram -> NAGA MANI MIZO TRIPURA`, `puducherry -> TAMIL NADO`), and a fuzzy substring match to catch variants.
- After running, verify `year` is present and complete; if not, update `manual_map` inside `src/add_year_month.py` to add more mappings.

Validation:

You can run a quick validation script that checks the enriched dataset for `year` completeness and exercises the time-series builder:

```bash
python -m src.validate_dataset
```
