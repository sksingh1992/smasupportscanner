import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

def calculate_sma(df, period, price_col='Close'):
    """Calculate Simple Moving Average"""
    return df[price_col].rolling(window=period).mean()

def slope(series, length=3):
    """Calculate slope of a series over given length"""
    y = series[-length:]
    x = np.arange(length)
    if len(y) < length:
        return np.nan
    cov = np.cov(x, y)[0][1]
    var = np.var(x)
    return 0 if var == 0 else cov / var

def is_green(candle):
    """Check if candle is green (close > open)"""
    return candle["Close"] > candle["Open"]

def candle_body_low(candle):
    """Get the lower part of candle body"""
    return min(candle["Open"], candle["Close"])

def touches_sma(candle, sma_value):
    """Check if green candle touches SMA (body or lower wick)"""
    if not is_green(candle):
        return False
    # Check if candle body or lower wick touches SMA
    return (candle["Low"] <= sma_value <= candle["High"])

def check_slope_upwards(df, idx, period=3, sma_column="SMA"):
    """Check if SMA has upward slope"""
    if idx < period:
        return False
    subset = df[sma_column].iloc[idx - period + 1 : idx + 1]
    return slope(subset, length=period) > 0

def find_crossover_up(df, idx):
    """Find upward crossover of SMA20 over SMA50"""
    if idx == 0:
        return False
    return (df["SMA20"].iloc[idx-1] <= df["SMA50"].iloc[idx-1]) and (df["SMA20"].iloc[idx] > df["SMA50"].iloc[idx])

def calculate_bounce_percentage(high_price, support_low):
    """Calculate bounce percentage from support low"""
    return ((high_price - support_low) / support_low) * 100

def scanner(df, bounce_threshold=1.0):
    """
    Main scanner function implementing the trading rules:
    1. SMA20 crossover SMA50 upwards
    2. Support on SMA20 or SMA50 (S1)
    3. Bounce of 1%+ (B1)
    4. Subsequent supports (S2, S3, etc.)
    5. Higher lows after each bounce
    6. Continuous upward slope for both SMAs
    """
    df = df.copy().reset_index(drop=True)
    df["SMA20"] = calculate_sma(df, 20)
    df["SMA50"] = calculate_sma(df, 50)

    results = []
    
    # State machine variables
    state = 0  # 0: waiting for crossover, 1: waiting for S1, 2: waiting for B1, 3: waiting for S2+, 4: pattern complete
    support_count = 0
    bounce_count = 0
    last_support_low = np.nan
    last_support_candle_idx = -1
    crossover_idx = -1
    
    i = 20  # Start after enough data for SMAs
    while i < len(df):
        candle = df.iloc[i]
        sma20, sma50 = candle["SMA20"], candle["SMA50"]

        # Skip if SMAs are not available
        if pd.isna(sma20) or pd.isna(sma50):
            i += 1
            continue

        # Check if both SMAs have upward slope
        sma20_slope_ok = check_slope_upwards(df, i, 3, "SMA20")
        sma50_slope_ok = check_slope_upwards(df, i, 3, "SMA50")
        
        if not (sma20_slope_ok and sma50_slope_ok):
            # Reset if slopes are not upward
            state, support_count, bounce_count, last_support_low, last_support_candle_idx = 0, 0, 0, np.nan, -1
            i += 1
            continue

        # Check for crossover
        if find_crossover_up(df, i):
            state = 1
            support_count = 0
            bounce_count = 0
            last_support_low = np.nan
            last_support_candle_idx = -1
            crossover_idx = i
            i += 1
            continue

        # Check if price goes below SMA50 (pattern invalid)
        if state > 0 and candle["Close"] < sma50:
            state, support_count, bounce_count, last_support_low, last_support_candle_idx = 0, 0, 0, np.nan, -1
            i += 1
            continue

        # State machine logic
        if state == 0:
            # Waiting for crossover
            i += 1
            continue
            
        elif state == 1:
            # Waiting for S1 (first support after crossover)
            if touches_sma(candle, sma20) or touches_sma(candle, sma50):
                support_count = 1
                last_support_low = candle_body_low(candle)
                last_support_candle_idx = i
                state = 2
                results.append({
                    "Date": df.index[i], 
                    "Support": f"S{support_count}",
                    "Type": "First Support",
                    "SMA_Touched": "SMA20" if touches_sma(candle, sma20) else "SMA50",
                    "Price": candle["Close"]
                })
            i += 1
            continue

        elif state == 2:
            # Waiting for B1 (first bounce of 1%+)
            required_bounce_price = last_support_low * (1 + bounce_threshold / 100)
            if candle["High"] >= required_bounce_price:
                bounce_count += 1
                state = 3
                results.append({
                    "Date": df.index[i], 
                    "Support": f"B{bounce_count}",
                    "Type": "Bounce",
                    "Bounce_%": round(calculate_bounce_percentage(candle["High"], last_support_low), 2),
                    "Price": candle["High"]
                })
            i += 1
            continue

        elif state == 3:
            # Waiting for S2+ (subsequent supports after bounce)
            if touches_sma(candle, sma20) or touches_sma(candle, sma50):
                current_low = candle_body_low(candle)
                
                # Check if current support low is higher than previous support low
                if current_low > last_support_low:
                    support_count += 1
                    last_support_low = current_low
                    last_support_candle_idx = i
                    
                    # Add to results
                    results.append({
                        "Date": df.index[i], 
                        "Support": f"S{support_count}",
                        "Type": f"Support {support_count}",
                        "SMA_Touched": "SMA20" if touches_sma(candle, sma20) else "SMA50",
                        "Price": candle["Close"],
                        "Previous_Support_Low": round(last_support_low, 2)
                    })
                    
                    # Continue pattern - go back to waiting for bounce
                    state = 2
                else:
                    # Support low is not higher - invalid pattern
                    state, support_count, bounce_count, last_support_low, last_support_candle_idx = 0, 0, 0, np.nan, -1
            i += 1
            continue

    return pd.DataFrame(results)

# 🚀 Streamlit UI
st.set_page_config(page_title="SMA Support Scanner", layout="wide")
st.title("📈 SMA Support Scanner - Trading Pattern Detector")

# Sidebar for configuration
st.sidebar.header("Configuration")
bounce_threshold = st.sidebar.slider("Bounce Threshold (%)", 0.5, 5.0, 1.0, 0.1)

# Main input area
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Enter Stock Symbol (e.g. BAJAJ-AUTO.NS)", "BAJAJ-AUTO.NS")
    timeframe = st.selectbox("Select Timeframe", ["15m", "30m", "1h", "1d"])

with col2:
    start_date = st.date_input("From Date")
    end_date = st.date_input("To Date")

# Run scanner button
if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner("Downloading data and analyzing patterns..."):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, interval=timeframe)
            
            if df.empty:
                st.error("❌ No data found for given symbol/date range.")
            else:
                st.success(f"✅ Data downloaded successfully! {len(df)} candles found.")
                
                # Run scanner
                results = scanner(df, bounce_threshold)
                
                if results.empty:
                    st.warning("⚠️ No valid S3+ support patterns found in this range.")
                    st.info("💡 Try adjusting the date range or check if the stock meets the pattern criteria.")
                else:
                    st.success(f"🎯 Found {len(results)} pattern events!")
                    
                    # Display results
                    st.subheader("📊 Pattern Results")
                    st.dataframe(results, use_container_width=True)
                    
                    # Summary statistics
                    st.subheader("📈 Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Supports", len(results[results['Support'].str.startswith('S')]))
                    
                    with col2:
                        st.metric("Total Bounces", len(results[results['Support'].str.startswith('B')]))
                    
                    with col3:
                        if len(results) > 0:
                            avg_bounce = results[results['Bounce_%'].notna()]['Bounce_%'].mean()
                            st.metric("Avg Bounce %", f"{avg_bounce:.2f}%" if not pd.isna(avg_bounce) else "N/A")
                    
                    # Pattern visualization info
                    st.subheader("🔍 Pattern Analysis")
                    st.info("""
                    **Pattern Rules Applied:**
                    - ✅ SMA20 crossover SMA50 upwards
                    - ✅ Support on SMA20 or SMA50 (green candles)
                    - ✅ Bounce of 1%+ after each support
                    - ✅ Higher lows after each bounce
                    - ✅ Continuous upward slope for both SMAs
                    - ✅ Pattern continues until price closes below SMA50
                    """)
                    
        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
            st.info("💡 Please check your symbol format and internet connection.")

# Add information about the scanner
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ About This Scanner")
st.sidebar.info("""
This scanner identifies specific trading patterns based on SMA crossovers and support levels.

**Key Features:**
- Detects SMA20/SMA50 upward crossovers
- Identifies support levels on SMAs
- Tracks 1%+ bounces
- Ensures higher lows after bounces
- Validates upward SMA slopes
""")

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit and yfinance*")