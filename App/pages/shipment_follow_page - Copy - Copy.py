import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path

from common.helpers import DATA_DIR  # dùng path Data chung

import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CẤU HÌNH & HẰNG SỐ
# ============================================================

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

# KPI THÁNG
KPI_VOLUME = 80.0      # TEU / month
KPI_PROFIT = 15500.0   # USD / month


# ============================================================
# HÀM THÁNG 11/2025 -> 11/2026
# ============================================================

def get_month_key_range():
    """Tạo list tháng từ 11/2025 đến 11/2026 dạng YYYY-MM."""
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


# ============================================================
# LOAD / SAVE
# ============================================================

def _empty_month_df() -> pd.DataFrame:
    """Tạo DataFrame trống với đúng dtype (ETD/ETA là datetime)."""
    data = {}
    for c in BASE_COLUMNS:
        if c in ["ETD", "ETA"]:
            data[c] = pd.Series(dtype="datetime64[ns]")
        else:
            data[c] = pd.Series(dtype="object")
    return pd.DataFrame(data)


def load_month_df(month_key: str) -> pd.DataFrame:
    """
    Load data 1 tháng từ Shipments.xlsx.
    Nếu chưa có sheet, trả về DataFrame trống với cấu trúc chuẩn.
    """
    if SHIPMENT_FILE.exists():
        try:
            sheets = pd.read_excel(SHIPMENT_FILE, sheet_name=None)
            if month_key in sheets:
                df = sheets[month_key]

                # đảm bảo đủ cột
                for c in BASE_COLUMNS:
                    if c not in df.columns:
                        df[c] = None

                # ETD/ETA parse sang datetime để dùng DateColumn
                for col in ["ETD", "ETA"]:
                    df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

                df = df[BASE_COLUMNS + [c for c in df.columns if c not in BASE_COLUMNS]]
                return df
        except Exception as e:
            st.error(f"Lỗi đọc file Shipments.xlsx: {e}")

    return _empty_month_df()


def save_month_df(month_key: str, df: pd.DataFrame):
    """
    Lưu DataFrame của 1 tháng vào file Shipments.xlsx.
    Giữ nguyên các sheet tháng khác.
    """
    SHIPMENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sheets = {}
    if SHIPMENT_FILE.exists():
        try:
            sheets = pd.read_excel(SHIPMENT_FILE, sheet_name=None)
        except Exception as e:
            st.error(f"Lỗi đọc file Shipments.xlsx khi lưu: {e}")
            sheets = {}

    sheets[month_key] = df

    with pd.ExcelWriter(SHIPMENT_FILE, engine="openpyxl") as writer:
        for name, sdf in sheets.items():
            sdf.to_excel(writer, sheet_name=name, index=False)


# ============================================================
# TÍNH TOÁN VOLUME & PROFIT
# ============================================================

def compute_volume_profit(df: pd.DataFrame) -> pd.DataFrame:
    """Tính Volume (TEU) & Profit từ Container Type + Quantity + Selling/Buying."""
    df = df.copy()

    for c in ["Container Type", "Quantity", "Selling Rate", "Buying Rate"]:
        if c not in df.columns:
            df[c] = None

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Selling Rate"] = pd.to_numeric(df["Selling Rate"], errors="coerce").fillna(0.0)
    df["Buying Rate"] = pd.to_numeric(df["Buying Rate"], errors="coerce").fillna(0.0)

    # Volume (TEU) từng dòng
    volumes = []
    for _, row in df.iterrows():
        ctype = str(row.get("Container Type") or "").strip().upper()
        qty = row["Quantity"]
        teu_per_cont = CONTAINER_TEU_MAP.get(ctype, 0.0)
        volumes.append(qty * teu_per_cont)
    df["Volume"] = volumes

    # Profit từng dòng
    df["Profit"] = (df["Selling Rate"] - df["Buying Rate"]) * df["Quantity"]

    return df


# ============================================================
# ALERT SI / CY
# ============================================================

def find_alerts(df: pd.DataFrame, column_name: str, hours_before: int = 48) -> pd.DataFrame:
    """
    Lọc những lô có SI/CY trong vòng `hours_before` tới (so với thời điểm hiện tại).
    Cột SI/CY lưu dạng text, cố gắng parse thành datetime.
    """
    if column_name not in df.columns or df.empty:
        return pd.DataFrame(columns=df.columns)

    now = datetime.now()
    horizon = now + timedelta(hours=hours_before)

    parsed = pd.to_datetime(df[column_name], errors="coerce", dayfirst=True)
    mask = (parsed.notna()) & (parsed >= now) & (parsed <= horizon)

    alert_df = df[mask].copy()
    if not alert_df.empty:
        alert_df[column_name + "_parsed"] = parsed[mask]
    return alert_df


# ============================================================
# UI CHÍNH
# ============================================================

def render_follow_shipment_page():
    """Trang Follow Shipment – theo dõi lô hàng theo tháng."""
    st.markdown(
        "<div class='section-title'>Follow Shipment – Theo dõi lô hàng</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-sub'>Quản lý trạng thái các lô hàng theo từng tháng (11/2025 → 11/2026). Mỗi tháng là 1 sheet trong Shipments.xlsx.</div>",
        unsafe_allow_html=True,
    )

    # ---------- Chọn tháng ----------
    month_keys = get_month_key_range()
    today = date.today()
    current_key = f"{today.year}-{today.month:02d}"
    default_index = month_keys.index(current_key) if current_key in month_keys else 0

    month_choice = st.selectbox(
        "Chọn tháng cần xem / cập nhật",
        options=month_keys,
        index=default_index,
        help="Format: YYYY-MM. Mỗi tháng là 1 sheet riêng trong file Shipments.xlsx",
    )
    st.caption(f"📁 File lưu trữ: `{SHIPMENT_FILE}` – Sheet: `{month_choice}`")

    # ---------- Load + tính toán per row ----------
    df_month = load_month_df(month_choice)
    df_month = compute_volume_profit(df_month)

    # ---------- Bộ lọc Carrier / Status ----------
    st.markdown("### 🔍 Bộ lọc")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        carrier_filter = st.selectbox("Lọc theo Carrier", ["All"] + CARRIER_OPTIONS)
    with col_f2:
        status_filter = st.selectbox("Lọc theo Status", ["All"] + STATUS_OPTIONS)

    df_filtered = df_month.copy()
    if carrier_filter != "All":
        df_filtered = df_filtered[df_filtered["Carrier"] == carrier_filter]
    if status_filter != "All":
        df_filtered = df_filtered[df_filtered["Status"] == status_filter]

    # Recompute để chắc chắn Volume/Profit đúng trên view đã lọc
    df_filtered = compute_volume_profit(df_filtered)

    # ---------- Cấu hình data_editor ----------
    column_config = {
        "ETD": st.column_config.DateColumn(
            "ETD (Date)",
            format="DD-MMM-YYYY",
        ),
        "ETA": st.column_config.DateColumn(
            "ETA (Date)",
            format="DD-MMM-YYYY",
        ),
        "Container Type": st.column_config.SelectboxColumn(
            "Container Type",
            options=CONTAINER_TYPES,
            help="Chọn loại cont. Volume sẽ được tính tự động theo TEU.",
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=STATUS_OPTIONS,
        ),
        "Carrier": st.column_config.SelectboxColumn(
            "Carrier",
            options=CARRIER_OPTIONS,
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            help="Số lượng cont",
            min_value=0,
            step=1,
        ),
        "Volume": st.column_config.NumberColumn(
            "Volume (TEU)",
            help="Tự động tính: Quantity x TEU theo Container Type",
            disabled=True,
            format="%.1f",
        ),
        "Selling Rate": st.column_config.NumberColumn(
            "Selling Rate (USD/cont)",
            format="%.2f",
        ),
        "Buying Rate": st.column_config.NumberColumn(
            "Buying Rate (USD/cont)",
            format="%.2f",
        ),
        "Profit": st.column_config.NumberColumn(
            "Profit (USD)",
            help="Tự động tính: (Selling - Buying) x Quantity",
            disabled=True,
            format="%.2f",
        ),
        "HDL FEE carrier": st.column_config.NumberColumn(
            "HDL FEE carrier (USD)",
            format="%.2f",
        ),
    }

    st.markdown("### 📋 Bảng shipment của tháng đã chọn")

    edited = st.data_editor(
        df_filtered,
        use_container_width=True,
        num_rows="dynamic",
        key=f"shipment_editor_{month_choice}",
        column_config=column_config,
    )

    # Tính lại Volume + Profit cho DataFrame đã edit
    edited = compute_volume_profit(edited)

    # ---------- TÍNH TỔNG (KHÔNG TÍNH KEEP SPACE + CANCELLED) ----------
    if "Status" in edited.columns:
        status_clean = edited["Status"].fillna("").astype(str).str.strip()
        mask_real = ~status_clean.isin(["Keep Space", "Cancelled"])
    else:
        mask_real = pd.Series(True, index=edited.index)

    total_teu = edited.loc[mask_real, "Volume"].sum() if "Volume" in edited.columns else 0.0
    total_profit = edited.loc[mask_real, "Profit"].sum() if "Profit" in edited.columns else 0.0

    # ---------- KPI PROGRESS BAR ----------
    st.markdown("### KPI MONTH")

    vol_pct = total_teu / KPI_VOLUME if KPI_VOLUME > 0 else 0
    prof_pct = total_profit / KPI_PROFIT if KPI_PROFIT > 0 else 0

    vol_pct_clamped = max(0.0, min(vol_pct, 1.0))
    prof_pct_clamped = max(0.0, min(prof_pct, 1.0))

    st.write(f"Volume: {total_teu:.1f} / {KPI_VOLUME:.1f} TEU ({vol_pct*100:,.1f}%)")
    st.progress(vol_pct_clamped, text=f"Volume: {vol_pct*100:,.1f}% KPI")

    st.write(f"Profit: {total_profit:,.2f} / {KPI_PROFIT:,.2f} USD ({prof_pct*100:,.1f}%)")
    st.progress(prof_pct_clamped, text=f"Profit: {prof_pct*100:,.1f}% KPI")

    # ---------- DỮ LIỆU THỰC (đã bỏ Keep Space & Cancelled, dùng cho Customer & Week) ----------
    df_real = edited.loc[mask_real].copy()

    st.markdown("---")

    # ============================================================
    # 3 BIỂU ĐỒ: DONUT STATUS / TREEMAP CUSTOMER / HEATMAP TUẦN
    # ============================================================

    st.markdown("### 📊 Tổng quan Shipment tháng")

    col_status, col_customer, col_week = st.columns(3)

    # ---------- 1. PIE/DONUT – Shipment Status (LẤY TOÀN BỘ, kể cả Cancel / Keep Space) ----------
    df_status = edited.copy()
    if not df_status.empty:
        df_status["Status_clean"] = df_status["Status"].fillna("Unknown")

        status_summary = (
            df_status.groupby("Status_clean", dropna=False)
            .agg(
                Shipments=("Customer", "count"),
                Volume_TEUS=("Volume", "sum"),
                Profit_USD=("Profit", "sum"),
            )
            .reset_index()
        )

        fig_status = px.pie(
            status_summary,
            values="Shipments",       # số lô hàng theo từng Status
            names="Status_clean",
            hole=0.4,
        )
        fig_status.update_traces(textposition="inside", textinfo="percent+label")
        fig_status.update_layout(
            title="Shipment Status",
            margin=dict(t=40, b=20, l=0, r=0),
            showlegend=False,
        )
    else:
        fig_status = None
        status_summary = None

    # ---------- 2. TREEMAP – Volume & Profit theo Customer (dùng df_real) ----------
    if not df_real.empty:
        df_real["Customer_clean"] = df_real["Customer"].fillna("Unknown")

        customer_summary = (
            df_real.groupby("Customer_clean", dropna=False)
            .agg(
                Shipments=("Customer", "count"),
                Volume_TEUS=("Volume", "sum"),
                Profit_USD=("Profit", "sum"),
            )
            .reset_index()
        )

        fig_customer = px.treemap(
            customer_summary,
            path=["Customer_clean"],
            values="Volume_TEUS",
            color="Profit_USD",
            color_continuous_scale="Blues",
            hover_data={
                "Shipments": True,
                "Volume_TEUS": ":.1f",
                "Profit_USD": ":,.0f",
            },
        )
        fig_customer.update_layout(
            title="Volume (TEU) & Profit theo Customer",
            margin=dict(t=40, b=20, l=0, r=0),
        )
    else:
        fig_customer = None
        customer_summary = None

    # ---------- 3. HEATMAP – Volume & Profit theo tuần ISO (dùng df_real) ----------
    df_week = None
    fig_week = None
    week_summary = None

    if not df_real.empty and "ETD" in df_real.columns:
        df_week = df_real.copy()
        df_week["ETD_parsed"] = pd.to_datetime(df_week["ETD"], errors="coerce")
        df_week = df_week[df_week["ETD_parsed"].notna()]

        if not df_week.empty:
            iso_info = df_week["ETD_parsed"].dt.isocalendar()
            df_week["ISO_Week"] = iso_info.week
            df_week["ISO_Year"] = iso_info.year

            week_summary = (
                df_week.groupby(["ISO_Year", "ISO_Week"])
                .agg(
                    Shipments=("Customer", "count"),
                    Volume_TEUS=("Volume", "sum"),
                    Profit_USD=("Profit", "sum"),
                )
                .reset_index()
                .sort_values(["ISO_Year", "ISO_Week"])
            )

            week_summary["WeekLabel"] = (
                week_summary["ISO_Year"].astype(str)
                + "-W"
                + week_summary["ISO_Week"].astype(str).str.zfill(2)
            )

            # tạo heatmap 2 dòng: Volume & Profit
            melt_df = week_summary.melt(
                id_vars=["WeekLabel"],
                value_vars=["Volume_TEUS", "Profit_USD"],
                var_name="Metric",
                value_name="Value",
            )
            metric_map = {
                "Volume_TEUS": "Volume (TEU)",
                "Profit_USD": "Profit (USD)",
            }
            melt_df["Metric"] = melt_df["Metric"].map(metric_map)

            fig_week = px.density_heatmap(
                melt_df,
                x="WeekLabel",
                y="Metric",
                z="Value",
                color_continuous_scale="Viridis",
                labels={"WeekLabel": "ISO Week", "Metric": "", "Value": ""},
            )
            fig_week.update_layout(
                title="Volume (TEU) & Profit theo tuần ISO",
                margin=dict(t=40, b=40, l=0, r=0),
            )

    # ---------- VẼ 3 CHART TRÊN CÙNG 1 HÀNG ----------
    with col_status:
        st.markdown("#### 📦 Shipment Status")
        if fig_status is not None:
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu Status để hiển thị.")

    with col_customer:
        st.markdown("#### 📈 Volume & Profit theo Customer")
        if fig_customer is not None:
            st.plotly_chart(fig_customer, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu Customer (sau khi bỏ Keep Space & Cancelled).")

    with col_week:
        st.markdown("#### 📅 Volume & Profit theo tuần ISO")
        if fig_week is not None:
            st.plotly_chart(fig_week, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu tuần ISO (sau khi bỏ Keep Space & Cancelled).")

    # Bảng chi tiết nếu cần
    with st.expander("📋 Xem chi tiết bảng tổng hợp (Status / Customer / Tuần)"):
        if status_summary is not None:
            st.subheader("Status (tất cả lô, bao gồm Keep Space & Cancelled)")
            st.dataframe(status_summary, use_container_width=True)
        if customer_summary is not None:
            st.subheader("Customer (đã bỏ Keep Space & Cancelled)")
            st.dataframe(customer_summary, use_container_width=True)
        if week_summary is not None:
            st.subheader("Tuần ISO (đã bỏ Keep Space & Cancelled)")
            st.dataframe(week_summary, use_container_width=True)

    # ============================================================
    # LƯU
    # ============================================================

    st.markdown("### 💾 Lưu dữ liệu tháng này")
    col_save1, col_save2 = st.columns([1, 3])
    with col_save1:
        if st.button("💾 Lưu tháng này", type="primary", key=f"save_{month_choice}"):
            # Cập nhật lại vào df_month (trường hợp đang lọc)
            df_month.update(edited)
            cleaned = df_month.dropna(how="all")
            save_month_df(month_choice, cleaned)
            st.success(f"Đã lưu dữ liệu cho tháng {month_choice} vào {SHIPMENT_FILE}")
            st.balloons()

    with col_save2:
        st.info(
            "KPI MONTH & chart Customer / tuần chỉ tính các lô không phải Keep Space / Cancelled."
        )

    # ============================================================
    # CẢNH BÁO SI / CY
    # ============================================================

    st.markdown("---")
    st.markdown("### ⏰ Cảnh báo SI / CY trong 48 giờ tới")

    si_alerts = find_alerts(df_month, "SI", hours_before=48)
    cy_alerts = find_alerts(df_month, "CY", hours_before=48)

    if si_alerts.empty and cy_alerts.empty:
        st.success("Hiện không có lô hàng nào có SI/CY trong vòng 48 giờ tới.")
    else:
        if not si_alerts.empty:
            st.error("🚨 SI trong 48 giờ:")
            show_cols = [
                c
                for c in [
                    "Customer",
                    "Routing",
                    "BKG NO",
                    "HBL NO",
                    "Carrier",
                    "Container Type",
                    "Quantity",
                    "SI",
                    "SI_parsed",
                ]
                if c in si_alerts.columns
            ]
            st.dataframe(si_alerts[show_cols], use_container_width=True)

        if not cy_alerts.empty:
            st.warning("⚠ CY trong 48 giờ:")
            show_cols = [
                c
                for c in [
                    "Customer",
                    "Routing",
                    "BKG NO",
                    "HBL NO",
                    "Carrier",
                    "Container Type",
                    "Quantity",
                    "CY",
                    "CY_parsed",
                ]
                if c in cy_alerts.columns
            ]
            st.dataframe(cy_alerts[show_cols], use_container_width=True)
