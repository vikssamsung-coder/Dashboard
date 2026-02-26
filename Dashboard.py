# Dashbaord.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

# -----------------------------
# Page config + light "PowerBI-ish" styling
# -----------------------------
st.set_page_config(
    page_title="Digital Marketing Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      .kpi-card {
        border: 1px solid #D9E2EF;
        border-radius: 10px;
        padding: 12px 14px;
        background: #FFFFFF;
        height: 110px;
      }
      .kpi-title { font-size: 12px; font-weight: 700; color: #1f2a44; }
      .kpi-value { font-size: 26px; font-weight: 800; margin-top: 2px; }
      .kpi-sub   { font-size: 12px; color: #6b778c; margin-top: -2px; }
      .kpi-delta { font-size: 12px; font-weight: 700; }
      .panel {
        border: 1px solid #D9E2EF;
        border-radius: 10px;
        padding: 10px 12px;
        background: #FFFFFF;
      }
      .panel-title { font-size: 13px; font-weight: 800; color: #1f2a44; margin-bottom: 6px; }
      div[data-testid="stDateInput"] label,
      div[data-testid="stSelectbox"] label { font-weight: 700 !important; color: #1f2a44 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Demo data generators (replace with your real dataset later)
# -----------------------------
@st.cache_data
def make_demo_data(start_dt: date, end_dt: date):
    dates = pd.date_range(start_dt, end_dt, freq="MS")
    if len(dates) < 3:
        dates = pd.date_range(start_dt, end_dt + timedelta(days=60), freq="MS")

    rng = np.random.default_rng(42)

    spend = np.clip(rng.normal(35, 12, size=len(dates)), 8, None) * 1000
    revenue = spend * np.clip(rng.normal(2.2, 0.6, size=len(dates)), 0.8, None)

    traffic = np.clip(rng.normal(8000, 1400, size=len(dates)), 2000, None).astype(int)
    ctr = np.clip(rng.normal(0.25, 0.05, size=len(dates)), 0.08, 0.45)
    conv_rate = np.clip(rng.normal(0.14, 0.03, size=len(dates)), 0.05, 0.25)

    clicks = (traffic * ctr).astype(int)
    leads = (clicks * np.clip(rng.normal(0.75, 0.08, size=len(dates)), 0.4, 0.95)).astype(int)
    sales = (leads * conv_rate).astype(int)
    cpa = np.clip(spend / np.maximum(sales, 1), 0.5, None)

    df_ts = pd.DataFrame({
        "month": dates,
        "spend": spend,
        "revenue": revenue,
        "traffic": traffic,
        "ctr": ctr,
        "conversion_rate": conv_rate,
        "clicks": clicks,
        "leads": leads,
        "sales": sales,
        "cpa": cpa
    })

    age_brackets = ["10-20", "20-30", "30-40", "40-50", "50-60", "60+"]
    age_values = np.clip(rng.normal([3, 4, 2, 6, 4, 2], 0.6), 0.6, None) * 1000
    df_age = pd.DataFrame({"age": age_brackets, "website_traffic": age_values.astype(int)})

    channels = ["Facebook", "Insta.", "Twitter", "Youtube", "LinkedIn"]
    metrics = ["Traffic", "Clicks", "Interact", "Share"]
    mat = np.clip(rng.normal(60, 22, size=(len(metrics), len(channels))), 5, 100).astype(int)
    df_heat = pd.DataFrame(mat, index=metrics, columns=channels).reset_index().rename(columns={"index": "Metric"})

    campaigns = ["Tech Trends Takeoff", "Eco-Friendly Futures", "Accelerate 2025", "Vision 360"]
    df_campaign = pd.DataFrame({
        "Campaign Name": campaigns,
        "Clicks": rng.integers(800, 90000, size=len(campaigns)),
        "Spend": np.round(rng.normal(800, 900, size=len(campaigns)).clip(50, None), 0).astype(int),
        "Revenue": np.round(rng.normal(2200, 1800, size=len(campaigns)).clip(90, None), 0).astype(int),
    })
    return df_ts, df_age, df_heat, df_campaign

def fmt_k(value, currency=False, decimals=1):
    sign = "$" if currency else ""
    if abs(value) >= 1000:
        return f"{sign}{value/1000:.{decimals}f}K"
    return f"{sign}{value:.0f}"

def delta_text(curr, prev, is_percent=False, currency=False):
    pct = 0.0 if prev == 0 else (curr - prev) / prev * 100.0
    arrow = "▲" if pct >= 0 else "▼"
    color = "#2E7D32" if pct >= 0 else "#C62828"
    if is_percent:
        vs_line = f"vs prev {prev*100:.1f}% ({pct:+.1f}%) {arrow}"
    else:
        vs_line = f"vs prev {fmt_k(prev, currency=currency)} ({pct:+.1f}%) {arrow}"
    return vs_line, color

def mini_bar(curr, prev):
    mx = max(curr, prev, 1e-9)
    return [prev/mx, curr/mx]

def kpi_card(title, curr, prev, value_format="k", currency=False, is_percent=False):
    if is_percent:
        v = f"{curr*100:.1f}%"
    elif value_format == "k":
        v = fmt_k(curr, currency=currency)
    else:
        v = f"{curr:.2f}" if isinstance(curr, float) else f"{curr}"

    vs_line, color = delta_text(curr, prev, is_percent=is_percent, currency=currency)
    bars = mini_bar(curr, prev)

    st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{v}</div>
          <div class="kpi-sub">
            <span class="kpi-delta" style="color:{color};">{vs_line}</span>
          </div>
        </div>
    """, unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Previous"], y=[bars[0]], marker=dict(opacity=0.6)))
    fig.add_trace(go.Bar(x=["Current"], y=[bars[1]]))
    fig.update_layout(
        height=60, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[0, 1.05]),
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# -----------------------------
# Header + Filters
# -----------------------------
left, mid, right = st.columns([2.2, 5.5, 2.3], vertical_alignment="center")
with left:
    st.markdown("### **Mokkup.ai**")
with mid:
    st.markdown("## **DIGITAL MARKETING DASHBOARD**")
with right:
    c1, c2 = st.columns(2)
    with c1:
        start_dt = st.date_input("Start date", value=date(2024, 1, 1))
    with c2:
        end_dt = st.date_input("End date", value=date(2025, 6, 30))

df_ts, df_age, df_heat, df_campaign = make_demo_data(start_dt, end_dt)

f1, f2, f3, f4 = st.columns([2.2, 2.2, 2.2, 3.4], vertical_alignment="center")
with f3:
    channel_type = st.selectbox("Channel Type", ["Organic", "Paid", "Referral", "All"], index=0)
with f4:
    campaign = st.selectbox("Campaign", ["All"] + df_campaign["Campaign Name"].tolist(), index=0)

# (Placeholder filter hook for future real data)
df_sorted = df_ts.sort_values("month").reset_index(drop=True)
curr_row = df_sorted.iloc[-1]
prev_row = df_sorted.iloc[-2] if len(df_sorted) >= 2 else curr_row

# -----------------------------
# KPI row
# -----------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6, gap="small")
with k1:
    kpi_card("Total Spend", curr_row["spend"], prev_row["spend"], value_format="k")
with k2:
    kpi_card("Total Sales Revenue", curr_row["revenue"], prev_row["revenue"], value_format="k")
with k3:
    kpi_card("Website Traffic", float(curr_row["traffic"]), float(prev_row["traffic"]), value_format="k")
with k4:
    kpi_card("Conversion Rate", float(curr_row["conversion_rate"]), float(prev_row["conversion_rate"]), is_percent=True)
with k5:
    kpi_card("Click Through Rate", float(curr_row["ctr"]), float(prev_row["ctr"]), is_percent=True)
with k6:
    kpi_card("Cost Per Acquisition", float(curr_row["cpa"]), float(prev_row["cpa"]), value_format="raw", currency=True)

st.write("")

# -----------------------------
# Middle row: Timeline + Distribution
# -----------------------------
c_left, c_right = st.columns([6.5, 3.5], gap="small")

with c_left:
    st.markdown('<div class="panel"><div class="panel-title">Timeline Chart</div>', unsafe_allow_html=True)

    toggle1, toggle2, spacer = st.columns([1.6, 1.6, 6.8])
    with toggle1:
        mode = st.selectbox("", ["Spend vs Revenue", "Traffic vs CTR"], label_visibility="collapsed")
    with toggle2:
        st.selectbox("", ["Monthly"], index=0, label_visibility="collapsed")

    fig = go.Figure()
    if mode == "Spend vs Revenue":
        fig.add_trace(go.Scatter(
            x=df_sorted["month"], y=df_sorted["spend"]/1000,
            mode="lines+markers", name="Spend", fill="tozeroy"
        ))
        fig.add_trace(go.Scatter(
            x=df_sorted["month"], y=df_sorted["revenue"]/1000,
            mode="lines+markers", name="Revenue", fill="tozeroy"
        ))
        fig.update_yaxes(title_text="Spend/Revenue (K)")
    else:
        fig.add_trace(go.Scatter(
            x=df_sorted["month"], y=df_sorted["traffic"]/1000,
            mode="lines+markers", name="Traffic", fill="tozeroy"
        ))
        fig.add_trace(go.Scatter(
            x=df_sorted["month"], y=df_sorted["ctr"]*100,
            mode="lines+markers", name="CTR (%)", yaxis="y2"
        ))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", title="CTR (%)"))
        fig.update_yaxes(title_text="Traffic (K)")

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with c_right:
    st.markdown('<div class="panel"><div class="panel-title">Metric Distribution</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns([2, 2, 2])
    with a1:
        metric = st.selectbox("of", ["Website Traffic", "Clicks", "Leads"], index=0, label_visibility="collapsed")
    with a2:
        st.selectbox("", ["for"], index=0, label_visibility="collapsed")
    with a3:
        st.selectbox("Age Brackets", ["Age Brackets"], index=0, label_visibility="collapsed")

    df_plot = df_age.copy()
    ycol = "website_traffic"
    if metric == "Clicks":
        df_plot[ycol] = (df_plot[ycol] * 0.25).astype(int)
    elif metric == "Leads":
        df_plot[ycol] = (df_plot[ycol] * 0.12).astype(int)

    fig2 = px.bar(df_plot, x="age", y=ycol)
    fig2.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title=None,
        yaxis_title="Traffic (in Thousands)"
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Bottom row: Funnel + Engagement + Campaign table
# -----------------------------
b1, b2, b3 = st.columns([3.3, 3.3, 3.4], gap="small")

with b1:
    st.markdown('<div class="panel"><div class="panel-title">Conversion Funnel</div>', unsafe_allow_html=True)

    f_traffic = int(curr_row["traffic"])
    f_clicks = int(curr_row["clicks"])
    f_leads = int(curr_row["leads"])
    f_sales = int(curr_row["sales"])

    funnel_df = pd.DataFrame({
        "Stage": ["Traffic", "Clicks", "Leads", "Sales"],
        "Value": [f_traffic, f_clicks, f_leads, f_sales]
    })

    fig3 = go.Figure(go.Funnel(
        y=funnel_df["Stage"],
        x=funnel_df["Value"],
        textinfo="value"
    ))
    fig3.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="panel"><div class="panel-title">Engagement by Channels</div>', unsafe_allow_html=True)

    heat = df_heat.set_index("Metric")
    fig4 = go.Figure(data=go.Heatmap(
        z=heat.values,
        x=heat.columns,
        y=heat.index,
        hoverongaps=False
    ))
    fig4.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with b3:
    st.markdown('<div class="panel"><div class="panel-title">Campaign Details</div>', unsafe_allow_html=True)

    df_tbl = df_campaign.copy()
    if campaign != "All":
        df_tbl = df_tbl[df_tbl["Campaign Name"] == campaign]

    show_tbl = df_tbl.copy()
    show_tbl["Spend"] = show_tbl["Spend"].map(lambda x: f"${x:,}")
    show_tbl["Revenue"] = show_tbl["Revenue"].map(lambda x: f"${x:,}")
    st.dataframe(show_tbl, use_container_width=True, height=240)
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Demo dashboard in Streamlit (layout inspired by your PowerBI screenshot). Replace demo data with your real dataset.")