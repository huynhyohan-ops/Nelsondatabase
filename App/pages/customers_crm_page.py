import streamlit as st

def render_crm_page():
    """CRM placeholder."""
    st.markdown(
        "<div class='section-title'>CRM – Khách hàng & Sales pipeline</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Sau này anh có thể quản lý danh sách khách, pipeline, lịch sử báo giá tại đây.</div>",
        unsafe_allow_html=True,
    )
    st.info("Hiện tại chỉ là khung demo. Sau này anh có thể nối với Excel / DB để quản lý khách.")
