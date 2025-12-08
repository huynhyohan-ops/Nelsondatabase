from theme_loader import load_theme
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
    
    # Lấy sub_page hiện tại
    sub_page = st.session_state.get("sub_page")

    # 🎨 Load theme phù hợp theo từng phần
    if sub_page == "SHIPMENT.Follow":
        load_theme("follow_shipment_dark")  # theme cho Follow Shipment
    elif sub_page == "SHIPMENT.Dashboard":
        load_theme("dark_themes")  # theme neon cho Dashboard
    else:
        # Mặc định hub dùng theme dashboard nhẹ hơn
        load_theme("dark_themes")

    # --- Giao diện chính ---
    st.markdown(
        "<div class='section-title'>Shipment center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Theo dõi lô hàng, kiểm tra KPI, xem tổng quan dashboard.</div>",
        unsafe_allow_html=True,
    )

    # --- Hai card chính ---
    if not sub_page:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Follow shipment</div>"
                "<div class='info-card-value'>Tracking</div>"
                "<div class='info-card-sub'>Theo dõi tiến độ lô hàng & cảnh báo.</div></div>",
                unsafe_allow_html=True,
            )
            if st.button("📦 Vào Follow Shipment", key="btn_ship_follow", use_container_width=True):
                st.session_state["sub_page"] = "SHIPMENT.Follow"
                safe_rerun()

        with c2:
            st.markdown(
                "<div class='info-card'><div class='info-card-title'>Dashboard</div>"
                "<div class='info-card-value'>KPI</div>"
                "<div class='info-card-sub'>Biểu đồ, báo cáo tổng hợp shipment.</div></div>",
                unsafe_allow_html=True,
            )
            if st.button("📊 Vào Dashboard", key="btn_ship_dashboard", use_container_width=True):
                st.session_state["sub_page"] = "SHIPMENT.Dashboard"
                safe_rerun()

    # --- Nếu người dùng đang trong sub-page ---
    if sub_page and sub_page.startswith("SHIPMENT."):
        st.markdown("---")
        if st.button("⬅️ Quay lại menu Shipment", key="btn_back_shipment"):
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
