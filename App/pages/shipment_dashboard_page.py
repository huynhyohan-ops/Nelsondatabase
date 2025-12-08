
import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import plotly.io as pio
import os

from common.data_loader import load_all_sheets
from common.kpi_calculator import compute_kpis
from common.plot_utils import (
    line_chart_volume_profit,
    bar_chart_direct_coload_volume,
    horizontal_bar_top_clients,
    bar_top_destinations,
    stacked_area_segment_trend,
    group_bar_profit_cost_margin
)

def render_dashboard_page():
    st.markdown("<h1 style='color:#4D6D9A;'>📊 Operations Dashboard</h1>", unsafe_allow_html=True)

    all_data = load_all_sheets()
    df_all = pd.concat(all_data.values(), ignore_index=True)
    df_all["ETD"] = pd.to_datetime(df_all["ETD"], errors="coerce")
    df_all["Month_Label"] = df_all["ETD"].dt.strftime("%b")
    df_all["Quarter"] = df_all["ETD"].dt.to_period("Q").astype(str)
    df_all["Year"] = df_all["ETD"].dt.year

    # Custom date input style
    st.markdown("""
        <style>
        .stDateInput input {
            background-color: #c2e3ea !important;
            color: #003366 !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### <span style='color:#ffffff;'>🎛️ Filters</span>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        time_range = st.radio("Time Range", ["All", "Month", "Quarter", "Year"], horizontal=True)
    with col2:
        customer_type = st.radio("Customer Type", ["All", "Direct", "Coload"], horizontal=True)
    with col3:
        metric_selected = st.radio("Metric", ["Shipment", "TEUs", "Profit"], horizontal=True)
    with col4:
        date_range = st.date_input("Date Range", [])

    df_filtered = df_all.copy()
    if customer_type != "All":
        df_filtered = df_filtered[df_filtered["Customer Type"] == customer_type]
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range)
        df_filtered = df_filtered[(df_filtered["ETD"] >= start_date) & (df_filtered["ETD"] <= end_date)]

    if time_range == "Month":
        group_col = "Month_Label"
    elif time_range == "Quarter":
        group_col = "Quarter"
    elif time_range == "Year":
        group_col = "Year"
    else:
        group_col = "Month_Label"

    # KPI Cards – 4 khung riêng biệt
    st.markdown("---")
    st.markdown("### <span style='color:#ffffff;'>📈 KPIs</span>", unsafe_allow_html=True)
    kpis = compute_kpis(df_filtered)
    kpi_cols = st.columns(4)
    kpi_colors = ["#1A2B44", "#1A2B44", "#1A2B44", "#1A2B44"]

    for i, (label, value) in enumerate(kpis.items()):
        with kpi_cols[i]:
            st.markdown(f"""
                <div style='background-color:{kpi_colors[i]}; padding:16px; border-radius:10px; text-align:center;'>
                    <h5 style='color:#ffffff; margin-bottom:8px;'>{label}</h5>
                    <h2 style='color:#00C0F2; margin:0;'>{value}</h2>
                </div>
            """, unsafe_allow_html=True)

    # Main Analytics
    st.markdown("---")
    st.markdown("### <span style='color:#ffffff;'>🔍 Main Analytics</span>", unsafe_allow_html=True)
    col_main1, col_main2 = st.columns(2)

    if metric_selected == "Shipment":
        agg_data = df_filtered.groupby(group_col).size().reset_index(name="Shipment Count")
        y_metric = agg_data["Shipment Count"]
    elif metric_selected == "TEUs":
        agg_data = df_filtered.groupby(group_col)["Volume"].sum().reset_index()
        y_metric = agg_data["Volume"]
    else:
        agg_data = df_filtered.groupby(group_col)["Profit"].sum().reset_index()
        y_metric = agg_data["Profit"]

    with col_main1:
        st.markdown(f"<span style='color:#003366;'>📈 {metric_selected} Over Time</span>", unsafe_allow_html=True)
        fig1 = line_chart_volume_profit(agg_data[group_col], y_metric, y_metric)
        st.plotly_chart(fig1, use_container_width=True)

    with col_main2:
        st.markdown("<span style='color:#003366;'>📊 Direct vs Coload Volume & Profit</span>", unsafe_allow_html=True)
        fig2 = bar_chart_direct_coload_volume(df_filtered)
        st.plotly_chart(fig2, use_container_width=True)

    # Sub Charts
    st.markdown("### <span style='color:#ffffff;'>📊 Sub Charts</span>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("<span style='color:#003366;'>🏆 Top 5 Clients by Profit</span>", unsafe_allow_html=True)
        top_clients = df_filtered.groupby("Customer")["Profit"].sum().nlargest(5)
        fig3 = horizontal_bar_top_clients(top_clients.index, top_clients.values)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("<span style='color:#003366;'>🚚 Top Destinations by Shipment Volume</span>", unsafe_allow_html=True)
        top_dest = df_filtered.groupby("Routing")["Volume"].sum().nlargest(5)
        fig4 = bar_top_destinations(top_dest.index, top_dest.values)
        st.plotly_chart(fig4, use_container_width=True)

    with col3:
        st.markdown("<span style='color:#003366;'>📉 Segment Trend Over Time</span>", unsafe_allow_html=True)
        df_filtered["Segment"] = df_filtered["Routing"].astype(str).str[:3]
        segment_df = df_filtered.groupby([group_col, "Segment"])["Volume"].sum().unstack(fill_value=0)
        fig5 = stacked_area_segment_trend(segment_df.index, segment_df.T.to_dict(orient="list"))
        st.plotly_chart(fig5, use_container_width=True)

    with col4:
        st.markdown("<span style='color:#003366;'>💹 Profit vs Cost vs Margin</span>", unsafe_allow_html=True)
        pcm = df_filtered.groupby(group_col)[["Profit", "Buying Rate", "Selling Rate"]].sum().reset_index()
        margin = pcm["Profit"]
        fig6 = group_bar_profit_cost_margin(pcm[group_col], pcm["Profit"], pcm["Buying Rate"], margin)
        st.plotly_chart(fig6, use_container_width=True)

    # Export PDF button
    st.markdown("---")
    if st.button("📄 Export Dashboard Charts to PDF"):
        charts = [fig1, fig2, fig3, fig4, fig5, fig6]
        filenames = []
        for i, fig in enumerate(charts):
            file = f"chart_{i}.png"
            pio.write_image(fig, file, format="png", width=900, height=500)
            filenames.append(file)

        pdf = FPDF(orientation="L", unit="mm", format="A4")
        for img in filenames:
            pdf.add_page()
            pdf.image(img, x=10, y=20, w=270)

        pdf_path = "dashboard_export.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="dashboard_export.pdf", mime="application/pdf")

        for f in filenames:
            os.remove(f)
        os.remove(pdf_path)
