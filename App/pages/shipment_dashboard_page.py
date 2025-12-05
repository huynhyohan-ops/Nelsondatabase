import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from contextlib import nullcontext

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Dùng lại các hàm & helper từ trang Follow Shipment
from pages.shipment_follow_page import (
    load_all_shipments,
    filter_by_timeframe,
    aggregate_kpi_categories,
    extract_destination,
    render_filter_state,
)


def render_dashboard_page():
    """KPI Dashboard cho shipment – tách riêng khỏi trang nhập liệu."""
    st.markdown(
        """
        <div class='page-hero'>
            <div class='page-hero__title'>📊 Shipment KPI Dashboard</div>
            <div class='page-hero__desc'>Tổng quan Direct vs Coload, routing & customer loss với bố cục mới. Bộ lọc, tính toán và biểu đồ giữ nguyên.</div>
            <div class='page-hero__badges'>
                <span class='badge-pill'>Volume & Profit</span>
                <span class='badge-pill'>Routing</span>
                <span class='badge-pill'>Customer loss</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='surface-title'>Bộ lọc & phạm vi xem</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='surface-sub'>Dùng chung control với trang Follow Shipment để đảm bảo thống nhất dữ liệu.</div>",
        unsafe_allow_html=True,
    )

    # Đọc toàn bộ Shipments.xlsx
    df_all = load_all_shipments()
    if df_all.empty:
        st.info("Chưa có dữ liệu trong Shipments.xlsx để dựng KPI Dashboard.")
        return

    # Bộ lọc dùng chung với Follow Shipment (Customer Type / Timeframe / Show loss / Search khách)
    filter_state, filters_changed = render_filter_state()
    spinner_context = st.spinner("Đang áp dụng bộ lọc và dựng biểu đồ...") if filters_changed else nullcontext()

    # Để dùng sau cho KPI nhóm & expander
    df_time = pd.DataFrame()
    volume_profit = pd.DataFrame()
    loss_by_type = pd.DataFrame()
    loss_detail = pd.DataFrame()
    top_routing = pd.DataFrame()

    with spinner_context:
        # Lọc theo Customer Type + search trên toàn bộ dataset
        df_view = df_all.copy()
        if filter_state["customer_type"] != "All":
            df_view = df_view[df_view["Customer Type"] == filter_state["customer_type"]]
        if filter_state["customer_query"].strip():
            query = filter_state["customer_query"].strip().lower()
            df_view = df_view[df_view["Customer"].fillna("").str.lower().str.contains(query)]

        # Áp dụng timeframe trên df_view
        df_time = filter_by_timeframe(df_view, filter_state["timeframe"])

        # Đồng thời tạo df_all_time theo cùng filter/timeframe (dùng cho logic history)
        df_all_filtered = df_all.copy()
        if filter_state["customer_type"] != "All":
            df_all_filtered = df_all_filtered[df_all_filtered["Customer Type"] == filter_state["customer_type"]]
        if filter_state["customer_query"].strip():
            query = filter_state["customer_query"].strip().lower()
            df_all_filtered = df_all_filtered[
                df_all_filtered["Customer"].fillna("").str.lower().str.contains(query)
            ]
        df_all_time = (
            filter_by_timeframe(df_all_filtered, filter_state["timeframe"])
            if not df_all_filtered.empty
            else df_all_filtered
        )

        # Quick KPI header sau filter
        header_cols = st.columns(4)
        with header_cols[0]:
            st.metric("Shipments đã lọc", len(df_time))
        with header_cols[1]:
            st.metric("Timeframe", filter_state["timeframe"])
        with header_cols[2]:
            st.metric("Customer type", filter_state["customer_type"])
        with header_cols[3]:
            st.metric("Hiển thị loss", "Có" if filter_state["show_loss"] else "Không")

        def _clean_real_shipments(df: pd.DataFrame) -> pd.DataFrame:
            if df.empty:
                return df
            df = df.copy()
            df["Status_clean"] = df["Status"].fillna("").astype(str).str.strip()
            # Loại Keep Space & Cancelled
            df = df[~df["Status_clean"].isin(["Keep Space", "Cancelled"])]
            df["Customer Type"] = df["Customer Type"].fillna("Unknown")
            df["Destination"] = df["Routing"].apply(extract_destination)
            return df

        # perf_df: dùng để tính Volume/Profit, routing, biểu đồ chi tiết
        perf_df = _clean_real_shipments(df_all_time if not df_all_time.empty else df_time)
        # history_df: dùng để tính khách loss (≥ 3 tháng không ship)
        history_df = _clean_real_shipments(df_all_filtered)

        # ---------- OPTION CHO BIỂU ĐỒ CHI TIẾT ----------
        st.markdown(
            "<div class='surface-title'>📊 Direct vs Coload – Tổng quan & biểu đồ chi tiết</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='surface-sub'>Các lựa chọn hiển thị vẫn dùng cùng dataset sau filter, chỉ đổi bố cục trình bày.</div>",
            unsafe_allow_html=True,
        )

        control_cols = st.columns([1.1, 1.1, 1.2])
        with control_cols[0]:
            chart_dimension = st.selectbox(
                "Nhóm theo",
                ["Customer Type", "Customer"],
                key="kpi_chart_dimension",
            )
        with control_cols[1]:
            chart_metric = st.selectbox(
                "Chỉ số",
                ["Volume", "Profit", "Shipments"],
                key="kpi_chart_metric",
            )
        with control_cols[2]:
            chart_type = st.radio(
                "Loại biểu đồ",
                ["Histogram", "Pie", "Bar"],
                horizontal=True,
                key="kpi_chart_type",
            )

        # ---------- TÍNH DỮ LIỆU TỔNG QUAN ----------
        st.markdown(
            "<div class='surface-title'>📌 Tổng quan Direct vs Coload</div>",
            unsafe_allow_html=True,
        )

        if not perf_df.empty:
            perf_df = perf_df.copy()
            perf_df["Customer Type"] = perf_df["Customer Type"].replace("", pd.NA).fillna("Unknown")
            volume_profit = (
                perf_df.groupby("Customer Type", dropna=False)[["Volume", "Profit"]]
                .sum()
                .reset_index()
            )

        if filter_state["show_loss"] and not history_df.empty:
            history_df = history_df.dropna(subset=["ETD", "Customer"])
            history_df["ETD"] = pd.to_datetime(history_df["ETD"], errors="coerce")
            last_ship = history_df.groupby("Customer")["ETD"].max().reset_index()
            cutoff_date = datetime.now() - timedelta(days=90)
            loss_detail = last_ship[last_ship["ETD"] < cutoff_date].copy()
            loss_detail = loss_detail.merge(
                history_df[["Customer", "Customer Type"]].drop_duplicates(), on="Customer", how="left"
            )
            loss_detail["Customer Type"] = loss_detail["Customer Type"].fillna("Unknown")
            loss_detail["DaysSince"] = (datetime.now() - loss_detail["ETD"]).dt.days
            if not loss_detail.empty:
                loss_by_type = (
                    loss_detail.groupby("Customer Type", dropna=False).agg(
                        LostCustomers=("Customer", "nunique"),
                        AvgDaysSince=("DaysSince", "mean"),
                    )
                ).reset_index()

        routing_detail = pd.DataFrame()
        routing_counts = pd.DataFrame()
        top_routing = pd.DataFrame()
        if not perf_df.empty:
            routing_detail = perf_df.copy()
            routing_detail = routing_detail[routing_detail["Destination"].astype(str).str.len() > 0]

            routing_filter_cols = st.columns([1, 1.4])
            dest_options = ["All"] + sorted(routing_detail["Destination"].dropna().unique().tolist())
            default_dest = st.session_state.get("kpi_routing_destination", "All")
            if default_dest not in dest_options:
                default_dest = "All"
            with routing_filter_cols[0]:
                selected_destination = st.selectbox(
                    "Destination (tách tự động từ Routing)",
                    dest_options,
                    index=dest_options.index(default_dest) if default_dest in dest_options else 0,
                    key="kpi_routing_destination",
                    help="Ví dụ Routing 'HPH - DENVER' sẽ được đếm ở Destination = DENVER.",
                )
            with routing_filter_cols[1]:
                st.caption("Dùng ô tìm kiếm khách và Customer Type để lọc routing theo khách/Direct-Coload.")

            if selected_destination != "All":
                routing_detail = routing_detail[routing_detail["Destination"] == selected_destination]

            routing_counts = (
                routing_detail.groupby(["Customer Type", "Destination"], dropna=False)
                .size()
                .reset_index(name="Shipments")
                if not routing_detail.empty
                else pd.DataFrame()
            )
            if not routing_counts.empty:
                top_routing = routing_counts.sort_values("Shipments", ascending=False).groupby("Customer Type").head(1)

        has_no_overview = volume_profit.empty and top_routing.empty and (
            loss_by_type.empty or not filter_state["show_loss"]
        )

        # ---------- BUILD FIGURE OVERVIEW & DETAIL ----------
        fig_overview = None
        fig_detail = None

        if not has_no_overview:
            fig_overview = make_subplots(
                rows=1,
                cols=3,
                subplot_titles=[
                    "Volume & Profit theo Customer Type",
                    "Routing phổ biến nhất",
                    "Customer Loss (≥3 tháng không ship)",
                ],
                horizontal_spacing=0.08,
            )

            if not volume_profit.empty:
                fig_overview.add_trace(
                    go.Bar(
                        x=volume_profit["Customer Type"],
                        y=volume_profit["Volume"],
                        name="Volume (TEU)",
                        marker_color="#2563eb",
                        text=volume_profit["Volume"],
                        textposition="outside",
                    ),
                    row=1,
                    col=1,
                )
                fig_overview.add_trace(
                    go.Bar(
                        x=volume_profit["Customer Type"],
                        y=volume_profit["Profit"],
                        name="Profit (USD)",
                        marker_color="#16a34a",
                        text=volume_profit["Profit"],
                        textposition="outside",
                    ),
                    row=1,
                    col=1,
                )
            if not top_routing.empty:
                fig_overview.add_trace(
                    go.Bar(
                        x=top_routing["Customer Type"],
                        y=top_routing["Shipments"],
                        name="Routing nổi bật",
                        marker_color="#f59e0b",
                        text=top_routing["Destination"],
                        textposition="outside",
                    ),
                    row=1,
                    col=2,
                )
            if filter_state["show_loss"] and not loss_by_type.empty:
                fig_overview.add_trace(
                    go.Bar(
                        x=loss_by_type["Customer Type"],
                        y=loss_by_type["LostCustomers"],
                        name="Khách loss",
                        marker_color="#ef4444",
                        text=loss_by_type["AvgDaysSince"].round(0),
                        texttemplate="Ngày trung bình: %{text}",
                    ),
                    row=1,
                    col=3,
                )
            fig_overview.update_layout(
                barmode="group",
                legend_title="Chỉ báo",
                margin=dict(t=60, b=40),
                hovermode="x unified",
                title=f"So sánh Direct vs Coload ({filter_state['timeframe']})",
            )
            fig_overview.update_xaxes(tickangle=-25)

        # Biểu đồ chi tiết nếu có dữ liệu
        if not perf_df.empty:
            chart_data = perf_df.copy()
            chart_data["Customer Type"] = chart_data["Customer Type"].replace("", pd.NA).fillna("Unknown")
            chart_data["Customer"] = chart_data["Customer"].replace("", pd.NA).fillna("Unknown")

            grouped_chart = (
                chart_data.groupby(chart_dimension, dropna=False)
                .agg(
                    Volume=("Volume", "sum"),
                    Profit=("Profit", "sum"),
                    Shipments=("Customer", "count"),
                )
                .reset_index()
            )

            if not grouped_chart.empty:
                if chart_type == "Histogram":
                    fig_detail = px.histogram(
                        grouped_chart,
                        x=chart_dimension,
                        y=chart_metric,
                        color=chart_dimension if chart_dimension == "Customer Type" else None,
                        title=f"Histogram {chart_metric} theo {chart_dimension}",
                        labels={chart_dimension: chart_dimension, chart_metric: chart_metric},
                    )
                    fig_detail.update_layout(margin=dict(t=60, b=40))
                elif chart_type == "Pie":
                    fig_detail = px.pie(
                        grouped_chart,
                        names=chart_dimension,
                        values=chart_metric,
                        title=f"Tỉ trọng {chart_metric} theo {chart_dimension}",
                    )
                    fig_detail.update_traces(
                        textinfo="label+percent",
                        hovertemplate="%{label}: %{value}<extra></extra>",
                    )
                else:
                    fig_detail = px.bar(
                        grouped_chart,
                        x=chart_dimension,
                        y=chart_metric,
                        color=chart_dimension if chart_dimension == "Customer Type" else None,
                        text=chart_metric,
                        title=f"Bar chart {chart_metric} theo {chart_dimension}",
                        labels={chart_dimension: chart_dimension, chart_metric: chart_metric},
                    )
                    fig_detail.update_traces(textposition="outside")
                    fig_detail.update_layout(margin=dict(t=60, b=40))

        # ---------- LAYOUT: 1 HÀNG 2 CỘT ----------
        if fig_overview is None and fig_detail is None:
            st.info("Chưa có dữ liệu đủ để vẽ biểu đồ tổng hợp.")
        else:
            col_overview, col_detail = st.columns([1.4, 1.6])

            with col_overview:
                if fig_overview is not None:
                    st.plotly_chart(fig_overview, use_container_width=True)
                if filter_state["show_loss"] and not loss_detail.empty:
                    st.subheader("Khách loss (≥3 tháng)")
                    show_loss_cols = [
                        c
                        for c in ["Customer", "Customer Type", "ETD", "DaysSince"]
                        if c in loss_detail.columns
                    ]
                    st.dataframe(loss_detail[show_loss_cols], use_container_width=True, height=260)

            with col_detail:
                st.markdown("#### 📈 Biểu đồ chi tiết")
                if fig_detail is not None:
                    st.plotly_chart(fig_detail, use_container_width=True)
                else:
                    st.caption("Không có dữ liệu sau khi áp dụng bộ lọc để vẽ biểu đồ chi tiết.")

    # ---------- KPI NHÓM ----------
    st.markdown("<div class='surface-title'>📈 KPI theo nhóm</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='surface-sub'>Revenue / Orders / Conversion trình bày dạng metric cho dễ so sánh.</div>",
        unsafe_allow_html=True,
    )
    kpi_group_df = aggregate_kpi_categories(df_time)
    kpi_cols = st.columns(3)
    for idx, (label, value, note) in enumerate(
        zip(kpi_group_df["Category"], kpi_group_df["Value"], kpi_group_df["Note"])
    ):
        with kpi_cols[idx]:
            if label == "Conversion Rate":
                st.metric(label, f"{value:.1f}%", help=note)
            elif label == "Revenue":
                st.metric(label, f"{value:,.0f} USD", help=note)
            else:
                st.metric(label, f"{int(value)}", help=note)

    with st.expander("📋 Xem dữ liệu đã lọc"):
        st.subheader("Dataset sau filter/timeframe")
        st.dataframe(df_time, use_container_width=True)

        if not volume_profit.empty:
            st.subheader("Volume & Profit theo nhóm")
            st.dataframe(volume_profit, use_container_width=True)

        if not loss_by_type.empty:
            st.subheader("Customer loss theo nhóm")
            st.dataframe(loss_by_type, use_container_width=True)

        if not loss_detail.empty:
            st.subheader("Danh sách khách không ship 3 tháng gần nhất")
            st.dataframe(
                loss_detail[["Customer", "Customer Type", "ETD", "DaysSince"]],
                use_container_width=True,
            )

        if not top_routing.empty:
            st.subheader("Routing phổ biến theo nhóm")
            st.dataframe(
                top_routing.rename(columns={"Destination": "Routing (đích)"}),
                use_container_width=True,
            )
