import streamlit as st

from common.helpers import RAW_DIR, DATA_DIR, safe_rerun
from common.style import inject_global_css

from pages.pricing_upload_page import render_upload_and_normalize
from pages.pricing_quote_page import render_quote_page
from pages.pricing_schedules_page import render_schedules_page
from pages.shipment_follow_page import render_follow_shipment_page
from pages.shipment_dashboard_page import render_dashboard_page
from pages.customers_crm_page import render_crm_page


def render_pricing_hub():
    st.markdown(
        "<div class='section-title'>Pricing center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Quản lý bảng giá, tạo báo giá, xem lịch tàu.</div>",
        unsafe_allow_html=True,
    )

    sub_page = st.session_state.get("sub_page")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Upload & Normalize</div>"
            "<div class='info-card-value'>RAW → Master</div>"
            "<div class='info-card-sub'>Upload file RAW & chuẩn hoá bảng giá.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("☁️ Vào Upload & Normalize", key="btn_pricing_upload", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Upload"
            safe_rerun()

    with c2:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Quote</div>"
            "<div class='info-card-value'>Ocean Freight</div>"
            "<div class='info-card-sub'>Tạo báo giá nhanh từ Master Pricing.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("💲 Vào Quote", key="btn_pricing_quote", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Quote"
            safe_rerun()

    with c3:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Schedules</div>"
            "<div class='info-card-value'>Lịch tàu</div>"
            "<div class='info-card-sub'>Cut-off, ETD/ETA theo tuyến & carrier.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("📅 Vào Schedules", key="btn_pricing_schedules", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Schedules"
            safe_rerun()

    sub_page = st.session_state.get("sub_page")
    if sub_page and sub_page.startswith("PRICING."):
        st.markdown("---")
        if st.button("⬅️ Quay lại menu Pricing", key="btn_back_pricing"):
            st.session_state["sub_page"] = None
            safe_rerun()

        if sub_page == "PRICING.Upload":
            render_upload_and_normalize()
        elif sub_page == "PRICING.Quote":
            render_quote_page()
        elif sub_page == "PRICING.Schedules":
            render_schedules_page()


def render_shipment_hub():
    st.markdown(
        "<div class='section-title'>Shipment center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Theo dõi lô hàng & dashboard vận hành.</div>",
        unsafe_allow_html=True,
    )

    sub_page = st.session_state.get("sub_page")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Follow Shipment</div>"
            "<div class='info-card-value'>Tracking</div>"
            "<div class='info-card-sub'>Quản lý database shipment & tình trạng.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("📦 Vào Follow Shipment", key="btn_ship_follow", use_container_width=True):
            st.session_state["sub_page"] = "SHIPMENT.Follow"
            safe_rerun()

    with c2:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>Dashboard</div>"
            "<div class='info-card-value'>KPI</div>"
            "<div class='info-card-sub'>Tổng quan shipment, doanh thu, tuyến.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("📊 Vào Dashboard", key="btn_ship_dashboard", use_container_width=True):
            st.session_state["sub_page"] = "SHIPMENT.Dashboard"
            safe_rerun()

    sub_page = st.session_state.get("sub_page")
    if sub_page and sub_page.startswith("SHIPMENT."):
        st.markdown("---")
        if st.button("⬅️ Quay lại menu Shipment", key="btn_back_shipment"):
            st.session_state["sub_page"] = None
            safe_rerun()

        if sub_page == "SHIPMENT.Follow":
            render_follow_shipment_page()
        elif sub_page == "SHIPMENT.Dashboard":
            render_dashboard_page()


def render_customers_hub():
    st.markdown(
        "<div class='section-title'>Customer center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>CRM, khách hàng & sales pipeline.</div>",
        unsafe_allow_html=True,
    )

    sub_page = st.session_state.get("sub_page")

    c1, _ = st.columns([2, 1])

    with c1:
        st.markdown(
            "<div class='info-card'><div class='info-card-title'>CRM</div>"
            "<div class='info-card-value'>Khách hàng</div>"
            "<div class='info-card-sub'>Quản lý thông tin khách & lịch sử báo giá.</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("👤 Vào CRM", key="btn_cus_crm", use_container_width=True):
            st.session_state["sub_page"] = "CUSTOMERS.CRM"
            safe_rerun()

    sub_page = st.session_state.get("sub_page")
    if sub_page and sub_page.startswith("CUSTOMERS."):
        st.markdown("---")
        if st.button("⬅️ Quay lại menu Customers", key="btn_back_customers"):
            st.session_state["sub_page"] = None
            safe_rerun()

        if sub_page == "CUSTOMERS.CRM":
            render_crm_page()


def main():
    st.set_page_config(
        page_title="Pudong Pricing – Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_global_css()

    # === INIT SESSION STATE ===
    if "pricing_version" not in st.session_state:
        st.session_state["pricing_version"] = 0
    if "markup_map" not in st.session_state:
        st.session_state["markup_map"] = {}
    if "main_section" not in st.session_state:
        st.session_state["main_section"] = "PRICING"  # PRICING / SHIPMENT / CUSTOMERS
    if "sub_page" not in st.session_state:
        st.session_state["sub_page"] = None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # WELCOME + MAIN SECTION TABS
    # ============================================================
    st.markdown(
        """
        <h1 style="margin-bottom:0.1rem;">Welcome, Nelson 👋</h1>
        <p style="color:#6b7280; margin-bottom:1rem;">Pudong Logistics Pricing Suite – chọn nhóm chức năng để bắt đầu.</p>
        """,
        unsafe_allow_html=True,
    )

    main_section = st.session_state["main_section"]

    with st.container():
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button(
                ("💰 PRICING (đang chọn)" if main_section == "PRICING" else "💰 PRICING"),
                use_container_width=True,
            ):
                st.session_state["main_section"] = "PRICING"
                st.session_state["sub_page"] = None
                safe_rerun()
        with col_b:
            if st.button(
                ("📦 SHIPMENT (đang chọn)" if main_section == "SHIPMENT" else "📦 SHIPMENT"),
                use_container_width=True,
            ):
                st.session_state["main_section"] = "SHIPMENT"
                st.session_state["sub_page"] = None
                safe_rerun()
        with col_c:
            if st.button(
                ("👤 CUSTOMERS (đang chọn)" if main_section == "CUSTOMERS" else "👤 CUSTOMERS"),
                use_container_width=True,
            ):
                st.session_state["main_section"] = "CUSTOMERS"
                st.session_state["sub_page"] = None
                safe_rerun()

    st.markdown("---")

    # ============================================================
    # RENDER HUB THEO NHÓM
    # ============================================================
    if main_section == "PRICING":
        render_pricing_hub()
    elif main_section == "SHIPMENT":
        render_shipment_hub()
    elif main_section == "CUSTOMERS":
        render_customers_hub()


if __name__ == "__main__":
    main()
