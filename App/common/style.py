import streamlit as st

def inject_global_css():
    st.markdown(
        """
    <style>
    :root {
        --pd-sidebar-bg: #F9FAFB;
        --pd-tab-bg: #FFFFFF;
        --pd-tab-active-bg: #E0F2FE;
        --pd-text: #374151;
        --pd-title: #1F2937;
        --pd-icon-normal: #60A5FA;
        --pd-icon-active: #3B82F6;
    }

    [data-testid="stAppViewContainer"] {
        background: #f3f4f6;
        color: var(--pd-text);
    }
    [data-testid="stHeader"] {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(6px);
        border-bottom: 1px solid #e5e7eb;
    }
    [data-testid="stToolbar"] {display: none;}

    /* Ẩn sidebar hoàn toàn */
    section[data-testid="stSidebar"] {
        display: none;
    }

    .info-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 18px;
        color: #111827;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 18px rgba(15,23,42,0.06);
        margin-bottom: 0.75rem;
    }
    .info-card-title {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.25rem;
    }
    .info-card-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
    }
    .info-card-sub {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 0.1rem;
    }

    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0.5rem;
        margin-bottom: 0.2rem;
    }
    .section-sub {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 0.8rem;
    }

    label {
        color: #374151 !important;
        font-weight: 500;
    }

    .stDataFrame {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }

    details summary {
        font-weight: 600;
    }

    .top-main-tabs {
        margin-top: 0.5rem;
        margin-bottom: 0.6rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
