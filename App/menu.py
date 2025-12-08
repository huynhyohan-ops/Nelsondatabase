# App/menu.py
import streamlit as st

def top_menu(active: str):
    """
    Thanh menu ngang cấp 1 cho toàn bộ app.
    active: 'pricing' | 'shipment' | 'customers'
    """

    cols = st.columns(3)

    # Mỗi cột là một "tab" lớn
    with cols[0]:
        st.page_link(
            "pages/pricing_hub_page.py",
            label="💰 Pricing" if active == "pricing" else "Pricing",
        )

    with cols[1]:
        st.page_link(
            "pages/shipment_hub_page.py",
            label="📦 Shipment" if active == "shipment" else "Shipment",
        )

    with cols[2]:
        st.page_link(
            "pages/customers_hub_page.py",
            label="👤 Customers" if active == "customers" else "Customers",
        )

    # Đường gạch ngăn menu với nội dung
    st.markdown("---")
