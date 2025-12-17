# ============================================
# helpers.py (fixed – stable – no circular import)
# ============================================

import streamlit as st
from pathlib import Path
import pandas as pd

# --------------------------------------------
# PATHS
# --------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "DATA"
RAW_DIR = BASE_DIR / "RAW"

# Provide MASTER_FILE for upload_page compatibility
MASTER_FILE = DATA_DIR / "MasterFullPricing.xlsx"

# --------------------------------------------
# SAFE RERUN
# --------------------------------------------
def safe_rerun():
    st.cache_data.clear()
    st.rerun()

# --------------------------------------------
# LOAD MASTER
# --------------------------------------------
def load_master():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"MasterFullPricing not found at {MASTER_FILE}")

    df = pd.read_excel(MASTER_FILE)
    df.columns = df.columns.str.strip()
    return df

# --------------------------------------------
# CACHE VERSION
# --------------------------------------------
@st.cache_data(show_spinner=False)
def load_master_cached():
    return load_master()
