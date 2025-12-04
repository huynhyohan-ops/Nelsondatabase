from menu import top_menu

import streamlit as st

from common.helpers import RAW_DIR, DATA_DIR, safe_rerun
from common.style import inject_global_css

from pages.customers_crm_page import render_crm_page


def init_customers_state():
    """Khởi tạo session_state & folder cho Customers hub."""
    if "sub_page" not in st.session_state:
        st.session_state["sub_page"] = "CUSTOMERS.CRM"

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    inject_global_css()


def render_customers_hub():
    """Trang hub Customers (CRM)."""

    st.markdown(
        "<div class='section-title'>Customer center</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Quản lý khách hàng & CRM.</div>",
        unsafe_allow_html=True,
    )

    # Hiện tại Customers chỉ có 1 mục CRM
    st.markdown("---")
    render_crm_page()


# Khi page này được Streamlit gọi
init_customers_state()
top_menu(active="customers")
render_customers_hub()
