import plotly.graph_objects as go

# =========================================================
#  DARK NAVY VISUAL THEME - FINAL HIGH CONTRAST VERSION
# =========================================================

PRIMARY_BLUE = "#4DB8FF"     # Đường và cột chính
SECONDARY_BLUE = "#72D0FF"   # Màu phụ
ACCENT_BLUE = "#A3E4FF"      # Màu sáng hơn
TEXT_MAIN = "#F2F8FF"        # Chữ trắng sáng (trục, nhãn)
TEXT_HIGHLIGHT = "#BEE9FF"   # Tiêu đề & legend
BG_DARK = "#0A2E4D"          # Nền navy
GRID_COLOR = "#1F4B73"       # Lưới nhẹ

# === 1. Shipment Over Time ===
def line_chart_volume_profit(x, volume, profit):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=volume, name="Volume",
        mode="lines+markers",
        line=dict(color=PRIMARY_BLUE, width=3),
        marker=dict(size=8, color=ACCENT_BLUE)
    ))
    fig.add_trace(go.Scatter(
        x=x, y=profit, name="Profit",
        mode="lines+markers",
        line=dict(color=SECONDARY_BLUE, width=3),
        marker=dict(size=8, color=SECONDARY_BLUE)
    ))
    fig.update_layout(
        title=dict(text="📈 Shipment Over Time", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        legend=dict(
            font=dict(color=TEXT_HIGHLIGHT, size=12),
            bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        margin=dict(t=50, b=30)
    )
    return fig


# === 2. Direct vs Coload Volume & Profit ===
def bar_chart_direct_coload_volume(df, customer_type_col="Customer Type", volume_col="Volume"):
    grouped = df.groupby(customer_type_col)[volume_col].sum().reindex(["Direct", "Coload"]).fillna(0)
    fig = go.Figure(data=[
        go.Bar(name="Direct", x=["Direct"], y=[grouped["Direct"]], marker_color=PRIMARY_BLUE),
        go.Bar(name="Coload", x=["Coload"], y=[grouped["Coload"]], marker_color=SECONDARY_BLUE)
    ])
    fig.update_layout(
        title=dict(text="📊 Direct vs Coload Volume & Profit", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        showlegend=False,
        xaxis=dict(showgrid=False, color=TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        margin=dict(t=50, b=30)
    )
    return fig


# === 3. Top Clients by Profit ===
def horizontal_bar_top_clients(clients, profits):
    bar_colors = ['#56CCF2', '#4DB8FF', '#72D0FF', '#A3E4FF', '#C9F1FF']
    fig = go.Figure(data=[
        go.Bar(y=clients[::-1], x=profits[::-1], orientation='h', marker_color=bar_colors[::-1])
    ])
    fig.update_layout(
        title=dict(text="🏆 Top 5 Clients by Profit", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        xaxis=dict(gridcolor=GRID_COLOR, color=TEXT_MAIN),
        yaxis=dict(color=TEXT_MAIN),
        legend=dict(font=dict(color=TEXT_HIGHLIGHT, size=12)),
        margin=dict(t=50, b=40)
    )
    return fig


# === 4. Top Destinations by Volume ===
def bar_top_destinations(destinations, volumes):
    bar_colors = ['#4DB8FF', '#5DC4FF', '#72D0FF', '#97E1FF', '#BDEEFF']
    fig = go.Figure(data=[
        go.Bar(x=destinations, y=volumes, marker_color=bar_colors[:len(destinations)])
    ])
    fig.update_layout(
        title=dict(text="🚚 Top Destinations by Shipment Volume", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        xaxis=dict(color=TEXT_MAIN, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        legend=dict(font=dict(color=TEXT_HIGHLIGHT, size=12)),
        margin=dict(t=50, b=40)
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
        title=dict(text="📉 Segment Trend Over Time", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        xaxis=dict(gridcolor=GRID_COLOR, color=TEXT_MAIN),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_MAIN),
        legend=dict(font=dict(color=TEXT_HIGHLIGHT, size=12), bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=50, b=40)
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
        title=dict(text="💹 Profit vs Cost vs Margin", font=dict(color=TEXT_HIGHLIGHT, size=18)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        xaxis=dict(gridcolor=GRID_COLOR, color=TEXT_MAIN),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_MAIN),
        legend=dict(font=dict(color=TEXT_HIGHLIGHT, size=12)),
        margin=dict(t=50, b=40)
    )
    return fig


# === 7. Default Layout Helper ===
def apply_default_layout(fig):
    return fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_MAIN),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_MAIN),
        legend=dict(font=dict(color=TEXT_HIGHLIGHT)),
        margin=dict(t=40)
    )
