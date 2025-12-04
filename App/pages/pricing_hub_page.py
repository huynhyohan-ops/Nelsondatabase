from menu import top_menu

import streamlit as st

from common.helpers import RAW_DIR, DATA_DIR, safe_rerun
from common.style import inject_global_css

from pages.pricing_upload_page import render_upload_and_normalize
from pages.pricing_quote_page import render_quote_page
from pages.pricing_schedules_page import render_schedules_page


def init_pricing_state():
    """Khởi tạo session_state & folder cho Pricing hub."""
    if "pricing_version" not in st.session_state:
        st.session_state["pricing_version"] = 0
    if "markup_map" not in st.session_state:
        st.session_state["markup_map"] = {}
    if "sub_page" not in st.session_state:
        st.session_state["sub_page"] = None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    inject_global_css()


def render_pricing_hub():
    """Trang hub Pricing (Upload & Normalize / Quote / Schedules)."""

    st.markdown(
        "<div class='section-title'>Pricing center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Quản lý bảng giá, tạo báo giá, xem lịch tàu.</div>",
        unsafe_allow_html=True,
    )

    # Lấy trạng thái sub_page hiện tại (PRICING.Upload / PRICING.Quote / PRICING.Schedules)
    sub_page = st.session_state.get("sub_page")

    # 3 cột card chức năng
    c1, c2, c3 = st.columns(3)

    # --- CARD 1: Upload & Normalize ---
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

    # --- CARD 2: Quote ---
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

    # --- CARD 3: Schedules ---
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

    # --- Phần render sub-page chi tiết ---
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


# Khi file này được gọi như 1 page, chỉ cần init + render hub
# Khi page này được gọi như 1 trang multi-page
init_pricing_state()
top_menu(active="pricing")     # ⬅️ menu ngang 3 mục
render_pricing_hub()
