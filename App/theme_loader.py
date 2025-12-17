import streamlit as st
import pathlib


def load_theme(theme_name: str):
    """
    Load CSS theme by filename from /themes/ folder
    + theme_name: tên file CSS (bỏ đuôi .css)
    """

    # Đường dẫn tuyệt đối đến thư mục themes/
    base_path = pathlib.Path(__file__).parent
    css_path = base_path / "themes" / f"{theme_name}.css"

    # --- Lớp nền cơ bản (gradient xanh đen dịu sáng) ---
    base_reset = """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: radial-gradient(circle at 20% 30%, #0a1a2f 0%, #0d1220 60%, #101827 100%) !important;
        color: #E5E7EB !important;
        font-family: 'Inter', 'IBM Plex Sans', sans-serif !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0a101f 100%) !important;
        color: #E5E7EB !important;
        border-right: 1px solid rgba(59,130,246,0.15);
        box-shadow: 0 0 20px rgba(0, 200, 255, 0.05);
    }

    /* Văn bản mặc định */
    .stMarkdown, .stText, .stWrite, p, label, h1, h2, h3, h4, h5, h6 {
        color: #E2E8F0 !important;
    }

    /* Fix các input và select box để đồng bộ màu */
    input, select, textarea {
        background-color: rgba(17,24,39,0.8) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(59,130,246,0.25) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
    }

    input:focus, select:focus, textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 8px rgba(59,130,246,0.5);
        outline: none !important;
    }

    /* Streamlit buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #00FFFF 0%, #3B82F6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        box-shadow: 0 0 20px rgba(0, 200, 255, 0.25) !important;
        transition: all 0.3s ease-in-out !important;
    }

    div.stButton > button:hover {
        box-shadow: 0 0 35px rgba(0, 200, 255, 0.55) !important;
        transform: translateY(-1px);
    }

    /* Card hiển thị dữ liệu */
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
        color: #A5F3FC !important;
        text-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
    }

    /* Bảng dữ liệu */
    table {
        background-color: rgba(15,23,42,0.8) !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }

    /* Các container card / khung tổng */
    div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Tăng hiệu ứng phát sáng tổng thể */
    * {
        text-shadow: 0 0 2px rgba(59,130,246,0.25);
    }
    </style>
    """

    # --- Load file theme cụ thể (nếu tồn tại) ---
    custom_css = ""
    if css_path.exists():
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
                # Quan trọng: render HTML thực (không bị in text)
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
                st.success(f"✅ Loaded theme: {theme_name}.css", icon="🎨")
        except Exception as e:
            st.error(f"❌ Lỗi khi load theme '{theme_name}.css': {e}")
    else:
        st.warning(f"⚠️ Theme '{theme_name}.css' not found in /themes/")

    # --- Áp dụng lớp nền cơ bản ---
    st.markdown(base_reset, unsafe_allow_html=True)
