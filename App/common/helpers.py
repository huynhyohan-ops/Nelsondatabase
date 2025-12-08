from pathlib import Path
import sys
import streamlit as st
import pandas as pd

# ============================================================
# PATH CONFIG — luôn đúng kể cả anh chạy từ đâu
# ============================================================

# File này nằm ở: PricingSystem/App/common/helpers.py
# parents[0] = common
# parents[1] = App
# parents[2] = PricingSystem  → đây là BASE_DIR
BASE_DIR = Path(__file__).resolve().parents[2]

APP_DIR = BASE_DIR / "App"
ENGINE_DIR = BASE_DIR / "Engine"
DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "Assets"
OUTPUT_DIR = BASE_DIR / "Output"

LOG_DIR = OUTPUT_DIR / "Quotes_Log"
PDF_DIR = OUTPUT_DIR / "Quotes_Client_PDF"

MASTER_FILE = DATA_DIR / "Master_FullPricing.xlsx"
LOGO_FILE = ASSETS_DIR / "logo_pudong.png"
RAW_DIR = BASE_DIR / "Raw"  # thư mục chứa RAW excel (upload từ Streamlit)

# Thêm Engine vào sys.path để import được quote_engine_v1, quote_pdf, ...
if str(ENGINE_DIR) not in sys.path:
    sys.path.append(str(ENGINE_DIR))

# Thêm App vào sys.path để các file trong App import lẫn nhau bằng "from common...."
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))

# Import from Engine
from .cost_engine import load_master


# ============================================================
# CACHED LOADER
# ============================================================

@st.cache_data
def load_master_cached(path: Path, version: int) -> pd.DataFrame:
    """
    Cache Master Pricing theo path + version.
    Khi version thay đổi (sau khi bấm Normalize), cache sẽ bị invalid và đọc file mới.
    """
    return load_master(path)


# ============================================================
# HELPER
# ============================================================

def safe_rerun():
    """Rerun an toàn cho mọi version Streamlit."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
