"""
app.py  –  Retail Sales Analytics Dashboard
============================================
Run:  streamlit run retail_dashboard/app.py
      (from the workspace root, so the Excel file path resolves correctly)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label { color: #94a3b8 !important; font-size:0.75rem; }

    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }
    .kpi-label { font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
    .kpi-value { font-size: 1.85rem; font-weight: 700; color: #f1f5f9; line-height: 1.1; }

    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #cbd5e1;
        border-left: 3px solid #6366f1; padding-left: 10px;
        margin: 28px 0 16px;
    }

    .block-container { padding-top: 1.5rem !important; }

    [data-testid="stDataFrame"] { border-radius: 8px; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 8px; color: #94a3b8; padding: 6px 18px;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important; color: #fff !important; border-color: #6366f1 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Colour palette ────────────────────────────────────────────────────────────
PALETTE = [
    "#6366f1", "#22d3ee", "#34d399", "#f59e0b",
    "#f87171", "#a78bfa", "#fb923c", "#38bdf8"
]

PLOTLY_THEME = dict(
    plot_bgcolor="#1e293b",
    paper_bgcolor="#1e293b",
    font_color="#cbd5e1",
    font_family="Inter, system-ui, sans-serif",
    colorway=PALETTE,
    xaxis=dict(gridcolor="#334155", zeroline=False),
    yaxis=dict(gridcolor="#334155", zeroline=False),
    margin=dict(t=40, b=30, l=10, r=10),
)

# legend is kept OUTSIDE PLOTLY_THEME so any caller can pass legend= freely
_LEGEND_DEFAULT = dict(
    bgcolor="rgba(0,0,0,0)",
    bordercolor="#334155"
)


def apply_theme(fig):
    fig.update_layout(**PLOTLY_THEME)
    fig.update_layout(legend=_LEGEND_DEFAULT)
    return fig


def fmt_inr(v: float) -> str:
    """Format number as Indian Rupees in Lakhs / Crores."""
    if abs(v) >= 1e7:
        return f"₹{v/1e7:.2f} Cr"
    if abs(v) >= 1e5:
        return f"₹{v/1e5:.1f} L"
    return f"₹{v:,.0f}"


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading & processing data…")
def get_data():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from data_processor import load_data
    return load_data()


data = get_data()
sales_df    = data["sales"]
kpis        = data["kpis"]
monthly     = data["monthly_trend"]
cat_perf    = data["category_perf"]
reg_perf    = data["region_perf"]
chan_perf   = data["channel_perf"]
seg_perf    = data["segment_perf"]
top_prod    = data["top_products"]
rep_perf    = data["rep_perf"]
pay_mix     = data["payment_mix"]
city_sales  = data["city_sales"]
profit_dist = data["profit_dist"]


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR  –  Filters
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🛍️ Retail Analytics")
    st.markdown("---")

    years = sorted(sales_df["Year"].dropna().unique().tolist())
    sel_years = st.multiselect("📅 Year", years, default=years)

    regions = sorted(sales_df["Region"].dropna().unique().tolist())
    sel_regions = st.multiselect("🗺️ Region", regions, default=regions)

    categories = sorted(sales_df["Category"].dropna().unique().tolist())
    sel_cats = st.multiselect("📦 Category", categories, default=categories)

    segments = sorted(sales_df["Segment"].dropna().unique().tolist())
    sel_segs = st.multiselect("👥 Segment", segments, default=segments)

    channels = sorted(sales_df["Sales_Channel"].dropna().unique().tolist())
    sel_chan = st.multiselect("📡 Channel", channels, default=channels)

    st.markdown("---")
    st.markdown("<span style='color:#475569;font-size:0.72rem;'>Built with Streamlit + Plotly</span>",
                unsafe_allow_html=True)


# ── Apply global filters ──────────────────────────────────────────────────────
mask = (
    sales_df["Year"].isin(sel_years) &
    sales_df["Region"].isin(sel_regions) &
    sales_df["Category"].isin(sel_cats) &
    sales_df["Segment"].isin(sel_segs) &
    sales_df["Sales_Channel"].isin(sel_chan)
)
fdf = sales_df[mask].copy()


def compute_kpis(df):
    rev  = df["Sales_Amount"].sum()
    prof = df["Profit"].sum()
    return {
        "total_revenue":     float(rev),
        "total_profit":      float(prof),
        "total_orders":      int(df["Order_ID"].nunique()),
        "total_customers":   int(df["Customer_ID"].nunique()),
        "avg_order_value":   float(df["Sales_Amount"].mean()) if len(df) else 0,
        "avg_profit_margin": float((prof / rev * 100)) if rev else 0,
        "avg_ship_days":     float(df["Ship_Days"].dropna().mean()) if len(df) else 0,
        "total_quantity":    int(df["Quantity"].sum()),
    }


fkpis = compute_kpis(fdf)


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(90deg,#4f46e5,#0ea5e9);
            border-radius:14px;padding:22px 28px;margin-bottom:24px;">
  <h1 style="color:#fff;margin:0;font-size:1.8rem;font-weight:800;letter-spacing:-0.02em;">
    🛍️ Retail Sales Analytics Dashboard
  </h1>
  <p style="color:#c7d2fe;margin:4px 0 0;font-size:0.9rem;">
    End-to-end performance &amp; profitability analytics · India Market
  </p>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ═════════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)

kpi_configs = [
    (c1, "💰 Revenue",       fmt_inr(fkpis["total_revenue"])),
    (c2, "📈 Profit",        fmt_inr(fkpis["total_profit"])),
    (c3, "🛒 Orders",        f"{fkpis['total_orders']:,}"),
    (c4, "👤 Customers",     f"{fkpis['total_customers']:,}"),
    (c5, "🧾 Avg Order",     fmt_inr(fkpis["avg_order_value"])),
    (c6, "📊 Profit Margin", f"{fkpis['avg_profit_margin']:.1f}%"),
    (c7, "📦 Qty Sold",      f"{fkpis['total_quantity']:,}"),
    (c8, "🚚 Avg Ship Days", f"{fkpis['avg_ship_days']:.1f}d"),
]

for col, label, value in kpi_configs:
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends", "🗺️ Geography", "📦 Products & Categories",
    "👥 Segments & Channels", "🏆 Leaderboard"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – TRENDS
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Monthly Revenue & Profit Trend</div>',
                unsafe_allow_html=True)

    mf = (fdf.groupby(["Year", "Month", "Month_Name", "YearMonth"], as_index=False)
          .agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique"))
          .sort_values(["Year", "Month"]))

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(go.Bar(
        x=mf["YearMonth"], y=mf["Revenue"],
        name="Revenue", marker_color="#6366f1", opacity=0.85
    ), secondary_y=False)
    fig_trend.add_trace(go.Scatter(
        x=mf["YearMonth"], y=mf["Profit"],
        name="Profit", line=dict(color="#34d399", width=2.5),
        mode="lines+markers", marker=dict(size=5)
    ), secondary_y=True)
    fig_trend.update_yaxes(title_text="Revenue (₹)", secondary_y=False,
                           gridcolor="#334155", tickfont_color="#94a3b8")
    fig_trend.update_yaxes(title_text="Profit (₹)", secondary_y=True,
                           gridcolor="rgba(0,0,0,0)", tickfont_color="#94a3b8")
    fig_trend.update_xaxes(tickangle=45, tickfont_color="#94a3b8", gridcolor="#334155")
    fig_trend.update_layout(**PLOTLY_THEME, title_text="Monthly Revenue & Profit", height=360)
    fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_trend, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Revenue by Day of Week</div>',
                    unsafe_allow_html=True)
        dow_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
        dow_df = (fdf.assign(DOW=fdf["Order_Date"].dt.dayofweek)
                  .groupby("DOW", as_index=False)
                  .agg(Revenue=("Sales_Amount", "sum"))
                  .sort_values("DOW"))
        dow_df["Day"] = dow_df["DOW"].map(dow_map)
        fig_dow = px.bar(dow_df, x="Day", y="Revenue",
                         color="Revenue", color_continuous_scale=["#312e81", "#6366f1", "#a5b4fc"],
                         title="Revenue by Day of Week")
        fig_dow.update_coloraxes(showscale=False)
        apply_theme(fig_dow)
        fig_dow.update_layout(height=300)
        st.plotly_chart(fig_dow, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Orders vs Avg Order Value</div>',
                    unsafe_allow_html=True)
        scatter_df = (fdf.groupby("YearMonth", as_index=False)
                      .agg(Orders=("Order_ID", "nunique"),
                           AvgOrderVal=("Sales_Amount", "mean"),
                           Revenue=("Sales_Amount", "sum")))
        fig_scat = px.scatter(scatter_df, x="Orders", y="AvgOrderVal",
                              size="Revenue", color="Revenue",
                              color_continuous_scale=["#1e40af", "#6366f1", "#a5b4fc"],
                              hover_name="YearMonth",
                              title="Orders vs Avg Order Value (bubble=Revenue)")
        apply_theme(fig_scat)
        fig_scat.update_layout(height=300, coloraxis_showscale=False)
        st.plotly_chart(fig_scat, use_container_width=True)

    st.markdown('<div class="section-title">Rolling 3-Month Profit Margin</div>',
                unsafe_allow_html=True)
    mf2 = mf.copy()
    mf2["Margin"] = (mf2["Profit"] / mf2["Revenue"] * 100).replace([np.inf, -np.inf], 0)
    mf2["Rolling_Margin"] = mf2["Margin"].rolling(3, min_periods=1).mean()
    fig_margin = go.Figure()
    fig_margin.add_trace(go.Scatter(
        x=mf2["YearMonth"], y=mf2["Margin"],
        name="Monthly Margin %", line=dict(color="#94a3b8", dash="dot", width=1.5),
        mode="lines"
    ))
    fig_margin.add_trace(go.Scatter(
        x=mf2["YearMonth"], y=mf2["Rolling_Margin"],
        name="3M Rolling Avg", line=dict(color="#f59e0b", width=2.5),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.1)"
    ))
    fig_margin.add_hline(y=0, line_dash="dash", line_color="#f87171", line_width=1.5,
                         annotation_text="Break-even", annotation_position="bottom right")
    apply_theme(fig_margin)
    fig_margin.update_layout(height=280, title_text="Profit Margin % over Time")
    st.plotly_chart(fig_margin, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – GEOGRAPHY
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown('<div class="section-title">Revenue by Region</div>', unsafe_allow_html=True)
        rp = (fdf.groupby("Region", as_index=False)
              .agg(Revenue=("Sales_Amount", "sum"),
                   Profit=("Profit", "sum"),
                   Orders=("Order_ID", "nunique"))
              .assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100).round(1))
              .sort_values("Revenue", ascending=True))
        fig_reg = go.Figure(go.Bar(
            x=rp["Revenue"], y=rp["Region"],
            orientation="h",
            marker=dict(
                color=rp["Revenue"],
                colorscale=[[0, "#312e81"], [0.5, "#6366f1"], [1, "#a5b4fc"]],
                showscale=False,
                cornerradius=6,
            ),
            text=[fmt_inr(v) for v in rp["Revenue"]],
            textposition="outside",
        ))
        apply_theme(fig_reg)
        fig_reg.update_layout(height=300, title_text="Revenue by Region")
        st.plotly_chart(fig_reg, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Profit Margin by Region</div>', unsafe_allow_html=True)
        rp_sorted = rp.sort_values("Margin")
        colors = ["#f87171" if m < 0 else "#34d399" for m in rp_sorted["Margin"]]
        fig_pm = go.Figure(go.Bar(
            x=rp_sorted["Margin"], y=rp_sorted["Region"],
            orientation="h",
            marker_color=colors,
            text=[f"{m:.1f}%" for m in rp_sorted["Margin"]],
            textposition="outside",
        ))
        apply_theme(fig_pm)
        fig_pm.update_layout(height=300, title_text="Profit Margin % by Region")
        st.plotly_chart(fig_pm, use_container_width=True)

    st.markdown('<div class="section-title">Top 15 Cities by Revenue</div>', unsafe_allow_html=True)
    city_df = (fdf.groupby(["City", "Region"], as_index=False)
               .agg(Revenue=("Sales_Amount", "sum"),
                    Profit=("Profit", "sum"),
                    Orders=("Order_ID", "nunique"))
               .nlargest(15, "Revenue"))
    fig_city = px.bar(city_df, x="City", y="Revenue",
                      color="Region", barmode="group",
                      color_discrete_sequence=PALETTE,
                      title="Top 15 Cities by Revenue",
                      hover_data={"Profit": True, "Orders": True})
    apply_theme(fig_city)
    fig_city.update_layout(height=350, xaxis_tickangle=35)
    st.plotly_chart(fig_city, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Region × Category Heat Map</div>', unsafe_allow_html=True)
        heat = (fdf.groupby(["Region", "Category"], as_index=False)
                .agg(Revenue=("Sales_Amount", "sum")))
        pivot = heat.pivot(index="Region", columns="Category", values="Revenue").fillna(0)
        fig_heat = px.imshow(pivot,
                             color_continuous_scale=["#0f172a", "#312e81", "#6366f1", "#a5b4fc"],
                             title="Revenue Heat Map: Region × Category",
                             aspect="auto")
        apply_theme(fig_heat)
        fig_heat.update_layout(height=300)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Orders by Region & Channel</div>', unsafe_allow_html=True)
        rc = (fdf.groupby(["Region", "Sales_Channel"], as_index=False)
              .agg(Orders=("Order_ID", "nunique")))
        fig_rc = px.bar(rc, x="Region", y="Orders", color="Sales_Channel",
                        barmode="stack", color_discrete_sequence=PALETTE,
                        title="Orders Split by Channel per Region")
        apply_theme(fig_rc)
        fig_rc.update_layout(height=300)
        st.plotly_chart(fig_rc, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 – PRODUCTS & CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Category Revenue Share</div>', unsafe_allow_html=True)
        cp = (fdf.groupby("Category", as_index=False)
              .agg(Revenue=("Sales_Amount", "sum"),
                   Profit=("Profit", "sum")))
        fig_donut = go.Figure(go.Pie(
            labels=cp["Category"], values=cp["Revenue"],
            hole=0.55,
            marker=dict(colors=PALETTE, line=dict(color="#0f172a", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Revenue: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>"
        ))
        fig_donut.update_layout(**PLOTLY_THEME, height=340, title_text="Revenue by Category",
                                annotations=[dict(text="Category", x=0.5, y=0.5,
                                                  font_size=14, font_color="#cbd5e1", showarrow=False)])
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Category Profit Margin</div>', unsafe_allow_html=True)
        cp2 = cp.assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100).round(1)).sort_values("Margin")
        colors_cat = ["#f87171" if m < 0 else "#34d399" for m in cp2["Margin"]]
        fig_cpm = go.Figure(go.Bar(
            x=cp2["Margin"], y=cp2["Category"], orientation="h",
            marker_color=colors_cat,
            text=[f"{m:.1f}%" for m in cp2["Margin"]], textposition="outside"
        ))
        apply_theme(fig_cpm)
        fig_cpm.update_layout(height=340, title_text="Profit Margin % by Category")
        st.plotly_chart(fig_cpm, use_container_width=True)

    st.markdown('<div class="section-title">Top 10 Products by Revenue</div>', unsafe_allow_html=True)
    tp = (fdf.groupby("Product_Name", as_index=False)
          .agg(Revenue=("Sales_Amount", "sum"),
               Profit=("Profit", "sum"),
               Orders=("Order_ID", "nunique"))
          .assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100).round(1))
          .nlargest(10, "Revenue"))
    fig_toprod = px.bar(tp, x="Revenue", y="Product_Name",
                        orientation="h", color="Margin",
                        color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                        title="Top 10 Products (colour = Profit Margin %)",
                        hover_data={"Orders": True, "Profit": True})
    apply_theme(fig_toprod)
    fig_toprod.update_layout(height=380, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_toprod, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Revenue vs Profit by Category</div>', unsafe_allow_html=True)
        fig_bubble = px.scatter(cp.assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100)),
                                x="Revenue", y="Profit",
                                size="Revenue", color="Category",
                                color_discrete_sequence=PALETTE,
                                text="Category",
                                title="Revenue vs Profit (bubble=Revenue)")
        fig_bubble.update_traces(textposition="top center", textfont_size=10)
        apply_theme(fig_bubble)
        fig_bubble.update_layout(height=330, showlegend=False)
        st.plotly_chart(fig_bubble, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Discount Distribution by Category</div>', unsafe_allow_html=True)
        fig_box = px.box(fdf, x="Category", y="Discount",
                         color="Category",
                         color_discrete_sequence=PALETTE,
                         title="Discount % Distribution per Category")
        apply_theme(fig_box)
        fig_box.update_layout(height=330, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown('<div class="section-title">Quantity Sold by Category Over Time</div>', unsafe_allow_html=True)
    qty_time = (fdf.groupby(["YearMonth", "Category"], as_index=False)
                .agg(Qty=("Quantity", "sum")))
    fig_qty = px.area(qty_time, x="YearMonth", y="Qty", color="Category",
                      color_discrete_sequence=PALETTE,
                      title="Monthly Quantity Sold by Category")
    apply_theme(fig_qty)
    fig_qty.update_layout(height=300, xaxis_tickangle=45)
    st.plotly_chart(fig_qty, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 – SEGMENTS & CHANNELS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Revenue by Customer Segment</div>', unsafe_allow_html=True)
        sp = (fdf.groupby("Segment", as_index=False)
              .agg(Revenue=("Sales_Amount", "sum"),
                   Profit=("Profit", "sum"),
                   Orders=("Order_ID", "nunique"))
              .assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100).round(1)))
        fig_seg = go.Figure(go.Pie(
            labels=sp["Segment"], values=sp["Revenue"],
            hole=0.5,
            marker=dict(colors=[PALETTE[0], PALETTE[2], PALETTE[3]],
                        line=dict(color="#0f172a", width=2)),
            textinfo="label+percent"
        ))
        fig_seg.update_layout(**PLOTLY_THEME, height=320, title_text="Revenue by Segment",
                              annotations=[dict(text="Segment", x=0.5, y=0.5,
                                               font_size=12, font_color="#cbd5e1", showarrow=False)])
        st.plotly_chart(fig_seg, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Sales Channel Revenue & Orders</div>', unsafe_allow_html=True)
        chp = (fdf.groupby("Sales_Channel", as_index=False)
               .agg(Revenue=("Sales_Amount", "sum"),
                    Orders=("Order_ID", "nunique")))
        fig_chan = make_subplots(specs=[[{"secondary_y": True}]])
        fig_chan.add_trace(go.Bar(
            x=chp["Sales_Channel"], y=chp["Revenue"],
            name="Revenue", marker_color=PALETTE[0], opacity=0.85
        ), secondary_y=False)
        fig_chan.add_trace(go.Scatter(
            x=chp["Sales_Channel"], y=chp["Orders"],
            name="Orders", mode="markers+lines",
            marker=dict(color=PALETTE[2], size=10),
            line=dict(color=PALETTE[2])
        ), secondary_y=True)
        fig_chan.update_layout(**PLOTLY_THEME, height=320, title_text="Channel Revenue & Orders")
        fig_chan.update_layout(legend=_LEGEND_DEFAULT)
        st.plotly_chart(fig_chan, use_container_width=True)

    st.markdown('<div class="section-title">Segment × Region Revenue Heat Map</div>', unsafe_allow_html=True)
    sr = (fdf.groupby(["Segment", "Region"], as_index=False)
          .agg(Revenue=("Sales_Amount", "sum")))
    pvt = sr.pivot(index="Segment", columns="Region", values="Revenue").fillna(0)
    fig_sr = px.imshow(pvt, color_continuous_scale=["#0f172a", "#312e81", "#6366f1", "#a5b4fc"],
                       title="Revenue: Segment × Region", aspect="auto",
                       text_auto=".2s")
    apply_theme(fig_sr)
    fig_sr.update_layout(height=280)
    st.plotly_chart(fig_sr, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Payment Method Mix</div>', unsafe_allow_html=True)
        pm = (fdf.groupby("Payment_Method", as_index=False)
              .agg(Revenue=("Sales_Amount", "sum"),
                   Orders=("Order_ID", "nunique")))
        fig_pm2 = px.pie(pm, values="Revenue", names="Payment_Method",
                         color_discrete_sequence=PALETTE,
                         title="Revenue Share by Payment Method")
        apply_theme(fig_pm2)
        fig_pm2.update_layout(height=320)
        st.plotly_chart(fig_pm2, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Segment Profit Margin Comparison</div>', unsafe_allow_html=True)
        sp2 = (fdf.groupby(["Segment", "Category"], as_index=False)
               .agg(Revenue=("Sales_Amount", "sum"),
                    Profit=("Profit", "sum")))
        sp2["Margin"] = (sp2["Profit"] / sp2["Revenue"] * 100).round(1)
        fig_seg2 = px.bar(sp2, x="Segment", y="Margin", color="Category",
                          barmode="group", color_discrete_sequence=PALETTE,
                          title="Profit Margin by Segment & Category")
        apply_theme(fig_seg2)
        fig_seg2.update_layout(height=320)
        st.plotly_chart(fig_seg2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 – LEADERBOARD
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Sales Rep Leaderboard</div>', unsafe_allow_html=True)

    rp_df = (fdf.groupby("Sales_Rep", as_index=False)
             .agg(Revenue=("Sales_Amount", "sum"),
                  Profit=("Profit", "sum"),
                  Orders=("Order_ID", "nunique"),
                  Customers=("Customer_ID", "nunique"))
             .assign(Margin=lambda d: (d["Profit"] / d["Revenue"] * 100).round(1))
             .sort_values("Revenue", ascending=False))

    col1, col2 = st.columns([1.4, 0.6])

    with col1:
        fig_rep = go.Figure(go.Bar(
            x=rp_df["Revenue"], y=rp_df["Sales_Rep"],
            orientation="h",
            marker=dict(
                color=rp_df["Revenue"],
                colorscale=[[0, "#312e81"], [1, "#a5b4fc"]],
                showscale=False,
            ),
            text=[fmt_inr(v) for v in rp_df["Revenue"]],
            textposition="outside",
        ))
        apply_theme(fig_rep)
        fig_rep.update_layout(
            height=max(300, len(rp_df) * 38),
            title_text="Revenue by Sales Rep",
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_rep, use_container_width=True)

    with col2:
        rp_show = rp_df.copy()
        rp_show["Revenue"] = rp_show["Revenue"].apply(fmt_inr)
        rp_show["Profit"]  = rp_show["Profit"].apply(fmt_inr)
        rp_show["Margin"]  = rp_show["Margin"].astype(str) + "%"
        st.dataframe(
            rp_show[["Sales_Rep", "Revenue", "Profit", "Margin", "Orders", "Customers"]]
            .rename(columns={"Sales_Rep": "Rep", "Customers": "Cust."}),
            use_container_width=True,
            hide_index=True,
            height=max(300, len(rp_df) * 38),
        )

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-title">Rep Performance Radar</div>', unsafe_allow_html=True)
        rp_radar = rp_df.nlargest(8, "Revenue")
        categories_r = ["Revenue", "Profit", "Orders", "Customers"]
        rp_norm = rp_radar[categories_r].copy()
        for c in categories_r:
            mn, mx = rp_norm[c].min(), rp_norm[c].max()
            rp_norm[c] = ((rp_norm[c] - mn) / (mx - mn + 1e-9)) * 100
        fig_radar = go.Figure()
        for i, row in rp_norm.iterrows():
            name = rp_radar.loc[i, "Sales_Rep"]
            fig_radar.add_trace(go.Scatterpolar(
                r=row[categories_r].tolist() + [row[categories_r[0]]],
                theta=categories_r + [categories_r[0]],
                fill="toself", name=name,
                line=dict(width=1.5),
                opacity=0.7
            ))
        apply_theme(fig_radar)
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#1e293b",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155"),
                angularaxis=dict(gridcolor="#334155")
            ),
            height=380,
            title_text="Normalised Performance Radar (Top 8 Reps)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col4:
        st.markdown('<div class="section-title">Revenue vs Profit Scatter (Reps)</div>', unsafe_allow_html=True)
        fig_rep_scat = px.scatter(rp_df, x="Revenue", y="Profit",
                                  size="Orders", color="Margin",
                                  color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
                                  text="Sales_Rep",
                                  title="Revenue vs Profit per Rep (bubble=Orders)")
        fig_rep_scat.update_traces(textposition="top center", textfont_size=9)
        apply_theme(fig_rep_scat)
        fig_rep_scat.update_layout(height=380)
        st.plotly_chart(fig_rep_scat, use_container_width=True)

    # ── Full Data Explorer ─────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 Filtered Data Explorer</div>', unsafe_allow_html=True)

    disp_cols = ["Order_ID", "Order_Date", "Customer_Name", "Segment", "Region", "City",
                 "Category", "Product_Name", "Quantity", "Sales_Amount", "Cost_Amount",
                 "Profit", "Profit_Margin", "Discount", "Payment_Method", "Sales_Channel", "Sales_Rep"]
    disp = fdf[disp_cols].copy()
    disp["Sales_Amount"]  = disp["Sales_Amount"].round(0)
    disp["Profit"]        = disp["Profit"].round(0)
    disp["Profit_Margin"] = disp["Profit_Margin"].round(1)
    disp["Discount"]      = (disp["Discount"] * 100).round(1).astype(str) + "%"

    st.dataframe(
        disp.sort_values("Order_Date", ascending=False).head(500),
        use_container_width=True,
        hide_index=True,
        height=350,
        column_config={
            "Order_Date":    st.column_config.DateColumn("Order Date"),
            "Sales_Amount":  st.column_config.NumberColumn("Revenue", format="₹%,.0f"),
            "Cost_Amount":   st.column_config.NumberColumn("Cost",    format="₹%,.0f"),
            "Profit":        st.column_config.NumberColumn("Profit",  format="₹%,.0f"),
            "Profit_Margin": st.column_config.NumberColumn("Margin%"),
        }
    )

    csv_data = disp.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Data (CSV)",
        data=csv_data,
        file_name="retail_sales_filtered.csv",
        mime="text/csv",
    )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#475569;font-size:0.72rem;
            border-top:1px solid #1e293b;margin-top:32px;padding-top:12px;">
  🛍️ Retail Sales Analytics Dashboard · Built with Python, Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
