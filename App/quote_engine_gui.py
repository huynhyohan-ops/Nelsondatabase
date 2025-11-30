from pathlib import Path
import sys
from datetime import date
import base64
from typing import List

import os
import streamlit as st
import pandas as pd

# ============================================================
# PATH & IMPORT CONFIG
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENGINE_DIR = BASE_DIR / "Engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.append(str(ENGINE_DIR))

DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "Assets"
OUTPUT_DIR = BASE_DIR / "Output"

LOG_DIR = OUTPUT_DIR / "Quotes_Log"
PDF_DIR = OUTPUT_DIR / "Quotes_Client_PDF"

MASTER_FILE = DATA_DIR / "Master_FullPricing.xlsx"
LOGO_FILE = ASSETS_DIR / "logo_pudong.png"

from quote_engine_v1 import (
    load_master,
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


# ============================================================
# CACHED LOADER
# ============================================================

@st.cache_data
def load_master_cached(path: Path) -> pd.DataFrame:
    return load_master(path)


# ============================================================
# MAIN APP
# ============================================================

def main():
    st.set_page_config(page_title="Quote Engine v1", layout="wide")
    st.title("📦 Quote Engine – từ Master Pricing")

    # === Load Master ===
    try:
        master_df = load_master_cached(MASTER_FILE)
    except FileNotFoundError as e:
        st.error(f"Không load được Master file: {e}")
        st.stop()

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

    # init markup map trong session_state
    if "markup_map" not in st.session_state:
        st.session_state["markup_map"] = {}

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

        # ----- BUILD LIST PLACE OF DELIVERY THEO POL -----
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
            help="Anh có thể chọn 1 hoặc nhiều cảng đích. Hệ thống sẽ tạo báo giá riêng cho từng cảng trong 1 lần chạy.",
        )

        # ----- POD FILTER PHỤ THUỘC PLACE OF DELIVERY -----
        pod_filter = None

        if len(selected_places) == 1 and places_for_pol:
            # Lọc danh sách POD thực tế cho tuyến này
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
                st.caption("Không có POD cụ thể trong Master cho tuyến này – hệ thống sẽ lấy tất cả.")
                pod_filter = None
        else:
            # Nhiều PlaceOfDelivery: POD không lọc, lấy all via
            st.caption(
                "Đang chọn nhiều Place of Delivery → POD sẽ không lọc, hệ thống tự lấy mọi via tốt nhất cho từng tuyến."
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

        
        # ================== MARKUP CONTROLS – UPGRADED ==================
        st.markdown("**Markup / Profit per Carrier (USD per container)**")

        # Gợi ý markup mặc định theo loại hàng
        def suggest_markup(carrier, commodity_type):
            if commodity_type.upper() == "REEFER":
                return 150.0
            elif commodity_type.upper() == "FAK":
                return 80.0
            return 50.0

        # Chuẩn bị bảng editable
        markup_defaults = [
            {"Carrier": carrier, "Markup (USD/cont)": suggest_markup(carrier, commodity_type)}
            for carrier in carrier_list
        ]
        df_markup = pd.DataFrame(markup_defaults)

        edited_markup_df = st.data_editor(
            df_markup,
            use_container_width=True,
            num_rows="fixed",
            key="markup_editor"
        )

        # Tạo markup_map từ bảng người dùng chỉnh
        markup_map = {
            row["Carrier"]: float(row["Markup (USD/cont)"])
            for _, row in edited_markup_df.iterrows()
        }

        # Lưu vào session_state để dùng sau
        st.session_state["markup_map"] = markup_map

        # Tính lãi dự kiến
        total_containers = (
            r20 + r40 + c20 + c40 + c40hq + c45 + c40nor
            if commodity_type.upper() != "REEFER"
            else r20 + r40
        )
        if markup_map:
            avg_markup = sum(markup_map.values()) / len(markup_map)
            total_profit = avg_markup * total_containers
            st.metric("Tổng lãi ước tính", f"${total_profit:,.0f}")
        else:
            st.caption("Không có markup nào – hệ thống sẽ dùng cost gốc từ Master.")

        st.markdown("---")
        preview_btn = st.button("🔍 Preview internal cost (no markup)")
        generate_btn = st.button("🚀 Generate Quote")

    # ================== BUILD COMMON OBJECTS (containers, request) ==================
    any_action = preview_btn or generate_btn

    if any_action:
        # Build container list theo plan
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
            st.stop()

        if not selected_places:
            st.error("Vui lòng chọn ít nhất 1 Place of Delivery.")
            st.stop()

        # Customer info dùng chung
        customer = CustomerInfo(
            name=customer_name.strip(),
            contact_person=contact_person or None,
            email=email or None,
            sales_person=sales_person or None,
            quote_date=None,
            valid_until=None,
        )

        # Engine options dùng chung
        engine_opts = EngineOptions(
            preferred_carriers=preferred_carriers,
            excluded_carriers=excluded_carriers,
            max_options_per_quote=int(max_options_per_quote),
            sort_by="total_amount",
            include_premium_option=False,
            currency=currency,
            markup_per_carrier=st.session_state.get("markup_map", {}),
        )

        # ========== PREVIEW INTERNAL COST (no markup) ==========
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
                    st.dataframe(prev_result["preview"])
                    with st.expander(
                        f"Debug (rows & filters) – preview cho {dest}"
                    ):
                        st.json(prev_result.get("debug", {}))

        # ========== GENERATE QUOTE (với markup nếu có) ==========
        if generate_btn:
            st.markdown("---")
            st.subheader("3️⃣ Kết quả Quote")

            successful_results: List[dict] = []

            for dest in selected_places:
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

                # Gọi engine
                result = generate_quote(master_df, req)

                if "error" in result:
                    st.error(f"{result['error']}: {result.get('message', '')}")
                    with st.expander(f"Chi tiết lỗi / debug – {dest}"):
                        st.json(result)
                    # sang cảng tiếp theo
                    continue

                successful_results.append(result)

                # Summary
                summary = result["summary"]
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

                options = result["options"]

                # Bảng tóm tắt options
                st.markdown("### Options (TOP carriers theo total amount)")
                table_rows = []
                for opt in options:
                    table_rows.append(
                        {
                            "Option": f"{opt['index']}"
                            + (" ⭐" if opt["is_recommended"] else ""),
                            "Carrier": opt["carrier"],
                            "RateType": opt["rate_type"],
                            "Contract": opt["contract_identifier"],
                            "Total": opt["total_ocean_amount"],
                            "Validity": f"{opt['valid_from']} → {opt['valid_to']}",
                            "Commodity": opt["commodity_type"],
                            "Notes": opt["notes"],
                        }
                    )
                st.dataframe(pd.DataFrame(table_rows))

                # Chi tiết từng option
                st.markdown("### Chi tiết từng Option")
                for opt in options:
                    title = (
                        f"Option {opt['index']} – {opt['carrier']} "
                        f"({opt['total_ocean_amount']} {opt['currency']})"
                    )
                    if opt["is_recommended"]:
                        title += " ⭐ Recommended"

                    with st.expander(title, expanded=opt["is_recommended"]):
                        st.write(f"**Carrier:** {opt['carrier']}")
                        st.write(f"**RateType:** {opt['rate_type']}")
                        st.write(f"**Contract:** {opt['contract_identifier']}")
                        st.write(f"**Commodity:** {opt['commodity_type']}")
                        st.write(
                            f"**Validity:** {opt['valid_from']} → {opt['valid_to']}"
                        )
                        st.write(f"**Notes:** {opt['notes']}")
                        st.write("**Container plan:**")
                        df_plan = pd.DataFrame(opt["container_plan"])
                        st.table(df_plan)

                # Debug
                with st.expander(f"Debug (rows & filters) – quote cho {dest}"):
                    st.json(result.get("debug", {}))

                # ================== 4️⃣ LƯU & XUẤT FILE BÁO GIÁ (PER DEST) ==================
                st.markdown("---")
                st.subheader(f"4️⃣ Lưu & xuất file báo giá – {dest}")

                # 4.1 Lưu log nội bộ (Excel)
                log_path = save_quote_internal(result)
                st.success(f"Đã lưu log nội bộ: {log_path}")

                # 4.2 Tạo PDF báo giá (single destination)
                try:
                    pdf_path = generate_quote_pdf(result, logo_path=str(LOGO_FILE))
                    st.info(f"Đã tạo file PDF báo giá: {pdf_path}")

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    # Nút tải file PDF
                    st.download_button(
                        label=f"📄 Tải file báo giá (PDF) – {dest}",
                        data=pdf_bytes,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                    )

                    # Preview PDF trên trang bằng iframe base64
                    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
                    pdf_display = f"""
                    <iframe src="data:application/pdf;base64,{b64}"
                            width="100%" height="800px" type="application/pdf"></iframe>
                    """
                    st.markdown("### 🔎 Xem trước file báo giá (PDF)")
                    st.markdown(pdf_display, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Không tạo được PDF: {e}")

            # ================== PDF MULTI-DESTINATION (NẾU >1 KẾT QUẢ OK) ==================
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


if __name__ == "__main__":
    main()
