from __future__ import annotations

from pathlib import Path
import os
import re
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Any, Optional

import pandas as pd

# ============================================================
# PATH CONFIG – auto detect PricingSystem root
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "Assets"
OUTPUT_DIR = BASE_DIR / "Output"

LOG_DIR = OUTPUT_DIR / "Quotes_Log"
PDF_DIR = OUTPUT_DIR / "Quotes_Client_PDF"

MASTER_FILE = DATA_DIR / "Master_FullPricing.xlsx"
SOC_FILE = DATA_DIR / "PUC_SOC.xlsx"
COUNTER_FILE = DATA_DIR / "quote_counters.csv"
LOGO_FILE = ASSETS_DIR / "logo_pudong.png"


# ===================== DATA MODELS =====================

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
    is_soc: bool = False  # True = loại SOC (chỉ lấy COC)


@dataclass
class ContainerPlanItem:
    type: str   # "20GP", "40HQ", "20RF", ...
    quantity: int


@dataclass
class EngineOptions:
    preferred_carriers: Optional[List[str]] = None
    excluded_carriers: Optional[List[str]] = None
    max_options_per_quote: int = 5
    sort_by: str = "total_amount"
    include_premium_option: bool = False
    currency: str = "USD"
    # NEW: mark-up theo hãng (USD / container)
    markup_per_carrier: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuoteRequest:
    customer: CustomerInfo
    shipment: ShipmentInfo
    containers: List[ContainerPlanItem]
    engine_options: EngineOptions


# ===================== LOAD MASTER =====================

def load_master(master_path: Path | str = MASTER_FILE) -> pd.DataFrame:
    """
    Đọc sheet 'Master' từ Master_FullPricing.xlsx.
    """
    master_path = Path(master_path)
    if not master_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file Master tại: {master_path}")
    if not master_path.is_file():
        raise FileNotFoundError(f"Đường dẫn không phải file Excel: {master_path}")

    df = pd.read_excel(master_path, sheet_name="Master")
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ===================== CORE ENGINE =====================

def generate_quote(master_df: pd.DataFrame, req: QuoteRequest) -> Dict[str, Any]:
    """
    Core quote engine:
    - Filter Master theo POL, PlaceOfDelivery, POD (optional), Commodity, SOC, Carrier...
    - Tính tổng theo container plan (có cộng mark-up per carrier nếu có).
    - Nếu không chọn preferred carriers -> lấy TOP 5 carrier rẻ nhất (1 option/carrier).
    """
    shipment = req.shipment
    options_cfg = req.engine_options

    if not shipment.place_of_delivery:
        return {
            "error": "MISSING_PLACE_OF_DELIVERY",
            "message": "Place of Delivery là bắt buộc.",
        }

    # Fix None -> []
    if options_cfg.preferred_carriers is None:
        options_cfg.preferred_carriers = []
    if options_cfg.excluded_carriers is None:
        options_cfg.excluded_carriers = []

    # Chuẩn hóa markup map: {CARRIER_UPPER: float}
    markup_map: Dict[str, float] = {}
    if options_cfg.markup_per_carrier:
        for k, v in options_cfg.markup_per_carrier.items():
            try:
                markup_map[k.upper().strip()] = float(v)
            except (TypeError, ValueError):
                continue

    df = master_df.copy()

    # ---- Lọc theo POL ----
    pol_upper = shipment.pol.upper().strip()
    df["POL_upper"] = df["POL"].astype(str).str.upper().str.strip()
    df = df[df["POL_upper"] == pol_upper]
    if df.empty:
        return {
            "error": "NO_RATE_FOUND",
            "message": f"Không tìm thấy dòng giá nào với POL = {shipment.pol}.",
        }

    # ---- Lọc theo PlaceOfDelivery (contains) ----
    place_key = shipment.place_of_delivery.upper().strip()
    df["Place_upper"] = df["PlaceOfDelivery"].astype(str).str.upper()
    df = df[df["Place_upper"].str.contains(place_key, na=False)]
    if df.empty:
        return {
            "error": "NO_RATE_FOUND",
            "message": f"Không tìm thấy dòng giá nào có PlaceOfDelivery chứa: {shipment.place_of_delivery}.",
        }

    # ---- Lọc theo POD (optional) ----
    if shipment.pod:
        pod_key = shipment.pod.upper().strip()
        df["POD_upper"] = df["POD"].astype(str).str.upper()
        df = df[df["POD_upper"].str.contains(pod_key, na=False)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": f"Không tìm thấy dòng giá nào PlaceOfDelivery='{shipment.place_of_delivery}' có POD chứa: {shipment.pod}.",
            }

    # ---- Lọc theo CommodityType ----
    commodity = shipment.commodity_type
    if commodity and commodity.upper() != "ANY":
        df["Commodity_upper"] = df["CommodityType"].astype(str).str.upper()
        com_up = commodity.upper()

        if com_up == "FAK":
            df = df[
                df["Commodity_upper"].str.contains("FAK", na=False)
                & ~df["Commodity_upper"].str.contains("REEFER", na=False)
            ]
        elif com_up == "REEFER":
            df = df[df["Commodity_upper"].str.contains("REEFER", na=False)]
        elif com_up == "FIX RATE":
            df = df[df["Commodity_upper"].str.contains("FIX RATE", na=False)]
        elif com_up == "SHORT TERM GDSM":
            df = df[df["Commodity_upper"].str.contains("SHORT TERM GDSM", na=False)]
        else:
            df = df[df["Commodity_upper"] == com_up]

        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": f"Không có dòng giá nào với CommodityType = {commodity} khớp các filter còn lại.",
            }

    # ---- Lọc SOC: is_soc=True = loại SOC ----
    if shipment.is_soc:
        df["Routing_upper"] = df["RoutingNote"].astype(str).str.upper()
        df = df[~df["Routing_upper"].str.contains("SOC", na=False)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": "Không còn dòng giá nào sau khi loại SOC.",
            }

    # ---- Lọc preferred / excluded carriers ----
    df["Carrier_upper"] = df["Carrier"].astype(str).str.upper().str.strip()

    if options_cfg.preferred_carriers:
        pref = [c.upper().strip() for c in options_cfg.preferred_carriers]
        df = df[df["Carrier_upper"].isin(pref)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": f"Không có dòng giá nào thuộc các hãng: {options_cfg.preferred_carriers}.",
            }

    if options_cfg.excluded_carriers:
        excl = [c.upper().strip() for c in options_cfg.excluded_carriers]
        df = df[~df["Carrier_upper"].isin(excl)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": "Tất cả các dòng giá đều thuộc các hãng bị exclude.",
            }

    # ---- Hàm lấy đơn giá thực tế (có cộng markup) ----
    def get_effective_rate(row: pd.Series, cont_type: str):
        # Reefer mapping
        if cont_type == "20RF":
            for col in ["20RF", "20GP"]:
                if col in row.index and not pd.isna(row[col]):
                    base = row[col]
                    break
            else:
                return None
        elif cont_type == "40RF":
            for col in ["40RF", "40HQ", "40GP"]:
                if col in row.index and not pd.isna(row[col]):
                    base = row[col]
                    break
            else:
                return None
        else:
            base = row.get(cont_type, None)

        if base is None or pd.isna(base):
            return None

        extra = markup_map.get(row["Carrier_upper"], 0.0)
        return float(base) + float(extra)

    def has_all_rates(row: pd.Series) -> bool:
        for item in req.containers:
            rate = get_effective_rate(row, item.type)
            if rate is None or pd.isna(rate):
                return False
        return True

    df_valid = df[df.apply(has_all_rates, axis=1)].copy()
    if df_valid.empty:
        return {
            "error": "NO_VALID_RATE_FOR_PLAN",
            "message": "Không có dòng giá nào có đủ giá cho tất cả loại container trong plan.",
        }

    # ---- Tính tổng ----
    def compute_total(row: pd.Series) -> float:
        total = 0.0
        for item in req.containers:
            rate = get_effective_rate(row, item.type)
            if rate is None or pd.isna(rate):
                return float("inf")
            total += float(rate) * item.quantity
        return total

    df_valid["TotalAmount"] = df_valid.apply(compute_total, axis=1)

    # ---- Chọn options ----
    if not options_cfg.preferred_carriers:
        # Lấy dòng rẻ nhất cho mỗi carrier, sau đó TOP 5
        df_valid_sorted = df_valid.sort_values(by="TotalAmount", ascending=True)
        idx_min = df_valid_sorted.groupby("Carrier_upper")["TotalAmount"].idxmin()
        df_per_carrier = df_valid.loc[idx_min].copy()
        df_sorted = df_per_carrier.sort_values(by="TotalAmount", ascending=True)
        df_top = df_sorted.head(5).reset_index(drop=True)
    else:
        df_sorted = df_valid.sort_values(by="TotalAmount", ascending=True)
        max_n = max(1, options_cfg.max_options_per_quote)
        df_top = df_sorted.head(max_n).reset_index(drop=True)

    if df_top.empty:
        return {
            "error": "NO_RATE_FOUND",
            "message": "Không có option nào sau khi chọn TOP.",
        }

    # ---- Build output JSON ----
    containers_summary = ", ".join(
        f"{item.quantity} x {item.type}" for item in req.containers
    )

    options_out = []
    for option_index, (_, row) in enumerate(df_top.iterrows(), start=1):
        # container_rates
        container_rates: Dict[str, float] = {}
        for item in req.containers:
            rate = get_effective_rate(row, item.type)
            container_rates[item.type] = float(rate)

        # breakdown
        container_plan = []
        for item in req.containers:
            unit_rate = container_rates[item.type]
            amount = unit_rate * item.quantity
            container_plan.append(
                {
                    "type": item.type,
                    "quantity": item.quantity,
                    "unit_rate": unit_rate,
                    "amount": amount,
                }
            )

        option = {
            "index": option_index,
            "is_recommended": option_index == 1,
            "carrier": str(row["Carrier"]),
            "rate_type": str(row.get("RateType", "")),
            "pol": str(row["POL"]),
            "pod": str(row["POD"]),
            "place_of_delivery": str(row["PlaceOfDelivery"]),
            "contract_identifier": None
            if pd.isna(row.get("ContractIdentifier", None))
            else str(row.get("ContractIdentifier", "")),
            "commodity_type": None
            if pd.isna(row.get("CommodityType", None))
            else str(row.get("CommodityType", "")),
            "valid_from": str(row.get("EffectiveDate", "")),
            "valid_to": str(row.get("ExpirationDate", "")),
            "container_rates": container_rates,
            "container_plan": container_plan,
            "total_ocean_amount": float(row["TotalAmount"]),
            "currency": options_cfg.currency,
            "notes": build_notes(row),
        }
        options_out.append(option)

    today_iso = date.today().isoformat()
    quote_ref_no = build_quote_ref(req)

    # ---- SUMMARY ----
    summary = {
        # Thông tin khách hàng
        "customer_name": req.customer.name,
        "customer_email": req.customer.email,
        "contact_person": req.customer.contact_person,
        "sales_person": req.customer.sales_person,

        # Thông tin tuyến
        "route": f"{shipment.pol} → {shipment.place_of_delivery}",
        "pol": shipment.pol,
        "pod": shipment.pod,
        "place_of_delivery": shipment.place_of_delivery,

        # Kế hoạch container
        "containers_summary": containers_summary,

        # Điều kiện khác
        "valid_until": None,
        "incoterm": shipment.incoterm,
        "commodity_type": shipment.commodity_type,
        "is_soc": shipment.is_soc,
        "currency": options_cfg.currency,
    }

    debug_info = {
        "rows_after_filters": int(len(df)),
        "rows_with_full_rates": int(len(df_valid)),
        "rows_returned": int(len(df_top)),
    }

    return {
        "quote_ref_no": quote_ref_no,
        "quote_date": today_iso,
        "summary": summary,
        "options": options_out,
        "debug": debug_info,
    }


# ===================== PREVIEW COST (NO MARKUP) =====================

def preview_cost_by_carrier(
    master_df: pd.DataFrame,
    shipment: ShipmentInfo,
    containers: List[ContainerPlanItem],
) -> Dict[str, Any]:
    """
    Preview internal cost (không cộng markup), per carrier:
    - Filter giống generate_quote (POL, PlaceOfDelivery, POD, Commodity, SOC).
    - Yêu cầu đủ giá cho toàn bộ container plan.
    - Lấy dòng rẻ nhất cho mỗi carrier, sort theo TotalBase ASC.
    Trả về:
    {
        "preview": DataFrame,
        "debug": {...}
    }
    hoặc { "error": ..., "message": ... }
    """

    if not shipment.place_of_delivery:
        return {
            "error": "MISSING_PLACE_OF_DELIVERY",
            "message": "Place of Delivery là bắt buộc.",
        }

    df = master_df.copy()

    # ---- Lọc theo POL ----
    pol_upper = shipment.pol.upper().strip()
    df["POL_upper"] = df["POL"].astype(str).str.upper().str.strip()
    df = df[df["POL_upper"] == pol_upper]
    if df.empty:
        return {
            "error": "NO_RATE_FOUND",
            "message": f"Không tìm thấy dòng giá nào với POL = {shipment.pol}.",
        }

    # ---- Lọc theo PlaceOfDelivery (contains) ----
    place_key = shipment.place_of_delivery.upper().strip()
    df["Place_upper"] = df["PlaceOfDelivery"].astype(str).str.upper()
    df = df[df["Place_upper"].str.contains(place_key, na=False)]
    if df.empty:
        return {
            "error": "NO_RATE_FOUND",
            "message": f"Không tìm thấy dòng giá nào có PlaceOfDelivery chứa: {shipment.place_of_delivery}.",
        }

    # ---- Lọc theo POD (optional) ----
    if shipment.pod:
        pod_key = shipment.pod.upper().strip()
        df["POD_upper"] = df["POD"].astype(str).str.upper()
        df = df[df["POD_upper"].str.contains(pod_key, na=False)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": f"Không tìm thấy dòng giá nào PlaceOfDelivery='{shipment.place_of_delivery}' có POD chứa: {shipment.pod}.",
            }

    # ---- Lọc theo CommodityType ----
    commodity = shipment.commodity_type
    if commodity and commodity.upper() != "ANY":
        df["Commodity_upper"] = df["CommodityType"].astype(str).str.upper()
        com_up = commodity.upper()

        if com_up == "FAK":
            df = df[
                df["Commodity_upper"].str.contains("FAK", na=False)
                & ~df["Commodity_upper"].str.contains("REEFER", na=False)
            ]
        elif com_up == "REEFER":
            df = df[df["Commodity_upper"].str.contains("REEFER", na=False)]
        elif com_up == "FIX RATE":
            df = df[df["Commodity_upper"].str.contains("FIX RATE", na=False)]
        elif com_up == "SHORT TERM GDSM":
            df = df[df["Commodity_upper"].str.contains("SHORT TERM GDSM", na=False)]
        else:
            df = df[df["Commodity_upper"] == com_up]

        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": f"Không có dòng giá nào với CommodityType = {commodity} khớp các filter còn lại.",
            }

    # ---- Lọc SOC: is_soc=True = loại SOC ----
    if shipment.is_soc:
        df["Routing_upper"] = df["RoutingNote"].astype(str).str.upper()
        df = df[~df["Routing_upper"].str.contains("SOC", na=False)]
        if df.empty:
            return {
                "error": "NO_RATE_FOUND",
                "message": "Không còn dòng giá nào sau khi loại SOC.",
            }

    df["Carrier_upper"] = df["Carrier"].astype(str).str.upper().str.strip()

    # ---- Hàm lấy đơn giá base (không markup) ----
    def get_base_rate(row: pd.Series, cont_type: str):
        if cont_type == "20RF":
            for col in ["20RF", "20GP"]:
                if col in row.index and not pd.isna(row[col]):
                    return row[col]
            return None
        if cont_type == "40RF":
            for col in ["40RF", "40HQ", "40GP"]:
                if col in row.index and not pd.isna(row[col]):
                    return row[col]
            return None
        return row.get(cont_type, None)

    def has_all_rates(row: pd.Series) -> bool:
        for item in containers:
            rate = get_base_rate(row, item.type)
            if rate is None or pd.isna(rate):
                return False
        return True

    df_valid = df[df.apply(has_all_rates, axis=1)].copy()
    if df_valid.empty:
        return {
            "error": "NO_VALID_RATE_FOR_PLAN",
            "message": "Không có dòng giá nào có đủ giá cho tất cả loại container trong plan.",
        }

    def compute_total(row: pd.Series) -> float:
        total = 0.0
        for item in containers:
            rate = get_base_rate(row, item.type)
            if rate is None or pd.isna(rate):
                return float("inf")
            total += float(rate) * item.quantity
        return total

    df_valid["TotalBase"] = df_valid.apply(compute_total, axis=1)

    # Lấy dòng rẻ nhất cho mỗi carrier
    df_valid_sorted = df_valid.sort_values(by="TotalBase", ascending=True)
    idx_min = df_valid_sorted.groupby("Carrier_upper")["TotalBase"].idxmin()
    df_per_carrier = df_valid.loc[idx_min].copy()
    df_per_carrier = df_per_carrier.sort_values(by="TotalBase", ascending=True)

    preview_cols = [
        "Carrier", "TotalBase", "POL", "POD", "PlaceOfDelivery",
        "RateType", "ContractIdentifier", "CommodityType",
        "EffectiveDate", "ExpirationDate", "RoutingNote",
    ]
    preview_cols = [c for c in preview_cols if c in df_per_carrier.columns]

    df_preview = df_per_carrier[preview_cols].copy()
    df_preview.rename(
        columns={
            "TotalBase": "Total (base USD)",
            "ContractIdentifier": "Contract",
            "CommodityType": "Commodity",
            "EffectiveDate": "ValidFrom",
            "ExpirationDate": "ValidTo",
        },
        inplace=True,
    )

    debug_info = {
        "rows_after_filters": int(len(df)),
        "rows_with_full_rates": int(len(df_valid)),
        "carriers_returned": int(len(df_preview)),
    }

    return {
        "preview": df_preview,
        "debug": debug_info,
    }


# ===================== HELPER FUNCTIONS =====================

def normalize_customer_key(name: str) -> str:
    """
    Convert tên khách thành key đơn giản để dùng trong REF:
    VD: "Sorachi Logistics Co., Ltd" -> "SORACHI"
    """
    if not name:
        return "CUST"
    up = name.upper()
    first_word = up.split()[0]
    key = re.sub(r"[^A-Z0-9]", "", first_word)
    return key or "CUST"


def build_quote_ref(req: QuoteRequest) -> str:
    """
    REF QUOTATION = CUSTOMERKEY-DDMMM-SEQ
    VD: SORACHI-27NOV-1, SORACHI-27NOV-2
    Đếm theo (customer, ngày).
    """
    customer_key = normalize_customer_key(req.customer.name)
    today = date.today()
    date_code = today.strftime("%d%b").upper()  # 27NOV

    if COUNTER_FILE.exists():
        df_ct = pd.read_csv(
            COUNTER_FILE,
            dtype={"CustomerKey": str, "DateCode": str, "Counter": int},
        )
    else:
        df_ct = pd.DataFrame(columns=["CustomerKey", "DateCode", "Counter"])

    mask = (df_ct["CustomerKey"] == customer_key) & (df_ct["DateCode"] == date_code)
    if mask.any():
        current = int(df_ct.loc[mask, "Counter"].iloc[0])
        new_counter = current + 1
        df_ct.loc[mask, "Counter"] = new_counter
    else:
        new_counter = 1
        df_ct = pd.concat(
            [
                df_ct,
                pd.DataFrame(
                    [
                        {
                            "CustomerKey": customer_key,
                            "DateCode": date_code,
                            "Counter": new_counter,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    df_ct.to_csv(COUNTER_FILE, index=False)
    return f"{customer_key}-{date_code}-{new_counter}"


def build_notes(row: pd.Series) -> str:
    """
    Gộp một số thông tin thành notes: RateType + RoutingNote.
    """
    parts = []
    rate_type = row.get("RateType", None)
    routing = row.get("RoutingNote", None)

    if isinstance(rate_type, str) and rate_type.strip():
        parts.append(rate_type.strip())
    if isinstance(routing, str) and routing.strip():
        parts.append(routing.strip())

    return " / ".join(parts)


def pretty_print_quote(result: Dict[str, Any]) -> None:
    """
    In kết quả quote ra console (để debug nếu cần).
    """
    if "error" in result:
        print("[ERROR]", result["error"])
        print("Message:", result.get("message", ""))
        return

    print("=" * 70)
    print(f"QUOTE REF : {result['quote_ref_no']}")
    print(f"QUOTE DATE: {result.get('quote_date')}")
    s = result["summary"]
    print(f"CUSTOMER  : {s['customer_name']}")
    print(f"ROUTE     : {s['route']}")
    print(f"CONTAINERS: {s['containers_summary']}")
    print(f"INCOTERM  : {s.get('incoterm')}")
    print(f"COMMODITY : {s.get('commodity_type')}")
    print(f"SOC       : {s.get('is_soc')}")
    print("-" * 70)

    options = result["options"]
    for opt in options:
        tag = " (RECOMMENDED)" if opt["is_recommended"] else ""
        print(f"Option {opt['index']}{tag}")
        print(f"  Carrier   : {opt['carrier']}")
        print(f"  RateType  : {opt['rate_type']}")
        print(f"  Contract  : {opt['contract_identifier']}")
        print(f"  Commodity : {opt['commodity_type']}")
        print(f"  Validity  : {opt['valid_from']} → {opt['valid_to']}")
        print(f"  Total     : {opt['total_ocean_amount']} {opt['currency']}")
        print("  Container plan:")
        for cp in opt["container_plan"]:
            print(
                f"    - {cp['quantity']} x {cp['type']} "
                f"@ {cp['unit_rate']} = {cp['amount']}"
            )
        print(f"  Notes     : {opt['notes']}")
        print("-" * 70)

    print("DEBUG:", result.get("debug", {}))
    print("=" * 70)


# ===================== EXPORT / LOG INTERNAL =====================

def quote_result_to_dfs(result: Dict[str, Any]):
    """
    Chuyển result sang 3 DataFrame:
    - SUMMARY: 1 dòng
    - OPTIONS: mỗi option 1 dòng
    - DETAILS: breakdown container per option
    """
    summary = result["summary"]
    options = result["options"]

    df_summary = pd.DataFrame(
        [
            {
                "QuoteRef": result["quote_ref_no"],
                "QuoteDate": result["quote_date"],
                "Customer": summary["customer_name"],
                "CustomerEmail": summary.get("customer_email"),
                "ContactPerson": summary.get("contact_person"),
                "SalesPerson": summary.get("sales_person"),
                "Route": summary["route"],
                "POL": summary["pol"],
                "POD": summary["pod"],
                "PlaceOfDelivery": summary["place_of_delivery"],
                "Containers": summary["containers_summary"],
                "Incoterm": summary["incoterm"],
                "Commodity": summary["commodity_type"],
                "SOC": summary["is_soc"],
                "Currency": summary["currency"],
            }
        ]
    )

    rows_opt = []
    rows_plan = []

    for opt in options:
        rows_opt.append(
            {
                "Option": opt["index"],
                "IsRecommended": opt["is_recommended"],
                "Carrier": opt["carrier"],
                "RateType": opt["rate_type"],
                "Contract": opt["contract_identifier"],
                "Total": opt["total_ocean_amount"],
                "Validity": f"{opt['valid_from']} → {opt['valid_to']}",
                "Commodity": opt["commodity_type"],
                "Notes": opt["notes"],
            }
        )
        for cp in opt["container_plan"]:
            rows_plan.append(
                {
                    "Option": opt["index"],
                    "Carrier": opt["carrier"],
                    "Type": cp["type"],
                    "Qty": cp["quantity"],
                    "UnitRate": cp["unit_rate"],
                    "Amount": cp["amount"],
                    "Currency": opt["currency"],
                }
            )

    df_options = pd.DataFrame(rows_opt)
    df_plan = pd.DataFrame(rows_plan)

    return df_summary, df_options, df_plan


def save_quote_internal(result: Dict[str, Any]) -> str:
    """
    Lưu log nội bộ mỗi lần generate (SUMMARY + OPTIONS + DETAILS).
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    summary = result["summary"]
    quote_ref = result["quote_ref_no"]
    customer = summary["customer_name"]
    safe_customer = "".join(
        c for c in customer if c.isalnum() or c in " _-"
    ).strip()

    filename = f"{quote_ref} - {safe_customer}.xlsx"
    filepath = LOG_DIR / filename

    df_summary, df_options, df_plan = quote_result_to_dfs(result)

    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        df_summary.to_excel(writer, sheet_name="SUMMARY", index=False)
        df_options.to_excel(writer, sheet_name="OPTIONS", index=False)
        df_plan.to_excel(writer, sheet_name="DETAILS", index=False)

        wb = writer.book
        ws = writer.sheets["SUMMARY"]
        fmt_bold = wb.add_format({"bold": True})
        ws.set_column("A:A", 18, fmt_bold)
        ws.set_column("B:Z", 30)

    return str(filepath)


# ===================== DEMO (optional) =====================

if __name__ == "__main__":
    # Demo console nhỏ
    master = load_master()
    customer = CustomerInfo(name="Demo Customer", email="demo@example.com")
    shipment = ShipmentInfo(pol="HCM", place_of_delivery="LOS ANGELES")
    containers = [ContainerPlanItem(type="40HQ", quantity=1)]
    engine_opts = EngineOptions()
    req = QuoteRequest(
        customer=customer,
        shipment=shipment,
        containers=containers,
        engine_options=engine_opts,
    )
    result = generate_quote(master, req)
    pretty_print_quote(result)
