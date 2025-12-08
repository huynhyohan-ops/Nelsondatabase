import streamlit as st
from pathlib import Path

from common.helpers import DATA_DIR, RAW_DIR, MASTER_FILE, safe_rerun
from normalize_pricing_work import normalize_all_from_streamlit


def render_upload_and_normalize():
    """Upload & Normalize bảng giá RAW → Master."""
    st.markdown(
        "<div class='section-title'>Upload & Normalize bảng giá</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Upload file RAW (.xlsx), hệ thống sẽ tự động chuẩn hoá sang Master_FullPricing.xlsx trong thư mục Data.</div>",
        unsafe_allow_html=True,
    )

    col_u1, col_u2 = st.columns([2, 1])

    with col_u1:
        uploaded_raw = st.file_uploader(
            "Upload file giá RAW (.xlsx)",
            type=["xlsx"],
            accept_multiple_files=True,
            help="Anh có thể chọn 1 hoặc nhiều file RAW (FAK, ONE_SPECIAL, SCFI...)",
        )

    with col_u2:
        st.markdown(
            f"<div class='info-card'><div class='info-card-title'>Master Pricing version</div>"
            f"<div class='info-card-value'>{st.session_state['pricing_version']}</div>"
            f"<div class='info-card-sub'>{MASTER_FILE.name}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    if st.button("🧹 Normalize RAW → Master", use_container_width=True):
        if not uploaded_raw:
            st.warning("Anh cần upload ít nhất 1 file RAW trước.")
        else:
            RAW_DIR.mkdir(parents=True, exist_ok=True)

            for f in uploaded_raw:
                out_path = RAW_DIR / f.name
                with open(out_path, "wb") as g:
                    g.write(f.getbuffer())

            try:
                with st.spinner(
                    "Đang Normalize bảng giá RAW → Master_FullPricing.xlsx ..."
                ):
                    normalize_all_from_streamlit(
                        raw_dir_override=RAW_DIR,
                        data_dir_override=DATA_DIR,
                    )
                st.session_state["pricing_version"] += 1
                st.success("✅ Đã Normalize & cập nhật Master Pricing thành công.")

                safe_rerun()
            except Exception as e:
                st.error(f"Lỗi khi Normalize: {e}")

    st.markdown("---")
    st.caption(
        "Sau khi Normalize xong, chuyển sang chức năng **Quote** trong nhóm Pricing để tạo báo giá từ Master Pricing mới."
    )
