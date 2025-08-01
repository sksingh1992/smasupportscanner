import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime

def calculate_sma(df, period, price_col='Close'):
    """Calculate Simple Moving Average"""
    return df[price_col].rolling(window=period).mean()

def slope(series, length=3):
    """Calculate slope of a series"""
    if len(series) < length:
        return np.nan
    y = series.iloc[-length:].values
    x = np.arange(length)
    if len(y) < length:
        return np.nan
    
    # Calculate slope using linear regression
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x * x)
    
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0
    
    slope_val = (n * sum_xy - sum_x * sum_y) / denominator
    return slope_val

def is_green_candle(candle):
    """Check if candle is green (close > open)"""
    return candle["Close"] > candle["Open"]

def candle_body_low(candle):
    """Get the lower end of candle body"""
    return min(candle["Open"], candle["Close"])

def touches_sma(candle, sma_value, tolerance=0.001):
    """Check if green candle touches SMA (body or wick)"""
    if not is_green_candle(candle):
        return False
    
    # Check if SMA is within the candle's range (low to high)
    return candle["Low"] <= sma_value * (1 + tolerance) and candle["High"] >= sma_value * (1 - tolerance)

def check_slope_upwards(df, idx, period=3, sma_column="SMA20"):
    """Check if SMA has upward slope"""
    if idx < period - 1:
        return False
    
    start_idx = max(0, idx - period + 1)
    end_idx = idx + 1
    subset = df[sma_column].iloc[start_idx:end_idx]
    
    if len(subset) < 2:
        return False
    
    slope_val = slope(subset, min(len(subset), period))
    return not pd.isna(slope_val) and slope_val > 0

def find_crossover_up(df, idx):
    """Find SMA20 crossing above SMA50"""
    if idx == 0:
        return False
    
    prev_sma20 = df["SMA20"].iloc[idx-1]
    prev_sma50 = df["SMA50"].iloc[idx-1]
    curr_sma20 = df["SMA20"].iloc[idx]
    curr_sma50 = df["SMA50"].iloc[idx]
    
    if pd.isna(prev_sma20) or pd.isna(prev_sma50) or pd.isna(curr_sma20) or pd.isna(curr_sma50):
        return False
    
    return prev_sma20 <= prev_sma50 and curr_sma20 > curr_sma50

def calculate_bounce_percentage(support_low, high_price):
    """Calculate bounce percentage from support low to high"""
    if support_low == 0:
        return 0
    return ((high_price - support_low) / support_low) * 100

def advanced_scanner(df, bounce_threshold=1.0):
    """
    Advanced scanner implementing the complete trading strategy
    
    States:
    0: Waiting for crossover
    1: After crossover, waiting for first support (S1)
    2: After S1, waiting for bounce
    3: After bounce, waiting for next support
    """
    
    df = df.copy()
    df = df.reset_index()
    df["SMA20"] = calculate_sma(df, 20)
    df["SMA50"] = calculate_sma(df, 50)
    
    results = []
    
    # State variables
    state = 0
    support_count = 0
    last_support_low = np.nan
    last_support_idx = -1
    crossover_idx = -1
    bounce_count = 0
    last_bounce_high = np.nan
    
    # Start from index 50 to ensure we have enough SMA data
    for i in range(50, len(df)):
        candle = df.iloc[i]
        sma20, sma50 = candle["SMA20"], candle["SMA50"]
        
        # Skip if SMA values are NaN
        if pd.isna(sma20) or pd.isna(sma50):
            continue
        
        # Check if both SMAs have upward slope
        sma20_slope_up = check_slope_upwards(df, i, 3, "SMA20")
        sma50_slope_up = check_slope_upwards(df, i, 3, "SMA50")
        
        # Reset if slopes are not upward or price closes below SMA50
        if not (sma20_slope_up and sma50_slope_up) or candle["Close"] < sma50:
            if state > 0:  # Only reset if we were in a pattern
                state = 0
                support_count = 0
                last_support_low = np.nan
                last_support_idx = -1
                crossover_idx = -1
                bounce_count = 0
                last_bounce_high = np.nan
            continue
        
        # State 0: Looking for crossover
        if state == 0:
            if find_crossover_up(df, i):
                state = 1
                crossover_idx = i
                support_count = 0
                last_support_low = np.nan
                last_support_idx = -1
                bounce_count = 0
                last_bounce_high = np.nan
            continue
        
        # State 1: After crossover, looking for S1 (first support)
        elif state == 1:
            if touches_sma(candle, sma20) or touches_sma(candle, sma50):
                support_count = 1
                last_support_low = candle_body_low(candle)
                last_support_idx = i
                state = 2  # Move to waiting for bounce
                
                # Record S1 (no bounce required for first support)
                results.append({
                    "Date": candle["Date"] if "Date" in candle else df.index[i],
                    "Index": i,
                    "Support_Level": "S1",
                    "Support_Low": last_support_low,
                    "SMA20": sma20,
                    "SMA50": sma50,
                    "Bounce_From_Previous": "N/A (First Support)"
                })
            continue
        
        # State 2: After support, waiting for bounce
        elif state == 2:
            if last_support_idx >= 0:
                # Calculate bounce from last support low
                bounce_pct = calculate_bounce_percentage(last_support_low, candle["High"])
                
                if bounce_pct >= bounce_threshold:
                    bounce_count += 1
                    last_bounce_high = candle["High"]
                    state = 3  # Move to waiting for next support
            continue
        
        # State 3: After bounce, waiting for next support
        elif state == 3:
            if touches_sma(candle, sma20) or touches_sma(candle, sma50):
                current_support_low = candle_body_low(candle)
                
                # Check if current support low is higher than previous support low
                if current_support_low > last_support_low:
                    support_count += 1
                    
                    # Calculate bounce percentage from previous support
                    bounce_from_prev = calculate_bounce_percentage(last_support_low, last_bounce_high)
                    
                    # Record the support
                    results.append({
                        "Date": candle["Date"] if "Date" in candle else df.index[i],
                        "Index": i,
                        "Support_Level": f"S{support_count}",
                        "Support_Low": current_support_low,
                        "SMA20": sma20,
                        "SMA50": sma50,
                        "Bounce_From_Previous": f"{bounce_from_prev:.2f}%"
                    })
                    
                    # Update state variables
                    last_support_low = current_support_low
                    last_support_idx = i
                    state = 2  # Go back to waiting for bounce
                else:
                    # Current support is not higher, invalidate pattern
                    state = 0
                    support_count = 0
                    last_support_low = np.nan
                    last_support_idx = -1
                    crossover_idx = -1
                    bounce_count = 0
                    last_bounce_high = np.nan
            continue
    
    # Filter results to only show patterns that reached at least S3
    if results:
        df_results = pd.DataFrame(results)
        
        # Group by crossover sequence and check if S3 was reached
        valid_results = []
        current_sequence = []
        
        for _, row in df_results.iterrows():
            current_sequence.append(row)
            
            # If we hit S3, mark all previous supports in this sequence as valid
            if row["Support_Level"] == "S3":
                valid_results.extend(current_sequence)
                current_sequence = []  # Reset for next sequence
            
            # If we encounter S1 and we already have items in sequence, 
            # it means we're starting a new sequence
            elif row["Support_Level"] == "S1" and len(current_sequence) > 1:
                current_sequence = [row]  # Start new sequence
        
        # Add any remaining S3+ supports
        for row in current_sequence:
            if row["Support_Level"] not in ["S1", "S2"]:
                valid_results.append(row)
        
        return pd.DataFrame(valid_results)
    
    return pd.DataFrame()

# 🚀 Streamlit UI
st.title("📈 Advanced S3+ SMA Support Scanner")
st.markdown("""
### Trading Rules Implemented:
1. **SMA20 crosses above SMA50** (upward crossover)
2. **Both SMAs maintain upward slope** throughout the pattern
3. **S1**: First green candle support on SMA20/50 after crossover
4. **Bounce**: Minimum 1% bounce from support low
5. **S3+**: Subsequent supports with higher lows after each bounce
6. **Pattern validation**: Only shows results that reach at least S3
""")

# Input section
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Enter Stock Symbol", "BAJAJ-AUTO.NS", help="Use Yahoo Finance format (e.g., AAPL, BAJAJ-AUTO.NS)")
    timeframe = st.selectbox("Select Timeframe", ["15m", "30m", "1h", "1d"], index=2)

with col2:
    start_date = st.date_input("From Date", value=pd.Timestamp.now() - pd.Timedelta(days=30))
    end_date = st.date_input("To Date", value=pd.Timestamp.now())

bounce_threshold = st.slider("Minimum Bounce Threshold (%)", 0.5, 5.0, 1.0, 0.1)

if st.button("🔍 Run Advanced Scanner", type="primary"):
    with st.spinner("Downloading data and running analysis..."):
        try:
            # Download data
            df = yf.download(symbol, start=start_date, end=end_date, interval=timeframe)
            
            if df.empty:
                st.error("❌ No data found for the given symbol/date range.")
            else:
                st.success(f"✅ Downloaded {len(df)} candles for {symbol}")
                
                # Run scanner
                results = advanced_scanner(df, bounce_threshold)
                
                if results.empty:
                    st.warning("⚠️ No valid S3+ support patterns found in this range.")
                    st.info("💡 Try adjusting the date range or bounce threshold.")
                else:
                    st.success(f"🎯 Found {len(results)} valid support levels!")
                    
                    # Display results
                    st.subheader("📊 Scan Results")
                    
                    # Format the dataframe for better display
                    display_df = results.copy()
                    if "Date" in display_df.columns:
                        display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d %H:%M")
                    
                    # Round numeric columns
                    numeric_cols = ["Support_Low", "SMA20", "SMA50"]
                    for col in numeric_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].round(2)
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Summary statistics
                    st.subheader("📈 Pattern Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_supports = len(results)
                        st.metric("Total Supports", total_supports)
                    
                    with col2:
                        s3_plus = len(results[results["Support_Level"].str.extract(r'S(\d+)')[0].astype(int) >= 3])
                        st.metric("S3+ Supports", s3_plus)
                    
                    with col3:
                        if len(results) > 0:
                            avg_support = results["Support_Low"].mean()
                            st.metric("Avg Support Level", f"{avg_support:.2f}")
                
        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
            st.info("Please check your symbol format and try again.")

# Add information section
with st.expander("ℹ️ How to Use This Scanner"):
    st.markdown("""
    ### Symbol Format Examples:
    - **US Stocks**: AAPL, GOOGL, TSLA
    - **Indian Stocks**: RELIANCE.NS, TCS.NS, BAJAJ-AUTO.NS
    - **Other Markets**: Use Yahoo Finance symbol format
    
    ### Timeframe Selection:
    - **15m/30m**: For intraday trading
    - **1h**: For short-term swing trading  
    - **1d**: For position trading
    
    ### Understanding Results:
    - **S1**: First support after SMA crossover (no bounce required)
    - **S2**: Second support after 1%+ bounce from S1
    - **S3+**: Valid pattern confirmation - scanner shows all supports from this point
    - **Higher Lows**: Each subsequent support must have a higher low than the previous
    """)