# App/App.py (hoặc app.py)
import streamlit as st

pricing_page = st.Page(
    "pages/pricing_hub_page.py",
    title="Pricing",
    icon="💰",
    default=True,
)

shipment_page = st.Page(
    "pages/shipment_hub_page.py",
    title="Shipment",
    icon="📦",
)

customers_page = st.Page(
    "pages/customers_hub_page.py",
    title="Customers",
    icon="👤",
)

pages = [pricing_page, shipment_page, customers_page]

# Ẩn navigation built-in, vì mình dùng menu riêng
pg = st.navigation(pages=pages, position="hidden")

st.set_page_config(
    page_title="Pudong Pricing – Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pg.run()
