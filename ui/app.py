import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# Config
PROJECT_ROOT = Path(__file__).parent.parent
API_URL = "http://localhost:8000"

sys.path.insert(0, str(PROJECT_ROOT))

# Helper functions
def load_file_to_api(file: Path) -> dict:
    """Call FastAPI /api/load with selected file path."""
    resp = requests.post(
        f"{API_URL}/api/load",
        json={"file_path": str(file)},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

def explore_data() -> dict:
    resp = requests.post(
        f"{API_URL}/api/explore",
        json={"data_key": "loaded_data"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

def generate_executive_report() -> dict:
    resp = requests.post(
        f"{API_URL}/api/report",
        json={"data_key": "loaded_data", "report_type": "executive_summary"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()

def get_api_health() -> dict:
    resp = requests.get(f"{API_URL}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()

# Streamlit UI
st.set_page_config(
    page_title="GOAT Data Analyst",
    page_icon="📊",
    layout="wide",
)

st.title("🐐 GOAT Data Analyst ")

# API status
with st.sidebar:
    st.header("API Status")
    try:
        health = get_api_health()
        st.success(
            f"API: {health.get('status')} · "
            f"Agents: {health.get('agents_registered')}"
        )
    except Exception as e:
        st.error(f"API not reachable: {e}")
        st.stop()

    st.markdown("---")
    st.header("Select Data File")
    data_dir = PROJECT_ROOT / "data"
    csv_files = sorted(p.name for p in data_dir.glob("*.csv"))
    csv_files_display = [f for f in csv_files if f != "sample_data.csv"] or csv_files

    selected_name = st.selectbox(
        "Choose CSV from data/ folder",
        options=csv_files_display,
        index=0 if csv_files_display else None,
    )

    load_button = st.button("📥 Load Data", type="primary")

if not selected_name:
    st.warning("No CSV files found in data/ directory.")
    st.stop()

selected_path = PROJECT_ROOT / "data" / selected_name

# Session state containers
if "load_result" not in st.session_state:
    st.session_state.load_result = None
if "explore_result" not in st.session_state:
    st.session_state.explore_result = None
if "report_result" not in st.session_state:
    st.session_state.report_result = None

# Load data
if load_button:
    with st.spinner(f"Loading {selected_name} via API…"):
        try:
            load_result = load_file_to_api(selected_path)
            st.session_state.load_result = load_result
            st.session_state.explore_result = None
            st.session_state.report_result = None
            st.success(
                f"Loaded {load_result.get('rows')} rows × "
                f"{load_result.get('columns')} columns."
            )
        except Exception as e:
            st.error(f"Load failed: {e}")

load_result = st.session_state.load_result

col_main, col_side = st.columns([3, 2])

with col_main:
    st.subheader("1. Data Preview")
    if load_result:
        st.caption(f"File: {load_result.get('file_path')}")
        try:
            cache_resp = requests.get(f"{API_URL}/api/cache/loaded_data", timeout=30)
            cache_resp.raise_for_status()
            cache_data = cache_resp.json()
            head_records = cache_data.get("head", [])
            if head_records:
                df_head = pd.DataFrame.from_records(head_records)
                st.dataframe(df_head, use_container_width=True, height=260)
            else:
                st.info("No preview rows available.")
        except Exception as e:
            st.error(f"Failed to fetch preview: {e}")
    else:
        st.info("Load a dataset from the sidebar to begin.")

with col_side:
    st.subheader("Quick Info")
    if load_result:
        st.metric("Rows", load_result.get("rows", 0))
        st.metric("Columns", load_result.get("columns", 0))
        st.write("Columns:")
        st.write(", ".join(load_result.get("columns_list", [])[:10]) + " …")
    else:
        st.write("Waiting for data…")

st.markdown("---")

# Explore section
st.subheader("2. Explore Data")

explore_col1, explore_col2 = st.columns([1, 2])
with explore_col1:
    explore_btn = st.button("🔍 Run Exploration")

if explore_btn:
    if not load_result:
        st.warning("Please load a dataset first.")
    else:
        with st.spinner("Exploring data…"):
            try:
                exp_result = explore_data()
                st.session_state.explore_result = exp_result
                st.success("Exploration complete.")
            except Exception as e:
                st.error(f"Explore failed: {e}")

exp_result = st.session_state.explore_result

with explore_col2:
    if exp_result:
        summary = exp_result.get("summary", {})
        st.write("**Numeric columns:**", summary.get("numeric_columns_count"))
        st.write("**Categorical columns:**", summary.get("categorical_columns_count"))

        dq = summary.get("data_quality", {})
        st.write("**Data quality:**")
        st.write(
            f"- Overall score: {dq.get('overall_quality_score')}\n"
            f"- Null %: {dq.get('null_percentage')}%\n"
            f"- Duplicate rows: {dq.get('duplicate_rows')} "
            f"({dq.get('duplicate_percentage')}%)"
        )

st.markdown("---")

# Report section
st.subheader("3. Generate Executive Summary Report")

report_btn = st.button("📄 Generate Report")

if report_btn:
    if not load_result:
        st.warning("Please load a dataset first.")
    else:
        with st.spinner("Generating report…"):
            try:
                rep_result = generate_executive_report()
                st.session_state.report_result = rep_result
                st.success("Report generated.")
            except Exception as e:
                st.error(f"Report failed: {e}")

rep_result = st.session_state.report_result

if rep_result:
    result = rep_result.get("result", {})
    st.write("### Summary Statement")
    st.write(result.get("summary_statement", ""))

    st.write("### Dataset Info")
    ds = result.get("dataset_info", {})
    st.json(ds)

    st.write("### Data Quality")
    dq = result.get("data_quality", {})
    st.json(dq)
