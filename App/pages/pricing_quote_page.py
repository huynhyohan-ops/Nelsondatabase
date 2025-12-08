# ==================== PRICING_QUOTE_PAGE.PY ====================

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import List, Dict
from html import escape

from common.models import (
    CustomerInfo,
    ShipmentInfo,
    ContainerPlanItem,
    EngineOptions,
    QuoteRequest,
    load_master,
    filter_by_validity,
)
from common.cost_engine import generate_quote
from common.schedule_engine import get_schedule_for


# ================================================================
# HELPERS – CACHE & COMMON
# ================================================================
@st.cache_data
def get_master_df():
    """
    Cache Master Pricing để tránh load lại mỗi lần tương tác UI.
    """
    return load_master()


def _sort_options(options):
    """
    Sắp xếp options: is_recommended = True sẽ nằm ở dòng đầu tiên,
    sau đó sort theo index.
    """
    return sorted(
        options,
        key=lambda o: (not o.get("is_recommended", False), o.get("index", 0)),
    )


def _build_quote_ref(summary: dict) -> str:
    """
    Quote ref no luôn = Customer name + ngày thực tế
    Ví dụ: Sorachi - 4DEC-2025
    """
    customer_name = summary.get("customer_name") or "-"
    qdate_str = summary.get("quote_date")

    d: date | None = None
    if qdate_str:
        try:
            d = date.fromisoformat(qdate_str[:10])
        except Exception:
            try:
                d = datetime.strptime(qdate_str, "%Y-%m-%d").date()
            except Exception:
                d = None

    if d is None:
        d = date.today()

    ref_date = f"{d.day}{d.strftime('%b').upper()}-{d.year}"
    return f"{customer_name} - {ref_date}"


def _build_preview_html(df: pd.DataFrame) -> str:
    """
    Xuất bảng ra HTML để anh copy bỏ vào VBA Excel.
    """
    headers = df.columns.tolist()
    lines = [
        "<table border='1' cellspacing='0' cellpadding='3'>",
        "  <thead>",
        "    <tr>",
    ]
    for h in headers:
        lines.append(f"      <th>{escape(str(h))}</th>")
    lines += [
        "    </tr>",
        "  </thead>",
        "  <tbody>",
    ]

    for _, row in df.iterrows():
        lines.append("    <tr>")
        for h in headers:
            val = row[h]
            if pd.isna(val):
                val = ""
            lines.append(f"      <td>{escape(str(val))}</td>")
        lines.append("    </tr>")

    lines += [
        "  </tbody>",
        "</table>",
    ]
    return "\n".join(lines)


# ================================================================
# PREVIEW INTERNAL COST – NÂNG CẤP CHỌN EXP XA NHẤT & RẺ NHẤT
# ================================================================
def _preview_internal_cost(
    master_df: pd.DataFrame,
    shipment: ShipmentInfo,
    containers: List[ContainerPlanItem],
) -> Dict:
    """
    Preview internal cost + schedule theo từng carrier.
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

    # ---- Lọc theo Validity (ExpirationDate >= ngày mốc) ----
    df = filter_by_validity(df, shipment.cargo_ready_date)
    if df.empty:
        return {
            "error": "NO_RATE_IN_DATE_RANGE",
            "message": "Không có dòng giá nào còn hiệu lực tại ngày cargo ready / ngày hiện tại.",
        }

    df["Carrier_upper"] = df["Carrier"].astype(str).str.upper().str.strip()

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
    df_valid["ExpirationDate_dt"] = pd.to_datetime(
    df_valid["ExpirationDate"], 
    format="%d-%b",  # ví dụ: 14-DEC
    errors="coerce"
).apply(lambda d: d.replace(year=date.today().year) if pd.notna(d) else d)

    # ================================
    # 🔁 CHỌN GIÁ HIỆU LỰC TẠI TODAY → GIÁ THẤP NHẤT
    # ================================
    today = pd.Timestamp.today().normalize()

    # Parse lại EffectiveDate và ExpirationDate, gán năm hiện tại
    df_valid["EffectiveDate_dt"] = pd.to_datetime(
        df_valid["EffectiveDate"],
        format="%d-%b",
        errors="coerce"
    ).apply(lambda d: d.replace(year=today.year) if pd.notna(d) else d)

    df_valid["ExpirationDate_dt"] = pd.to_datetime(
        df_valid["ExpirationDate"],
        format="%d-%b",
        errors="coerce"
    ).apply(lambda d: d.replace(year=today.year) if pd.notna(d) else d)

    # Lọc những dòng còn hiệu lực tại thời điểm hôm nay
    df_valid = df_valid[
        (df_valid["EffectiveDate_dt"] <= today) &
        (df_valid["ExpirationDate_dt"] >= today)
    ].copy()

    if df_valid.empty:
        return {
            "error": "NO_VALID_RATE_FOR_TODAY",
            "message": f"Không có dòng giá nào còn hiệu lực tại ngày hôm nay ({today.strftime('%d-%b-%Y')})."
        }

    # Chọn dòng có chi phí thấp nhất cho mỗi Carrier
    idx_best = df_valid.groupby("Carrier_upper")["TotalBase"].idxmin()
    df_per_carrier = df_valid.loc[idx_best].copy()
    df_per_carrier = df_per_carrier.sort_values(by="TotalBase", ascending=True).reset_index(drop=True)


    # ---- Build DataFrame preview theo format UI ----
    cont_types = []
    for item in containers:
        if item.type not in cont_types:
            cont_types.append(item.type)

    rows = []
    for idx, (_, row) in enumerate(df_per_carrier.iterrows(), start=1):
        base_rates: Dict[str, float] = {}
        for ct in cont_types:
            r = get_base_rate(row, ct)
            base_rates[ct] = "" if r is None or pd.isna(r) else float(r)

        sched = get_schedule_for(
            carrier=str(row.get("Carrier", "")),
            pol=shipment.pol,
            pod_code=str(row.get("POD", "")),
            cargo_ready_iso=shipment.cargo_ready_date,
        )

        transit_str = ""
        tmin = sched.get("transit_min")
        tmax = sched.get("transit_max")
        if tmin and tmax:
            transit_str = f"{tmin}-{tmax}d"

        preview_row = {
            "#": idx,
            "Carrier": row.get("Carrier", ""),
            "POD": row.get("POD", ""),
            "Place of Delivery": row.get("PlaceOfDelivery", ""),
            "Service": sched.get("service", ""),
            "Vessel": sched.get("vessel", ""),
            "ETD": sched.get("etd", ""),
            "Transit": transit_str,
            "RoutingNote": row.get("RoutingNote", ""),
            "EffectiveDate": row.get("EffectiveDate", ""),
            "ExpirationDate": row.get("ExpirationDate", ""),
            "CommodityType": row.get("CommodityType", ""),
            "RateType": row.get("RateType", ""),
        }

        for ct in cont_types:
            preview_row[ct] = base_rates.get(ct, "")

        rows.append(preview_row)

    df_preview = pd.DataFrame(rows)

    debug_info = {
        "rows_after_filters": int(len(df)),
        "rows_with_full_rates": int(len(df_valid)),
        "carriers_returned": int(len(df_preview)),
    }

    return {"preview_df": df_preview, "debug": debug_info}

# ================================================================
# MAIN QUOTE PAGE
# ================================================================
def render_quote_page():

    st.markdown("## 💲 Pricing – Create Quote")
    st.markdown(
        "Nhập thông tin lô hàng, chọn loại container và hệ thống sẽ đề xuất bảng giá + lịch tàu phù hợp nhất."
    )

    # Session state
    if "quote_result" not in st.session_state:
        st.session_state["quote_result"] = None   # full result từ generate_quote
        st.session_state["preview_df"] = None     # DataFrame internal cost
        st.session_state["mode"] = None           # "preview" hoặc "full"
        st.session_state["summary"] = {}
        st.session_state["selected_cont_types"] = []

    # ===================== LOAD MASTER ======================
    try:
        master_df = get_master_df()
    except Exception as e:
        st.error(f"❌ Lỗi load Master Pricing:\n\n{e}")
        return

    carrier_list = sorted(master_df["Carrier"].dropna().unique().tolist())
    pol_list = sorted(master_df["POL"].dropna().unique().tolist())

    # ===================== SUMMARY CARDS =====================
    total_rows = len(master_df)
    unique_carriers = len(carrier_list)
    pricing_version = (
        master_df["PricingVersion"].max()
        if "PricingVersion" in master_df.columns
        else "-"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Master rows", f"{total_rows:,}")
    with c2:
        st.metric("Unique carriers", unique_carriers)
    with c3:
        st.metric("Pricing version", pricing_version)

    st.markdown("---")

    # ================================================================
    # 1️⃣ CUSTOMER & SHIPMENT
    # ================================================================
    st.subheader("1️⃣ Customer & Shipment")

    cust_col, ship_col = st.columns(2)

    # -------- CUSTOMER INFO --------
    with cust_col:
        st.markdown("**Customer info**")
        customer_name = st.text_input("Customer name *", value="Demo Customer")
        contact_person = st.text_input("Contact person")
        email = st.text_input("Email")
        sales_person = st.text_input("Sales person", value="Nelson")

        today_iso = date.today().isoformat()
        st.caption(f"📅 Quote date: {today_iso}")

    # -------- SHIPMENT INFO --------
    with ship_col:
        st.markdown("**Shipment info**")

        pol = st.selectbox(
            "POL *",
            options=pol_list,
            index=pol_list.index("HCM") if "HCM" in pol_list else 0,
        )

        df_pol = master_df.copy()
        df_pol["POL_up"] = df_pol["POL"].astype(str).str.upper().str.strip()
        pol_upper = pol.upper().strip()

        places_for_pol = (
            df_pol[df_pol["POL_up"] == pol_upper]["PlaceOfDelivery"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        places_for_pol = sorted(places_for_pol)

        selected_places = st.multiselect(
            "Place of Delivery *",
            options=places_for_pol,
            default=places_for_pol[:1] if places_for_pol else [],
        )

        # POD filter (optional)
        raw_pod = ""
        if len(selected_places) == 1:
            raw_pod = st.text_input("POD (via) – optional", value="")

        pod_filter = raw_pod.strip() or None

        cargo_ready_date = st.date_input(
            "Cargo ready date (optional)", value=date.today()
        )

        incoterm = "FOB"  # fixed

        commodity_type = st.selectbox(
            "Commodity type",
            ["FAK", "REEFER", "REEFER FAK"],
            index=0,
        )

        is_soc = st.checkbox("SOC (shipper own container)?", value=False)

    st.markdown("---")

    # ================================================================
    # 2️⃣ CONTAINER PLAN + ENGINE OPTIONS
    # ================================================================
    st.subheader("2️⃣ Container plan & Engine options")

    plan_col, opts_col = st.columns(2)

    # -------- CONTAINER PLAN --------
    with plan_col:
        st.markdown("**Container plan**")

        if commodity_type.upper() in ["REEFER", "REEFER FAK"]:
            st.caption("Hàng reefer – chọn container:")

            c1, c2 = st.columns(2)
            with c1:
                sel_r20 = st.checkbox("20RF")
            with c2:
                sel_r40 = st.checkbox("40RF")

            r20 = 1 if sel_r20 else 0
            r40 = 1 if sel_r40 else 0

            c20 = c40 = c40hq = c45 = c40nor = 0

        else:
            st.caption("Tick chọn container (mặc định quantity = 1).")

            row1 = st.columns(3)
            row2 = st.columns(3)

            with row1[0]:
                sel_c20 = st.checkbox("20GP")
            with row1[1]:
                sel_c40 = st.checkbox("40GP")
            with row1[2]:
                sel_c40hq = st.checkbox("40HQ")

            with row2[0]:
                sel_c45 = st.checkbox("45HQ")
            with row2[1]:
                sel_c40nor = st.checkbox("40NOR")

            c20 = 1 if sel_c20 else 0
            c40 = 1 if sel_c40 else 0
            c40hq = 1 if sel_c40hq else 0
            c45 = 1 if sel_c45 else 0
            c40nor = 1 if sel_c40nor else 0

            r20 = r40 = 0

    # -------- ENGINE OPTIONS --------
    with opts_col:
        st.markdown("**Engine options (advanced)**")

        preferred_carriers = st.multiselect(
            "Preferred carriers", options=carrier_list, default=[]
        )

        excluded_carriers = st.multiselect(
            "Excluded carriers", options=carrier_list, default=[]
        )

        max_options = st.number_input(
            "Max options per quote", min_value=1, max_value=10, value=5
        )

        currency = st.selectbox("Currency", ["USD", "VND"], index=0)

        st.markdown("**Markup per carrier (USD/cont)**")

        def suggest_markup(carrier, typ):
            if typ.upper() == "REEFER":
                return 150
            if typ.upper() == "FAK":
                return 80
            return 50

        df_markup = pd.DataFrame(
            [{"Carrier": c, "Markup": suggest_markup(c, commodity_type)} for c in carrier_list]
        )

        df_edit = st.data_editor(
            df_markup,
            use_container_width=True,
            key="markup_editor",
            num_rows="fixed",
        )

        markup_map = {row["Carrier"]: float(row["Markup"]) for _, row in df_edit.iterrows()}
        st.session_state["markup_map"] = markup_map

        preview_btn = st.button("🔍 Preview internal cost")
        generate_btn = st.button("🚀 Generate Quote")

    # ================================================================
    # 3️⃣ ENGINE CALL – CHỈ CHẠY KHI BẤM NÚT
    # ================================================================
    if preview_btn or generate_btn:
        # Build container objects + list cont types
        containers: List[ContainerPlanItem] = []
        selected_cont_types: List[str] = []

        if r20:
            containers.append(ContainerPlanItem("20RF", 1))
            selected_cont_types.append("20RF")
        if r40:
            containers.append(ContainerPlanItem("40RF", 1))
            selected_cont_types.append("40RF")

        if c20:
            containers.append(ContainerPlanItem("20GP", 1))
            selected_cont_types.append("20GP")
        if c40:
            containers.append(ContainerPlanItem("40GP", 1))
            selected_cont_types.append("40GP")
        if c40hq:
            containers.append(ContainerPlanItem("40HQ", 1))
            selected_cont_types.append("40HQ")
        if c45:
            containers.append(ContainerPlanItem("45HQ", 1))
            selected_cont_types.append("45HQ")
        if c40nor:
            containers.append(ContainerPlanItem("40NOR", 1))
            selected_cont_types.append("40NOR")

        if not containers:
            st.error("❌ Anh phải chọn ít nhất 1 container để báo giá.")
            return

        shipment = ShipmentInfo(
            pol=pol,
            pod=pod_filter,
            place_of_delivery=selected_places[0] if selected_places else "",
            cargo_ready_date=str(cargo_ready_date) if cargo_ready_date else None,
            incoterm=incoterm,
            commodity_type=commodity_type,
            is_soc=is_soc,
        )

        customer = CustomerInfo(
            name=customer_name,
            contact_person=contact_person,
            email=email,
            sales_person=sales_person,
            quote_date=today_iso,
        )

        engine_opts = EngineOptions(
            preferred_carriers=preferred_carriers or [],
            excluded_carriers=excluded_carriers or [],
            max_options_per_quote=max_options,
            currency=currency,
            markup_per_carrier=markup_map,
        )

        req = QuoteRequest(
            customer=customer,
            shipment=shipment,
            containers=containers,
            engine_options=engine_opts,
        )

        with st.spinner("⏳ Đang tính toán..."):
            result_quote = generate_quote(master_df, req)

            if "error" in result_quote:
                st.error(f"❌ {result_quote['message']}")
                return

            summary = result_quote.get("summary", {}) or {}
            summary.setdefault("customer_name", customer_name)
            summary.setdefault("pol", pol)
            summary.setdefault("place_of_delivery", shipment.place_of_delivery)
            summary.setdefault(
                "containers_summary",
                ", ".join(f"{it.quantity} x {it.type}" for it in containers),
            )
            summary.setdefault("commodity_type", commodity_type)
            summary["quote_date"] = result_quote.get("quote_date", today_iso)

            if preview_btn:
                preview = _preview_internal_cost(master_df, shipment, containers)
                if "error" in preview:
                    st.error(f"❌ {preview['message']}")
                    return

                df_preview = preview["preview_df"]

                # Đưa option recommended (từ generate_quote) lên đầu nếu tìm được
                options = result_quote.get("options", [])
                rec_opt = None
                for opt in options:
                    if opt.get("is_recommended"):
                        rec_opt = opt
                        break
                if rec_opt is not None and not df_preview.empty:
                    mask = (
                        (df_preview["Carrier"] == rec_opt.get("carrier"))
                        & (df_preview["POD"] == rec_opt.get("pod"))
                        & (
                            df_preview["Place of Delivery"]
                            == rec_opt.get("place_of_delivery")
                        )
                    )
                    if mask.any():
                        rec_rows = df_preview[mask]
                        other_rows = df_preview[~mask]
                        df_preview = pd.concat(
                            [rec_rows, other_rows], ignore_index=True
                        )
                        df_preview["#"] = range(1, len(df_preview) + 1)

                st.session_state["mode"] = "preview"
                st.session_state["quote_result"] = result_quote
                st.session_state["preview_df"] = df_preview
                st.session_state["summary"] = summary
                st.session_state["selected_cont_types"] = selected_cont_types

            elif generate_btn:
                st.session_state["mode"] = "full"
                st.session_state["quote_result"] = result_quote
                st.session_state["summary"] = summary
                st.session_state["selected_cont_types"] = selected_cont_types

    # ================================================================
    # 4️⃣ RENDER KẾT QUẢ TỪ SESSION STATE
    # ================================================================
    mode = st.session_state.get("mode")
    summary = st.session_state.get("summary", {}) or {}

    if not mode:
        return

    quote_result = st.session_state.get("quote_result")
    selected_cont_types = st.session_state.get("selected_cont_types", [])

    quote_ref = _build_quote_ref(summary)
    route_display = f"{summary.get('pol', '-') } → {summary.get('place_of_delivery', '-')}"
    containers_summary = summary.get("containers_summary", "-")

    st.subheader("🚀 Quote Result")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Quote ref no", quote_ref)
    with m2:
        st.metric("Route", route_display)
    with m3:
        st.metric("Containers summary", containers_summary)

    # ---------------- PREVIEW INTERNAL COST ----------------
    if mode == "preview":
        df_preview = st.session_state.get("preview_df")
        if df_preview is None or df_preview.empty:
            st.warning("Không có dữ liệu preview.")
            return

        st.caption(
            "🔍 Internal cost preview – dòng đầu tiên tương ứng option được recommend (is_recommended = True)."
        )

        st.dataframe(df_preview, use_container_width=True)

        with st.expander("📋 Copy HTML cho Excel VBA"):
            html_table = _build_preview_html(df_preview)
            st.code(html_table, language="html")

        with st.expander("Xem raw data (JSON – generate_quote)"):
            st.json(quote_result)

        return

    # ---------------- FULL QUOTE RESULT (Generate Quote) ----------------
    if mode == "full":
        if not quote_result or "options" not in quote_result:
            st.warning("Không có option nào được tạo.")
            return

        st.markdown(
            f"**Customer:** {summary.get('customer_name','-')}  \n"
            f"**Commodity:** {summary.get('commodity_type','-')}  \n"
            f"**Containers:** {containers_summary}"
        )

        options_sorted = _sort_options(quote_result["options"])

        rows = []
        for opt in options_sorted:
            rates = opt.get("container_rates", {}) or {}

            tmin = opt.get("transit_min")
            tmax = opt.get("transit_max")
            transit_str = (
                f"{tmin}-{tmax}d" if (tmin is not None and tmax is not None) else ""
            )

            rows.append(
                {
                    "#": opt.get("index"),
                    "Recommended": "✅" if opt.get("is_recommended") else "",
                    "Carrier": opt.get("carrier"),
                    "POD": opt.get("pod"),
                    "Place of Delivery": opt.get("place_of_delivery"),
                    "Service": opt.get("service"),
                    "Vessel": opt.get("vessel"),
                    "ETD": opt.get("etd"),
                    "ETA": opt.get("eta"),
                    "Transit": transit_str,
                    "20GP": rates.get("20GP", ""),
                    "40GP": rates.get("40GP", ""),
                    "40HQ": rates.get("40HQ", ""),
                    "45HQ": rates.get("45HQ", ""),
                    "40NOR": rates.get("40NOR", ""),
                    "20RF": rates.get("20RF", ""),
                    "40RF": rates.get("40RF", ""),
                    "Total (USD)": opt.get("total_ocean_amount"),
                }
            )

        df_options = pd.DataFrame(rows)
        st.dataframe(df_options, use_container_width=True)

        with st.expander("Xem raw data (JSON – generate_quote)"):
            st.json(quote_result)

        # PDF
        from common.generator import generate_quote_pdf

        pdf_path = generate_quote_pdf(quote_result)

        st.success("PDF generated successfully!")
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Download PDF",
                data=f.read(),
                file_name=pdf_path.split("/")[-1],
                mime="application/pdf",
            )
