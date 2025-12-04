import streamlit as st

def render_dashboard_page():
    """Dashboard demo."""
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
