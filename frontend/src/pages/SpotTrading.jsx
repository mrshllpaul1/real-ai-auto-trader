import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight,
  RefreshCw, Search, Zap, Brain, AlertTriangle, CheckCircle, XCircle,
  ArrowRight, BarChart2, Activity, Clock, ChevronDown, ChevronUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Price Ticker Component
const PriceTicker = ({ symbol, name, price, change24h, volume24h, onClick, selected }) => {
  const isPositive = change24h >= 0;
  
  return (
    <motion.div
      onClick={onClick}
      className={`p-4 rounded-xl cursor-pointer transition-all ${
        selected 
          ? 'bg-[#00FF94]/10 border-2 border-[#00FF94]' 
          : 'bg-[#111] border border-[#222] hover:border-[#444]'
      }`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      data-testid={`ticker-${symbol.toLowerCase()}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#222] flex items-center justify-center text-sm font-bold text-white">
            {symbol.slice(0, 2)}
          </div>
          <div>
            <div className="text-white font-bold text-sm">{symbol}</div>
            <div className="text-[#666] text-xs">{name}</div>
          </div>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
          isPositive ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF4444]/20 text-[#FF4444]'
        }`}>
          {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {isPositive ? '+' : ''}{change24h?.toFixed(2)}%
        </div>
      </div>
      <div className="text-xl font-bold text-white">
        ${price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 1 ? 2 : 6 })}
      </div>
      {volume24h && (
        <div className="text-xs text-[#666] mt-1">
          Vol: ${(volume24h * price / 1e6).toFixed(2)}M
        </div>
      )}
    </motion.div>
  );
};

// Order Form Component
const OrderForm = ({ symbol, pairDetails, onOrder, balance }) => {
  const [side, setSide] = useState('buy');
  const [orderType, setOrderType] = useState('market');
  const [amount, setAmount] = useState('');
  const [usdAmount, setUsdAmount] = useState('');
  const [price, setPrice] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const currentPrice = pairDetails?.price?.last || 0;
  const userBalance = pairDetails?.user_balance || 0;
  const usdBalance = balance?.usd_balance || 0;
  
  // Calculate conversion
  useEffect(() => {
    if (amount && currentPrice) {
      setUsdAmount((parseFloat(amount) * currentPrice).toFixed(2));
    }
  }, [amount, currentPrice]);
  
  const handleUsdChange = (value) => {
    setUsdAmount(value);
    if (value && currentPrice) {
      setAmount((parseFloat(value) / currentPrice).toFixed(8));
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await onOrder({
        symbol,
        side,
        order_type: orderType,
        amount: side === 'sell' ? parseFloat(amount) : undefined,
        usd_amount: side === 'buy' ? parseFloat(usdAmount) : undefined,
        price: orderType === 'limit' ? parseFloat(price) : undefined,
        use_ai_timing: useAI
      });
    } finally {
      setLoading(false);
    }
  };
  
  const setPercentage = (pct) => {
    if (side === 'buy') {
      setUsdAmount((usdBalance * pct / 100).toFixed(2));
    } else {
      setAmount((userBalance * pct / 100).toFixed(8));
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Buy/Sell Toggle */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setSide('buy')}
          className={`flex-1 py-3 rounded-xl font-bold transition-all ${
            side === 'buy' 
              ? 'bg-[#00FF94] text-black' 
              : 'bg-[#222] text-[#888] hover:bg-[#333]'
          }`}
          data-testid="buy-btn"
        >
          BUY
        </button>
        <button
          type="button"
          onClick={() => setSide('sell')}
          className={`flex-1 py-3 rounded-xl font-bold transition-all ${
            side === 'sell' 
              ? 'bg-[#FF4444] text-white' 
              : 'bg-[#222] text-[#888] hover:bg-[#333]'
          }`}
          data-testid="sell-btn"
        >
          SELL
        </button>
      </div>
      
      {/* Order Type */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setOrderType('market')}
          className={`flex-1 py-2 rounded-lg text-sm transition-all ${
            orderType === 'market' 
              ? 'bg-[#333] text-white border border-[#00FF94]' 
              : 'bg-[#222] text-[#888] border border-[#333]'
          }`}
        >
          Market
        </button>
        <button
          type="button"
          onClick={() => setOrderType('limit')}
          className={`flex-1 py-2 rounded-lg text-sm transition-all ${
            orderType === 'limit' 
              ? 'bg-[#333] text-white border border-[#00FF94]' 
              : 'bg-[#222] text-[#888] border border-[#333]'
          }`}
        >
          Limit
        </button>
      </div>
      
      {/* Limit Price */}
      {orderType === 'limit' && (
        <div>
          <label className="text-xs text-[#888] mb-1 block">Limit Price (USD)</label>
          <input
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder={currentPrice.toString()}
            className="w-full bg-[#1a1a1a] border border-[#333] rounded-xl px-4 py-3 text-white focus:border-[#00FF94] outline-none"
            data-testid="limit-price-input"
          />
        </div>
      )}
      
      {/* Amount Input */}
      <div>
        <div className="flex justify-between text-xs text-[#888] mb-1">
          <span>{side === 'buy' ? 'USD Amount' : `${symbol} Amount`}</span>
          <span>
            Available: {side === 'buy' 
              ? `$${usdBalance?.toFixed(2)}` 
              : `${userBalance?.toFixed(6)} ${symbol}`}
          </span>
        </div>
        {side === 'buy' ? (
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#888]">$</span>
            <input
              type="number"
              value={usdAmount}
              onChange={(e) => handleUsdChange(e.target.value)}
              placeholder="0.00"
              className="w-full bg-[#1a1a1a] border border-[#333] rounded-xl pl-8 pr-4 py-3 text-white focus:border-[#00FF94] outline-none"
              data-testid="usd-amount-input"
            />
          </div>
        ) : (
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00000000"
            className="w-full bg-[#1a1a1a] border border-[#333] rounded-xl px-4 py-3 text-white focus:border-[#00FF94] outline-none"
            data-testid="crypto-amount-input"
          />
        )}
      </div>
      
      {/* Quick Percentage Buttons */}
      <div className="flex gap-2">
        {[25, 50, 75, 100].map(pct => (
          <button
            key={pct}
            type="button"
            onClick={() => setPercentage(pct)}
            className="flex-1 py-2 bg-[#222] rounded-lg text-xs text-[#888] hover:bg-[#333] hover:text-white transition-colors"
          >
            {pct}%
          </button>
        ))}
      </div>
      
      {/* Conversion Display */}
      {amount && currentPrice && (
        <div className="p-3 bg-[#1a1a1a] rounded-xl text-sm">
          <div className="flex justify-between text-[#888]">
            <span>You will {side === 'buy' ? 'receive' : 'get'}</span>
            <span className="text-white font-medium">
              {side === 'buy' 
                ? `≈ ${parseFloat(amount).toFixed(6)} ${symbol}`
                : `≈ $${(parseFloat(amount) * currentPrice).toFixed(2)}`
              }
            </span>
          </div>
        </div>
      )}
      
      {/* AI Timing Toggle */}
      <div 
        onClick={() => setUseAI(!useAI)}
        className={`p-3 rounded-xl cursor-pointer transition-all ${
          useAI 
            ? 'bg-[#9D00FF]/20 border border-[#9D00FF]' 
            : 'bg-[#1a1a1a] border border-[#333]'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain size={16} className={useAI ? 'text-[#9D00FF]' : 'text-[#666]'} />
            <span className="text-sm text-white">Use AI Signal Analysis</span>
          </div>
          <div className={`w-10 h-5 rounded-full transition-colors ${useAI ? 'bg-[#9D00FF]' : 'bg-[#333]'}`}>
            <div className={`w-4 h-4 rounded-full bg-white transition-transform mt-0.5 ${useAI ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'}`} />
          </div>
        </div>
      </div>
      
      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || !amount || (orderType === 'limit' && !price)}
        className={`w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 ${
          side === 'buy'
            ? 'bg-[#00FF94] text-black hover:bg-[#00DD80] disabled:bg-[#00FF94]/30'
            : 'bg-[#FF4444] text-white hover:bg-[#DD3333] disabled:bg-[#FF4444]/30'
        } disabled:cursor-not-allowed`}
        data-testid="submit-order-btn"
      >
        {loading ? (
          <RefreshCw size={20} className="animate-spin" />
        ) : (
          <>
            {side === 'buy' ? 'Buy' : 'Sell'} {symbol}
            <ArrowRight size={20} />
          </>
        )}
      </button>
    </form>
  );
};

// AI Signal Card
const AISignalCard = ({ signal }) => {
  if (!signal) return null;
  
  const getSignalColor = (score) => {
    if (score > 0.3) return '#00FF94';
    if (score < -0.3) return '#FF4444';
    return '#FFB800';
  };
  
  const signalColor = getSignalColor(signal.score);
  
  return (
    <div className="bg-[#111] border border-[#222] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain size={18} className="text-[#9D00FF]" />
        <span className="text-white font-bold">AI Analysis</span>
      </div>
      
      <div className="flex items-center justify-between mb-4">
        <div className="text-2xl font-bold" style={{ color: signalColor }}>
          {signal.signal?.toUpperCase() || 'NEUTRAL'}
        </div>
        <div className="text-right">
          <div className="text-xs text-[#888]">Confidence</div>
          <div className="text-lg font-bold text-white">{(signal.confidence * 100 || 0).toFixed(0)}%</div>
        </div>
      </div>
      
      <div className="h-2 bg-[#222] rounded-full overflow-hidden mb-4">
        <div 
          className="h-full rounded-full transition-all"
          style={{ 
            width: `${(signal.score + 1) * 50}%`, 
            backgroundColor: signalColor 
          }}
        />
      </div>
      
      <div className="text-sm text-[#888]">
        {signal.recommendation || 'No specific recommendation'}
      </div>
      
      {signal.components && (
        <div className="mt-4 pt-4 border-t border-[#222]">
          <div className="text-xs text-[#888] mb-2">Signal Components</div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(signal.components).map(([key, value]) => {
              // Format value based on type
              let displayValue;
              let colorClass = 'text-[#888]';
              
              if (typeof value === 'number') {
                displayValue = value.toFixed(2);
                colorClass = value > 0 ? 'text-[#00FF94]' : value < 0 ? 'text-[#FF4444]' : 'text-[#888]';
              } else if (typeof value === 'object' && value !== null) {
                // Extract score or signal from nested objects
                const score = value.score ?? value.signal ?? value.value;
                if (typeof score === 'number') {
                  displayValue = score.toFixed(2);
                  colorClass = score > 0 ? 'text-[#00FF94]' : score < 0 ? 'text-[#FF4444]' : 'text-[#888]';
                } else {
                  displayValue = score ? String(score) : '-';
                }
              } else {
                displayValue = value ? String(value) : '-';
              }
              
              return (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-[#666] capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className={colorClass}>{displayValue}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced AI Recommendation Card Component
const EnhancedRecommendationCard = ({ rec, onClick }) => {
  const getActionColor = (actionColor) => {
    switch(actionColor) {
      case 'success': return { bg: 'bg-[#00FF94]/20', text: 'text-[#00FF94]', border: 'border-[#00FF94]/30' };
      case 'danger': return { bg: 'bg-[#FF4444]/20', text: 'text-[#FF4444]', border: 'border-[#FF4444]/30' };
      default: return { bg: 'bg-[#FFB800]/20', text: 'text-[#FFB800]', border: 'border-[#FFB800]/30' };
    }
  };
  
  const colors = getActionColor(rec.action_color);
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div 
      className="p-3 bg-[#1a1a1a] rounded-lg border border-[#222] hover:border-[#444] transition-all cursor-pointer"
      onClick={() => onClick && onClick(rec.symbol)}
    >
      {/* Header Row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#222] flex items-center justify-center text-xs font-bold text-white">
            {rec.symbol.slice(0, 2)}
          </div>
          <div>
            <div className="font-bold text-white flex items-center gap-2">
              {rec.symbol}
              {rec.rank && rec.rank <= 3 && (
                <span className="text-[10px] bg-[#FFB800]/20 text-[#FFB800] px-1.5 py-0.5 rounded">
                  #{rec.rank}
                </span>
              )}
            </div>
            <div className="text-xs text-[#666]">${rec.price?.toFixed(2)}</div>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-1">
          <div className={`px-2 py-1 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
            {rec.action}
          </div>
          {rec.historical_accuracy && (
            <div className="flex items-center gap-1 text-[10px] text-[#888]">
              <CheckCircle size={10} />
              {(rec.historical_accuracy * 100).toFixed(0)}% acc
            </div>
          )}
        </div>
      </div>
      
      {/* Confidence and Score Bars */}
      <div className="space-y-2 mb-3">
        {/* Confidence Bar */}
        <div>
          <div className="flex justify-between text-[10px] text-[#888] mb-1">
            <span>Confidence</span>
            <span className="text-white font-medium">{(rec.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-[#222] rounded-full overflow-hidden">
            <div 
              className="h-full bg-[#9D00FF] rounded-full transition-all"
              style={{ width: `${rec.confidence * 100}%` }}
            />
          </div>
        </div>
        
        {/* Trend Strength */}
        {rec.trend_strength !== undefined && (
          <div>
            <div className="flex justify-between text-[10px] text-[#888] mb-1">
              <span>Trend Strength</span>
              <span className="text-white font-medium">{(rec.trend_strength * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-[#222] rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-[#00FF94] to-[#FFB800] rounded-full transition-all"
                style={{ width: `${rec.trend_strength * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Key Metrics Row */}
      <div className="grid grid-cols-3 gap-2 mb-2">
        {rec.potential_return !== undefined && (
          <div className="text-center p-1.5 bg-[#111] rounded">
            <div className="text-[10px] text-[#666]">Potential</div>
            <div className="text-xs text-[#00FF94] font-medium">+{rec.potential_return}%</div>
          </div>
        )}
        {rec.risk_reward_ratio !== undefined && (
          <div className="text-center p-1.5 bg-[#111] rounded">
            <div className="text-[10px] text-[#666]">R/R</div>
            <div className="text-xs text-white font-medium">{rec.risk_reward_ratio}x</div>
          </div>
        )}
        {rec.change_24h !== undefined && (
          <div className="text-center p-1.5 bg-[#111] rounded">
            <div className="text-[10px] text-[#666]">24h</div>
            <div className={`text-xs font-medium ${rec.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF4444]'}`}>
              {rec.change_24h >= 0 ? '+' : ''}{rec.change_24h.toFixed(1)}%
            </div>
          </div>
        )}
      </div>
      
      {/* Expandable Details */}
      <button
        onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        className="w-full flex items-center justify-between text-xs text-[#888] hover:text-white transition-colors"
      >
        <span>{rec.recommendation}</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="mt-3 pt-3 border-t border-[#222] space-y-2"
        >
          {/* Price Targets */}
          {(rec.price_target || rec.stop_loss) && (
            <div className="grid grid-cols-2 gap-2">
              {rec.price_target && (
                <div className="p-2 bg-[#00FF94]/10 border border-[#00FF94]/30 rounded">
                  <div className="text-[10px] text-[#888]">Target</div>
                  <div className="text-sm text-[#00FF94] font-medium">${rec.price_target}</div>
                </div>
              )}
              {rec.stop_loss && (
                <div className="p-2 bg-[#FF4444]/10 border border-[#FF4444]/30 rounded">
                  <div className="text-[10px] text-[#888]">Stop Loss</div>
                  <div className="text-sm text-[#FF4444] font-medium">${rec.stop_loss}</div>
                </div>
              )}
            </div>
          )}
          
          {/* Component Signals */}
          {rec.components && Object.keys(rec.components).length > 0 && (
            <div>
              <div className="text-[10px] text-[#888] mb-1">Component Signals</div>
              <div className="grid grid-cols-2 gap-1">
                {Object.entries(rec.components).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-[10px] p-1 bg-[#111] rounded">
                    <span className="text-[#666] capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className={
                      typeof value === 'object' && value.score 
                        ? (value.score > 0 ? 'text-[#00FF94]' : value.score < 0 ? 'text-[#FF4444]' : 'text-[#888]')
                        : 'text-[#888]'
                    }>
                      {typeof value === 'object' && value.score ? value.score.toFixed(2) : '-'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

// Holdings Table
const HoldingsTable = ({ holdings }) => {
  if (!holdings || holdings.length === 0) {
    return (
      <div className="text-center py-8 text-[#666]">
        <DollarSign size={32} className="mx-auto mb-2 opacity-50" />
        <p>No crypto holdings</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {holdings.map((holding) => (
        <div 
          key={holding.symbol}
          className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-xl"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#222] flex items-center justify-center text-xs font-bold text-white">
              {holding.symbol.slice(0, 2)}
            </div>
            <div>
              <div className="text-white font-medium">{holding.symbol}</div>
              <div className="text-xs text-[#666]">{holding.amount.toFixed(6)}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-white font-medium">${holding.usd_value?.toFixed(2)}</div>
            <div className="text-xs text-[#666]">@ ${holding.price?.toFixed(2)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

const SpotTrading = () => {
  const [pairs, setPairs] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [pairDetails, setPairDetails] = useState(null);
  const [balance, setBalance] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [recommendationsSummary, setRecommendationsSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [orderResult, setOrderResult] = useState(null);
  const [showOrderResult, setShowOrderResult] = useState(false);
  const [tradingStatus, setTradingStatus] = useState(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recFilter, setRecFilter] = useState('all'); // all, bullish, bearish, high_confidence
  
  // Fetch trading status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/spot/status`);
      if (res.ok) {
        setTradingStatus(await res.json());
      }
    } catch (err) {
      console.error('Status fetch error:', err);
    }
  }, []);
  
  // Fetch all pairs with prices
  const fetchPairs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/spot/pairs`);
      if (res.ok) {
        const data = await res.json();
        setPairs(data.pairs || []);
      }
    } catch (err) {
      console.error('Pairs fetch error:', err);
    }
  }, []);
  
  // Fetch selected pair details
  const fetchPairDetails = useCallback(async (symbol) => {
    try {
      const res = await fetch(`${API_URL}/api/spot/pair/${symbol}`);
      if (res.ok) {
        setPairDetails(await res.json());
      }
    } catch (err) {
      console.error('Pair details error:', err);
    }
  }, []);
  
  // Fetch user balance
  const fetchBalance = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/spot/balance`);
      if (res.ok) {
        setBalance(await res.json());
      }
    } catch (err) {
      console.error('Balance fetch error:', err);
    }
  }, []);
  
  // Fetch AI recommendations
  const fetchRecommendations = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/spot/ai-recommendations?min_confidence=0.5&limit=15`);
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
        setRecommendationsSummary(data.summary || null);
      }
    } catch (err) {
      console.error('Recommendations error:', err);
    }
  }, []);
  
  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStatus(),
        fetchPairs(),
        fetchBalance(),
        fetchRecommendations()
      ]);
      setLoading(false);
    };
    
    loadData();
    
    // Refresh prices every 10 seconds
    const interval = setInterval(fetchPairs, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchPairs, fetchBalance, fetchRecommendations]);
  
  // Fetch details when symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      fetchPairDetails(selectedSymbol);
    }
  }, [selectedSymbol, fetchPairDetails]);
  
  // Handle order placement
  const handleOrder = async (orderData) => {
    try {
      const res = await fetch(`${API_URL}/api/spot/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });
      
      const result = await res.json();
      
      if (res.ok) {
        setOrderResult({ success: true, ...result });
        fetchBalance(); // Refresh balance
      } else {
        setOrderResult({ success: false, error: result.detail || 'Order failed' });
      }
      
      setShowOrderResult(true);
      setTimeout(() => setShowOrderResult(false), 5000);
    } catch (err) {
      setOrderResult({ success: false, error: err.message });
      setShowOrderResult(true);
      setTimeout(() => setShowOrderResult(false), 5000);
    }
  };
  
  // Filter pairs by search
  const filteredPairs = pairs.filter(p => 
    p.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  // Filter recommendations
  const filteredRecommendations = recommendations.filter(rec => {
    if (recFilter === 'bullish') return rec.score > 0.2;
    if (recFilter === 'bearish') return rec.score < -0.2;
    if (recFilter === 'high_confidence') return rec.confidence > 0.7;
    return true; // 'all'
  });
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] p-6 flex items-center justify-center">
        <div className="flex items-center gap-3 text-[#888]">
          <RefreshCw size={24} className="animate-spin" />
          <span>Loading spot trading...</span>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="spot-trading-page">
      {/* Order Result Toast */}
      <AnimatePresence>
        {showOrderResult && orderResult && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className={`fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg flex items-center gap-3 ${
              orderResult.success 
                ? 'bg-[#00FF94]/20 border border-[#00FF94]' 
                : 'bg-[#FF4444]/20 border border-[#FF4444]'
            }`}
          >
            {orderResult.success ? (
              <CheckCircle size={20} className="text-[#00FF94]" />
            ) : (
              <XCircle size={20} className="text-[#FF4444]" />
            )}
            <div>
              <div className={`font-medium ${orderResult.success ? 'text-[#00FF94]' : 'text-[#FF4444]'}`}>
                {orderResult.success ? 'Order Placed!' : 'Order Failed'}
              </div>
              <div className="text-xs text-[#888]">
                {orderResult.success 
                  ? `${orderResult.details?.side} ${orderResult.details?.volume?.toFixed(6)} ${orderResult.details?.symbol}`
                  : orderResult.error}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
              <Activity className="text-[#00FF94]" />
              Spot Trading
            </h1>
            <p className="text-[#888] mt-1">Buy and sell crypto with AI-powered signals</p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Trading Status */}
            {tradingStatus?.budget && (
              <div className={`px-4 py-2 rounded-xl text-sm flex items-center gap-2 ${
                tradingStatus.budget.real_trading_enabled
                  ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/30'
                  : 'bg-[#FFB800]/20 text-[#FFB800] border border-[#FFB800]/30'
              }`}>
                {tradingStatus.budget.real_trading_enabled ? (
                  <>
                    <Zap size={14} />
                    Live Trading
                  </>
                ) : (
                  <>
                    <AlertTriangle size={14} />
                    Paper Mode
                  </>
                )}
              </div>
            )}
            
            <button
              onClick={() => { fetchPairs(); fetchBalance(); }}
              className="px-4 py-2 bg-[#222] rounded-xl text-white flex items-center gap-2 hover:bg-[#333] transition-colors"
              data-testid="refresh-btn"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
        </div>
      </motion.div>
      
      {/* Balance Overview */}
      {balance && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
        >
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign size={16} className="text-[#00FF94]" />
              <span className="text-xs text-[#888]">USD Balance</span>
            </div>
            <div className="text-2xl font-bold text-white">${balance.usd_balance?.toFixed(2)}</div>
          </div>
          
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart2 size={16} className="text-[#9D00FF]" />
              <span className="text-xs text-[#888]">Crypto Value</span>
            </div>
            <div className="text-2xl font-bold text-white">${balance.total_crypto_value?.toFixed(2)}</div>
          </div>
          
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={16} className="text-[#FFB800]" />
              <span className="text-xs text-[#888]">Portfolio Total</span>
            </div>
            <div className="text-2xl font-bold text-white">${balance.total_portfolio_value?.toFixed(2)}</div>
          </div>
          
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock size={16} className="text-[#FF4444]" />
              <span className="text-xs text-[#888]">Holdings</span>
            </div>
            <div className="text-2xl font-bold text-white">{balance.holdings_count}</div>
          </div>
        </motion.div>
      )}
      
      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - Pair Selection */}
        <div className="lg:col-span-1 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search pairs..."
              className="w-full bg-[#111] border border-[#222] rounded-xl pl-10 pr-4 py-3 text-white focus:border-[#00FF94] outline-none"
              data-testid="search-input"
            />
          </div>
          
          {/* Pairs Grid */}
          <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto scrollbar-thin">
            {filteredPairs.map(pair => (
              <PriceTicker
                key={pair.symbol}
                symbol={pair.symbol}
                name={pair.name}
                price={pair.price}
                change24h={pair.change_24h}
                volume24h={pair.volume_24h}
                onClick={() => setSelectedSymbol(pair.symbol)}
                selected={selectedSymbol === pair.symbol}
              />
            ))}
          </div>
          
          {/* Holdings */}
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <BarChart2 size={16} className="text-[#00FF94]" />
              Your Holdings
            </h3>
            <HoldingsTable holdings={balance?.holdings} />
          </div>
        </div>
        
        {/* Middle Column - Trading Panel */}
        <div className="lg:col-span-1 space-y-4">
          {/* Selected Pair Info */}
          {pairDetails && (
            <div className="bg-[#111] border border-[#222] rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-2xl font-bold text-white">{pairDetails.symbol}</div>
                  <div className="text-sm text-[#888]">{pairDetails.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">
                    ${pairDetails.price?.last?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: pairDetails.price?.last > 1 ? 2 : 6 })}
                  </div>
                  <div className={`text-sm ${pairDetails.price?.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF4444]'}`}>
                    {pairDetails.price?.change_24h >= 0 ? '+' : ''}{pairDetails.price?.change_24h?.toFixed(2)}% 24h
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">24h High</div>
                  <div className="text-sm text-white font-medium">${pairDetails.price?.high_24h?.toFixed(2)}</div>
                </div>
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">24h Low</div>
                  <div className="text-sm text-white font-medium">${pairDetails.price?.low_24h?.toFixed(2)}</div>
                </div>
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">Spread</div>
                  <div className="text-sm text-white font-medium">{pairDetails.price?.spread?.toFixed(4)}%</div>
                </div>
              </div>
              
              {pairDetails.user_balance > 0 && (
                <div className="mt-4 p-3 bg-[#1a1a1a] rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#888]">Your Balance</span>
                    <span className="text-white font-medium">
                      {pairDetails.user_balance?.toFixed(6)} {pairDetails.symbol}
                      <span className="text-[#666] ml-2">(${pairDetails.user_balance_usd?.toFixed(2)})</span>
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Order Form */}
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
              <ArrowUpRight size={16} className="text-[#00FF94]" />
              Place Order
            </h3>
            <OrderForm 
              symbol={selectedSymbol}
              pairDetails={pairDetails}
              onOrder={handleOrder}
              balance={balance}
            />
          </div>
        </div>
        
        {/* Right Column - AI Signals */}
        <div className="lg:col-span-1 space-y-4">
          {/* AI Signal for Selected Pair */}
          {pairDetails?.ai_signal && (
            <AISignalCard signal={pairDetails.ai_signal} />
          )}
          
          {/* AI Recommendations */}
          <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
            <button
              onClick={() => setShowRecommendations(!showRecommendations)}
              className="w-full p-4 flex items-center justify-between hover:bg-[#1a1a1a] transition-colors"
              data-testid="toggle-recommendations-btn"
            >
              <div className="flex items-center gap-2">
                <Brain size={18} className="text-[#9D00FF]" />
                <span className="text-white font-bold">AI Recommendations</span>
                {recommendationsSummary && (
                  <span className="text-xs text-[#888] bg-[#222] px-2 py-1 rounded-full">
                    {recommendationsSummary.high_confidence_count} high confidence
                  </span>
                )}
              </div>
              {showRecommendations ? <ChevronUp size={18} className="text-[#888]" /> : <ChevronDown size={18} className="text-[#888]" />}
            </button>
            
            <AnimatePresence>
              {showRecommendations && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-[#222]"
                >
                  {/* Summary Stats */}
                  {recommendationsSummary && (
                    <div className="p-4 bg-[#1a1a1a] border-b border-[#222]">
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div>
                          <div className="text-xs text-[#888]">Bullish</div>
                          <div className="text-lg font-bold text-[#00FF94]">
                            {recommendationsSummary.bullish_count}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-[#888]">Neutral</div>
                          <div className="text-lg font-bold text-[#FFB800]">
                            {recommendationsSummary.neutral_count}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-[#888]">Bearish</div>
                          <div className="text-lg font-bold text-[#FF4444]">
                            {recommendationsSummary.bearish_count}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs">
                        <span className="text-[#666]">Avg Confidence</span>
                        <span className="text-white font-medium">
                          {(recommendationsSummary.avg_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )}
                  
                  {/* Filter Buttons */}
                  <div className="p-4 border-b border-[#222] flex gap-2 flex-wrap">
                    <button
                      onClick={() => setRecFilter('all')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        recFilter === 'all'
                          ? 'bg-[#9D00FF] text-white'
                          : 'bg-[#222] text-[#888] hover:bg-[#333]'
                      }`}
                    >
                      All ({recommendations.length})
                    </button>
                    <button
                      onClick={() => setRecFilter('bullish')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        recFilter === 'bullish'
                          ? 'bg-[#00FF94] text-black'
                          : 'bg-[#222] text-[#888] hover:bg-[#333]'
                      }`}
                    >
                      Bullish ({recommendations.filter(r => r.score > 0.2).length})
                    </button>
                    <button
                      onClick={() => setRecFilter('bearish')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        recFilter === 'bearish'
                          ? 'bg-[#FF4444] text-white'
                          : 'bg-[#222] text-[#888] hover:bg-[#333]'
                      }`}
                    >
                      Bearish ({recommendations.filter(r => r.score < -0.2).length})
                    </button>
                    <button
                      onClick={() => setRecFilter('high_confidence')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        recFilter === 'high_confidence'
                          ? 'bg-[#FFB800] text-black'
                          : 'bg-[#222] text-[#888] hover:bg-[#333]'
                      }`}
                    >
                      High Confidence ({recommendations.filter(r => r.confidence > 0.7).length})
                    </button>
                  </div>
                  
                  {/* Recommendations List */}
                  <div className="p-4 max-h-[500px] overflow-y-auto space-y-2">
                    {filteredRecommendations.map((rec, idx) => (
                      <EnhancedRecommendationCard
                        key={idx}
                        rec={rec}
                        onClick={(symbol) => setSelectedSymbol(symbol)}
                      />
                    ))}
                    
                    {filteredRecommendations.length === 0 && (
                      <div className="text-center py-8 text-[#666]">
                        <Brain size={32} className="mx-auto mb-2 opacity-50" />
                        <p>No recommendations match this filter</p>
                      </div>
                    )}
                    
                    {recommendations.length === 0 && (
                      <div className="text-center py-8 text-[#666]">
                        <Brain size={32} className="mx-auto mb-2 opacity-50" />
                        <p>No recommendations available</p>
                        <p className="text-xs mt-2">Enable AI features to see recommendations</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          {/* Trading Tips */}
          <div className="bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10 border border-[#333] rounded-xl p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="text-[#FFB800] flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-white font-bold mb-2">Trading Tips</h3>
                <ul className="text-sm text-[#888] space-y-1">
                  <li>• Always check AI signals before trading</li>
                  <li>• Use limit orders for better prices</li>
                  <li>• Set stop-losses to protect your capital</li>
                  <li>• Don't invest more than you can afford</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpotTrading;
