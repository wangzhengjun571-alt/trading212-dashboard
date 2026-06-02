import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from api import (
    get_account_info, get_cash, get_portfolio,
    get_orders, get_dividends, get_pies
)

st.set_page_config(
    page_title="Kaiser · Trading 212 财务仪表板",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Trading 212 财务仪表板")
st.caption("Kaiser Wang · 真实账户")

# ── 侧边栏 ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("设置")
    currency = st.selectbox("显示货币", ["GBP", "USD", "EUR"], index=0)
    st.divider()
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 数据加载 ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    errors = {}
    data = {}
    for name, fn in [
        ("account", get_account_info),
        ("cash", get_cash),
        ("portfolio", get_portfolio),
        ("orders", get_orders),
        ("dividends", get_dividends),
        ("pies", get_pies),
    ]:
        try:
            data[name] = fn()
        except requests.HTTPError as e:
            errors[name] = f"HTTP {e.response.status_code}"
        except Exception as e:
            errors[name] = str(e)
    return data, errors


data, errors = load_all()

if errors:
    with st.expander("⚠️ API 错误", expanded=True):
        for k, v in errors.items():
            if "401" in v:
                st.error(f"**{k}**: {v} — API Key 无效或权限不足，请在 Trading 212 App 重新生成 Key 并更新 `.env` 文件。")
            else:
                st.warning(f"**{k}**: {v}")

# ── 账户总览 ───────────────────────────────────────────────────────────────────
st.subheader("账户总览")
cash = data.get("cash", {})
account = data.get("account", {})

col1, col2, col3, col4 = st.columns(4)
col1.metric("账户总值", f"£{cash.get('total', 0):,.2f}")
col2.metric("可用现金", f"£{cash.get('free', 0):,.2f}")
col3.metric("已投资金额", f"£{cash.get('invested', 0):,.2f}")
ppl = cash.get('ppl', 0)
col4.metric("未实现盈亏", f"£{ppl:,.2f}", delta=f"{ppl:+.2f}")

st.divider()

# ── 持仓明细 ───────────────────────────────────────────────────────────────────
portfolio_raw = data.get("portfolio", [])

if portfolio_raw:
    st.subheader("持仓明细")
    df = pd.DataFrame(portfolio_raw)

    rename = {
        "currentPrice": "current_price",
        "averagePrice": "avg_price",
        "initialFillDate": "open_date",
        "ticker": "ticker",
        "quantity": "quantity",
        "ppl": "ppl",
        "fxPpl": "fx_ppl",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "current_price" in df.columns and "quantity" in df.columns:
        df["market_value"] = df["current_price"] * df["quantity"]
    if "avg_price" in df.columns and "quantity" in df.columns:
        df["cost_basis"] = df["avg_price"] * df["quantity"]

    col_labels = {
        "ticker": "代码",
        "quantity": "持仓数量",
        "avg_price": "成本均价",
        "current_price": "现价",
        "market_value": "市值",
        "cost_basis": "持仓成本",
        "ppl": "未实现盈亏",
    }

    tab1, tab2 = st.tabs(["📋 持仓表格", "📊 图表分析"])

    with tab1:
        display_cols = [c for c in
                        ["ticker", "quantity", "avg_price", "current_price",
                         "market_value", "cost_basis", "ppl"]
                        if c in df.columns]
        df_display = df[display_cols].copy()
        if "market_value" in df_display.columns:
            df_display = df_display.sort_values("market_value", ascending=False)
        df_display = df_display.rename(columns={k: v for k, v in col_labels.items() if k in df_display.columns})
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        if "market_value" in df.columns and "ticker" in df.columns:
            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(
                    df, values="market_value", names="ticker",
                    title="持仓市值分布",
                    hole=0.4,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                if "ppl" in df.columns:
                    df_sorted = df.sort_values("ppl")
                    colors = ["#ef4444" if v < 0 else "#22c55e" for v in df_sorted["ppl"]]
                    fig_ppl = go.Figure(go.Bar(
                        x=df_sorted["ppl"], y=df_sorted["ticker"],
                        orientation="h", marker_color=colors,
                    ))
                    fig_ppl.update_layout(title="各持仓未实现盈亏",
                                          xaxis_title="盈亏 (£)", yaxis_title="")
                    st.plotly_chart(fig_ppl, use_container_width=True)
else:
    if "portfolio" not in errors:
        st.info("当前无持仓。")

st.divider()

# ── 订单历史 ───────────────────────────────────────────────────────────────────
orders_raw = data.get("orders", {})
orders_list = orders_raw.get("items", []) if isinstance(orders_raw, dict) else orders_raw

if orders_list:
    st.subheader("近期订单记录")
    df_orders = pd.DataFrame(orders_list)
    if "dateExecuted" in df_orders.columns:
        df_orders["dateExecuted"] = pd.to_datetime(df_orders["dateExecuted"], errors="coerce")
        df_orders = df_orders.sort_values("dateExecuted", ascending=False)

    order_col_labels = {
        "ticker": "代码",
        "type": "类型",
        "filledQuantity": "成交数量",
        "fillPrice": "成交均价",
        "dateExecuted": "成交时间",
        "status": "状态",
    }
    display_order_cols = [c for c in
                          ["ticker", "type", "filledQuantity", "fillPrice",
                           "dateExecuted", "status"]
                          if c in df_orders.columns]
    df_orders_display = df_orders[display_order_cols].head(50).copy()
    df_orders_display = df_orders_display.rename(columns={k: v for k, v in order_col_labels.items() if k in df_orders_display.columns})
    st.dataframe(df_orders_display, use_container_width=True, hide_index=True)

st.divider()

# ── 股息记录 ───────────────────────────────────────────────────────────────────
divs_raw = data.get("dividends", {})
divs_list = divs_raw.get("items", []) if isinstance(divs_raw, dict) else divs_raw

if divs_list:
    st.subheader("股息收入记录")
    df_div = pd.DataFrame(divs_list)
    if "paidOn" in df_div.columns:
        df_div["paidOn"] = pd.to_datetime(df_div["paidOn"], errors="coerce")
        df_div = df_div.sort_values("paidOn", ascending=False)

    total_div = df_div["amount"].sum() if "amount" in df_div.columns else 0
    st.metric("累计股息收入", f"£{total_div:,.2f}")

    if "paidOn" in df_div.columns and "amount" in df_div.columns:
        df_div["月份"] = df_div["paidOn"].dt.to_period("M").astype(str)
        monthly = df_div.groupby("月份")["amount"].sum().reset_index()
        fig_div = px.bar(monthly, x="月份", y="amount",
                         title="月度股息收入", labels={"amount": "金额 (£)"})
        st.plotly_chart(fig_div, use_container_width=True)

    div_col_labels = {
        "ticker": "代码",
        "amount": "金额 (£)",
        "paidOn": "到账日期",
        "quantity": "持仓数量",
    }
    display_div_cols = [c for c in ["ticker", "amount", "paidOn", "quantity"]
                        if c in df_div.columns]
    df_div_display = df_div[display_div_cols].head(50).copy()
    df_div_display = df_div_display.rename(columns={k: v for k, v in div_col_labels.items() if k in df_div_display.columns})
    st.dataframe(df_div_display, use_container_width=True, hide_index=True)

# ── 投资组合（Pies）────────────────────────────────────────────────────────────
pies_raw = data.get("pies", [])
if pies_raw:
    st.divider()
    st.subheader("投资组合（Pies）")
    for pie in pies_raw:
        name = pie.get("settings", {}).get("name", pie.get("id", "未命名"))
        result = pie.get("result", {})
        invested = result.get("investedValue", 0)
        current = result.get("value", 0)
        ppl_pie = current - invested
        with st.expander(f"🥧 {name}  —  £{current:,.2f}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("已投入", f"£{invested:,.2f}")
            c2.metric("当前市值", f"£{current:,.2f}")
            c3.metric("盈亏", f"£{ppl_pie:,.2f}", delta=f"{ppl_pie:+.2f}")
