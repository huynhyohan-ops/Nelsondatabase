import streamlit as st

def render_schedules_page():
    """Schedules placeholder."""
    st.markdown(
        "<div class='section-title'>Schedules – Lịch tàu / lịch giao nhận</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Dùng để show lịch tàu theo carrier / tuyến, cut-off, ETD/ETA...</div>",
        unsafe_allow_html=True,
    )
    st.info("Tab này hiện để trống cho anh phát triển thêm sau.")
