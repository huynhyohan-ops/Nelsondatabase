from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
from datetime import date

from .models import (
    ShipmentInfo,
    CustomerInfo,
    ContainerPlanItem,
    EngineOptions,
    QuoteRequest,
    filter_by_validity,
)
from .models import load_master
from .schedule_engine import get_schedule_for


def map_reefer_containers(df: pd.DataFrame) -> pd.DataFrame:
    """Map giá từ 20GP, 40GP, 40HQ sang 20RF, 40RF theo từng loại CommodityType và Carrier."""
    df = df.copy()

    cond_reefer_cosco = (df["CommodityType"].str.upper() == "REEFER") & (df["Carrier"].str.upper() == "COSCO")
    df.loc[cond_reefer_cosco, "20RF"] = df.loc[cond_reefer_cosco, "20GP"]
    df.loc[cond_reefer_cosco, "40RF"] = df.loc[cond_reefer_cosco, "40HQ"]

    cond_reefer_fak_one = (df["CommodityType"].str.upper() == "REEFER FAK") & (df["Carrier"].str.upper() == "ONE")
    df.loc[cond_reefer_fak_one, "20RF"] = df.loc[cond_reefer_fak_one, "20GP"]
    df.loc[cond_reefer_fak_one, "40RF"] = df.loc[cond_reefer_fak_one, "40GP"]

    return df


def generate_quote(master_df: pd.DataFrame, req: QuoteRequest) -> Dict[str, Any]:
    ship = req.shipment
    opt = req.engine_options
    df = master_df.copy()

    # 1. Filter POL
    df["POL_up"] = df["POL"].astype(str).str.upper().str.strip()
    df = df[df["POL_up"] == ship.pol.upper().strip()]
    if df.empty:
        return {"error": "NO_RATE", "message": "Không có giá POL."}

    # 2. Filter Place of Delivery
    key = ship.place_of_delivery.upper().strip()
    df["PODel_up"] = df["PlaceOfDelivery"].astype(str).str.upper()
    df = df[df["PODel_up"].str.contains(key, na=False)]
    if df.empty:
        return {"error": "NO_RATE", "message": "Không match PlaceOfDelivery."}

    # 3. Filter POD (optional)
    if ship.pod:
        pk = ship.pod.upper().strip()
        df["POD_up"] = df["POD"].astype(str).str.upper()
        df = df[df["POD_up"].str.contains(pk, na=False)]
        if df.empty:
            return {"error": "NO_RATE", "message": "Không match POD."}

    # 4. Validity filter
    df = filter_by_validity(df, ship.cargo_ready_date)
    if df.empty:
        return {"error": "NO_RATE", "message": "Hết hiệu lực."}

    # 5. FAK/REEFER + SOC filtering
    df["Routing_up"] = df["RoutingNote"].astype(str).fillna("").str.upper().str.strip()
    df["Commodity_up"] = df["CommodityType"].astype(str).fillna("").str.upper().str.strip()

    if not ship.is_reefer() and not ship.is_soc:
        pass
    elif not ship.is_reefer() and ship.is_soc:
        combined_text = df["Routing_up"].fillna("") + " " + df["Commodity_up"].fillna("")
        df = df[~combined_text.str.contains(r"\bSOC\b", na=False)]
    elif ship.is_reefer():
        df = df[df["Commodity_up"].str.contains("REEFER", na=False)]

    # 🔁 ⬇️ THÊM BƯỚC MAPPING TẠI ĐÂY
    df = map_reefer_containers(df)

    # 6. Filter lowest price per carrier
    if "Total" not in df.columns:
        def calc_tmp_total(row):
            val = 0
            for c in req.containers:
                r = row.get(c.type, None)
                if isinstance(r, (float, int)):
                    val += r
            return val
        df["Total"] = df.apply(calc_tmp_total, axis=1)

    df = df.sort_values(["Carrier", "Total"], ascending=[True, True])
    df = df.groupby("Carrier", as_index=False).first()

    # 7. Check rate availability
    def has_all_rates(row):
        for c in req.containers:
            rate = row.get(c.type, None)
            if rate is None or (isinstance(rate, float) and pd.isna(rate)):
                return False
        return True
    df = df[df.apply(has_all_rates, axis=1)].copy()
    if df.empty:
        return {"error": "NO_RATE", "message": "Thiếu giá container."}

    # 8. Final price calc (with markup)
    def calc_total(row):
        total = 0
        for c in req.containers:
            rate = row[c.type]
            carrier_key = str(row["Carrier"]).upper()
            markup = opt.markup_map.get(carrier_key, 0) if hasattr(opt, "markup_map") else 0
            total += (rate + markup) * c.quantity
        return total
    df["Total"] = df.apply(calc_total, axis=1)

    # 9. Sort and limit result
    df = df.sort_values("Total").reset_index(drop=True)
    max_opts = opt.max_options_per_quote or 10
    df_top = df.head(max_opts)

    # 10. Build result
    options = []
    for idx, row in df_top.iterrows():
        ct = {}
        for c in req.containers:
            if c.type in row:
                ct[c.type] = float(row[c.type])

        carrier_key = str(row["Carrier"]).upper()
        carrier_markup = opt.markup_map.get(carrier_key, 0) if hasattr(opt, "markup_map") else 0
        ct_with_markup = {k: v + carrier_markup for k, v in ct.items()}

        sched = get_schedule_for(
            carrier=str(row["Carrier"]),
            pol=ship.pol,
            pod_code=str(row["POD"]),
            cargo_ready_iso=ship.cargo_ready_date,
        )

        options.append({
            "index": idx + 1,
            "is_recommended": idx == 0,
            "carrier": row["Carrier"],
            "place_of_delivery": row["PlaceOfDelivery"],
            "pol": row["POL"],
            "pod": row["POD"],
            "service": sched.get("service"),
            "etd": sched.get("etd"),
            "eta": sched.get("eta"),
            "vessel": sched.get("vessel"),
            "WeekLabel": sched.get("week_label"),
            "transit_min": sched.get("transit_min"),
            "transit_max": sched.get("transit_max"),
            "RoutingNote": row.get("RoutingNote", "-"),
            "CommodityType": row.get("CommodityType", "-"),
            "container_rates": ct_with_markup,
            "total_ocean_amount": float(row["Total"]),
            "currency": opt.currency,
        })

    # Summary
    summ = {
        "customer_name": req.customer.name,
        "pol": ship.pol,
        "place_of_delivery": ship.place_of_delivery,
        "commodity_type": ship.commodity_type,
        "containers_summary": ", ".join(f"{c.quantity} x {c.type}" for c in req.containers),
        "is_soc": ship.is_soc,
    }

    return {
        "quote_ref_no": f"QT-{date.today().strftime('%Y%m%d')}",
        "quote_date": date.today().isoformat(),
        "summary": summ,
        "options": options,
        "containers": [c.type for c in req.containers],
    }
