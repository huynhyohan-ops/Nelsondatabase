def compute_kpis(df):
    """
    Tính toán KPI từ dữ liệu shipment.
    - Total Shipments: Chỉ tính lô hàng Confirmed
    - Total TEUs: Tổng Volume của các lô Confirmed
    - Profit: Tính toàn bộ
    - Growth %: So sánh profit tháng gần nhất và tháng trước
    """
    # Chỉ giữ Confirmed
    df_confirmed = df[df["Status"].str.lower() == "confirmed"]

    total_shipments = len(df_confirmed)
    total_teus = df_confirmed["Volume"].sum()
    total_profit = df["Profit"].sum()

    # Tính tăng trưởng từ Profit
    latest = df["ETD_Month"].max()
    prev = latest - 1

    profit_latest = df[df["ETD_Month"] == latest]["Profit"].sum()
    profit_prev = df[df["ETD_Month"] == prev]["Profit"].sum()

    growth = ((profit_latest - profit_prev) / profit_prev * 100) if profit_prev else 0

    return {
        "Total Shipments": f"{total_shipments:,}",
        "Total TEUs": f"{total_teus:,.0f}",
        "Profit (USD)": f"${total_profit:,.0f}",
        "Growth %": f"{growth:.2f}%",
    }
