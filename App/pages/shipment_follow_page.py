import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from common.helpers import DATA_DIR

# ===================== CONFIG =====================
SHIPMENT_FILE = DATA_DIR / "Shipments.xlsx"

CONTAINER_TYPES = ["20GP", "40HQ", "20RF", "40RF", "45HQ", "40NOR"]

CONTAINER_TEU_MAP = {
    "20GP": 1,
    "20RF": 1,
    "40HQ": 2,
    "40RF": 2,
    "45HQ": 2,
    "40NOR": 2,
}

STATUS_OPTIONS = [
    "Submit",
    "Keep Space",
    "Confirmed",
    "Send SI",
    "Hbl Issue",
    "In Transit",
    "Delivered",
    "Cancelled",
]

CARRIER_OPTIONS = ["ONE", "CMA", "ZIM", "YML", "HPL", "MSK", "COSCO", "MSC", "WHL"]

STATUS_COLOR_MAP = {
    "Submit": "#E0F7FA",
    "Keep Space": "#BBDEFB",
    "Confirmed": "#90CAF9",
    "Send SI": "#FFE0B2",
    "Hbl Issue": "#FFCC80",
    "In Transit": "#FFF59D",
    "Delivered": "#C8E6C9",
    "Cancelled": "#EEEEEE",
}

BASE_COLUMNS = [
    "Customer",
    "Routing",
    "BKG NO",
    "HBL NO",
    "ETD",
    "ETA",
    "Container Type",
    "Quantity",
    "Volume",
    "Status",
    "Selling Rate",
    "Buying Rate",
    "Profit",
    "SI",
    "CY",
    "Carrier",
    "HDL FEE carrier",
]


# ===================== MONTH RANGE =====================
def get_month_key_range():
    """Generate months from 11/2025 to 11/2026"""
    months = []
    year = 2025
    month = 11
    while True:
        months.append(f"{year}-{month:02d}")
        if year == 2026 and month == 11:
            break
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


# ===================== LOAD FUNCTIONS =====================
def load_month_df(month_key: str) -> pd.DataFrame:
    """Load a sheet or create blank"""
    if SHIPMENT_FILE.exists():
        try:
            sheets = pd.read_excel(SHIPMENT_FILE, sheet_name=None)
            if month_key in sheets:
                df = sheets[month_key]

                for c in BASE_COLUMNS:
                    if c not in df.columns:
                        df[c] = None

                df = df[BASE_COLUMNS + [c for c in df.columns if c not in BASE_COLUMNS]]
                return df
        except Exception as e:
            st.error(f"Lỗi đọc file shipments: {e}")

    return pd.DataFrame(columns=BASE_COLUMNS)


def save_month_df(month_key: str, df: pd.DataFrame):
    """Save a sheet back to the workbook"""
    SHIPMENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sheets = {}
    if SHIPMENT_FILE.exists():
        try:
            sheets = pd.read_excel(SHIPMENT_FILE, sheet_name=None)
        except:
            sheets = {}

    sheets[month_key] = df

    with pd.ExcelWriter(SHIPMENT_FILE, engine="openpyxl") as writer:
        for name, sdf in sheets.items():
            sdf.to_excel(writer, sheet_name=name, index=False)


# ===================== CALCULATIONS =====================
def format_short_date(dt_string):
    """Convert YYYY-MM-DD -> 14-MAR."""
    try:
        dt = pd.to_datetime(dt_string, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.strftime("%d-%b").upper()
    except:
        return ""


def compute_volume_profit(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Selling Rate"] = pd.to_numeric(df["Selling Rate"], errors="coerce").fillna(0)
    df["Buying Rate"] = pd.to_numeric(df["Buying Rate"], errors="coerce").fillna(0)

    # Volume
    df["Volume"] = df.apply(
        lambda r: CONTAINER_TEU_MAP.get(str(r["Container Type"]).strip(), 0) * r["Quantity"],
        axis=1,
    )

    # Profit
    df["Profit"] = (df["Selling Rate"] - df["Buying Rate"]) * df["Quantity"]

    # Format ETD / ETA
    df["ETD"] = df["ETD"].apply(format_short_date)
    df["ETA"] = df["ETA"].apply(format_short_date)

    return df


def find_alerts(df, column_name, hours_before=48):
    """Warnings for SI or CY within 48 hours"""
    now = datetime.now()
    horizon = now + timedelta(hours=hours_before)

    parsed = pd.to_datetime(df[column_name], errors="coerce", dayfirst=True)
    mask = (parsed.notna()) & (parsed >= now) & (parsed <= horizon)

    alert_df = df[mask].copy()
    alert_df[column_name + "_parsed"] = parsed[mask]
    return alert_df


# ===================== COLORING =====================
def color_rows(row):
    status = row["Status"]
    return ["background-color: %s" % STATUS_COLOR_MAP.get(status, "white")] * len(row)


# ===================== MAIN UI =====================
def render_follow_shipment_page():

    st.markdown("<div class='section-title'>Follow Shipment – Monthly Tracking</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Quản lý lô hàng theo tháng (11/2025 → 11/2026)</div>", unsafe_allow_html=True)

    # Select month
    month_keys = get_month_key_range()
    today_key = f"{date.today().year}-{date.today().month:02d}"

    default_index = month_keys.index(today_key) if today_key in month_keys else 0

    month_choice = st.selectbox("Chọn tháng", month_keys, index=default_index)

    # Load
    df = load_month_df(month_choice)
    df = compute_volume_profit(df)

    # Filters
    st.markdown("### 🔍 Bộ lọc")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        carrier_filter = st.selectbox("Lọc theo Carrier", ["All"] + CARRIER_OPTIONS)

    with col_f2:
        status_filter = st.selectbox("Lọc theo Status", ["All"] + STATUS_OPTIONS)

    df_filtered = df.copy()

    if carrier_filter != "All":
        df_filtered = df_filtered[df_filtered["Carrier"] == carrier_filter]

    if status_filter != "All":
        df_filtered = df_filtered[df_filtered["Status"] == status_filter]

    # Editor config
    column_config = {
        "ETD": st.column_config.DateColumn("ETD (Date)", format="DD-MMM-YYYY"),
        "ETA": st.column_config.DateColumn("ETA (Date)", format="DD-MMM-YYYY"),
        "Container Type": st.column_config.SelectboxColumn("Container Type", options=CONTAINER_TYPES),
        "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
        "Carrier": st.column_config.SelectboxColumn("Carrier", options=CARRIER_OPTIONS),
        "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
        "Selling Rate": st.column_config.NumberColumn("Selling Rate (USD)", format="%.2f"),
        "Buying Rate": st.column_config.NumberColumn("Buying Rate (USD)", format="%.2f"),
        "Profit": st.column_config.NumberColumn("Profit", disabled=True, format="%.2f"),
        "Volume": st.column_config.NumberColumn("Volume (TEU)", disabled=True, format="%.1f"),
        "HDL FEE carrier": st.column_config.NumberColumn("HDL FEE carrier (USD)", format="%.2f"),
    }

    st.markdown("### 📋 Bảng Shipment")
    edited = st.data_editor(
        df_filtered,
        use_container_width=True,
        num_rows="dynamic",
        column_config=column_config,
        key=f"editor_{month_choice}",
    )

    edited = compute_volume_profit(edited)

    # Total calculations
    total_teu = edited["Volume"].sum()
    total_profit = edited["Profit"].sum()

    st.markdown(f"### 📊 Kết quả tháng {month_choice}")
    st.metric("Tổng TEU", f"{total_teu:.1f}")
    st.metric("Tổng Profit", f"{total_profit:,.2f} USD")

    # Save
    if st.button("💾 Lưu"):
        # merge filtered rows back into original full df
        df.update(edited)
        save_month_df(month_choice, df)
        st.success("Đã lưu dữ liệu!")

    # Alerts: SI + CY
    st.markdown("---")
    st.markdown("### ⏰ Cảnh báo SI / CY trong 48 giờ")

    si_alerts = find_alerts(df, "SI")
    cy_alerts = find_alerts(df, "CY")

    if si_alerts.empty and cy_alerts.empty:
        st.success("Không có cảnh báo 48h")
    else:
        if not si_alerts.empty:
            st.error("🚨 SI trong 48 giờ:")
            st.dataframe(si_alerts)

        if not cy_alerts.empty:
            st.warning("⚠ CY trong 48 giờ:")
            st.dataframe(cy_alerts)
