"""月次売上トレンド ダッシュボード - カテゴリ別可視化 (SiS版)."""

import altair as alt
import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(
    page_title="月次売上トレンド",
    page_icon=":chart_with_upwards_trend:",
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

session = get_active_session()


@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    df = session.sql(QUERY).to_pandas()
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

st.title(":chart_with_upwards_trend: 月次売上トレンド")
st.caption("カテゴリ別・地域別の売上推移を可視化")

# =============================================================================
# KPI Row
# =============================================================================

total_sales = filtered["sales_amount"].sum()
total_units = filtered["units_sold"].sum()
total_customers = filtered["customer_count"].sum()
num_months = filtered["sale_date"].nunique()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("総売上", f"¥{total_sales:,.0f}")
kpi2.metric("総販売数量", f"{total_units:,.0f}")
kpi3.metric("総顧客数", f"{total_customers:,.0f}")
kpi4.metric("データ月数", f"{num_months}ヶ月")

# =============================================================================
# Monthly Trend by Category (Line Chart)
# =============================================================================

monthly_by_cat = (
    filtered.groupby([pd.Grouper(key="sale_date", freq="MS"), "product_category"])["sales_amount"].sum().reset_index()
)

st.subheader("カテゴリ別 月次売上トレンド")

line_chart = (
    alt.Chart(monthly_by_cat)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("sale_date:T", title="月"),
        y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
        color=alt.Color("product_category:N", title="カテゴリ"),
        tooltip=[
            alt.Tooltip("sale_date:T", title="月", format="%Y-%m"),
            alt.Tooltip("product_category:N", title="カテゴリ"),
            alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
        ],
    )
    .properties(height=400)
)
st.altair_chart(line_chart, use_container_width=True)

# =============================================================================
# TOP N Sales Ranking
# =============================================================================

st.subheader(":trophy: 月×カテゴリ×地域 売上ランキング")

top_n = st.slider("表示件数", min_value=5, max_value=30, value=10, step=5)

top_df = (
    filtered.groupby(["sale_date", "product_category", "region"])["sales_amount"]
    .sum()
    .reset_index()
    .nlargest(top_n, "sales_amount")
    .reset_index(drop=True)
)
top_df["rank"] = range(1, len(top_df) + 1)
top_df["label"] = (
    top_df["sale_date"].dt.strftime("%Y-%m") + " / " + top_df["region"] + " / " + top_df["product_category"]
)

col_chart, col_table = st.columns([3, 2])

with col_chart:
    rank_chart = (
        alt.Chart(top_df)
        .mark_bar()
        .encode(
            x=alt.X("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
            y=alt.Y("label:N", title=None, sort="-x"),
            color=alt.Color("product_category:N", title="カテゴリ"),
            tooltip=[
                alt.Tooltip("sale_date:T", title="月", format="%Y-%m"),
                alt.Tooltip("region:N", title="地域"),
                alt.Tooltip("product_category:N", title="カテゴリ"),
                alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
            ],
        )
        .properties(height=max(top_n * 30, 200))
    )
    st.altair_chart(rank_chart, use_container_width=True)

with col_table:
    table_df = top_df[["rank", "sale_date", "product_category", "region", "sales_amount"]].copy()
    table_df["sale_date"] = table_df["sale_date"].dt.strftime("%Y-%m")
    table_df.columns = ["順位", "月", "カテゴリ", "地域", "売上"]
    st.dataframe(table_df.set_index("順位"))

# =============================================================================
# Area Chart - Stacked by Category
# =============================================================================

st.subheader("カテゴリ別 売上構成（積み上げ）")

area_chart = (
    alt.Chart(monthly_by_cat)
    .mark_area(opacity=0.7)
    .encode(
        x=alt.X("sale_date:T", title="月"),
        y=alt.Y("sales_amount:Q", title="売上 (¥)", stack=True, axis=alt.Axis(format="~s")),
        color=alt.Color("product_category:N", title="カテゴリ"),
        tooltip=[
            alt.Tooltip("sale_date:T", title="月", format="%Y-%m"),
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

st.subheader("地域 × カテゴリ 月次売上")

col1, col2 = st.columns(2)

with col1:
    monthly_by_region = (
        filtered.groupby([pd.Grouper(key="sale_date", freq="MS"), "region"])["sales_amount"].sum().reset_index()
    )
    region_chart = (
        alt.Chart(monthly_by_region)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("sale_date:T", title="月"),
            y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
            color=alt.Color("region:N", title="地域"),
            tooltip=[
                alt.Tooltip("sale_date:T", title="月", format="%Y-%m"),
                alt.Tooltip("region:N", title="地域"),
                alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
            ],
        )
        .properties(height=300)
    )
    st.markdown("**地域別トレンド**")
    st.altair_chart(region_chart, use_container_width=True)

with col2:
    cat_by_region = filtered.groupby(["region", "product_category"])["sales_amount"].sum().reset_index()
    bar_chart = (
        alt.Chart(cat_by_region)
        .mark_bar()
        .encode(
            x=alt.X("product_category:N", title="カテゴリ"),
            y=alt.Y("sales_amount:Q", title="売上 (¥)", axis=alt.Axis(format="~s")),
            color=alt.Color("product_category:N", title="カテゴリ"),
            column=alt.Column("region:N", title="地域"),
            tooltip=[
                alt.Tooltip("region:N", title="地域"),
                alt.Tooltip("product_category:N", title="カテゴリ"),
                alt.Tooltip("sales_amount:Q", title="売上", format=",.0f"),
            ],
        )
        .properties(width=120, height=300)
    )
    st.markdown("**地域×カテゴリ 売上比較**")
    st.altair_chart(bar_chart, use_container_width=True)

# =============================================================================
# Data Table
# =============================================================================

with st.expander("詳細データを表示"):
    display_df = monthly_by_cat.copy().rename(
        columns={
            "sale_date": "月",
            "product_category": "カテゴリ",
            "sales_amount": "売上",
        }
    )
    display_df["月"] = display_df["月"].dt.strftime("%Y年%m月")
    st.dataframe(display_df)
