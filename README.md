# 📈 SMA Support Scanner - Trading Pattern Detector

A comprehensive trading scanner that identifies specific support and bounce patterns based on SMA (Simple Moving Average) crossovers and support levels.

## 🎯 Trading Rules Implemented

The scanner follows these specific trading rules:

### 1. Initial Setup
- **SMA20 crossover SMA50 upwards**: The pattern starts when SMA20 crosses above SMA50
- **Both SMAs must have upward slope**: Confirms the price is consecutively raising

### 2. Support Pattern (S1)
- After crossover, any green candle(s) taking support on either SMA20 or SMA50
- Support means green candle body or lower wick must touch either SMA
- This becomes the first support (S1)

### 3. Bounce Pattern (B1)
- After S1, price must make a bounce/high of minimum 1% or more
- High is measured from the last green candle before bounce that intersected the SMA

### 4. Subsequent Supports (S2, S3, etc.)
- After each bounce of 1%+, when price reverses and comes back to SMA
- Green candle(s) making support on SMA20 or SMA50
- **Critical**: Current support candle's low must be higher than the previous support candle's low

### 5. Pattern Continuation
- Pattern continues until a full candle forms below SMA50
- Only S1 doesn't need a bounce before taking support
- All other supports need a bounce of 1%+ before taking support on SMA

### 6. Validation Rules
- Scanner analyzes pattern validity until S3 support
- From S3 onwards, shows every green candle that took support on either SMA
- If crossover doesn't make it to S3, pattern is invalid and scanner moves to next crossover

## 🚀 Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Running the Scanner

1. **Start the Streamlit app**:
```bash
streamlit run sma_support_scanner.py
```

2. **Configure parameters**:
   - **Stock Symbol**: Enter the stock symbol (e.g., "BAJAJ-AUTO.NS", "AAPL", "RELIANCE.NS")
   - **Timeframe**: Select from 15m, 30m, 1h, or 1d
   - **Date Range**: Choose start and end dates
   - **Bounce Threshold**: Adjust the minimum bounce percentage (default: 1.0%)

3. **Run the scanner**: Click "🚀 Run Scanner" button

### Understanding Results

The scanner provides detailed results including:

- **Date**: When the pattern event occurred
- **Support**: S1, S2, S3... for supports; B1, B2, B3... for bounces
- **Type**: Description of the event type
- **SMA_Touched**: Which SMA (20 or 50) was touched
- **Price**: Closing price at the event
- **Bounce_%**: Percentage bounce achieved (for bounce events)
- **Previous_Support_Low**: Previous support level (for comparison)

## 📊 Example Output

```
Date        Support  Type           SMA_Touched  Price    Bounce_%  Previous_Support_Low
2024-01-15  S1       First Support  SMA20        150.25   NaN       NaN
2024-01-18  B1       Bounce         NaN          152.50   1.50      NaN
2024-01-22  S2       Support 2      SMA50        151.75   NaN       150.25
2024-01-25  B2       Bounce         NaN          154.00   1.48      151.75
2024-01-29  S3       Support 3      SMA20        152.50   NaN       151.75
```

## 🔧 Technical Details

### Key Functions

- `calculate_sma()`: Calculates Simple Moving Average
- `slope()`: Calculates slope of a series
- `touches_sma()`: Checks if green candle touches SMA
- `find_crossover_up()`: Detects upward SMA crossover
- `scanner()`: Main scanning logic with state machine

### State Machine

The scanner uses a state machine to track pattern progression:

- **State 0**: Waiting for crossover
- **State 1**: Waiting for S1 (first support)
- **State 2**: Waiting for bounce
- **State 3**: Waiting for subsequent supports

## ⚠️ Important Notes

1. **Data Quality**: Ensure you have sufficient historical data for accurate SMA calculations
2. **Market Hours**: For intraday timeframes, consider market hours and gaps
3. **Pattern Validation**: The scanner validates patterns strictly according to the rules
4. **Higher Lows**: Each support must have a higher low than the previous support
5. **Continuous Slopes**: Both SMAs must maintain upward slopes throughout the pattern

## 🛠️ Customization

You can modify the scanner by adjusting:

- **Bounce threshold**: Change the minimum bounce percentage
- **SMA periods**: Modify SMA20 and SMA50 to different periods
- **Slope calculation**: Adjust the period for slope calculations
- **Support detection**: Modify the support touch criteria

## 📈 Trading Strategy

This scanner is designed for:

- **Trend following**: Identifies strong uptrends with support levels
- **Entry points**: Find optimal entry points after bounces
- **Risk management**: Use support levels as stop losses
- **Pattern recognition**: Identify recurring market structures

## 🤝 Contributing

Feel free to contribute improvements, bug fixes, or additional features to make this scanner more robust and useful for traders.

## 📄 License

This project is open source and available under the MIT License.

---

**Disclaimer**: This scanner is for educational and research purposes. Always do your own analysis and consider risk management before making trading decisions.