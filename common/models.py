# ==================== MODELS.PY (FINAL CLEAN VERSION) ====================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import date
import pandas as pd

# File này nằm ở: .../PricingSystem/App/common/models.py
# => APP_DIR = .../PricingSystem/App
APP_DIR = Path(__file__).resolve().parents[1]

# PROJECT_ROOT = .../PricingSystem
PROJECT_ROOT = APP_DIR.parent

# BACKWARD-COMPATIBILITY:
# Một số file cũ (vd: common/generator.py) đang dùng BASE_DIR
# nên ta alias BASE_DIR = PROJECT_ROOT để không bị ImportError nữa.
BASE_DIR = PROJECT_ROOT

# Data & Output nằm ngoài App:
DATA_DIR = PROJECT_ROOT / "Data"
OUTPUT_DIR = PROJECT_ROOT / "Output"

# File dùng trong app
MASTER_FILE = DATA_DIR / "Master_FullPricing.xlsx"
SOC_FILE = DATA_DIR / "PUC_SOC.xlsx"
COUNTER_FILE = OUTPUT_DIR / "quote_counters.csv"


# ================= DATA MODELS =================

@dataclass
class CustomerInfo:
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    sales_person: Optional[str] = None
    quote_date: Optional[str] = None
    valid_until: Optional[str] = None


@dataclass
class ShipmentInfo:
    pol: str
    pod: Optional[str] = None
    place_of_delivery: str = ""
    cargo_ready_date: Optional[str] = None
    incoterm: Optional[str] = None
    commodity_type: str = "ANY"
    is_soc: bool = False

    def is_reefer(self) -> bool:
        """
        Trả về True nếu shipment đang ở chế độ REEFER hoặc REEFER FAK.
        """
        if not self.commodity_type:
            return False
        ctype = str(self.commodity_type).strip().upper()
        return "REEFER" in ctype

@dataclass
class ContainerPlanItem:
    type: str
    quantity: int


@dataclass
class EngineOptions:
    preferred_carriers: Optional[List[str]] = None
    excluded_carriers: Optional[List[str]] = None
    max_options_per_quote: int = 5
    sort_by: str = "total_amount"
    include_premium_option: bool = False
    currency: str = "USD"
    markup_per_carrier: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuoteRequest:
    customer: CustomerInfo
    shipment: ShipmentInfo
    containers: List[ContainerPlanItem]
    engine_options: EngineOptions


# ================= MASTER LOADER =================

def load_master(master_path: Path | str = MASTER_FILE) -> pd.DataFrame:
    """
    Đọc file Master_FullPricing.xlsx, sheet 'Master'.
    """
    master_path = Path(master_path)
    if not master_path.exists():
        raise FileNotFoundError(f"Không tìm thấy Master: {master_path}")
    df = pd.read_excel(master_path, sheet_name="Master")
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ================= VALIDITY FILTER =================

from datetime import date
import pandas as pd

def filter_by_validity(df: pd.DataFrame, cargo_iso: str | None):
    """
    Lọc bảng giá theo ExpirationDate so với ngày cargo_ready_date.

    - Nếu không có cột ExpirationDate -> trả df gốc.
    - Nếu cargo_iso None hoặc parse lỗi -> lấy ngày hôm nay.
    - Chỉ giữ lại những dòng có ExpirationDate >= cargo_day.
    - Các dòng không có ExpirationDate (NaT) coi như luôn còn hiệu lực.
    """
    if "ExpirationDate" not in df.columns:
        return df

    # Xác định ngày cargo ở dạng pandas.Timestamp (datetime64[ns])
    if cargo_iso:
        cargo_ts = pd.to_datetime(cargo_iso, errors="coerce", dayfirst=True)
        if pd.isna(cargo_ts):
            cargo_ts = pd.Timestamp.today().normalize()
        else:
            cargo_ts = cargo_ts.normalize()
    else:
        cargo_ts = pd.Timestamp.today().normalize()

    # Ép ExpirationDate về datetime64[ns] và normalize về 00:00
    exp = pd.to_datetime(df["ExpirationDate"], errors="coerce", dayfirst=True).dt.normalize()

    # Giữ lại:
    # - Dòng không có ExpirationDate (NaT)
    # - Hoặc ExpirationDate >= cargo_ts
    mask = exp.isna() | (exp >= cargo_ts)

    return df[mask].copy()