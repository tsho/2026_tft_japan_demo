"""月次売上トレンド ダッシュボード - カテゴリ別可視化"""

import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(
    page_title="月次売上トレンド",
    page_icon=":material/trending_up:",
    layout="wide",
)

# =============================================================================
# Data Loading
# =============================================================================

QUERY = """
SELECT
    SALE_DATE,
    PRODUCT_CATEGORY,
    REGION,
    SUM(SALES_AMOUNT) AS SALES_AMOUNT,
    SUM(UNITS_SOLD) AS UNITS_SOLD,
    SUM(CUSTOMER_COUNT) AS CUSTOMER_COUNT
FROM TSHO_DB.TFT_DEMO_2026.MONTHLY_SALES
GROUP BY SALE_DATE, PRODUCT_CATEGORY, REGION
ORDER BY SALE_DATE
"""


@st.cache_data(ttl=600, show_spinner="Snowflakeからデータを読み込み中...")
def load_data() -> pd.DataFrame:
    import os
    import snowflake.connector

    token = os.environ.get("SNOWFLAKE_TOKEN")
    if token:
        ctx = snowflake.connector.connect(
            account=os.environ.get("SNOWFLAKE_ACCOUNT", ""),
            user=os.environ.get("SNOWFLAKE_USER", ""),
            password=token,
            role=os.environ.get("SNOWFLAKE_ROLE", ""),
        )
        df = pd.read_sql(QUERY, ctx)
        ctx.close()
    else:
        conn = st.connection("snowflake")
        df = conn.query(QUERY)
    df.columns = df.columns.str.lower()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df


df = load_data()

# =============================================================================
# Sidebar Filters
# =============================================================================

with st.sidebar:
    st.header("フィルター")

    all_regions = sorted(df["region"].unique())
    selected_regions = st.multiselect("地域", all_regions, default=all_regions)

    all_categories = sorted(df["product_category"].unique())
    selected_categories = st.multiselect("カテゴリ", all_categories, default=all_categories)

    year_range = st.slider(
        "年",
        min_value=int(df["sale_date"].dt.year.min()),
        max_value=int(df["sale_date"].dt.year.max()),
        value=(
            int(df["sale_date"].dt.year.min()),
            int(df["sale_date"].dt.year.max()),
        ),
    )

# Apply filters
filtered = df[
    (df["region"].isin(selected_regions))
    & (df["product_category"].isin(selected_categories))
    & (df["sale_date"].dt.year >= year_range[0])
    & (df["sale_date"].dt.year <= year_range[1])
]

# =============================================================================
# Page Header
# =============================================================================

st.markdown("# :material/trending_up: 月次売上トレンド")
st.caption("カテゴリ別・地域別の売上推移を可視化")

# =============================================================================
# KPI Row
# =============================================================================

total_sales = filtered["sales_amount"].sum()
total_units = filtered["units_sold"].sum()
total_customers = filtered["customer_count"].sum()
num_months = filtered["sale_date"].nunique()

with st.container(horizontal=True):
    st.metric("総売上", f"¥{total_sales:,.0f}", border=True)
    st.metric("総販売数量", f"{total_units:,.0f}", border=True)
    st.metric("総顧客数", f"{total_customers:,.0f}", border=True)
    st.metric("データ月数", f"{num_months}ヶ月", border=True)

# =============================================================================
# Monthly Trend by Category (Line Chart)
# =============================================================================

monthly_by_cat = (
    filtered.groupby([pd.Grouper(key="sale_date", freq="MS"), "product_category"])["sales_amount"]
    .sum()
    .reset_index()
)

st.markdown("### カテゴリ別 月次売上トレンド")

line_chart = (
    alt.Chart(monthly_by_cat)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("sale_date:T", title="月"),
        y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
        color=alt.Color("product_category:N", title="カテゴリ"),
        tooltip=[
            alt.Tooltip("sale_date:T", title="月", format="%Y年%m月"),
            alt.Tooltip("product_category:N", title="カテゴリ"),
            alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
        ],
    )
    .properties(height=400)
)
st.altair_chart(line_chart, use_container_width=True)

# =============================================================================
# Area Chart - Stacked by Category
# =============================================================================

st.markdown("### カテゴリ別 売上構成（積み上げ）")

area_chart = (
    alt.Chart(monthly_by_cat)
    .mark_area(opacity=0.7)
    .encode(
        x=alt.X("sale_date:T", title="月"),
        y=alt.Y("sales_amount:Q", title="売上 (¥)", stack=True, axis=alt.Axis(format="~s")),
        color=alt.Color("product_category:N", title="カテゴリ"),
        tooltip=[
            alt.Tooltip("sale_date:T", title="月", format="%Y年%m月"),
            alt.Tooltip("product_category:N", title="カテゴリ"),
            alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
        ],
    )
    .properties(height=350)
)
st.altair_chart(area_chart, use_container_width=True)

# =============================================================================
# Region x Category Breakdown
# =============================================================================

st.markdown("### 地域 × カテゴリ 月次売上")

col1, col2 = st.columns(2)

with col1:
    monthly_by_region = (
        filtered.groupby([pd.Grouper(key="sale_date", freq="MS"), "region"])["sales_amount"]
        .sum()
        .reset_index()
    )
    region_chart = (
        alt.Chart(monthly_by_region)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("sale_date:T", title="月"),
            y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
            color=alt.Color("region:N", title="地域"),
            tooltip=[
                alt.Tooltip("sale_date:T", title="月", format="%Y年%m月"),
                alt.Tooltip("region:N", title="地域"),
                alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    with st.container(border=True):
        st.markdown("**地域別トレンド**")
        st.altair_chart(region_chart, use_container_width=True)

with col2:
    cat_by_region = (
        filtered.groupby(["region", "product_category"])["sales_amount"]
        .sum()
        .reset_index()
    )
    bar_chart = (
        alt.Chart(cat_by_region)
        .mark_bar()
        .encode(
            x=alt.X("region:N", title="地域"),
            y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
            color=alt.Color("product_category:N", title="カテゴリ"),
            xOffset="product_category:N",
            tooltip=[
                alt.Tooltip("region:N", title="地域"),
                alt.Tooltip("product_category:N", title="カテゴリ"),
                alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    with st.container(border=True):
        st.markdown("**地域×カテゴリ 売上比較**")
        st.altair_chart(bar_chart, use_container_width=True)

# =============================================================================
# Data Table
# =============================================================================

with st.expander("詳細データを表示"):
    display_df = (
        monthly_by_cat.copy()
        .rename(columns={
            "sale_date": "月",
            "product_category": "カテゴリ",
            "sales_amount": "売上",
        })
    )
    display_df["月"] = display_df["月"].dt.strftime("%Y年%m月")
    st.dataframe(
        display_df,
        column_config={
            "売上": st.column_config.NumberColumn(format="¥%.0f"),
        },
        hide_index=True,
        use_container_width=True,
    )
