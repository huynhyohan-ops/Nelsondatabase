# ==================== COST_ENGINE.PY (WITH SCHEDULE) ====================

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
    load_master,
    filter_by_validity,
)
from .schedule_engine import get_schedule_for


# ================= QUOTE ENGINE CORE =================

def generate_quote(master_df: pd.DataFrame, req: QuoteRequest) -> Dict[str, Any]:

    ship = req.shipment
    opt = req.engine_options

    df = master_df.copy()

    # ========== FILTER 1: POL ==========
    df["POL_up"] = df["POL"].astype(str).str.upper().str.strip()
    df = df[df["POL_up"] == ship.pol.upper().strip()]
    if df.empty:
        return {"error": "NO_RATE", "message": "Không có giá POL."}

    # ========== FILTER 2: Place Of Delivery ==========
    key = ship.place_of_delivery.upper().strip()
    df["PODel_up"] = df["PlaceOfDelivery"].astype(str).str.upper()
    df = df[df["PODel_up"].str.contains(key, na=False)]
    if df.empty:
        return {"error": "NO_RATE", "message": "Không match PlaceOfDelivery."}

    # ========== FILTER 3: POD optional ==========
    if ship.pod:
        pk = ship.pod.upper().strip()
        df["POD_up"] = df["POD"].astype(str).str.upper()
        df = df[df["POD_up"].str.contains(pk, na=False)]
        if df.empty:
            return {"error": "NO_RATE", "message": "Không match POD."}

    # ========== FILTER 4: Commodity ==========
    if ship.commodity_type and ship.commodity_type != "ANY":
        cu = ship.commodity_type.upper()
        df["Com_up"] = df["CommodityType"].astype(str).str.upper()

        if cu == "FAK":
            df = df[df["Com_up"].str.contains("FAK", na=False)]
        elif cu == "REEFER":
            df = df[df["Com_up"].str.contains("REEFER", na=False)]
        else:
            df = df[df["Com_up"] == cu]
        if df.empty:
            return {"error": "NO_RATE", "message": "Commodity mismatch."}

    # ========== FILTER 5: SOC (loại SOC nếu is_soc=True) ==========
    if ship.is_soc:
        df["Routing_up"] = df["RoutingNote"].astype(str).str.upper()
        df = df[~df["Routing_up"].str.contains("SOC", na=False)]

    # ========== FILTER 6: Validity ==========
    df = filter_by_validity(df, ship.cargo_ready_date)
    if df.empty:
        return {"error": "NO_RATE", "message": "Hết hiệu lực."}

    # ========== Apply Carrier Filters ==========
    df["Carrier_up"] = df["Carrier"].astype(str).str.upper().str.strip()

    if opt.preferred_carriers:
        pref = [c.upper().strip() for c in opt.preferred_carriers]
        df = df[df["Carrier_up"].isin(pref)]

    if opt.excluded_carriers:
        exc = [c.upper().strip() for c in opt.excluded_carriers]
        df = df[~df["Carrier_up"].isin(exc)]

    if df.empty:
        return {"error": "NO_RATE", "message": "Không còn hãng phù hợp."}

    # ========== CHECK RATE AVAILABILITY ==========
    def has_all_rates(row):
        for c in req.containers:
            rate = row.get(c.type, None)
            if rate is None or pd.isna(rate):
                return False
        return True

    df = df[df.apply(has_all_rates, axis=1)].copy()
    if df.empty:
        return {"error": "NO_RATE", "message": "Thiếu giá container."}

    # ========== COMPUTE TOTAL ==========
    def calc_total(row):
        total = 0
        for c in req.containers:
            unit = row[c.type]
            total += unit * c.quantity
        return total

    df["Total"] = df.apply(calc_total, axis=1)

    # ========== SORT & LIMIT OPTIONS ==========
    df = df.sort_values("Total")
    max_opts = opt.max_options_per_quote or 5
    df_top = df.head(max_opts).reset_index(drop=True)

    # ========== BUILD RESULT (THÊM SCHEDULE) ==========
    options = []
    for idx, row in df_top.iterrows():
        ct = {c.type: row[c.type] for c in req.containers}

        plan = [
            {
                "type": c.type,
                "quantity": c.quantity,
                "unit_rate": ct[c.type],
                "amount": ct[c.type] * c.quantity,
            }
            for c in req.containers
        ]

        # --- Gọi schedule_engine cho từng option ---
        sched = get_schedule_for(
            carrier=str(row["Carrier"]),
            pol=ship.pol,
            pod_code=str(row["POD"]),
            cargo_ready_iso=ship.cargo_ready_date,
        )

        options.append(
            {
                "index": idx + 1,
                "is_recommended": idx == 0,
                "carrier": row["Carrier"],
                "place_of_delivery": row["PlaceOfDelivery"],
                "pol": row["POL"],
                "pod": row["POD"],

                # ====== SCHEDULE INFO ======
                "service": sched.get("service"),
                "etd": sched.get("etd"),
                "eta": sched.get("eta"),
                "vessel": sched.get("vessel"),
                "week_label": sched.get("week_label"),
                "transit_min": sched.get("transit_min"),
                "transit_max": sched.get("transit_max"),

                # ====== RATE INFO ======
                "container_rates": ct,
                "container_plan": plan,
                "total_ocean_amount": row["Total"],
                "currency": opt.currency,
            }
        )

    # Summary
    summ = {
        "customer_name": req.customer.name,
        "pol": ship.pol,
        "place_of_delivery": ship.place_of_delivery,
        "commodity_type": ship.commodity_type,
        "containers_summary": ", ".join(
            f"{c.quantity} x {c.type}" for c in req.containers
        ),
        "is_soc": ship.is_soc,
    }

    return {
        "quote_ref_no": f"QT-{date.today().strftime('%Y%m%d')}",
        "quote_date": date.today().isoformat(),
        "summary": summ,
        "options": options,
        "containers": [c.type for c in req.containers],
    }
