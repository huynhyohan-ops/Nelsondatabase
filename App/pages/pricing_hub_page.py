import streamlit as st

from menu import top_menu

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
        """
        <div class='page-hero'>
            <div class='page-hero__title'>Pricing center</div>
            <div class='page-hero__desc'>Quản lý bảng giá, tạo báo giá nhanh và kiểm tra lịch tàu. Các thao tác vẫn dùng chung core logic hiện có.</div>
            <div class='page-hero__badges'>
                <span class='badge-pill'>Upload & Normalize</span>
                <span class='badge-pill'>Quote engine</span>
                <span class='badge-pill'>Schedules</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick snapshot cho tình trạng hiện tại
    snapshot_cols = st.columns(4)
    with snapshot_cols[0]:
        st.metric("Phiên bản pricing", st.session_state.get("pricing_version", 0))
    with snapshot_cols[1]:
        st.metric("Markup đã lưu", len(st.session_state.get("markup_map", {})))
    with snapshot_cols[2]:
        current_sub = st.session_state.get("sub_page") or "Menu chính"
        st.metric("Đang truy cập", current_sub.replace("PRICING.", ""))
    with snapshot_cols[3]:
        st.metric("Thư mục RAW", "Đã tạo" if RAW_DIR.exists() else "Chưa có")

    # Lấy trạng thái sub_page hiện tại (PRICING.Upload / PRICING.Quote / PRICING.Schedules)
    sub_page = st.session_state.get("sub_page")

    st.markdown("<div class='surface-title'>Workspace</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='surface-sub'>Chọn luồng công việc cần thao tác. Giao diện được làm mới, giữ nguyên cách tính và dữ liệu.</div>",
        unsafe_allow_html=True,
    )

    # 3 cột card chức năng
    c1, c2, c3 = st.columns(3)

    # --- CARD 1: Upload & Normalize ---
    with c1:
        st.markdown(
            "<div class='action-card'><div class='info-card-title'>Upload & Normalize</div>"
            "<div class='info-card-value'>RAW → Master</div>"
            "<div class='info-card-sub'>Upload file RAW & chuẩn hoá bảng giá.</div>"
            "<div class='pill-note blue'>Bảo toàn logic chuẩn hoá</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Vào Upload & Normalize", key="btn_pricing_upload", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Upload"
            safe_rerun()

    # --- CARD 2: Quote ---
    with c2:
        st.markdown(
            "<div class='action-card'><div class='info-card-title'>Quote</div>"
            "<div class='info-card-value'>Ocean Freight</div>"
            "<div class='info-card-sub'>Tạo báo giá nhanh từ Master Pricing.</div>"
            "<div class='pill-note green'>Dùng lại generate_quote</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Vào Quote", key="btn_pricing_quote", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Quote"
            safe_rerun()

    # --- CARD 3: Schedules ---
    with c3:
        st.markdown(
            "<div class='action-card'><div class='info-card-title'>Schedules</div>"
            "<div class='info-card-value'>Lịch tàu</div>"
            "<div class='info-card-sub'>Cut-off, ETD/ETA theo tuyến & carrier.</div>"
            "<div class='pill-note amber'>Tự động từ master</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Vào Schedules", key="btn_pricing_schedules", use_container_width=True):
            st.session_state["sub_page"] = "PRICING.Schedules"
            safe_rerun()

    st.markdown("---")

    # --- Phần render sub-page chi tiết ---
    sub_page = st.session_state.get("sub_page")
    if sub_page and sub_page.startswith("PRICING."):
        st.markdown(
            "<div class='surface-title'>Chi tiết</div><div class='surface-sub'>Khu vực làm việc giữ nguyên engine & data, chỉ đổi bố cục hiển thị.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Quay lại menu Pricing", key="btn_back_pricing", use_container_width=True):
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
top_menu(active="pricing")     # menu ngang 3 mục
render_pricing_hub()
