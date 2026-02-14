# Enhanced Options Trading Page

Improvements to the Options Trading interface and functionality.

## 🎯 Overview

The Options Trading page provides:
- Options chain visualization
- Greeks calculation
- Strategy builder
- P/L simulation

## 📊 Options Chain Display

### Layout
```
+-------------------------------------------+
|  CALLS          STRIKE          PUTS      |
+-------------------------------------------+
| Bid  Ask  Vol  | $65,000 | Bid  Ask  Vol |
| 2.5  2.6  150  | $67,500 | 1.8  1.9  120 |
| 1.8  1.9  200  | $70,000 | 2.2  2.3  180 |
| 1.2  1.3  175  | $72,500 | 2.8  2.9  140 |
+-------------------------------------------+
```

### Data Points
- Bid/Ask prices
- Volume
- Open interest
- Implied volatility
- Greeks (Delta, Gamma, Theta, Vega)

## 🎲 Greeks Display

### Option Card
```jsx
<OptionGreeks
  delta={0.45}
  gamma={0.02}
  theta={-0.05}
  vega={0.15}
  iv={65.5}
/>
```

### Greeks Explanation
| Greek | Description | Range |
|-------|-------------|-------|
| Delta | Price sensitivity | -1 to 1 |
| Gamma | Delta change rate | 0 to 0.1 |
| Theta | Time decay | Negative |
| Vega | IV sensitivity | 0 to 1 |

## 📈 Strategy Builder

### Built-in Strategies
```javascript
STRATEGIES = [
  'long_call',
  'long_put',
  'covered_call',
  'protective_put',
  'bull_call_spread',
  'bear_put_spread',
  'straddle',
  'strangle',
  'iron_condor',
  'butterfly'
]
```

### Strategy Card
```jsx
<StrategyCard
  name="Bull Call Spread"
  legs={[
    { type: 'call', strike: 70000, action: 'buy' },
    { type: 'call', strike: 75000, action: 'sell' }
  ]}
  maxProfit={2500}
  maxLoss={500}
  breakeven={70500}
/>
```

## 💰 P/L Simulation

### Payoff Chart
```jsx
<PayoffChart
  strategy={selectedStrategy}
  currentPrice={68000}
  priceRange={[50000, 90000]}
  expirationDate="2026-03-15"
/>
```

### Scenario Analysis
- Price at expiration
- IV changes
- Time decay impact
- Probability of profit

## 📡 API Integration

### Get Options Chain
```bash
GET /api/options/chain/{symbol}
```

### Calculate Greeks
```bash
POST /api/options/greeks
{
  "spot_price": 68000,
  "strike": 70000,
  "expiry_days": 30,
  "iv": 0.65,
  "option_type": "call"
}
```

### Get Strategy P/L
```bash
POST /api/options/strategy/analyze
{
  "strategy": "bull_call_spread",
  "legs": [...]
}
```

## 🎨 UI Enhancements

### Color Coding
- Green: In the money
- Red: Out of the money
- Yellow: At the money

### Interactive Features
- Click to add to strategy
- Hover for details
- Drag to adjust strikes
- Real-time P/L updates

### Responsive Design
- Desktop: Full chain view
- Tablet: Scrollable chain
- Mobile: Strike-focused view

## ⚠️ Risk Warnings

### Displayed Warnings
- Maximum loss potential
- Theta decay reminder
- IV crush risk
- Expiration reminder

### Risk Metrics
```jsx
<RiskMetrics
  maxLoss={500}
  probabilityOfProfit={0.65}
  expectedValue={150}
  riskRewardRatio={3.5}
/>
```

## ✅ Enhancements Implemented

- [x] Real-time options chain
- [x] Greeks calculation
- [x] 10 built-in strategies
- [x] P/L simulation
- [x] Scenario analysis
- [x] Risk metrics
- [x] Responsive design
- [x] Interactive strategy builder

---

**Status**: Enhanced ✅
**Last Updated**: February 2026
