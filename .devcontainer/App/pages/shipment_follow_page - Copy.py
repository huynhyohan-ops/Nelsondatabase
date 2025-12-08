import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from common import shipment_analyzer as sa

def render_follow_shipment_page():
    st.title("📦 Shipment Follow Page")

    selected_month = st.sidebar.selectbox("📅 Chọn tháng", options=["Dec 2025"], index=0)
    df = sa.load_shipments(selected_month)

    # Volume và Profit KPI
    KPI_VOLUME = 80
    KPI_PROFIT = 15500

    kpi_volume = df[df["Status"].str.lower().isin(["confirmed", "submit"])]["Volume"].sum()
    kpi_profit = df["Profit"].sum()

    # 3 KPI cards hiển thị thẳng hàng
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="📦 Total Shipments", value=len(df))

    with col2:
        st.metric("📊 KPI Volume", f"{kpi_volume} / {KPI_VOLUME} TEU")
        st.progress(min(kpi_volume / KPI_VOLUME, 1.0))

    with col3:
        st.metric("💰 KPI Profit", f"${kpi_profit:,} / ${KPI_PROFIT:,}")
        st.progress(min(kpi_profit / KPI_PROFIT, 1.0))

    st.subheader("📌 Delay Selected Shipments")
    delay_options = st.multiselect("Chọn dòng delay (theo số thứ tự)", options=df.index.tolist())
    new_etd = st.date_input("📅 Chọn ngày ETD mới", value=datetime.today())

    if st.button("📤 Delay Selected"):
        for idx in delay_options:
            current_etd = df.at[idx, "ETD"]
            if pd.isna(df.at[idx, "ETD_Original"]):
                df.at[idx, "ETD_Original"] = current_etd
            log = f"{datetime.today().date()}:{current_etd.date()}→{new_etd}"
            if pd.isna(df.at[idx, "Delay_Log"]):
                df.at[idx, "Delay_Log"] = log
            else:
                df.at[idx, "Delay_Log"] += f" | {log}"
            df.at[idx, "ETD"] = pd.to_datetime(new_etd)

    # Tính toán lại các giá trị
    df = sa.calculate_all_columns(df)

    # Tính tiến trình ETA
    today = pd.Timestamp(datetime.today().date())

    def compute_eta_progress(etd, eta, ata):
        if pd.notnull(ata):
            return 100
        if pd.isnull(etd) or pd.isnull(eta):
            return 0
        total = (eta - etd).days
        passed = (today - etd).days
        if total <= 0:
            return 0
        return max(0, min(int((passed / total) * 100), 100))

    df["Progress ETA"] = df.apply(lambda row: compute_eta_progress(row["ETD"], row["ETA"], row["ATA"]), axis=1)

    # Cột sắp xếp thông minh
    df["Sort_Order"] = df["Status"].map({
        "Confirmed": 1,
        "Submit": 2,
        "Keep Space": 3,
        "Cancelled": 99
    }).fillna(50).astype(int)

    df.sort_values(by=["Sort_Order", "ETD"], inplace=True)

    # Editor & Save
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Progress ETA": st.column_config.ProgressColumn(
                label="🚚 ETA Progress",
                min_value=0,
                max_value=100,
                format="%d%%"
            )
        }
    )

    if st.button("💾 Save Data"):
        sa.save_shipments(selected_month, edited_df)
        st.success("Đã lưu dữ liệu vào file thành công!")
