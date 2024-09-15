import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Data Visualization", layout="wide")

def fetch_stock_data(symbol, start_date, end_date):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

def create_price_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    fig.update_layout(
        title='Stock Price History',
        yaxis_title='Price',
        xaxis_title='Date',
        height=600,
        template='plotly_white'
    )
    return fig

def main():
    st.title("Stock Data Visualization App")

    # User input
    symbol = st.text_input("Enter stock symbol (e.g., AAPL, GOOGL):", "AAPL").upper()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    date_range = st.date_input("Select date range:", [start_date, end_date])

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        st.warning("Please select both start and end dates.")
        return

    if st.button("Fetch Stock Data"):
        with st.spinner("Fetching data..."):
            hist_data, info = fetch_stock_data(symbol, start_date, end_date)

        if hist_data is not None and info is not None:
            # Display key financial information
            st.subheader(f"Key Financial Information for {symbol}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${info.get('currentPrice', 'N/A'):.2f}")
            col2.metric("Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B")
            col3.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):.2f}")

            # Display price history chart
            st.subheader("Stock Price History")
            fig = create_price_chart(hist_data)
            st.plotly_chart(fig, use_container_width=True)

            # Display financial data table
            st.subheader("Financial Data Table")
            df_display = hist_data[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
            df_display['Date'] = df_display['Date'].dt.date
            st.dataframe(df_display)

            # Download CSV
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f"{symbol}_stock_data.csv",
                mime="text/csv",
            )
        else:
            st.error("Failed to fetch stock data. Please check the symbol and try again.")

if __name__ == "__main__":
    main()
