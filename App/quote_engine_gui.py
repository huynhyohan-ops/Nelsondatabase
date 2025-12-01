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
RAW_DIR = BASE_DIR / "Raw"  # thư mục chứa RAW excel (upload từ Streamlit)

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
from normalize_pricing_work import normalize_all_from_streamlit  # gọi normalize từ GUI


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
# MAIN APP
# ============================================================

def main():
    st.set_page_config(
        page_title="Pudong Pricing – Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ======= GLOBAL CSS – TONE SÁNG + SIDEBAR NỔI RÕ =======
    st.markdown(
        """
    <style>
    /* Toàn màn */
    [data-testid="stAppViewContainer"] {
        background: #f3f4f6;
        color: #111827;
    }
    [data-testid="stHeader"] {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(6px);
        border-bottom: 1px solid #e5e7eb;
    }
    [data-testid="stToolbar"] {display: none;}

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1f2937;
        padding-top: 0.8rem;
        border-right: 1px solid #0f172a;
    }
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f9fafb;
        padding-left: 0.5rem;
        margin-bottom: 0.4rem;
    }
    .sidebar-subtitle {
        font-size: 0.8rem;
        color: #e5e7eb;
        padding-left: 0.5rem;
        margin-bottom: 0.8rem;
    }
    .sidebar-radio > div[role='radiogroup'] > label {
        padding: 0.35rem 0.75rem;
        border-radius: 0.6rem;
        margin-bottom: 0.15rem;
        color: #e5e7eb !important;
        font-weight: 500;
    }
    .sidebar-radio > div[role='radiogroup'] > label:hover {
        background-color: #374151;
    }
    .sidebar-radio > div[role='radiogroup'] > label span {
        font-size: 0.9rem;
    }

    /* Card style – white, shadow */
    .info-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 18px;
        color: #111827;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 18px rgba(15,23,42,0.06);
    }
    .info-card-title {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.25rem;
    }
    .info-card-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
    }
    .info-card-sub {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 0.1rem;
    }

    /* Section title */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0.5rem;
        margin-bottom: 0.2rem;
    }
    .section-sub {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 0.8rem;
    }

    /* Label form */
    label {
        color: #374151 !important;
        font-weight: 500;
    }

    /* Dataframe container */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }

    /* Expander header */
    details summary {
        font-weight: 600;
    }

    /* Top menu bar (cho mobile) */
    .top-menu-bar {
        background: #f3f4f6;
        border-bottom: 1px solid #e5e7eb;
        padding: 0.4rem 0.1rem 0.6rem 0.1rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # === INIT SESSION STATE ===
    if "pricing_version" not in st.session_state:
        st.session_state["pricing_version"] = 0
    if "markup_map" not in st.session_state:
        st.session_state["markup_map"] = {}
    if "current_menu" not in st.session_state:
        st.session_state["current_menu"] = "Cập nhật & Normalize bảng giá"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # MENU OPTIONS
    # ============================================================
    menu_options = (
        "Cập nhật & Normalize bảng giá",
        "Dashboard",
        "CRM",
        "Follow Shipment",
        "Schedule",
        "Quote",
    )
    current_menu = st.session_state["current_menu"]
    if current_menu not in menu_options:
        current_menu = menu_options[0]

    # ============================================================
    # SIDEBAR MENU
    # ============================================================
    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.4rem; font-weight:800; color:#ffffff; margin-bottom:0.2rem;'>Pudong</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='sidebar-subtitle'>Logistics Pricing Suite</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            "<div class='sidebar-title'>OVERVIEW</div>",
            unsafe_allow_html=True,
        )

        sidebar_index = menu_options.index(current_menu)
        st.radio(
            "",
            menu_options,
            index=sidebar_index,
            label_visibility="collapsed",
            key="sidebar_menu_radio",
        )

    # ============================================================
    # TOP MENU BAR (cho mobile / quick jump)
    # ============================================================
    st.markdown('<div class="top-menu-bar">', unsafe_allow_html=True)
    col_tm1, col_tm2, col_tm3, col_tm4 = st.columns([1.6, 2.4, 1.3, 1.3])

    with col_tm1:
        st.markdown("**🚀 Chọn chức năng**")

    top_index = menu_options.index(current_menu)
    with col_tm2:
        st.selectbox(
            "",
            options=menu_options,
            index=top_index,
            label_visibility="collapsed",
            key="top_menu_select",
        )

    with col_tm3:
        go_quote = st.button("💰 Quote", use_container_width=True)
    with col_tm4:
        go_dashboard = st.button("📊 Dashboard", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    # ======= XÁC ĐỊNH MENU HIỆN TẠI (KHÔNG ĐỤNG VÀO KEY WIDGET) =======
    # Giá trị chọn từ sidebar và top dropdown
    sidebar_val = st.session_state.get("sidebar_menu_radio", current_menu)
    top_val = st.session_state.get("top_menu_select", sidebar_val)

    if go_quote:
        chosen_menu = "Quote"
    elif go_dashboard:
        chosen_menu = "Dashboard"
    else:
        # Nếu user đổi dropdown trên top, ưu tiên top; ngược lại dùng sidebar
        if top_val != current_menu:
            chosen_menu = top_val
        else:
            chosen_menu = sidebar_val

    st.session_state["current_menu"] = chosen_menu
    menu = chosen_menu  # từ đây dùng biến menu

    # ============================================================
    # 1) TAB: CẬP NHẬT & NORMALIZE BẢNG GIÁ
    # ============================================================
    if menu == "Cập nhật & Normalize bảng giá":
        st.markdown(
            "<div class='section-title'>Cập nhật & Normalize bảng giá</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-sub'>Upload file RAW (.xlsx), hệ thống sẽ tự động chuẩn hoá sang Master_FullPricing.xlsx trong thư mục Data.</div>",
            unsafe_allow_html=True,
        )

        col_u1, col_u2 = st.columns([2, 1])

        with col_u1:
            uploaded_raw = st.file_uploader(
                "Upload file giá RAW (.xlsx)",
                type=["xlsx"],
                accept_multiple_files=True,
                help="Anh có thể chọn 1 hoặc nhiều file RAW (FAK, ONE_SPECIAL, SCFI...)",
            )

        with col_u2:
            st.markdown(
                f"<div class='info-card'><div class='info-card-title'>Master Pricing version</div>"
                f"<div class='info-card-value'>{st.session_state['pricing_version']}</div>"
                f"<div class='info-card-sub'>{MASTER_FILE.name}</div></div>",
                unsafe_allow_html=True,
            )

        st.write("")
        if st.button("🧹 Normalize RAW → Master", use_container_width=True):
            if not uploaded_raw:
                st.warning("Anh cần upload ít nhất 1 file RAW trước.")
            else:
                for f in uploaded_raw:
                    out_path = RAW_DIR / f.name
                    with open(out_path, "wb") as g:
                        g.write(f.getbuffer())

                try:
                    with st.spinner(
                        "Đang Normalize bảng giá RAW → Master_FullPricing.xlsx ..."
                    ):
                        normalize_all_from_streamlit(
                            raw_dir_override=RAW_DIR,
                            data_dir_override=DATA_DIR,
                        )
                    st.session_state["pricing_version"] += 1
                    st.success("✅ Đã Normalize & cập nhật Master Pricing thành công.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Lỗi khi Normalize: {e}")

        st.markdown("---")
        st.caption(
            "Sau khi Normalize xong, chuyển sang tab **Quote** để tạo báo giá từ Master Pricing mới."
        )
        return

    # ============================================================
    # 2) TAB: DASHBOARD (khung nhẹ, anh phát triển sau)
    # ============================================================
    if menu == "Dashboard":
        st.markdown(
            "<div class='section-title'>Dashboard</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-sub'>Tổng quan shipment, doanh thu & tình trạng tuyến. Anh có thể bổ sung biểu đồ / KPI sau.</div>",
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Total Shipments</div>"
                "<div class='info-card-value'>3,024</div>"
                "<div class='info-card-sub'>Demo số liệu</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Ocean Freight</div>"
                "<div class='info-card-value'>7,120</div>"
                "<div class='info-card-sub'>Shipment đường biển (demo)</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Air Freight</div>"
                "<div class='info-card-value'>2,147</div>"
                "<div class='info-card-sub'>Shipment đường hàng không (demo)</div></div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Road Freight</div>"
                "<div class='info-card-value'>8,892</div>"
                "<div class='info-card-sub'>Đơn vận tải nội địa (demo)</div></div>",
                unsafe_allow_html=True,
            )

        st.info("Anh có thể thêm biểu đồ (Altair / Plotly) ở đây sau này.")
        return

    # ============================================================
    # 3) TAB: CRM (placeholder)
    # ============================================================
    if menu == "CRM":
        st.markdown(
            "<div class='section-title'>CRM – Khách hàng & Sales pipeline</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-sub'>Sau này anh có thể quản lý danh sách khách, pipeline, lịch sử báo giá tại đây.</div>",
            unsafe_allow_html=True,
        )
        st.info("Hiện tại chỉ là khung demo. Sau này anh có thể nối với Excel / DB để quản lý khách.")
        return

    # ============================================================
    # 4) TAB: FOLLOW SHIPMENT (placeholder – sẽ build DB sau)
    # ============================================================
    if menu == "Follow Shipment":
        st.markdown(
            "<div class='section-title'>Follow Shipment – Theo dõi lô hàng</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-sub'>Tab này sẽ là database shipment dùng để tính KPI cho Dashboard. Hiện tại đang để khung, sẽ build database sau.</div>",
            unsafe_allow_html=True,
        )
        st.info("Sắp tới mình sẽ kết nối tab này với 1 file DB riêng để anh thêm/sửa shipment trực tiếp.")
        return

    # ============================================================
    # 5) TAB: SCHEDULE (placeholder)
    # ============================================================
    if menu == "Schedule":
        st.markdown(
            "<div class='section-title'>Schedule – Lịch tàu / lịch giao nhận</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-sub'>Dùng để show lịch tàu theo carrier / tuyến, cut-off, ETD/ETA...</div>",
            unsafe_allow_html=True,
        )
        st.info("Tab này hiện để trống cho anh phát triển thêm sau.")
        return

    # ============================================================
    # 6) TAB: QUOTE – TOÀN BỘ LOGIC BÁO GIÁ HIỆN TẠI
    # ============================================================

    # === Load Master (chỉ cho tab Quote) ===
    try:
        master_df = load_master_cached(MASTER_FILE, st.session_state["pricing_version"])
    except FileNotFoundError as e:
        st.error(f"Không load được Master file: {e}")
        st.info(
            "Anh hãy sang tab **'Cập nhật & Normalize bảng giá'** để upload RAW và bấm Normalize."
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

        total_containers = (
            r20 + r40 + c20 + c40 + c40hq + c45 + c40nor
            if commodity_type.upper() != "REEFER"
            else r20 + r40
        )
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
                    st.dataframe(prev_result["preview"])
                    with st.expander(
                        f"Debug (rows & filters) – preview cho {dest}"
                    ):
                        st.json(prev_result.get("debug", {}))

        # ========== GENERATE QUOTE ==========
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

                result = generate_quote(master_df, req)

                if "error" in result:
                    st.error(f"{result['error']}: {result.get('message', '')}")
                    with st.expander(f"Chi tiết lỗi / debug – {dest}"):
                        st.json(result)
                    continue

                successful_results.append(result)

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

                with st.expander(f"Debug (rows & filters) – quote cho {dest}"):
                    st.json(result.get("debug", {}))

                # ================== LƯU & XUẤT FILE BÁO GIÁ ==================
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


if __name__ == "__main__":
    main()
