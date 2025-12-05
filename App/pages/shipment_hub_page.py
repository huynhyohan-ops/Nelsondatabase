from menu import top_menu

import streamlit as st

from common.helpers import RAW_DIR, DATA_DIR, safe_rerun
from common.style import inject_global_css

from pages.shipment_follow_page import render_follow_shipment_page
from pages.shipment_dashboard_page import render_dashboard_page


def init_shipment_state():
    """Khởi tạo session_state & folder cho Shipment hub."""
    if "sub_page" not in st.session_state:
        st.session_state["sub_page"] = None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    inject_global_css()


def render_shipment_hub():
    """Trang hub Shipment (Follow shipment / Dashboard)."""

    st.markdown(
        """
        <div class='page-hero'>
            <div class='page-hero__title'>📦 Shipment center</div>
            <div class='page-hero__desc'>Theo dõi lô hàng, dashboard KPI và cảnh báo được tổ chức lại trực quan, giữ nguyên data pipeline.</div>
            <div class='page-hero__badges'>
                <span class='badge-pill'>Tracking</span>
                <span class='badge-pill'>KPI Dashboard</span>
                <span class='badge-pill'>Cảnh báo</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sub_page = st.session_state.get("sub_page")

    overview_cols = st.columns(3)
    with overview_cols[0]:
        st.metric("Khu vực", "Follow & Dashboard")
    with overview_cols[1]:
        st.metric("Đang xem", (sub_page or "Menu chính").replace("SHIPMENT.", ""))
    with overview_cols[2]:
        st.metric("Thư mục dữ liệu", "Sẵn sàng" if DATA_DIR.exists() else "Chưa có")

    st.markdown("<div class='surface-title'>Lối tắt</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='surface-sub'>Chọn luồng cần truy cập. Hệ thống tính toán, filter và biểu đồ giữ nguyên.</div>",
        unsafe_allow_html=True,
    )

    # 2 card chính của Shipment
    c1, c2 = st.columns(2)

    # --- CARD 1: Follow shipment ---
    with c1:
        st.markdown(
            "<div class='action-card'><div class='info-card-title'>Follow shipment</div>"
            "<div class='info-card-value'>Tracking</div>"
            "<div class='info-card-sub'>Theo dõi tiến độ lô hàng & cảnh báo.</div>"
            "<div class='pill-note blue'>Dùng lại bộ lọc hiện có</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("📦 Vào Follow Shipment", key="btn_ship_follow", use_container_width=True):
            st.session_state["sub_page"] = "SHIPMENT.Follow"
            safe_rerun()

    # --- CARD 2: Dashboard ---
    with c2:
        st.markdown(
            "<div class='action-card'><div class='info-card-title'>Dashboard</div>"
            "<div class='info-card-value'>KPI</div>"
            "<div class='info-card-sub'>Biểu đồ, báo cáo tổng hợp shipment.</div>"
            "<div class='pill-note green'>Plotly charts giữ nguyên</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("📊 Vào Dashboard", key="btn_ship_dashboard", use_container_width=True):
            st.session_state["sub_page"] = "SHIPMENT.Dashboard"
            safe_rerun()

    st.markdown("---")

    # --- Phần render sub-page ---
    if sub_page and sub_page.startswith("SHIPMENT."):
        st.markdown(
            "<div class='surface-title'>Chi tiết</div><div class='surface-sub'>Bố cục mới cho phần nội dung, giữ nguyên tính toán trong các hàm con.</div>",
            unsafe_allow_html=True,
        )
        if st.button("⬅️ Quay lại menu Shipment", key="btn_back_shipment", use_container_width=True):
            st.session_state["sub_page"] = None
            safe_rerun()

        if sub_page == "SHIPMENT.Follow":
            render_follow_shipment_page()
        elif sub_page == "SHIPMENT.Dashboard":
            render_dashboard_page()


# Khi page này được gọi như một trang multi-page
init_shipment_state()
top_menu(active="shipment")
render_shipment_hub()

