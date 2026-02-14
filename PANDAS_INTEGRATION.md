# Pandas Integration

Pandas is included in the backend requirements for data analysis.

## 📦 Installation

Pandas is already included in `backend/requirements.txt`:

```
pandas==2.3.3
```

## 📊 Usage Examples

### Data Analysis
```python
import pandas as pd

# Load OHLCV data
df = pd.DataFrame(ohlcv_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Calculate returns
df['returns'] = df['close'].pct_change()

# Calculate moving averages
df['sma_20'] = df['close'].rolling(20).mean()
df['sma_50'] = df['close'].rolling(50).mean()
```

### Technical Indicators
```python
# RSI calculation
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = calculate_rsi(df)
```

### Backtesting
```python
# Calculate strategy performance
def backtest_strategy(df, signals):
    df['signal'] = signals
    df['position'] = df['signal'].shift(1)
    df['strategy_returns'] = df['position'] * df['returns']
    
    total_return = df['strategy_returns'].sum()
    sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252)
    max_drawdown = (df['strategy_returns'].cumsum() - 
                   df['strategy_returns'].cumsum().cummax()).min()
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown
    }
```

### Data Export
```python
# Export to CSV
df.to_csv('trading_data.csv')

# Export to JSON
df.to_json('trading_data.json', orient='records')
```

## 🔗 Related Dependencies

```
numpy==2.4.1
scipy==1.16.0
scikit-learn==1.7.1
```

## ✅ Status

- [x] Pandas installed (v2.3.3)
- [x] NumPy integration
- [x] Used in data analysis
- [x] Used in backtesting
- [x] Used in feature engineering

---

**Status**: Installed ✅
**Version**: 2.3.3
