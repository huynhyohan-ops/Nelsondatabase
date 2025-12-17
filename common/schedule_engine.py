# ==================== SCHEDULE_ENGINE.PY ====================
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
import re

import pandas as pd

from .models import DATA_DIR


# ======= CẤU HÌNH FILE SCHEDULE =======
# Anh chỉnh lại tên file nếu khác
SCHEDULE_FILE = DATA_DIR / "Schedule.xlsx"   # ví dụ: Data/Schedule.xlsx


DAY_MAP: Dict[str, int] = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}

# ======= NHÓM CẢNG THEO VÙNG =======

# Bờ Tây (West Coast) – bao gồm cả Vancouver, Tacoma
WEST_PORTS = {
    "USLAX",  # Los Angeles
    "USLGB",  # Long Beach
    "USOAK",  # Oakland
    "USTIW",  # Tacoma
    "USSEA",  # Seattle
    "CAVAN",  # Vancouver
    "CATIW",  # inland/rail liên quan tới Tacoma (theo file anh)
}

# Bờ Đông (East Coast)
EC_PORTS = {
    "USNYC",  # New York
    "USSAV",  # Savannah
    "USCHS",  # Charleston
    "USORF",  # Norfolk
    "USJAX",  # Jacksonville
    "USBAL",  # Baltimore
    "USPHL",  # Philadelphia (nếu có)
}

# Gulf
GULF_PORTS = {
    "USHOU",  # Houston
    "USMOB",  # Mobile
    "USNOL",  # New Orleans
    "USNOLA",  # tuỳ anh dùng code nào
}


# Map 3-letter shorthand thành port code 5 chữ
THREE_TO_FIVE: Dict[str, str] = {
    # East / Gulf
    "CHS": "USCHS",
    "SAV": "USSAV",
    "NYC": "USNYC",
    "ORF": "USORF",
    "JAX": "USJAX",
    "BAL": "USBAL",
    "HOU": "USHOU",
    # West
    "LAX": "USLAX",
    "LGB": "USLGB",
    "OAK": "USOAK",
    "TIW": "USTIW",
    "SEA": "USSEA",
    "VAN": "CAVAN",
}


# ======= REGION & TRANSIT ESTIMATE =======

def classify_region(pod_code: str) -> str:
    """
    Phân loại vùng theo POD code.
    """
    pod = (pod_code or "").upper().strip()

    if pod in WEST_PORTS:
        return "WEST"
    if pod in EC_PORTS:
        return "EAST"
    if pod in GULF_PORTS:
        return "GULF"
    return "OTHER"


def estimate_transit(pod_code: str) -> tuple[Optional[int], Optional[int]]:
    """
    Rule transit:
      - Bờ Tây: 20–24 ngày
      - Bờ Đông + Gulf: 40–45 ngày
      - Khác: 30–40 (default)
    """
    region = classify_region(pod_code)
    if region == "WEST":
        return 20, 24
    if region in {"EAST", "GULF"}:
        return 40, 45
    return 30, 40


# ======= PARSE SERVICE STRING =======

@dataclass
class ServiceInfo:
    service_name: str
    pol_tag: str      # "HCM" / "HPH" / "ANY"
    weekday: str      # MON/TUE/.../SUN


def parse_service_string(raw: str) -> ServiceInfo:
    """
    Ví dụ:
        "GS2 (SUN)" -> service_name="GS2", pol_tag="ANY", weekday="SUN"
        "PS3 (HCM) (SAT)" -> service_name="PS3", pol_tag="HCM", weekday="SAT"
        "PS3 (HPH) (TUE)" -> service_name="PS3", pol_tag="HPH", weekday="TUE"
    """
    if not isinstance(raw, str):
        raw = str(raw or "")

    base = raw.split("(")[0].strip().upper()
    parts = re.findall(r"\(([^)]+)\)", raw)
    pol_tag = "ANY"
    weekday = "SUN"  # default

    for p in parts:
        token = p.strip().upper()
        if token in {"HCM", "HPH"}:
            pol_tag = token
        else:
            t3 = token[:3]
            if t3 in DAY_MAP:
                weekday = t3

    return ServiceInfo(service_name=base, pol_tag=pol_tag, weekday=weekday)


# ======= HELPER: TÁCH POD MASTER THÀNH LIST PORT CODE =======

def _extract_pod_candidates(pod_raw: str) -> List[str]:
    """
    Chuyển 1 chuỗi POD trong Master thành list port code có thể dùng để match Schedule.

    Ví dụ:
      "USSAV"          -> ["USSAV"]
      "USSAV/USCHS"    -> ["USSAV", "USCHS"]
      "USSAV/CHS"      -> ["USSAV", "CHS", "USCHS"]
      "USEC"           -> ["USNYC","USSAV","USCHS","USORF","USJAX","USBAL"]
      "USWC"           -> West ports (LAX, OAK, TIW, VAN...)
    """
    if not isinstance(pod_raw, str):
        pod_raw = str(pod_raw or "")

    tokens = re.split(r"[\/;,]+", pod_raw.upper())
    cands: set[str] = set()

    for tok in tokens:
        t = tok.strip()
        if not t:
            continue

        # Cụm vùng East / West
        if t == "USEC":
            cands.update(EC_PORTS)
            continue
        if t == "USWC":
            cands.update(WEST_PORTS)
            continue

        # Port code đầy đủ kiểu USCHS, USSAV, USTIW, CAVAN...
        if len(t) == 5 and (t.startswith("US") or t.startswith("CA")):
            cands.add(t)
            continue

        # Code 3 chữ kiểu CHS, SAV, LAX, VAN...
        if len(t) == 3:
            cands.add(t)
            if t in THREE_TO_FIVE:
                cands.add(THREE_TO_FIVE[t])
            else:
                # fallback: US + t
                cands.add("US" + t)
            continue

        # Các kiểu khác giữ nguyên
        cands.add(t)

    return list(cands)


# ======= LOAD & CHUẨN HÓA SCHEDULE =======

@lru_cache(maxsize=1)
def load_raw_schedule(path: Path | str = SCHEDULE_FILE) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file schedule: {path}")
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    return df


@lru_cache(maxsize=1)
def build_schedule_index() -> pd.DataFrame:
    """
    Chuẩn hóa schedule thành dạng "dễ join":
      mỗi dòng = 1 (Carrier, Service, POL_tag, PODCode, WeekNo, WeekLabel, Vessel, Weekday)
    """
    df = load_raw_schedule().copy()

    # Tên cột có thể là 'CARRIER NAME', 'CARRIER', ... anh chỉnh nếu khác
    carrier_col = "CARRIER NAME" if "CARRIER NAME" in df.columns else "CARRIER"
    service_col = "SERVICE"
    pod_col = "POD"

    week_cols: List[str] = [c for c in df.columns if str(c).upper().startswith("W")]

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        carriers_raw = str(row.get(carrier_col, "") or "")
        service_raw = str(row.get(service_col, "") or "")
        pod_raw = str(row.get(pod_col, "") or "")

        if not service_raw or not pod_raw or not carriers_raw:
            continue

        service_info = parse_service_string(service_raw)

        carriers = [c.strip().upper() for c in carriers_raw.split("/") if c.strip()]
        pod_codes = [p.strip().upper() for p in pod_raw.split(";") if p.strip()]

        for week_col in week_cols:
            vessel = row.get(week_col, None)
            if vessel is None or (isinstance(vessel, float) and pd.isna(vessel)):
                continue
            vessel_str = str(vessel).strip()
            if not vessel_str or vessel_str.upper().startswith("BLANK"):
                continue

            # Week number từ 'W49 (07 DEC - 13 DEC)'
            m = re.match(r"W(\d+)", str(week_col).strip().upper())
            week_no = int(m.group(1)) if m else None

            for carrier in carriers:
                for pod_code in pod_codes:
                    records.append(
                        {
                            "carrier": carrier,
                            "service_name": service_info.service_name,
                            "pol_tag": service_info.pol_tag,   # HCM / HPH / ANY
                            "weekday": service_info.weekday,   # SUN / SAT / ...
                            "pod_code": pod_code,
                            "week_no": week_no,
                            "week_label": str(week_col),
                            "vessel": vessel_str,
                        }
                    )

    if not records:
        return pd.DataFrame(
            columns=[
                "carrier",
                "service_name",
                "pol_tag",
                "weekday",
                "pod_code",
                "week_no",
                "week_label",
                "vessel",
            ]
        )

    idx = pd.DataFrame(records)
    return idx


# ======= UTIL: ISO WEEK -> DATE =======

def iso_to_gregorian(year: int, week: int, day: int) -> date:
    """
    Chuyển (year, ISO week, weekday) -> date.
    day: 1=Monday ... 7=Sunday
    """
    fourth_jan = date(year, 1, 4)
    delta = timedelta(days=(week - 1) * 7 + (day - fourth_jan.isoweekday()))
    return fourth_jan + delta


# ======= PUBLIC API: LẤY SCHEDULE CHO 1 OPTION =======

def get_schedule_for(
    carrier: str,
    pol: str,
    pod_code: str,
    cargo_ready_iso: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Trả về schedule cho 1 tuyến cụ thể (carrier + POL + POD) dựa trên bảng Schedule.

    - Nếu có cargo_ready_date:
        chọn tuần đầu tiên có week_no >= week(cargo_ready_date)
    - Nếu không:
        dùng tuần hiện tại (theo ngày hôm nay)
    """
    carrier_up = (carrier or "").upper().strip()
    pol_up = (pol or "").upper().strip()
    pod_up = (pod_code or "").upper().strip()

    if not carrier_up or not pod_up:
        return {}

    idx = build_schedule_index()
    if idx.empty:
        return {}

    # POD trong Master có thể là 'USSAV/USCHS', 'USSAV/CHS', 'USEC', ...
    pod_candidates = _extract_pod_candidates(pod_up)

    df = idx[
        (idx["carrier"] == carrier_up) &
        (idx["pod_code"].isin(pod_candidates))
    ]
    if df.empty:
        return {}

    # Lọc theo POL_tag: ANY hoặc trùng POL (HCM/HPH)
    df = df[(df["pol_tag"] == "ANY") | (df["pol_tag"] == pol_up)]
    if df.empty:
        return {}

    # Xác định ngày mốc
    if cargo_ready_iso:
        try:
            cargo_day = date.fromisoformat(cargo_ready_iso[:10])
        except Exception:
            cargo_day = date.today()
    else:
        # Nếu không nhập cargo_ready_date -> lấy hôm nay
        cargo_day = date.today()

    cargo_week = cargo_day.isocalendar().week
    year = cargo_day.year

    # Tìm tuần phù hợp: week_no >= cargo_week, nếu không có thì lấy tuần nhỏ nhất
    df_valid = df[df["week_no"].notna()]
    if df_valid.empty:
        return {}

    df_future = df_valid[df_valid["week_no"] >= cargo_week]
    if df_future.empty:
        row = df_valid.sort_values("week_no").iloc[0]
    else:
        row = df_future.sort_values("week_no").iloc[0]

    week_no = int(row["week_no"])
    weekday = str(row["weekday"] or "SUN").upper()
    day_index = DAY_MAP.get(weekday, 6)  # 0..6

    # ISO weekday: Monday=1 .. Sunday=7
    etd_date = iso_to_gregorian(year, week_no, day_index + 1)

    tmin, tmax = estimate_transit(pod_up)
    eta_date = etd_date + timedelta(days=int((tmin + tmax) / 2)) if tmin and tmax else None

    return {
        "carrier": row["carrier"],
        "service": row["service_name"],
        "pol_tag": row["pol_tag"],
        "weekday": weekday,
        "pod_code": pod_up,
        "week_no": week_no,
        "week_label": row["week_label"],
        "vessel": row["vessel"],
        "etd": etd_date,
        "eta": eta_date,
        "transit_min": tmin,
        "transit_max": tmax,
    }
