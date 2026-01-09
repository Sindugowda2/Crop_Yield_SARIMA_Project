import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from pathlib import Path

# try to import existing project helpers, but fail gracefully
try:
    from src.data_loader import load_final_dataset, load_cleaned_dataset
except Exception:
    load_final_dataset = None
    load_cleaned_dataset = None

try:
    from src.data_preprocessing import prepare_sarima_series
except Exception:
    prepare_sarima_series = None

try:
    from src.sarima_model import train_sarima
except Exception:
    train_sarima = None

# Page config
st.set_page_config(page_title="AgroDash", page_icon="🌾", layout="wide")

# Styling
PRIMARY = "#2E8B57"  # sea green
ACCENT = "#FFD54F"   # warm yellow
BG = "#F8FFF5"

st.markdown(f"""
<style>
[data-testid='stAppViewContainer'] {{ background: {BG}; }}
.header {{ background: linear-gradient(90deg, {PRIMARY}, #47C988); padding: 10px; border-radius: 8px; }}
.card {{ background: white; padding: 12px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
</style>
""", unsafe_allow_html=True)

# assets path
ASSETS = Path(__file__).parent / "assets"
logo_path = ASSETS / "logo.svg"
hero_path = ASSETS / "hero.svg"

# Sidebar navigation
if logo_path.exists():
    st.sidebar.image(str(logo_path))
else:
    st.sidebar.title("🌾 AgroDash")

# Dataset selection (prefers enriched with YEAR when available)
processed_dir = Path(__file__).parent.parent / "data" / "processed"
cleaned_path = processed_dir / "cleaned_crop_data.csv"
enriched_path = processed_dir / "cleaned_crop_data_with_year.csv"
final_path = Path(__file__).parent.parent / "data" / "final_dataset.csv"

dataset_options = ["Auto (prefer enriched)"]
if enriched_path.exists():
    dataset_options.append("Enriched (with YEAR)")
if cleaned_path.exists():
    dataset_options.append("Cleaned (raw)")
if final_path.exists():
    dataset_options.append("Final dataset")

dataset_choice = st.sidebar.selectbox("Dataset source", dataset_options, index=0)

menu = st.sidebar.radio("Navigate", ["Dashboard", "Crop Management", "Weather", "Market Prices", "Settings & Profiles", "About & Contact"], index=0)

# Load app-level dataset (for dashboard metrics)
data_root = Path(__file__).parent.parent / "data"
app_data = None
dataset_source = None
try:
    if dataset_choice == "Final dataset" and load_final_dataset:
        app_data = load_final_dataset()
        dataset_source = 'final'
    elif dataset_choice == "Enriched (with YEAR)" and load_cleaned_dataset:
        app_data, dataset_source = load_cleaned_dataset(prefer_enriched=True)
    elif dataset_choice == "Cleaned (raw)" and load_cleaned_dataset:
        app_data, dataset_source = load_cleaned_dataset(prefer_enriched=False)
    else:
        # Auto or any other option: prefer enriched when available
        if load_cleaned_dataset:
            app_data, dataset_source = load_cleaned_dataset(prefer_enriched=True)
        elif load_final_dataset:
            app_data = load_final_dataset()
            dataset_source = 'final'
except Exception:
    # Last-resort fallback
    try:
        app_data = pd.read_csv(data_root / "processed" / "cleaned_crop_data.csv")
        dataset_source = 'cleaned-fallback'
    except Exception:
        app_data = None
        dataset_source = None

# show active dataset in sidebar
if dataset_source:
    st.sidebar.info(f"Using dataset: {dataset_source}")
else:
    st.sidebar.warning("No dataset available — please add cleaned or final dataset into data/processed/")

# Top header row
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div class='header'><h1 style='color:white'>🌾 AgroDash — Crop Yield & Advisory</h1></div>", unsafe_allow_html=True)
        st.write("A colorful dashboard to monitor crop yields, weather, and market prices.")
    with col2:
        if hero_path.exists():
            st.image(str(hero_path))

# ===== Dashboard =====
if menu == "Dashboard":
    st.header("📊 Dashboard — Today's snapshot")
    if dataset_source and 'enrich' in str(dataset_source).lower():
        st.info("Using enriched dataset with YEAR — time-series and forecasts will be available.")
    elif dataset_source and 'cleaned' in str(dataset_source).lower():
        st.info("Using cleaned dataset (no YEAR) — some time-series features may be disabled.")
    # top stats
    col1, col2, col3, col4 = st.columns(4)
    # compute dynamic metrics when data available
    def get_states_count(df):
        if df is None:
            return 0
        for col in ['state_name','State_Name','STATE_NAME','State_Name']:
            if col in df.columns:
                return df[col].nunique()
        return 0

    def get_avg_yield(df):
        if df is None:
            return None
        candidates = ['yield_ton_per_hec','Yield_ton_per_hec','yield','Yield']
        for c in candidates:
            if c in df.columns:
                try:
                    return round(df[c].dropna().astype(float).mean(), 2)
                except Exception:
                    return None
        return None

    active_states = get_states_count(app_data)
    avg_yield = get_avg_yield(app_data)

    col1.metric("Active States", str(active_states) if active_states else "—")
    col2.metric("Alerts", "5", "-1")
    col3.metric("Avg Yield (t/ha)", str(avg_yield) if avg_yield is not None else "—")
    col4.metric("Forecast Ready", "Yes")

    st.markdown("### Quick Alerts")
    st.info("⚠️ Low rainfall alert for *Karnataka* — 20% below normal")
    st.success("✅ Fertilizer availability stable in your region")

    st.markdown("### Action Buttons")
    a1, a2, a3 = st.columns(3)
    if a1.button("📥 Refresh Data"):
        import time
        st.experimental_set_query_params(_refresh=int(time.time()))
        st.success("Refresh requested — reloading data")
    if a2.button("🔔 Send Alerts"):
        st.success("Alerts queued")
    if a3.button("📄 Export Report"):
        st.success("Report exported to Downloads")

# ===== Crop Management =====
elif menu == "Crop Management":
    st.header("🌱 Crop Management")
    sub = st.selectbox("Choose view", ["Field View", "Input Data", "ARIMA Prediction", "Recommendations"])

    # Prefer the app-level loaded dataset, otherwise try to load based on choice
    df = app_data
    if df is None:
        try:
            if dataset_choice == "Final dataset" and load_final_dataset:
                df = load_final_dataset()
                st.success("Loaded final_dataset.csv")
            elif dataset_choice == "Enriched (with YEAR)" and load_cleaned_dataset:
                df, _ = load_cleaned_dataset(prefer_enriched=True)
                st.success("Loaded enriched cleaned_crop_data_with_year.csv")
            elif dataset_choice == "Cleaned (raw)" and load_cleaned_dataset:
                df, _ = load_cleaned_dataset(prefer_enriched=False)
                st.success("Loaded cleaned_crop_data.csv")
            else:
                # auto fallback
                if load_cleaned_dataset:
                    df, src = load_cleaned_dataset(prefer_enriched=True)
                    st.success(f"Loaded {src} dataset")
                elif load_final_dataset:
                    df = load_final_dataset()
                    st.success("Loaded final_dataset.csv")
        except Exception as e:
            st.warning(f"Could not load selected dataset: {e}")

    # column helper
    def find_col(df, candidates):
        if df is None:
            return None
        cols = [c for c in df.columns]
        for cand in candidates:
            for c in cols:
                if cand.lower() == c.lower():
                    return c
        # try contains
        for cand in candidates:
            for c in cols:
                if cand.lower() in c.lower():
                    return c
        return None

    if sub == "Field View":
        st.subheader("Field View")
        st.write("(Map / grid of fields would appear here)")
        # show image using normal if/else to avoid returning DeltaGenerator object
        field_svg = ASSETS / "field_placeholder.svg"
        if field_svg.exists():
            st.image(str(field_svg))
        else:
            st.write("[Field image placeholder]")

        # State search: allow quick search/select of all Indian states present in dataset
        def get_states(df):
            if df is None:
                return []
            for col in ['state_name','State_Name','STATE_NAME','State_Name']:
                if col in df.columns:
                    return sorted(df[col].astype(str).str.title().unique())
            return []

        states = get_states(df)
        state_query = st.text_input("Search states")
        if states:
            if state_query:
                matches = [s for s in states if state_query.lower() in s.lower()]
                if matches:
                    state_sel = st.selectbox("Matched States", matches)
                else:
                    st.info("No matching states found")
                    state_sel = None
            else:
                state_sel = st.selectbox("Select State", states)
        else:
            st.info("No state data available in dataset")
            state_sel = None

        if state_sel:
            st.write(f"Selected state: {state_sel}")

    if sub == "Input Data":
        st.subheader("Input Data")
        st.write("Upload CSV with field measurements")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            df_up = pd.read_csv(uploaded)
            st.dataframe(df_up.head())

    if sub == "ARIMA Prediction":
        st.subheader("ARIMA / SARIMA Prediction")
        state_col = find_col(df, ['state_name','State_Name','STATE_NAME','state'])
        crop_col = find_col(df, ['crop','Crop'])
        year_col = find_col(df, ['year'])

        if df is None or state_col is None or crop_col is None:
            st.info("Dataset not loaded or missing state/crop columns. Check dataset selection in the sidebar.")
        else:
            state = st.selectbox("State", sorted(df[state_col].astype(str).unique()))
            crop = st.selectbox("Crop", sorted(df[crop_col].astype(str).unique()))

            if st.button("Run Forecast"):
                if prepare_sarima_series and train_sarima:
                    if year_col is None:
                        st.error("Selected dataset doesn't contain a 'year' column required for time-series. Use an enriched dataset.")
                    else:
                        try:
                            ts = prepare_sarima_series(df, state, crop)
                            forecast = train_sarima(ts)
                            st.line_chart(forecast)
                        except Exception as e:
                            # Try tolerant fallback matching when exact filter yields no data
                            st.warning(f"Initial forecast failed: {e}. Trying tolerant matching...")

                            def find_best_match(col, val):
                                val_l = val.lower().strip()
                                candidates = sorted(df[col].astype(str).unique())
                                # 1) exact ignore-case
                                for c in candidates:
                                    if c.lower().strip() == val_l:
                                        return c
                                # 2) substring contains
                                for c in candidates:
                                    if val_l in c.lower() or c.lower() in val_l:
                                        return c
                                # 3) token overlap
                                val_tokens = [t for t in val_l.split() if t]
                                for c in candidates:
                                    cl = c.lower()
                                    if any(tok in cl for tok in val_tokens):
                                        return c
                                return None

                            state_match = find_best_match(state_col, state)
                            crop_match = find_best_match(crop_col, crop)

                            if state_match is None or crop_match is None:
                                st.error(f"Forecast failed: {e}")
                            else:
                                st.info(f"Using matched values: State='{state_match}', Crop='{crop_match}'")
                                try:
                                    ts2 = prepare_sarima_series(df, state_match, crop_match)
                                    forecast2 = train_sarima(ts2)
                                    st.line_chart(forecast2)
                                except Exception as e2:
                                    st.error(f"Forecast failed after tolerant matching: {e2}")
                else:
                    st.warning("Modeling functions not available in this environment")

    if sub == "Recommendations":
        st.subheader("Recommendations")
        st.write("(Use your recommender module to show best/worst crops per state)")

# ===== Weather =====
elif menu == "Weather":
    st.header("☀️ Weather: Current & Forecast")
    st.write("This panel shows current weather and 7-day forecast and agro-advisories.")
    # placeholders
    c1, c2 = st.columns(2)
    c1.metric("Temperature (°C)", "29.2")
    c2.metric("Rainfall (mm)", "3.4")
    st.info("Agro-advisory: Delay transplanting in flood-prone zones.")

# ===== Market Prices =====
elif menu == "Market Prices":
    st.header("🏷️ Local Market Prices")
    st.write("Shows recent local mandi prices and trends.")
    st.table(pd.DataFrame({'Crop': ['Rice','Wheat','Potato'], 'Price (₹/qtl)': [2200, 1900, 800]}))

# ===== Settings & Profiles =====
elif menu == "Settings & Profiles":
    st.header("⚙️ Settings & Profiles")
    st.write("User profile and app settings")
    import re
    users_file = Path(__file__).parent.parent / "data" / "processed" / "users.csv"
    with st.form("profile_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        colour = st.color_picker("Theme color", value=PRIMARY)
        submitted = st.form_submit_button("Save")

    if submitted:
        if not name or not email:
            st.error("Please provide both name and email.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Please provide a valid email address.")
        else:
            row = {"name": name, "email": email, "colour": colour}
            try:
                if users_file.exists():
                    users = pd.read_csv(users_file)
                    users = pd.concat([users, pd.DataFrame([row])], ignore_index=True)
                else:
                    users = pd.DataFrame([row])
                users.to_csv(users_file, index=False)
                st.success("Profile saved")
            except Exception as e:
                st.error(f"Could not save profile: {e}")

# ===== About & Contact =====
elif menu == "About & Contact":
    st.header("About AgroDash")
    st.write("A demo app for crop yield prediction, weather advisories and local market monitoring.")
    st.write("Contact: support@example.com")

# Footer
st.markdown("---")
st.caption("Built with ❤️ for agricultural insights — customizable and extensible.")
