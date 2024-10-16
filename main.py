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

def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window):
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(data, window):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi, rsi.iloc[-1]  # Return both the RSI series and the latest RSI value

def create_price_chart(data, sma_window, ema_window):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=calculate_sma(data, sma_window),
        name=f'SMA ({sma_window})',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=calculate_ema(data, ema_window),
        name=f'EMA ({ema_window})',
        line=dict(color='orange')
    ))
    
    fig.update_layout(
        title='Stock Price History with SMA and EMA',
        yaxis_title='Price',
        xaxis_title='Date',
        height=500,
        template='plotly_white'
    )
    return fig

def create_rsi_chart(data, rsi_window):
    rsi_series, _ = calculate_rsi(data, rsi_window)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=rsi_series,
        name=f'RSI ({rsi_window})',
        line=dict(color='purple')
    ))
    
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    
    fig.update_layout(
        title='Relative Strength Index (RSI)',
        yaxis_title='RSI',
        xaxis_title='Date',
        height=300,
        template='plotly_white',
        yaxis=dict(range=[0, 100])
    )
    return fig

def main():
    st.title("Stock Data Visualization App")

    # User input
    symbol = st.text_input("Enter stock symbol (e.g., AAPL, GOOGL):", "AAPL").upper()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    date_range = st.date_input("Select date range:", [start_date, end_date])

    # Sidebar for technical indicator parameters
    st.sidebar.header("Technical Indicators")
    sma_window = st.sidebar.slider("SMA Window", min_value=5, max_value=200, value=20)
    ema_window = st.sidebar.slider("EMA Window", min_value=5, max_value=200, value=20)
    rsi_window = st.sidebar.slider("RSI Window", min_value=5, max_value=50, value=14)

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        st.warning("Please select both start and end dates.")
        return

    if st.button("Fetch Stock Data"):
        with st.spinner("Fetching data..."):
            hist_data, info = fetch_stock_data(symbol, start_date, end_date)

        if hist_data is not None and info is not None:
            # Calculate latest RSI value
            _, latest_rsi = calculate_rsi(hist_data, rsi_window)

            # Display key financial information
            st.subheader(f"Key Financial Information for {symbol}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"${info.get('currentPrice', 'N/A'):.2f}")
            col2.metric("Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B")
            
            # Handle 'N/A' or non-numeric values for trailingPE
            trailing_pe = info.get('trailingPE', 'N/A')
            if isinstance(trailing_pe, (int, float)):
                pe_display = f"{trailing_pe:.2f}"
            else:
                pe_display = str(trailing_pe)
            col3.metric("P/E Ratio", pe_display)
            
            # Display latest RSI value
            col4.metric("Latest RSI", f"{latest_rsi:.2f}")

            # Display price history chart with SMA and EMA
            st.subheader("Stock Price History with SMA and EMA")
            price_fig = create_price_chart(hist_data, sma_window, ema_window)
            st.plotly_chart(price_fig, use_container_width=True)

            # Display RSI chart
            st.subheader("Relative Strength Index (RSI)")
            rsi_fig = create_rsi_chart(hist_data, rsi_window)
            st.plotly_chart(rsi_fig, use_container_width=True)

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
