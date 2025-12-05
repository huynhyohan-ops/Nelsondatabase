import streamlit as st

def render_crm_page():
    """CRM placeholder."""
    st.markdown(
        """
        <div class='page-hero'>
            <div class='page-hero__title'>👤 CRM workspace</div>
            <div class='page-hero__desc'>Khung giao diện mới cho quản lý khách, pipeline và lịch sử báo giá. Logic kết nối dữ liệu sẽ được tái sử dụng khi bổ sung.</div>
            <div class='page-hero__badges'>
                <span class='badge-pill'>Sales pipeline</span>
                <span class='badge-pill'>Customer profile</span>
                <span class='badge-pill'>Activities</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(4)
    metrics = [
        ("Khách hoạt động", "—", "Đợi đồng bộ"),
        ("Cơ hội mở", "—", "Giữ logic tính riêng"),
        ("Tỷ lệ thắng", "—", "Sẽ lấy từ dữ liệu"),
        ("Báo giá gần nhất", "—", "Dữ liệu sẽ nối sau"),
    ]
    for idx, (label, value, note) in enumerate(metrics):
        with stat_cols[idx]:
            st.metric(label, value, help=note)

    st.markdown("<div class='surface-title'>Tổng quan</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='surface-sub'>Bố cục bảng & timeline được sắp xếp để dễ bổ sung nguồn dữ liệu trong tương lai.</div>",
        unsafe_allow_html=True,
    )

    overview_cols = st.columns([1.2, 1])
    with overview_cols[0]:
        st.markdown("**Danh sách khách (placeholder)**")
        st.dataframe(
            [{"Customer": "Demo", "Owner": "—", "Stage": "—", "Updated": "—"}],
            use_container_width=True,
        )

    with overview_cols[1]:
        st.markdown("**Ghi chú nhanh**")
        st.text_area("Thêm note cho khách", placeholder="Nhập nội dung...", height=140)
        st.selectbox("Trạng thái liên hệ", ["Chưa liên hệ", "Đang chăm sóc", "Closed"], index=0)
        st.date_input("Hẹn follow-up")
        st.button("Lưu nháp giao diện", use_container_width=True)

    st.markdown("---")
    st.info("Hiện tại chỉ làm mới layout. Khi nối dữ liệu thật, các phép tính và pipeline sẽ được tái sử dụng để giữ tính nhất quán.")
