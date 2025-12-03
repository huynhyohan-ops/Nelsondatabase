from datetime import date
import base64
from typing import List
import os    # ← THÊM DÒNG NÀY

import streamlit as st
import pandas as pd

from common.helpers import (
    MASTER_FILE,
    LOGO_FILE,
    load_master_cached,)

from quote_engine_v1 import (
    CustomerInfo,
    ShipmentInfo,
    ContainerPlanItem,
    EngineOptions,
    QuoteRequest,
    generate_quote,
    save_quote_internal,
    preview_cost_by_carrier,
)
from quote_pdf import generate_quote_pdf, generate_quote_pdf_multi


def render_quote_page():
    """Toàn bộ logic tab Quote – Ocean Freight Pricing."""

    # === Load Master (chỉ cho tab Quote) ===
    try:
        master_df = load_master_cached(MASTER_FILE, st.session_state["pricing_version"])
    except FileNotFoundError as e:
        st.error(f"Không load được Master file: {e}")
        st.info(
            "Anh hãy sang chức năng **Upload & Normalize** trong nhóm Pricing để upload RAW và bấm Normalize."
        )
        return

    # Chuẩn hoá dữ liệu cơ bản để fill form
    pol_list = sorted(master_df["POL"].dropna().astype(str).unique().tolist())
    carrier_list = (
        master_df["Carrier"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
        .tolist()
    )
    carrier_list = sorted(carrier_list)

    # ================== TITLE & SUMMARY CARDS ==================
    st.markdown(
        "<div class='section-title'>Quote – Ocean Freight Pricing</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Tạo báo giá nhanh từ Master Pricing, hỗ trợ multi-destination & PDF tự động.</div>",
        unsafe_allow_html=True,
    )

    c_top1, c_top2, c_top3 = st.columns(3)
    with c_top1:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Master rows</div>"
            f"<div class='info-card-value'>{len(master_df):,}</div>"
            "<div class='info-card-sub'>Số dòng giá hiện có</div></div>",
            unsafe_allow_html=True,
        )
    with c_top2:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Unique carriers</div>"
            f"<div class='info-card-value'>{len(carrier_list)}</div>"
            "<div class='info-card-sub'>Hãng đang active trong Master</div></div>",
            unsafe_allow_html=True,
        )
    with c_top3:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Pricing version</div>"
            f"<div class='info-card-value'>{st.session_state['pricing_version']}</div>"
            "<div class='info-card-sub'>Tăng sau mỗi lần Normalize</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")

    # ================== SECTION 1: CUSTOMER & SHIPMENT ==================
    st.subheader("1️⃣ Customer & Shipment")

    cust_col, ship_col = st.columns(2)

    # --- CUSTOMER INFO (LEFT) ---
    with cust_col:
        st.markdown("**Customer info**")
        customer_name = st.text_input("Customer name *", value="Test")
        contact_person = st.text_input("Contact person", value="")
        email = st.text_input("Email", value="")
        sales_person = st.text_input("Sales person", value="Nelson")

        today_iso = date.today().isoformat()
        st.caption(f"📅 Quote date (auto): {today_iso}")

    # --- SHIPMENT INFO (RIGHT) ---
    with ship_col:
        st.markdown("**Shipment info**")

        pol = st.selectbox(
            "POL *",
            options=pol_list,
            index=pol_list.index("HCM") if "HCM" in pol_list else 0,
        )

        df_pol = master_df.copy()
        df_pol["POL_upper"] = df_pol["POL"].astype(str).str.upper().str.strip()
        pol_upper = pol.upper().strip()

        places_for_pol = (
            df_pol[df_pol["POL_upper"] == pol_upper]["PlaceOfDelivery"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        places_for_pol = sorted(places_for_pol)

        if not places_for_pol:
            st.warning(
                "Không tìm thấy Place of Delivery nào trong Master cho POL này. "
                "Anh vui lòng kiểm tra lại file dữ liệu."
            )

        selected_places = st.multiselect(
            "Place of Delivery * (key chính để lọc giá – có thể chọn nhiều)",
            options=places_for_pol,
            default=places_for_pol[:1] if places_for_pol else [],
            help="Anh có thể chọn 1 hoặc nhiều cảng đích.",
        )

        pod_filter = None
        if len(selected_places) == 1 and places_for_pol:
            dest = selected_places[0]
            df_route = df_pol[
                (df_pol["POL_upper"] == pol_upper)
                & (
                    df_pol["PlaceOfDelivery"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                    == dest.upper().strip()
                )
            ]

            pod_options = (
                df_route["POD"]
                .dropna()
                .astype(str)
                .str.upper()
                .str.strip()
                .unique()
                .tolist()
            )
            pod_options = sorted(pod_options)

            if pod_options:
                pod_choice = st.selectbox(
                    "POD / Via port (optional – theo tuyến đã chọn)",
                    options=["(Tất cả POD)"] + pod_options,
                    index=0,
                    help="Nếu chọn (Tất cả POD) thì hệ thống sẽ lấy mọi via cho tuyến này.",
                )
                if pod_choice != "(Tất cả POD)":
                    pod_filter = pod_choice
            else:
                st.caption(
                    "Không có POD cụ thể trong Master cho tuyến này – hệ thống sẽ lấy tất cả."
                )
                pod_filter = None
        else:
            st.caption(
                "Đang chọn nhiều Place of Delivery → POD sẽ không lọc, hệ thống tự lấy mọi via tốt nhất."
            )
            pod_filter = None

        cargo_ready_date = st.date_input(
            "Cargo ready date (optional)", value=date.today()
        )

        incoterm = st.selectbox(
            "Incoterm", options=["FOB", "CIF", "EXW", "DAP"], index=0
        )

        commodity_type = st.selectbox(
            "Commodity type (ANY = không lọc)",
            options=["ANY", "FAK", "REEFER", "REEFER FAK", "FIX RATE", "SHORT TERM GDSM"],
            index=0,
        )

        is_soc = st.checkbox("Không dùng SOC (chỉ lấy COC)", value=False)

    # ================== SECTION 2: CONTAINER PLAN & ENGINE OPTIONS ==================
    st.subheader("2️⃣ Container plan & Engine options")

    plan_col, opts_col = st.columns(2)

    # --- CONTAINER PLAN (LEFT) ---
    with plan_col:
        st.markdown("**Container plan**")

        if commodity_type in ["REEFER", "REEFER FAK"]:
            r20 = st.number_input("Số lượng 20RF", min_value=0, value=0)
            r40 = st.number_input("Số lượng 40RF", min_value=0, value=0)
            c20 = c40 = c40hq = c45 = c40nor = 0
        else:
            r20 = r40 = 0
            c20 = st.number_input("Số lượng 20GP", min_value=0, value=0)
            c40 = st.number_input("Số lượng 40GP", min_value=0, value=0)
            c40hq = st.number_input("Số lượng 40HQ", min_value=0, value=0)
            c45 = st.number_input("Số lượng 45HQ", min_value=0, value=0)
            c40nor = st.number_input("Số lượng 40NOR", min_value=0, value=0)

    # --- ENGINE OPTIONS (RIGHT) ---
    with opts_col:
        st.markdown("**Engine options (advanced)**")

        preferred_carriers = st.multiselect(
            "Preferred carriers (để trống = cho tất cả, hệ thống tự chọn TOP carriers)",
            options=carrier_list,
            default=[],
        )

        excluded_carriers = st.multiselect(
            "Excluded carriers (optional)",
            options=carrier_list,
            default=[],
        )

        max_options_per_quote = st.number_input(
            "Max options per quote (chỉ dùng khi có preferred carriers)",
            min_value=1,
            max_value=10,
            value=5,
        )

        currency = st.selectbox("Currency", options=["USD", "VND"], index=0)

        st.markdown("**Markup / Profit per Carrier (USD per container)**")

        def suggest_markup(carrier, commodity_type):
            if commodity_type.upper() == "REEFER":
                return 150.0
            elif commodity_type.upper() == "FAK":
                return 80.0
            return 50.0

        markup_defaults = [
            {"Carrier": carrier, "Markup (USD/cont)": suggest_markup(carrier, commodity_type)}
            for carrier in carrier_list
        ]
        df_markup = pd.DataFrame(markup_defaults)

        edited_markup_df = st.data_editor(
            df_markup,
            use_container_width=True,
            num_rows="fixed",
            key="markup_editor",
        )

        markup_map = {
            row["Carrier"]: float(row["Markup (USD/cont)"])
            for _, row in edited_markup_df.iterrows()
        }

        st.session_state["markup_map"] = markup_map

        if commodity_type.upper() in ["REEFER", "REEFER FAK"]:
            total_containers = r20 + r40
        else:
            total_containers = r20 + r40 + c20 + c40 + c40hq + c45 + c40nor

        if markup_map and total_containers > 0:
            avg_markup = sum(markup_map.values()) / len(markup_map)
            total_profit = avg_markup * total_containers
            st.metric("Tổng lãi ước tính", f"${total_profit:,.0f}")
        else:
            st.caption("Không có markup hoặc không có container – hệ thống sẽ dùng cost gốc từ Master.")

        st.markdown("---")
        preview_btn = st.button("🔍 Preview internal cost (no markup)")
        generate_btn = st.button("🚀 Generate Quote")

    # ================== BUILD COMMON OBJECTS ==================
    any_action = preview_btn or generate_btn

    if any_action:
        containers: List[ContainerPlanItem] = []

        if commodity_type in ["REEFER", "REEFER FAK"]:
            if r20 > 0:
                containers.append(ContainerPlanItem(type="20RF", quantity=int(r20)))
            if r40 > 0:
                containers.append(ContainerPlanItem(type="40RF", quantity=int(r40)))
        else:
            if c20 > 0:
                containers.append(ContainerPlanItem(type="20GP", quantity=int(c20)))
            if c40 > 0:
                containers.append(ContainerPlanItem(type="40GP", quantity=int(c40)))
            if c40hq > 0:
                containers.append(ContainerPlanItem(type="40HQ", quantity=int(c40hq)))
            if c45 > 0:
                containers.append(ContainerPlanItem(type="45HQ", quantity=int(c45)))
            if c40nor > 0:
                containers.append(ContainerPlanItem(type="40NOR", quantity=int(c40nor)))

        if not containers:
            st.error("Vui lòng nhập ít nhất 1 container trong plan.")
            return

        if not selected_places:
            st.error("Vui lòng chọn ít nhất 1 Place of Delivery.")
            return

        customer = CustomerInfo(
            name=customer_name.strip(),
            contact_person=contact_person or None,
            email=email or None,
            sales_person=sales_person or None,
            quote_date=None,
            valid_until=None,
        )

        engine_opts = EngineOptions(
            preferred_carriers=preferred_carriers,
            excluded_carriers=excluded_carriers,
            max_options_per_quote=int(max_options_per_quote),
            sort_by="total_amount",
            include_premium_option=False,
            currency=currency,
            markup_per_carrier=st.session_state.get("markup_map", {}),
        )

        # map số lượng container theo type để dùng lại
        if commodity_type in ["REEFER", "REEFER FAK"]:
            qty_map = {"20RF": r20, "40RF": r40}
        else:
            qty_map = {
                "20GP": c20,
                "40GP": c40,
                "40HQ": c40hq,
                "45HQ": c45,
                "40NOR": c40nor,
            }

        # Các loại cont đang dùng trong plan (để tạo cột động)
        cont_types_in_plan = [t for t, q in qty_map.items() if q > 0]

        # ========== HÀM LẤY GIÁ TRỊ CONT TỪ MASTER (LẤY GIÁ THẤP NHẤT) ==========
        def get_cont_amounts_from_master(
            master: pd.DataFrame,
            opt: dict,
            place_of_delivery: str,
            summary: dict,
        ) -> dict:
            """
            Tìm các dòng rate trong Master tương ứng với option / carrier này,
            rồi lấy **giá thấp nhất (min) cho từng loại container** (đơn giá /1 cont, không nhân quantity).
            Dùng chung cho Preview & bảng Options cuối.
            """
            df = master.copy()

            def norm_one(s):
                return str(s).upper().strip()

            def norm_series(series: pd.Series):
                return series.astype(str).str.upper().str.strip()

            # Filter lần lượt theo các key nếu có cột
            carrier_val = opt.get("carrier")
            if carrier_val and "Carrier" in df.columns:
                df = df[norm_series(df["Carrier"]) == norm_one(carrier_val)]

            if "PlaceOfDelivery" in df.columns and place_of_delivery:
                df = df[
                    norm_series(df["PlaceOfDelivery"]) == norm_one(place_of_delivery)
                ]

            pol_val = summary.get("pol")
            if pol_val and "POL" in df.columns:
                df = df[norm_series(df["POL"]) == norm_one(pol_val)]

            pod_val = summary.get("pod")
            if pod_val and "POD" in df.columns:
                df = df[norm_series(df["POD"]) == norm_one(pod_val)]

            rate_type_val = opt.get("rate_type")
            if rate_type_val and "RateType" in df.columns:
                df = df[norm_series(df["RateType"]) == norm_one(rate_type_val)]

            contract_val = opt.get("contract_identifier")
            if contract_val and "Contract" in df.columns:
                df = df[
                    norm_series(df["Contract"])
                    == norm_one(contract_val)
                ]

            if df.empty:
                # không tìm thấy dòng tương ứng
                return {t: None for t in cont_types_in_plan}

            result = {}
            for t in cont_types_in_plan:
                if t in df.columns:
                    col_vals = pd.to_numeric(df[t], errors="coerce")
                    if col_vals.dropna().empty:
                        result[t] = None
                    else:
                        # 👉 lấy GIÁ THẤP NHẤT cho từng loại cont
                        rate = col_vals.min()
                        result[t] = float(rate)
                else:
                    result[t] = None
            return result

        # ========== PREVIEW INTERNAL COST ==========
        if preview_btn:
            st.markdown("---")
            st.subheader("🔍 Internal cost by carrier (no markup)")

            for dest in selected_places:
                st.markdown(f"#### 📍 Place of Delivery: {dest}")

                shipment_preview = ShipmentInfo(
                    pol=pol,
                    pod=pod_filter,
                    place_of_delivery=dest,
                    cargo_ready_date=cargo_ready_date.isoformat()
                    if cargo_ready_date
                    else None,
                    incoterm=incoterm,
                    commodity_type=commodity_type,
                    is_soc=is_soc,
                )

                prev_result = preview_cost_by_carrier(
                    master_df, shipment_preview, containers
                )
                if "error" in prev_result:
                    st.error(
                        f"{prev_result['error']}: {prev_result.get('message', '')}"
                    )
                else:
                    preview_df = prev_result["preview"].copy()

                    # Thêm các cột cont theo đúng Container Plan
                    preview_summary = {"pol": pol, "pod": pod_filter}

                    # Chuẩn hoá: nếu chưa có cột thì sẽ được add bằng giá từ Master
                    for idx, row in preview_df.iterrows():
                        opt_info = {
                            "carrier": row.get("Carrier"),
                            "rate_type": row.get("RateType") if "RateType" in preview_df.columns else None,
                            "contract_identifier": row.get("Contract") if "Contract" in preview_df.columns else None,
                        }
                        cont_amounts = get_cont_amounts_from_master(
                            master_df, opt_info, dest, preview_summary
                        )
                        for t in cont_types_in_plan:
                            preview_df.loc[idx, t] = cont_amounts.get(t)

                    # Bỏ cột Total nếu có (để anh tập trung xem unit price theo cont)
                    for col in ["Total (base USD)", "Total"]:
                        if col in preview_df.columns:
                            preview_df = preview_df.drop(columns=[col])

                    st.dataframe(preview_df)

                    with st.expander(
                        f"Debug (rows & filters) – preview cho {dest}"
                    ):
                        st.json(prev_result.get("debug", {}))

        # ========== GENERATE QUOTE ==========
        if generate_btn:
            st.markdown("---")
            st.subheader("3️⃣ Kết quả Quote")

            successful_results: List[dict] = []
            all_option_rows: List[dict] = []

            for dest_index, dest in enumerate(selected_places):
                st.markdown(f"## 🛳 Place of Delivery: {dest}")

                shipment = ShipmentInfo(
                    pol=pol,
                    pod=pod_filter,
                    place_of_delivery=dest,
                    cargo_ready_date=cargo_ready_date.isoformat()
                    if cargo_ready_date
                    else None,
                    incoterm=incoterm,
                    commodity_type=commodity_type,
                    is_soc=is_soc,
                )

                req = QuoteRequest(
                    customer=customer,
                    shipment=shipment,
                    containers=containers,
                    engine_options=engine_opts,
                )

                result = generate_quote(master_df, req)

                if "error" in result:
                    st.error(f"{result['error']}: {result.get('message', '')}")
                    with st.expander(f"Chi tiết lỗi / debug – {dest}"):
                        st.json(result)
                    continue

                successful_results.append(result)

                summary = result["summary"]
                options = result["options"]

                col_s1, col_s2, col_s3 = st.columns(3)

                with col_s1:
                    st.markdown(f"**Quote Ref:** `{result['quote_ref_no']}`")
                    st.markdown(f"**Quote date:** {result['quote_date']}")
                    st.markdown(f"**Customer:** {summary['customer_name']}")

                with col_s2:
                    st.markdown(f"**Route:** {summary['route']}")
                    st.markdown(
                        f"**Place of Delivery:** {summary['place_of_delivery']}"
                    )
                    st.markdown(f"**POD (via):** {summary.get('pod')}")

                with col_s3:
                    st.markdown(
                        f"**Containers:** {summary['containers_summary']}"
                    )
                    st.markdown(f"**Incoterm:** {summary.get('incoterm')}")
                    st.markdown(
                        f"**Commodity:** {summary.get('commodity_type')}"
                    )
                    st.markdown(f"**SOC:** {summary.get('is_soc')}")

                # --------- BUILD ROWS CHO BẢNG OPTIONS TỔNG ----------
                for opt in options:
                    row = {
                        "POL": summary.get("pol"),
                        "POD": summary.get("pod"),
                        "PlaceOfDelivery": dest,
                        "Carrier": opt["carrier"],
                        "RateType": opt["rate_type"],
                        "Contract": opt["contract_identifier"],
                        "Commodity": opt["commodity_type"],
                        "ValidFrom": opt["valid_from"],
                        "ValidTo": opt["valid_to"],
                        "RoutingNote": opt["notes"],
                        "__dest_order": dest_index,
                        "__sort_total": opt["total_ocean_amount"],
                    }

                    cont_amounts = get_cont_amounts_from_master(
                        master_df, opt, dest, summary
                    )
                    for t in cont_types_in_plan:
                        row[t] = cont_amounts.get(t)

                    all_option_rows.append(row)

                # Debug riêng cho từng POD
                with st.expander(f"Debug (rows & filters) – quote cho {dest}"):
                    st.json(result.get("debug", {}))

                # ================== LƯU & XUẤT FILE BÁO GIÁ CHO TỪNG POD ==================
                st.markdown("---")
                st.subheader(f"4️⃣ Lưu & xuất file báo giá – {dest}")

                log_path = save_quote_internal(result)
                st.success(f"Đã lưu log nội bộ: {log_path}")

                try:
                    pdf_path = generate_quote_pdf(result, logo_path=str(LOGO_FILE))
                    st.info(f"Đã tạo file PDF báo giá: {pdf_path}")

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    st.download_button(
                        label=f"📄 Tải file báo giá (PDF) – {dest}",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                    )

                    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f"""
                    <iframe src="data:application/pdf;base64,{b64}"
                            width="100%" height="800px" type="application/pdf"></iframe>
                    """
                    st.markdown("### 🔎 Xem trước file báo giá (PDF)")
                    st.markdown(pdf_display, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Không tạo được PDF: {e}")

            # --------- SAU KHI XỬ LÝ HẾT TẤT CẢ PLACEOFDELIVERY: VẼ BẢNG OPTIONS CHUNG ----------
            if all_option_rows:
                st.markdown("---")
                st.markdown("### Options (TOP carriers theo total amount) – tất cả PlaceOfDelivery")

                df_opts = pd.DataFrame(all_option_rows)

                # Sắp xếp: theo thứ tự anh chọn POD, rồi theo tổng amount tăng dần
                df_opts = df_opts.sort_values(["__dest_order", "__sort_total"])

                # Bỏ cột helper
                df_opts = df_opts.drop(columns=["__dest_order", "__sort_total"], errors="ignore")

                # Thứ tự cột: POL, POD, PlaceOfDelivery, Carrier, [cont], ...
                cont_cols_present = [t for t in cont_types_in_plan if t in df_opts.columns]
                base_cols_order = [
                    "POL",
                    "POD",
                    "PlaceOfDelivery",
                    "Carrier",
                    *cont_cols_present,
                    "RateType",
                    "Contract",
                    "Commodity",
                    "ValidFrom",
                    "ValidTo",
                    "RoutingNote",
                ]
                ordered = [c for c in base_cols_order if c in df_opts.columns]
                remaining = [c for c in df_opts.columns if c not in ordered]
                df_opts = df_opts[ordered + remaining]

                st.dataframe(df_opts)

            # ================== PDF MULTI-DESTINATION ==================
            if len(successful_results) > 1:
                st.markdown("---")
                st.subheader("📄 PDF tổng hợp – Multi Place of Delivery")

                try:
                    pdf_multi_path = generate_quote_pdf_multi(
                        successful_results, logo_path=str(LOGO_FILE)
                    )
                    st.info(f"Đã tạo file PDF MULTI DESTINATION: {pdf_multi_path}")

                    with open(pdf_multi_path, "rb") as f:
                        pdf_multi_bytes = f.read()

                    st.download_button(
                        label="📄 Tải PDF báo giá MULTI (tất cả Place of Delivery)",
                        data=pdf_multi_bytes,
                        file_name=os.path.basename(pdf_multi_path),
                        mime="application/pdf",
                    )

                    b64m = base64.b64encode(pdf_multi_bytes).decode("utf-8")
                    pdf_multi_display = f"""
                    <iframe src="data:application/pdf;base64,{b64m}"
                            width="100%" height="800px" type="application/pdf"></iframe>
                    """
                    st.markdown("### 🔎 Xem trước PDF MULTI (tổng hợp)")
                    st.markdown(pdf_multi_display, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Không tạo được PDF MULTI: {e}")