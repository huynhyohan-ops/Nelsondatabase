import plotly.graph_objects as go

# =========================================================
#  DARK NAVY VISUAL THEME - ENHANCED CONTRAST
# =========================================================

PRIMARY_BLUE = "#4DB8FF"     # Xanh sáng (đường chính)
SECONDARY_BLUE = "#86D1FF"   # Xanh trung nhạt
HIGHLIGHT_BLUE = "#A3E4FF"   # Xanh ánh sáng
AXIS_TEXT = "#E8F4FF"        # Chữ trục sáng hơn
BG_DARK = "#0A2E4D"          # Nền navy đậm
GRID_COLOR = "#1C446E"       # Lưới mềm dịu

# === 1. Line Chart Volume & Profit ===
def line_chart_volume_profit(x, volume, profit):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=volume, name="Volume",
                             mode="lines+markers", line=dict(color=PRIMARY_BLUE, width=3),
                             marker=dict(size=8, color=HIGHLIGHT_BLUE)))
    fig.add_trace(go.Scatter(x=x, y=profit, name="Profit",
                             mode="lines+markers", line=dict(color=SECONDARY_BLUE, width=3),
                             marker=dict(size=8, color=SECONDARY_BLUE)))
    fig.update_layout(
        title="📈 Shipment Over Time",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(t=40, b=20)
    )
    return fig


# === 2. Direct vs Coload ===
def bar_chart_direct_coload_volume(df, customer_type_col="Customer Type", volume_col="Volume"):
    grouped = df.groupby(customer_type_col)[volume_col].sum().reindex(["Direct", "Coload"]).fillna(0)
    fig = go.Figure(data=[
        go.Bar(name="Direct", x=["Direct"], y=[grouped["Direct"]], marker_color=PRIMARY_BLUE),
        go.Bar(name="Coload", x=["Coload"], y=[grouped["Coload"]], marker_color=SECONDARY_BLUE)
    ])
    fig.update_layout(
        title="📊 Direct vs Coload Volume & Profit",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        showlegend=False,
        xaxis=dict(showgrid=False, color=AXIS_TEXT),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(t=40, b=20)
    )
    return fig


# === 3. Top Clients by Profit ===
def horizontal_bar_top_clients(clients, profits):
    bar_colors = ['#56CCF2', '#4DB8FF', '#86D1FF', '#A3E4FF', '#C9F1FF']
    fig = go.Figure(data=[
        go.Bar(y=clients[::-1], x=profits[::-1], orientation='h', marker_color=bar_colors[::-1])
    ])
    fig.update_layout(
        title="🏆 Top 5 Clients by Profit",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(color=AXIS_TEXT),
        margin=dict(t=30, b=30)
    )
    return fig


# === 4. Top Destinations by Volume ===
def bar_top_destinations(destinations, volumes):
    bar_colors = ['#4DB8FF', '#5DC4FF', '#72D0FF', '#97E1FF', '#BDEEFF']
    fig = go.Figure(data=[
        go.Bar(x=destinations, y=volumes, marker_color=bar_colors[:len(destinations)])
    ])
    fig.update_layout(
        title="🚚 Top Destinations by Shipment Volume",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(color=AXIS_TEXT, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(t=30, b=30)
    )
    return fig


# === 5. Segment Trend Over Time ===
def stacked_area_segment_trend(months, data_dict):
    color_cycle = ['#4DB8FF', '#5DC4FF', '#72D0FF', '#97E1FF', '#BDEEFF']
    fig = go.Figure()
    for i, (segment, values) in enumerate(data_dict.items()):
        fig.add_trace(go.Scatter(
            x=months,
            y=values,
            stackgroup='one',
            name=segment,
            line=dict(color=color_cycle[i % len(color_cycle)], width=2)
        ))
    fig.update_layout(
        title="📉 Segment Trend Over Time",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR),
        margin=dict(t=30, b=30)
    )
    return fig


# === 6. Profit vs Cost vs Margin ===
def group_bar_profit_cost_margin(x, profit, cost, margin):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Profit", x=x, y=profit, marker_color="#4DB8FF"))
    fig.add_trace(go.Bar(name="Cost", x=x, y=cost, marker_color="#72D0FF"))
    fig.add_trace(go.Bar(name="Margin", x=x, y=margin, marker_color="#BDEEFF"))
    fig.update_layout(
        barmode='group',
        title="💹 Profit vs Cost vs Margin",
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(gridcolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR),
        margin=dict(t=30, b=30)
    )
    return fig


# === 7. Layout chung ===
def apply_default_layout(fig):
    return fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=AXIS_TEXT),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        margin=dict(t=30)
    )
