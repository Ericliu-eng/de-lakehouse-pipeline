from __future__ import annotations

import pandas as pd
import streamlit as st

from de_lakehouse_pipeline.load.db.connection import (
    connect,
    load_db_config,
    wait_for_db,
)


def load_price_changes(symbol: str, limit: int = 30) -> pd.DataFrame:
    sql = """
        WITH price_changes AS (
            SELECT
                symbol,
                ts::date AS trading_date,
                close AS close_price,
                LAG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY ts
                ) AS previous_close,
                close - LAG(close) OVER (
                    PARTITION BY symbol
                    ORDER BY ts
                ) AS price_change,
                ROUND(
                    (
                        (close - LAG(close) OVER (
                            PARTITION BY symbol
                            ORDER BY ts
                        ))
                        / NULLIF(LAG(close) OVER (
                            PARTITION BY symbol
                            ORDER BY ts
                        ), 0)
                    ) * 100,
                    2
                ) AS change_pct,
                volume
            FROM market_bars
            WHERE symbol = %s
        )
        SELECT
            symbol,
            trading_date,
            close_price,
            previous_close,
            price_change,
            change_pct,
            volume
        FROM price_changes
        ORDER BY trading_date DESC
        LIMIT %s;
    """

    cfg = load_db_config()
    wait_for_db(cfg, timeout_s=60)

    with connect(cfg) as conn:
        return pd.read_sql(sql, conn, params=(symbol, limit))


def render_dashboard() -> None:
    st.set_page_config(
        page_title="Stock Price Changes",
        page_icon="📈",
        layout="wide",
    )

    st.title("Stock Price Changes")

    symbol = st.sidebar.text_input("Symbol", value="AAPL").upper()
    limit = st.sidebar.slider("Rows", min_value=7, max_value=120, value=30)

    df = load_price_changes(symbol=symbol, limit=limit)

    if df.empty:
        st.warning(f"No price data found for {symbol}.")
        return

    latest = df.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest Close",
        f"${latest['close_price']:.2f}",
    )

    col2.metric(
        "Price Change",
        f"${latest['price_change']:.2f}"
        if latest["price_change"] is not None
        else "N/A",
    )

    col3.metric(
        "Change %",
        f"{latest['change_pct']:.2f}%"
        if latest["change_pct"] is not None
        else "N/A",
    )

    chart_df = df.sort_values("trading_date")

    st.subheader("Close Price Trend")
    st.line_chart(
        chart_df,
        x="trading_date",
        y="close_price",
    )

    st.subheader("Price Change Table")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    render_dashboard()