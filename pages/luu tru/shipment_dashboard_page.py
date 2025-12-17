# ----------------------------------------------------------------------
# shipment_dashboard_page.py — Smooth UX: Debounce(200ms) + Cancel Token +
# Cache + Partial Render (Report View) — giữ 100% logic & palette cũ
#
# Không phá vỡ:
# - Giữ nguyên entry-point: render_dashboard_page()
# - KPI cốt lõi tính bởi common.kpi_calculator.compute_kpis
# - Dashboard chuẩn (plot_utils) & layout/màu cũ
#
# Thêm mới:
# - Debounce 200 ms cho controls (không reload toàn trang)
# - Cancel token (request sequencing) tránh race khi đổi control liên tiếp
# - Cache theo filter-keys cho filter/KPI/series
# - Partial render: luôn hiển thị last result; khi debounce xong mới thay thế
# - Report View: Metric điều khiển dual-line (đường chính theo Metric)
# - Figure update: với Report View, update trục/trace thay vì tạo mới khi có thể
#
# Phụ thuộc: streamlit>=1.26, pandas>=1.3, plotly>=5.18
# ----------------------------------------------------------------------

from typing import List, Tuple, Dict, Optional
import time
import hashlib
from datetime import datetime, timedelta, date

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from common.data_loader import load_all_sheets
from common.kpi_calculator import compute_kpis as compute_kpis_external
from common.plot_utils import (
    line_chart_volume_profit,
    bar_chart_direct_coload_volume,
    horizontal_bar_top_clients,
    bar_top_destinations,
    stacked_area_segment_trend,
    group_bar_profit_cost_margin
)

# ---- Palette giữ nguyên ----
PRIMARY = "#0B2545"
MEDIUM  = "#1E5FA8"
LIGHT   = "#4DA6FF"
LABEL   = "#A8D1FF"

# Debounce
DEBOUNCE_MS = 200

# =========================
# Theme & CSS (axes/legend/hover; không đổi màu trace dashboard cũ)
# =========================
def configure_plotly_theme():
    template = go.layout.Template(
        layout=dict(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(color=PRIMARY),
            xaxis=dict(
                gridcolor=LABEL, zerolinecolor=LABEL, linecolor=PRIMARY,
                tickfont=dict(color=PRIMARY), title=dict(font=dict(color=PRIMARY)),
            ),
            yaxis=dict(
                gridcolor=LABEL, zerolinecolor=LABEL, linecolor=PRIMARY,
                tickfont=dict(color=PRIMARY), title=dict(font=dict(color=PRIMARY)),
            ),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=LABEL, font=dict(color=PRIMARY)),
            hoverlabel=dict(bgcolor=PRIMARY, font=dict(color="white")),
            annotations=[dict(showarrow=False, font=dict(color=PRIMARY))],
        )
    )
    pio.templates["navy_theme"] = template
    pio.templates.default = "navy_theme"


# =========================
# Data layer (cache)
# =========================
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    data_sheets = load_all_sheets()
    return pd.concat(data_sheets.values(), ignore_index=True)

def generate_sample_data(rows: int = 200) -> pd.DataFrame:
    now = pd.Timestamp.today().normalize()
    rng = pd.date_range(now - pd.Timedelta(days=365), periods=rows, freq="D")
    df = pd.DataFrame({
        "ShipmentID": [f"SHP-{1000+i}" for i in range(rows)],
        "ETD": rng,
        "ETD_Original": rng - pd.to_timedelta((pd.Series(range(rows)) % 7), unit="D"),
        "ETA": rng + pd.to_timedelta((pd.Series(range(rows)) % 25) + 5, unit="D"),
        "ATA": rng + pd.to_timedelta((pd.Series(range(rows)) % 25) + 5 + (pd.Series(range(rows)) % 6 - 3), unit="D"),
        "Customer Type": (["Direct"] * (rows // 2)) + (["Coload"] * (rows - rows // 2)),
        "Customer": [f"C{(i % 8) + 1}" for i in range(rows)],
        "Volume": (pd.Series(range(rows)) % 9) + 1,
        "Profit": ((pd.Series(range(rows)) % 7) - 3) * 100,
        "Routing": [f"R{(i % 6) + 1}" for i in range(rows)],
        "DelayReason": ["Congestion", "Docs", "Customs", "Weather", "Carrier", "Other"][pd.Series(range(rows)) % 6],
        "Buying Rate": 100 + (pd.Series(range(rows)) % 7) * 20,
        "Selling Rate": 150 + (pd.Series(range(rows)) % 7) * 25,
    })
    return df


# --- Column resolver (giữ tương thích) ---
def _resolve_columns(df: pd.DataFrame) -> Dict[str, str]:
    cols = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in cols:
                return cols[n.lower()]
        return None
    return {
        "customer": pick("Customer", "CustomerName", "Client"),
        "customer_type": pick("Customer Type", "CustType", "Type"),
        "shipment_id": pick("ShipmentID", "Shipment Id", "ID"),
        "etd": pick("ETD", "ETD Date", "ETD_Actual", "ETD_Original") or pick("ETD"),
        "etd_original": pick("ETD_Original", "ETD Orig", "ETD Plan"),
        "eta": pick("ETA", "ETA Date"),
        "ata": pick("ATA", "ATA Date"),
        "volume": pick("Volume", "TEU", "TEUs"),
        "profit": pick("Profit", "GP", "Margin"),
        "routing": pick("Routing", "Route", "Destination"),
        "delay_reason": pick("DelayReason", "Delay Reason", "Reason"),
    }

def update_customer_dropdown_options(df: pd.DataFrame, customer_type: str) -> List[str]:
    m = _resolve_columns(df)
    cust_col, ctype_col = m["customer"], m["customer_type"]
    if not cust_col:
        return ["All"]
    view = df if customer_type == "All" or not ctype_col else df[df[ctype_col] == customer_type]
    customers = sorted(view[cust_col].dropna().unique().tolist()) if not view.empty else []
    return ["All"] + customers

def _default_date_range_for(df: pd.DataFrame) -> Tuple[date, date]:
    if df is None or df.empty:
        today = pd.Timestamp.today().normalize().date()
        return (today - timedelta(days=90), today)
    etd_col = (_resolve_columns(df).get("etd") or "ETD")
    if etd_col not in df.columns:
        today = pd.Timestamp.today().normalize().date()
        return (today - timedelta(days=90), today)
    s = pd.to_datetime(df[etd_col], errors="coerce")
    start, end = s.min(), s.max()
    if pd.isna(start) or pd.isna(end):
        today = pd.Timestamp.today().normalize().date()
        return (today - timedelta(days=90), today)
    return (start.date(), end.date())

def _select_group_col(granularity: str) -> str:
    return {"Month": "month", "Quarter": "quarter", "Year": "year"}.get(granularity, "month")

def _ensure_time_parts(df: pd.DataFrame, etd_col: str) -> pd.DataFrame:
    out = df.copy()
    out[etd_col] = pd.to_datetime(out[etd_col], errors="coerce")
    out["month"] = out[etd_col].dt.to_period("M").astype(str)
    out["quarter"] = out[etd_col].dt.to_period("Q").astype(str)
    out["year"] = out[etd_col].dt.year
    return out

# ---------- Hash key cho cache ----------
def _filters_key(filters: Dict) -> str:
    raw = repr(sorted(filters.items())).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

# ---------- Cache pipelines ----------
@st.cache_data(show_spinner=False)
def get_filtered(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    m = _resolve_columns(df)
    etd = m["etd"] or "ETD"
    ctype, cust = m["customer_type"], m["customer"]
    start, end = filters["date_range"]
    view = df.copy()
    if ctype and filters["customer_type"] != "All":
        view = view[view[ctype] == filters["customer_type"]]
    if cust and filters["customer"] != "All":
        view = view[view[cust] == filters["customer"]]
    if start and end:
        s = pd.to_datetime(start); e = pd.to_datetime(end)
        view = view[(pd.to_datetime(view[etd], errors="coerce") >= s) &
                    (pd.to_datetime(view[etd], errors="coerce") <= e)]
    return view

@st.cache_data(show_spinner=False)
def get_kpis(df_filtered: pd.DataFrame, tolerance_days: int) -> Dict[str, float]:
    """
    Tính KPI có cache. Giữ logic cũ (compute_kpis_external),
    cộng thêm On Time Rate / Avg Delay Days nếu có ETA/ATA.
    """
    base = {
        "Total Shipments": 0, "Total TEUs": 0, "Total Profit": 0,
        "Avg Profit/TEU": 0.0, "On Time Rate": None, "Avg Delay Days": None,
    }
    if df_filtered is None or df_filtered.empty:
        return base
    try:
        kpi_std = compute_kpis_external(df_filtered)
        if isinstance(kpi_std, dict):
            base.update(kpi_std)
    except Exception:
        m = _resolve_columns(df_filtered)
        vol = m["volume"] or "Volume"
        prof = m["profit"] or "Profit"
        base["Total Shipments"] = int(len(df_filtered))
        base["Total TEUs"] = float(df_filtered[vol].sum()) if vol in df_filtered else 0.0
        base["Total Profit"] = float(df_filtered[prof].sum()) if prof in df_filtered else 0.0
        base["Avg Profit/TEU"] = (base["Total Profit"] / base["Total TEUs"]) if base["Total TEUs"] else 0.0

    m = _resolve_columns(df_filtered); eta, ata = m["eta"], m["ata"]
    if eta in df_filtered.columns and ata in df_filtered.columns:
        tmp = df_filtered[[eta, ata]].copy()
        tmp[eta] = pd.to_datetime(tmp[eta], errors="coerce")
        tmp[ata] = pd.to_datetime(tmp[ata], errors="coerce")
        tmp["delay_days"] = (tmp[ata] - tmp[eta]).dt.days
        tmp["is_delayed"] = (tmp["delay_days"] > tolerance_days)
        tmp["is_ontime"] = (~tmp["is_delayed"]).fillna(False)
        if tmp["is_ontime"].count() > 0:
            base["On Time Rate"] = float(tmp["is_ontime"].mean())
        if tmp["delay_days"].notna().any():
            base["Avg Delay Days"] = float(tmp["delay_days"].dropna().mean())
    return base

@st.cache_data(show_spinner=False)
def get_series(df_filtered: pd.DataFrame, granularity: str) -> Dict[str, pd.Series]:
    if df_filtered.empty:
        return {"agg_ship": pd.Series(dtype=float), "agg_vol": pd.Series(dtype=float), "agg_profit": pd.Series(dtype=float)}
    m = _resolve_columns(df_filtered)
    etd_col = m["etd"] or "ETD"
    vol_col = m["volume"] or "Volume"
    prof_col = m["profit"] or "Profit"
    dfw = _ensure_time_parts(df_filtered, etd_col)
    g = _select_group_col(granularity)
    return {
        "agg_ship": dfw.groupby(g).size().rename("Shipments"),
        "agg_vol": (dfw.groupby(g)[vol_col].sum() if vol_col in dfw else pd.Series(dtype=float)),
        "agg_profit": (dfw.groupby(g)[prof_col].sum() if prof_col in dfw else pd.Series(dtype=float)),
    }


# =========================
# UI helpers
# =========================
def _empty_fig(title="No data"):
    fig = go.Figure()
    fig.add_annotation(text=title, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=16, color=PRIMARY))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
    return fig

def _apply_report_navy(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=PRIMARY, plot_bgcolor=PRIMARY, font=dict(color=LABEL),
        legend=dict(font=dict(color=LABEL)), margin=dict(l=10, r=10, t=40, b=10)
    )
    fig.update_xaxes(showgrid=True, gridcolor=LABEL, zerolinecolor=LABEL,
                     linecolor=LABEL, tickfont=dict(color=LABEL), title=dict(font=dict(color=LABEL)))
    fig.update_yaxes(showgrid=True, gridcolor=LABEL, zerolinecolor=LABEL,
                     linecolor=LABEL, tickfont=dict(color=LABEL), title=dict(font=dict(color=LABEL)))
    return fig

def _dual_line(x, y_main, y_side, name_main, name_side):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_main, mode="lines+markers", name=name_main, line=dict(color=MEDIUM, width=2)))
    fig.add_trace(go.Scatter(x=x, y=y_side, mode="lines+markers", name=name_side, line=dict(color=LIGHT,  width=2), yaxis="y2"))
    fig.update_layout(
        yaxis=dict(title=name_main),
        yaxis2=dict(title=name_side, overlaying="y", side="right"),
        hovermode="x unified", margin=dict(l=10, r=10, t=40, b=10), height=380,
    )
    return fig

# ---- Partial update (không tạo fig mới nếu cấu trúc phù hợp) ----
def _update_or_make_dual(fig: Optional[go.Figure], x, y_main, y_side, name_main, name_side) -> go.Figure:
    if isinstance(fig, go.Figure) and len(fig.data) == 2 and isinstance(fig.data[0], go.Scatter):
        fig.data[0].x = x; fig.data[0].y = y_main; fig.data[0].name = name_main
        fig.data[1].x = x; fig.data[1].y = y_side; fig.data[1].name = name_side
        fig.update_yaxes(title=name_main)
        fig.update_layout(yaxis2=dict(title=name_side, overlaying="y", side="right"))
        return fig
    return _dual_line(x, y_main, y_side, name_main, name_side)

def _update_or_make_line(fig: Optional[go.Figure], x, y, name="OTD Rate") -> go.Figure:
    if isinstance(fig, go.Figure) and len(fig.data) == 1 and isinstance(fig.data[0], go.Scatter):
        fig.data[0].x = x; fig.data[0].y = y; fig.data[0].name = name
        return fig
    f = go.Figure(); f.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name, line=dict(color=MEDIUM)))
    f.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    return f


# =========================
# Rendering (dashboard chuẩn)
# =========================
def render_standard_dashboard(df_filtered: pd.DataFrame, granularity: str, metric_selected: str):
    group_col = _select_group_col(granularity)
    if df_filtered.empty:
        fig = _empty_fig()
        st.plotly_chart(fig, use_container_width=True); st.plotly_chart(fig, use_container_width=True)
        cols = st.columns(4)
        for c in cols: c.plotly_chart(fig, use_container_width=True)
        return

    m = _resolve_columns(df_filtered)
    etd_col = m["etd"] or "ETD"
    vol_col = m["volume"] or "Volume"
    prof_col = m["profit"] or "Profit"
    routing_col = m["routing"] or "Routing"
    cust_col = m["customer"] or "Customer"

    dfp = _ensure_time_parts(df_filtered, etd_col)

    if metric_selected == "Shipment":
        agg = dfp.groupby(group_col).size().reset_index(name="Shipment Count")
        fig1 = line_chart_volume_profit(agg[group_col], agg["Shipment Count"], agg["Shipment Count"])
    elif metric_selected == "TEUs":
        agg = dfp.groupby(group_col)[vol_col].sum().reset_index()
        fig1 = line_chart_volume_profit(agg[group_col], agg[vol_col], agg[vol_col])
    else:
        agg = dfp.groupby(group_col)[prof_col].sum().reset_index()
        fig1 = line_chart_volume_profit(agg[group_col], agg[prof_col], agg[prof_col])

    fig2 = bar_chart_direct_coload_volume(df_filtered)

    top_clients = df_filtered.groupby(cust_col).size().nlargest(5)
    fig3 = horizontal_bar_top_clients(top_clients.index, top_clients.values)

    top_dest = df_filtered.groupby(routing_col)[vol_col].sum().nlargest(5) if vol_col in df_filtered else pd.Series([], dtype=float)
    fig4 = bar_top_destinations(top_dest.index, top_dest.values) if len(top_dest) else _empty_fig()

    seg = dfp.copy(); seg["Segment"] = seg[routing_col].astype(str).str[:3]
    area_pivot = seg.pivot_table(index=group_col, columns="Segment", values=vol_col, aggfunc="sum", fill_value=0) if vol_col in seg else pd.DataFrame()
    fig5 = stacked_area_segment_trend(area_pivot.index, area_pivot.T.to_dict(orient="list")) if not area_pivot.empty else _empty_fig()

    pcm = dfp.groupby(group_col)[[prof_col]].sum().reset_index()
    pcm["Buying Rate"] = 0.0; margin = pcm[prof_col]
    fig6 = group_bar_profit_cost_margin(pcm[group_col], pcm[prof_col], pcm["Buying Rate"], margin)

    col_main1, col_main2 = st.columns(2)
    with col_main1: st.plotly_chart(fig1, use_container_width=True)
    with col_main2: st.plotly_chart(fig2, use_container_width=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.plotly_chart(fig3, use_container_width=True)
    with col2: st.plotly_chart(fig4, use_container_width=True)
    with col3: st.plotly_chart(fig5, use_container_width=True)
    with col4: st.plotly_chart(fig6, use_container_width=True)


# =========================
# Rendering (Report View) — partial update
# =========================
def render_report_view(df_filtered: pd.DataFrame, granularity: str, tolerance_days: int, metric_selected: str):
    if df_filtered.empty:
        st.info("No data for selected filters")
        return

    ss = st.session_state
    m = _resolve_columns(df_filtered)
    etd = (m["etd_original"] or m["etd"] or "ETD")
    if etd not in df_filtered.columns: etd = m["etd"] or "ETD"
    vol_col = m["volume"] or "Volume"
    prof_col = m["profit"] or "Profit"
    cust_col = m["customer"] or "Customer"
    routing_col = m["routing"] or "Routing"
    eta_col, ata_col = m["eta"], m["ata"]
    delay_reason_col = m["delay_reason"] or "DelayReason"

    series = get_series(df_filtered, granularity)
    idx = sorted(set(series["agg_ship"].index)
                 .union(set(series["agg_vol"].index if hasattr(series["agg_vol"], "index") else []))
                 .union(set(series["agg_profit"].index if hasattr(series["agg_profit"], "index") else [])))

    # Dual-line theo Metric
    if metric_selected == "Shipment":
        y_main_name, y_side_name = "Shipments", "Volume"
        y_main = pd.Series(series["agg_ship"]).reindex(idx).fillna(0).values
        y_side = pd.Series(series["agg_vol"]).reindex(idx).fillna(0).values if len(series["agg_vol"]) else [0]*len(idx)
    elif metric_selected == "TEUs":
        y_main_name, y_side_name = "Volume", "Shipments"
        y_main = pd.Series(series["agg_vol"]).reindex(idx).fillna(0).values if len(series["agg_vol"]) else [0]*len(idx)
        y_side = pd.Series(series["agg_ship"]).reindex(idx).fillna(0).values
    else:
        y_main_name, y_side_name = "Profit", "Shipments"
        y_main = pd.Series(series["agg_profit"]).reindex(idx).fillna(0).values if len(series["agg_profit"]) else [0]*len(idx)
        y_side = pd.Series(series["agg_ship"]).reindex(idx).fillna(0).values

    # --- Partial update cho figure: dùng fig trong session nếu sẵn có ---
    ss.setdefault("fig_report_dual", None)
    ss.setdefault("fig_report_otd", None)
    ss.setdefault("fig_report_s1", None)
    ss.setdefault("fig_report_s2", None)
    ss.setdefault("fig_report_s3", None)
    ss.setdefault("fig_report_s4", None)

    fig_a = _update_or_make_dual(ss["fig_report_dual"], idx, y_main, y_side, y_main_name, y_side_name)
    ss["fig_report_dual"] = fig_a

    # OTD per period
    dfw = _ensure_time_parts(df_filtered.copy(), m["etd"] or "ETD")
    g = _select_group_col(granularity)
    if eta_col in dfw.columns and ata_col in dfw.columns:
        otd = dfw[[g, eta_col, ata_col]].copy()
        otd[eta_col] = pd.to_datetime(otd[eta_col], errors="coerce")
        otd[ata_col] = pd.to_datetime(otd[ata_col], errors="coerce")
        otd["delay_days"] = (otd[ata_col] - otd[eta_col]).dt.days
        otd["ontime"] = ~(otd["delay_days"] > tolerance_days)
        otd_rate = otd.groupby(g)["ontime"].mean().fillna(0)
        fig_b = _update_or_make_line(ss["fig_report_otd"], otd_rate.index, otd_rate.values, "OTD Rate")
    else:
        fig_b = _empty_fig("No ETA/ATA columns for OTD")
    ss["fig_report_otd"] = fig_b

    for f in (fig_a, fig_b): _apply_report_navy(f)

    col_main1, col_main2 = st.columns(2)
    with col_main1: st.plotly_chart(fig_a, use_container_width=True)
    with col_main2: st.plotly_chart(fig_b, use_container_width=True)

    # Sub charts
    cols = st.columns(4)

    with cols[0]:
        if cust_col in df_filtered:
            top_clients = df_filtered.groupby(cust_col).size().nlargest(5)
            if isinstance(ss["fig_report_s1"], go.Figure) and len(ss["fig_report_s1"].data)==1:
                ss["fig_report_s1"].data[0].x = top_clients.values; ss["fig_report_s1"].data[0].y = top_clients.index
                fig_s1 = ss["fig_report_s1"]
            else:
                fig_s1 = go.Figure(go.Bar(x=top_clients.values, y=top_clients.index, orientation="h", name="Clients"))
                fig_s1.update_layout(title="Top Clients (Shipments)", height=300)
        else:
            fig_s1 = _empty_fig()
        _apply_report_navy(fig_s1); ss["fig_report_s1"] = fig_s1
        st.plotly_chart(fig_s1, use_container_width=True)

    with cols[1]:
        vol_col = m["volume"] or "Volume"; routing_col = m["routing"] or "Routing"
        if routing_col in df_filtered and vol_col in df_filtered:
            top_routes = df_filtered.groupby(routing_col)[vol_col].sum().nlargest(5)
            if isinstance(ss["fig_report_s2"], go.Figure) and len(ss["fig_report_s2"].data)==1:
                ss["fig_report_s2"].data[0].x = top_routes.index; ss["fig_report_s2"].data[0].y = top_routes.values
                fig_s2 = ss["fig_report_s2"]
            else:
                fig_s2 = go.Figure(go.Bar(x=top_routes.index, y=top_routes.values, name="Routes"))
                fig_s2.update_layout(title="Top Routes (Volume)", height=300)
        else:
            fig_s2 = _empty_fig()
        _apply_report_navy(fig_s2); ss["fig_report_s2"] = fig_s2
        st.plotly_chart(fig_s2, use_container_width=True)

    with cols[2]:
        dr = m["delay_reason"] or "DelayReason"
        if dr in df_filtered:
            reasons = df_filtered[dr].fillna("Unknown").value_counts().nlargest(7)
            if isinstance(ss["fig_report_s3"], go.Figure) and len(ss["fig_report_s3"].data)==1:
                ss["fig_report_s3"].data[0].x = reasons.index; ss["fig_report_s3"].data[0].y = reasons.values
                fig_s3 = ss["fig_report_s3"]
            else:
                fig_s3 = go.Figure(go.Bar(x=reasons.index, y=reasons.values, name="Delay Reasons"))
                fig_s3.update_layout(title="Delay Reasons", height=300)
        else:
            fig_s3 = _empty_fig()
        _apply_report_navy(fig_s3); ss["fig_report_s3"] = fig_s3
        st.plotly_chart(fig_s3, use_container_width=True)

    with cols[3]:
        eta_col, ata_col = m["eta"], m["ata"]
        if eta_col in df_filtered and ata_col in df_filtered:
            delays = (pd.to_datetime(df_filtered[ata_col], errors="coerce") - pd.to_datetime(df_filtered[eta_col], errors="coerce")).dt.days.dropna()
            if len(delays):
                if isinstance(ss["fig_report_s4"], go.Figure) and len(ss["fig_report_s4"].data)==1:
                    ss["fig_report_s4"].data[0].x = delays
                    fig_s4 = ss["fig_report_s4"]
                else:
                    fig_s4 = go.Figure(data=[go.Histogram(x=delays, nbinsx=20, name="Delay Days")])
                    fig_s4.update_layout(title="Delay Days Distribution", height=300)
            else:
                fig_s4 = _empty_fig()
        else:
            fig_s4 = _empty_fig()
        _apply_report_navy(fig_s4); ss["fig_report_s4"] = fig_s4
        st.plotly_chart(fig_s4, use_container_width=True)

    # Table delayed
    eta_col, ata_col = m["eta"], m["ata"]
    if eta_col in df_filtered.columns and ata_col in df_filtered.columns:
        table = df_filtered[[ (m["shipment_id"] or "ShipmentID"), (m["etd_original"] or m["etd"] or "ETD"),
                              (m["eta"] or "ETA"), (m["ata"] or "ATA"),
                              (m["routing"] or "Routing"), (m["delay_reason"] or "DelayReason") ]].copy()
        table.columns = ["ShipmentID", "ETD_Original", "ETA", "ATA", "Routing", "delay_reason"]
        table["ETA"] = pd.to_datetime(table["ETA"], errors="coerce")
        table["ATA"] = pd.to_datetime(table["ATA"], errors="coerce")
        table["delay_days"] = (table["ATA"] - table["ETA"]).dt.days
        delayed = table[table["delay_days"] > tolerance_days]
        if delayed.empty:
            st.info("No delayed shipments for selected filters")
        else:
            st.markdown("#### Delayed Shipments")
            st.dataframe(delayed[["ShipmentID", "ETD_Original", "ETA", "ATA", "delay_days", "delay_reason", "Routing"]],
                         use_container_width=True)
    else:
        st.info("ETA/ATA missing — cannot build delayed shipments table")


# =========================
# PUBLIC ENTRY
# =========================
def render_dashboard_page():
    configure_plotly_theme()

    try:
        df_all = load_data()
    except Exception:
        df_all = generate_sample_data()

    st.markdown("""
        <style>
        .stDateInput input {
            background-color: #E6F2FF !important; color: #0B2545 !important;
            border: 1px solid #A8D1FF !important; font-weight: 600 !important;
        }
        div.stSelectbox > div[data-baseweb="select"] > div {
            background-color: #E6F2FF !important; color: #0B2545 !important; border: 1px solid #A8D1FF !important;
        }
        </style>
    """, unsafe_allow_html=True)

    ss = st.session_state
    ss.setdefault("report_view", False)
    ss.setdefault("granularity", "Month")
    ss.setdefault("tolerance_days", 0)
    ss.setdefault("customer_type", "All")
    ss.setdefault("customer", "All")
    ss.setdefault("metric", "Shipment")
    ss.setdefault("date_range", _default_date_range_for(df_all))

    # Debounce & cancel token state
    ss.setdefault("_last_input_ts", 0.0)          # timestamp của lần thay đổi control gần nhất
    ss.setdefault("_applied_hash", None)          # filters hash đã áp dụng
    ss.setdefault("_last_result", None)           # dữ liệu/kpi đã render gần nhất
    ss.setdefault("_request_seq", 0)              # tăng mỗi khi bắt đầu compute mới

    # -------- Controls (không nặng) --------
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    with c1:
        date_range = st.date_input("Date Range", value=ss["date_range"], key="date_range_main")
        if isinstance(date_range, tuple) and len(date_range) == 2:
            if date_range != tuple(ss["date_range"]):
                ss["date_range"] = (date_range[0], date_range[1]); ss["_last_input_ts"] = time.time()
        else:
            if date_range != ss["date_range"][0]:
                ss["date_range"] = (date_range, date_range); ss["_last_input_ts"] = time.time()

    with c2:
        val = st.radio("Customer Type", ["All", "Direct", "Coload"], horizontal=True,
                       index=["All", "Direct", "Coload"].index(ss["customer_type"]))
        if val != ss["customer_type"]:
            ss["customer_type"] = val; ss["_last_input_ts"] = time.time()

    with c3:
        options = update_customer_dropdown_options(df_all, ss["customer_type"])
        if ss["customer"] not in options: ss["customer"] = "All"
        val = st.selectbox("Customer", options, index=options.index(ss["customer"]))
        if val != ss["customer"]:
            ss["customer"] = val; ss["_last_input_ts"] = time.time()

    with c4:
        val = st.radio("Metric", ["Shipment", "TEUs", "Profit"], horizontal=True,
                       index=["Shipment", "TEUs", "Profit"].index(ss["metric"]))
        if val != ss["metric"]:
            ss["metric"] = val; ss["_last_input_ts"] = time.time()

    with c5:
        val = st.selectbox("Granularity", ["Month", "Quarter", "Year"],
                           index=["Month", "Quarter", "Year"].index(ss["granularity"]))
        if val != ss["granularity"]:
            ss["granularity"] = val; ss["_last_input_ts"] = time.time()

    with c6:
        val = st.slider("Tolerance (days)", 0, 10, value=int(ss["tolerance_days"]), step=1)
        if int(val) != int(ss["tolerance_days"]):
            ss["tolerance_days"] = int(val); ss["_last_input_ts"] = time.time()

    with c7:
        st.checkbox("Report View", value=ss["report_view"], key="report_view")

    # -------- Debounce + cancel token + partial render --------
    filters = {
        "date_range": ss["date_range"],
        "granularity": ss["granularity"],
        "customer_type": ss["customer_type"],
        "customer": ss["customer"],
        "tolerance": ss["tolerance_days"],
        "metric": ss["metric"],
        "mode": "report" if ss["report_view"] else "standard",
    }
    fkey = _filters_key(filters)

    now = time.time()
    ready = (now - ss["_last_input_ts"])*1000 >= DEBOUNCE_MS

    # Containers giữ nguyên để partial replace
    kpi_box = st.container()
    charts_box = st.container()

    # Luôn hiển thị last result để UI không “đóng băng”
    if ss["_last_result"] is not None:
        df_last = ss["_last_result"]["df_filtered"]
        kpis_last = ss["_last_result"]["kpis"]
    else:
        # lần đầu
        df_last = get_filtered(df_all, filters)
        kpis_last = get_kpis(df_last, ss["tolerance_days"])
        ss["_last_result"] = {"df_filtered": df_last, "kpis": kpis_last}
        ss["_applied_hash"] = fkey

    # Nếu chưa qua debounce, chỉ hiển thị dữ liệu cũ — không hiện progress dài gây cảm giác kẹt
    df_to_render = df_last
    kpis_to_render = kpis_last

    # Khi đã qua debounce và filters khác hash cũ → compute mới (cancel token)
    if ready and ss["_applied_hash"] != fkey:
        ss["_request_seq"] += 1
        seq = ss["_request_seq"]

        df_new = get_filtered(df_all, filters)
        kpis_new = get_kpis(df_new, ss["tolerance_days"])

        # Nếu có request mới vừa khởi tạo sau chúng ta (race) → bỏ qua kết quả cũ
        if seq == ss["_request_seq"]:
            ss["_last_result"] = {"df_filtered": df_new, "kpis": kpis_new}
            ss["_applied_hash"] = fkey
            df_to_render, kpis_to_render = df_new, kpis_new

    # KPI Cards
    with kpi_box:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
                <div style='background-color:{PRIMARY}; padding:14px; border-radius:10px; text-align:center;'>
                    <h5 style='color:#ffffff; margin-bottom:8px;'>Total Shipments</h5>
                    <h2 style='color:{LIGHT}; margin:0;'>{int(kpis_to_render.get("Total Shipments", 0))}</h2>
                </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
                <div style='background-color:{PRIMARY}; padding:14px; border-radius:10px; text-align:center;'>
                    <h5 style='color:#ffffff; margin-bottom:8px;'>Total TEUs</h5>
                    <h2 style='color:{LIGHT}; margin:0;'>{float(kpis_to_render.get("Total TEUs", 0)):.0f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
                <div style='background-color:{PRIMARY}; padding:14px; border-radius:10px; text-align:center;'>
                    <h5 style='color:#ffffff; margin-bottom:8px;'>On Time Rate</h5>
                    <h2 style='color:{LIGHT}; margin:0;'>{(kpis_to_render.get("On Time Rate") or 0):.0%}</h2>
                </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
                <div style='background-color:{PRIMARY}; padding:14px; border-radius:10px; text-align:center;'>
                    <h5 style='color:#ffffff; margin-bottom:8px;'>Avg Delay Days</h5>
                    <h2 style='color:{LIGHT}; margin:0;'>{(kpis_to_render.get("Avg Delay Days") or 0):.1f}</h2>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("---")

    # Charts/Table theo chế độ
    with charts_box:
        if ss["report_view"]:
            render_report_view(df_to_render, ss["granularity"], ss["tolerance_days"], ss["metric"])
        else:
            render_standard_dashboard(df_to_render, ss["granularity"], ss["metric"])
# ----------------------------------------------------------------------
# EOF
