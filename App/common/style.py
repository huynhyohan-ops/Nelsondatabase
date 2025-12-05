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

    /* Hero header cho các trang chính */
    .page-hero {
        background: linear-gradient(120deg, #2563eb, #4f46e5);
        border-radius: 18px;
        padding: 22px 24px;
        color: #f8fafc;
        box-shadow: 0 16px 30px rgba(79, 70, 229, 0.2);
        margin-bottom: 1rem;
    }
    .page-hero__title {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .page-hero__desc {
        font-size: 0.95rem;
        opacity: 0.9;
    }
    .page-hero__badges {
        display: flex;
        gap: 8px;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }
    .badge-pill {
        background: rgba(255,255,255,0.15);
        color: #e0e7ff;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        border: 1px solid rgba(255,255,255,0.2);
    }

    /* Card hiện đại */
    .surface-card {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        padding: 18px;
    }
    .surface-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .surface-title {
        font-weight: 700;
        color: #0f172a;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .surface-sub {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }

    /* Grid cho các card chức năng */
    .action-card {
        background: linear-gradient(180deg, #ffffff, #f8fafc);
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 14px;
        height: 100%;
        box-shadow: 0 10px 18px rgba(15,23,42,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .action-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 26px rgba(37,99,235,0.12);
    }
    .action-card .info-card-title {color: #475569;}
    .action-card .info-card-value {font-size: 1.1rem;}
    .action-card .info-card-sub {margin-top: 0.25rem;}

    /* Layout utilities */
    .pill-note {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        background: #eef2ff;
        border-radius: 10px;
        color: #4338ca;
        font-size: 0.8rem;
    }
    .pill-note.green {background: #ecfdf3; color: #166534;}
    .pill-note.amber {background: #fffbeb; color: #92400e;}
    .pill-note.blue {background: #eff6ff; color: #1d4ed8;}

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
