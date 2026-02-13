import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight,
  RefreshCw, Search, Zap, Brain, AlertTriangle, CheckCircle, XCircle,
  ArrowRight, BarChart2, Activity, Clock, ChevronDown, ChevronUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  StatsGridSkeleton, 
  TradingPanelSkeleton, 
  TableSkeleton, 
  CardSkeleton 
} from '../components/LoadingSkeletons';

const API_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

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
          {isPositive ? '+' : ''}{(change24h ?? 0).toFixed(2)}%
        </div>
      </div>
      <div className="text-xl font-bold text-white">
        ${(price ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: price > 1 ? 2 : 6 })}
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
              ? `$${(usdBalance ?? 0).toFixed(2)}` 
              : `${(userBalance ?? 0).toFixed(6)} ${symbol}`}
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
  
  // Extract composite data from signal
  const composite = signal.composite || {};
  const score = composite.score || signal.score || 50;
  const confidence = composite.confidence || signal.confidence || 0;
  const signalText = composite.signal || signal.signal || 'hold';
  const components = signal.components || {};
  
  const getSignalColor = (s) => {
    if (s >= 60) return '#00FF94';  // Bullish
    if (s <= 40) return '#FF4444';  // Bearish
    return '#FFB800';  // Neutral
  };
  
  const signalColor = getSignalColor(score);
  
  return (
    <div className="bg-[#111] border border-[#222] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain size={18} className="text-[#9D00FF]" />
        <span className="text-white font-bold">AI Analysis</span>
      </div>
      
      <div className="flex items-center justify-between mb-4">
        <div className="text-2xl font-bold" style={{ color: signalColor }}>
          {signalText.toUpperCase().replace('_', ' ')}
        </div>
        <div className="text-right">
          <div className="text-xs text-[#888]">Confidence</div>
          <div className="text-lg font-bold text-white">{confidence.toFixed(0)}%</div>
        </div>
      </div>
      
      <div className="h-2 bg-[#222] rounded-full overflow-hidden mb-4">
        <div 
          className="h-full rounded-full transition-all"
          style={{ 
            width: `${Math.min(100, Math.max(0, score))}%`, 
            backgroundColor: signalColor 
          }}
        />
      </div>
      
      <div className="text-sm text-[#888]">
        Score: {score.toFixed(1)} / 100 | Models: {composite.models_used || 0}
      </div>
      
      {Object.keys(components).length > 0 && (
        <div className="mt-4 pt-4 border-t border-[#222]">
          <div className="text-xs text-[#888] mb-2">Signal Components</div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(components).map(([key, value]) => {
              // Format value based on type
              let displayValue;
              let colorClass = 'text-[#888]';
              
              if (typeof value === 'number') {
                displayValue = value.toFixed(2);
                colorClass = value >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]';
              } else if (typeof value === 'object' && value !== null) {
                // Extract score from nested objects
                const componentScore = value.score ?? value.signal ?? value.value;
                if (typeof componentScore === 'number') {
                  displayValue = componentScore.toFixed(2);
                  colorClass = componentScore >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]';
                } else {
                  displayValue = componentScore ? String(componentScore) : '-';
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
              <div className="text-xs text-[#666]">{(holding?.amount ?? 0).toFixed(6)}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-white font-medium">${(holding?.usd_value ?? 0).toFixed(2)}</div>
            <div className="text-xs text-[#666]">@ ${(holding?.price ?? 0).toFixed(2)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

const SpotTrading = ({ embedded = false }) => {
  const [pairs, setPairs] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [pairDetails, setPairDetails] = useState(null);
  const [balance, setBalance] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [orderResult, setOrderResult] = useState(null);
  const [showOrderResult, setShowOrderResult] = useState(false);
  const [tradingStatus, setTradingStatus] = useState(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  
  // Helper to safely fetch JSON with retry
  const safeFetchJSON = async (url, retries = 2) => {
    for (let i = 0; i <= retries; i++) {
      try {
        const res = await fetch(url);
        const contentType = res.headers.get('content-type');
        
        // Check if response is JSON before parsing
        if (res.ok && contentType && contentType.includes('application/json')) {
          const data = await res.json();
          console.log(`[SpotTrading] Fetch success: ${url}`, data ? 'Data received' : 'No data');
          return data;
        } else if (!res.ok) {
          console.warn(`[SpotTrading] Fetch ${url} failed with status ${res.status}, retry ${i + 1}/${retries + 1}`);
          if (i < retries) {
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
          }
        } else {
          // Log what we actually received for debugging
          const text = await res.text();
          console.warn(`[SpotTrading] Invalid content type for ${url}: ${contentType}, body length: ${text.length}`);
          console.warn(`[SpotTrading] Response preview:`, text.substring(0, 200));
        }
      } catch (err) {
        console.error(`[SpotTrading] Fetch ${url} error:`, err.message);
        if (i < retries) {
          await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
      }
    }
    console.error(`[SpotTrading] All retries failed for ${url}`);
    return null;
  };

  // Refresh functions for manual refresh
  const refreshData = async () => {
    console.log('[SpotTrading] Manual refresh triggered');
    const [pairsData, balanceData] = await Promise.all([
      safeFetchJSON(`${API_URL}/api/spot/pairs`),
      safeFetchJSON(`${API_URL}/api/spot/balance`)
    ]);
    
    if (pairsData?.pairs) {
      setPairs(pairsData.pairs);
    }
    if (balanceData) {
      setBalance(balanceData);
    }
  };
  
  // Fetch selected pair details
  const fetchPairDetails = useCallback(async (symbol) => {
    const data = await safeFetchJSON(`${API_URL}/api/spot/pair/${symbol}`);
    if (data) setPairDetails(data);
  }, []);
  
  // Initial load
  useEffect(() => {
    console.log('[SpotTrading] Component mounted, starting data load...');
    let isMounted = true;
    
    const loadData = async () => {
      setLoading(true);
      
      // Fetch non-Kraken data in parallel first (fast)
      const [statusData, recsData] = await Promise.all([
        safeFetchJSON(`${API_URL}/api/spot/status`),
        safeFetchJSON(`${API_URL}/api/spot/ai-recommendations`)
      ]);
      
      if (!isMounted) return;
      if (statusData) setTradingStatus(statusData);
      if (recsData?.recommendations) setRecommendations(recsData.recommendations);
      
      // Then fetch Kraken data sequentially to avoid rate limits
      const pairsData = await safeFetchJSON(`${API_URL}/api/spot/pairs`);
      if (!isMounted) return;
      if (pairsData?.pairs) {
        setPairs(pairsData.pairs);
        console.log('[SpotTrading] Pairs loaded:', pairsData.pairs.length);
      }
      
      // Small delay before balance
      await new Promise(r => setTimeout(r, 50));
      
      const balanceData = await safeFetchJSON(`${API_URL}/api/spot/balance`);
      if (!isMounted) return;
      if (balanceData) {
        setBalance(balanceData);
        console.log('[SpotTrading] Balance loaded:', balanceData.holdings?.length, 'holdings');
      }
      
      setLoading(false);
    };
    
    loadData();
    
    // Refresh prices every 15 seconds (increased from 10 to reduce API load)
    const interval = setInterval(async () => {
      if (!isMounted) return;
      const data = await safeFetchJSON(`${API_URL}/api/spot/pairs`);
      if (data?.pairs && isMounted) {
        setPairs(data.pairs);
      }
    }, 15000);
    
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []); // Empty dependency array - only run once on mount
  
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
        refreshData(); // Refresh balance and pairs
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
  
  if (loading) {
    return <PageLoadingSkeleton />;
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
                  ? `${orderResult.details?.side} ${(orderResult.details?.volume ?? 0).toFixed(6)} ${orderResult.details?.symbol}`
                  : orderResult.error}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Header - hidden when embedded */}
      {!embedded && (
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
                onClick={refreshData}
                className="px-4 py-2 bg-[#222] rounded-xl text-white flex items-center gap-2 hover:bg-[#333] transition-colors"
                data-testid="refresh-btn"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
          </div>
        </motion.div>
      )}
      
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
            <div className="text-2xl font-bold text-white">${(balance?.usd_balance ?? 0).toFixed(2)}</div>
          </div>
          
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart2 size={16} className="text-[#9D00FF]" />
              <span className="text-xs text-[#888]">Crypto Value</span>
            </div>
            <div className="text-2xl font-bold text-white">${(balance?.total_crypto_value ?? 0).toFixed(2)}</div>
          </div>
          
          <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={16} className="text-[#FFB800]" />
              <span className="text-xs text-[#888]">Portfolio Total</span>
            </div>
            <div className="text-2xl font-bold text-white">${(balance?.total_portfolio_value ?? 0).toFixed(2)}</div>
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
                    ${(pairDetails?.price?.last ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: pairDetails.price?.last > 1 ? 2 : 6 })}
                  </div>
                  <div className={`text-sm ${pairDetails.price?.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF4444]'}`}>
                    {pairDetails.price?.change_24h >= 0 ? '+' : ''}{(pairDetails?.price?.change_24h ?? 0).toFixed(2)}% 24h
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">24h High</div>
                  <div className="text-sm text-white font-medium">${(pairDetails?.price?.high_24h ?? 0).toFixed(2)}</div>
                </div>
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">24h Low</div>
                  <div className="text-sm text-white font-medium">${(pairDetails?.price?.low_24h ?? 0).toFixed(2)}</div>
                </div>
                <div className="bg-[#1a1a1a] rounded-lg p-2">
                  <div className="text-xs text-[#666]">Spread</div>
                  <div className="text-sm text-white font-medium">{(pairDetails?.price?.spread ?? 0).toFixed(4)}%</div>
                </div>
              </div>
              
              {pairDetails.user_balance > 0 && (
                <div className="mt-4 p-3 bg-[#1a1a1a] rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#888]">Your Balance</span>
                    <span className="text-white font-medium">
                      {(pairDetails?.user_balance ?? 0).toFixed(6)} {pairDetails.symbol}
                      <span className="text-[#666] ml-2">(${(pairDetails?.user_balance_usd ?? 0).toFixed(2)})</span>
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
                {recommendations.length > 0 && (
                  <span className="text-xs text-[#888] bg-[#222] px-2 py-1 rounded-full">
                    {recommendations.length}
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
                  <div className="p-4 max-h-[400px] overflow-y-auto space-y-2">
                    {recommendations.map((rec, idx) => (
                      <div 
                        key={idx}
                        onClick={() => setSelectedSymbol(rec.symbol)}
                        className="p-3 bg-[#1a1a1a] rounded-lg cursor-pointer hover:bg-[#222] transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{rec.symbol}</span>
                            <span className="text-xs text-[#666]">${(rec?.price ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: rec.price > 1 ? 2 : 6 })}</span>
                          </div>
                          <div className={`px-2 py-1 rounded text-xs font-medium ${
                            rec.score >= 60 ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                            rec.score <= 40 ? 'bg-[#FF4444]/20 text-[#FF4444]' :
                            'bg-[#FFB800]/20 text-[#FFB800]'
                          }`}>
                            {rec.signal?.toUpperCase()?.replace('_', ' ')}
                          </div>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-[#888]">{rec.recommendation}</span>
                          <span className={rec.score >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>
                            Score: {(rec?.score ?? 0).toFixed(1)} | Conf: {(rec?.confidence ?? 0).toFixed(1)}%
                          </span>
                        </div>
                        {/* Component breakdown */}
                        {rec.components && (
                          <div className="mt-2 pt-2 border-t border-[#333] grid grid-cols-5 gap-1 text-[10px]">
                            <div className="text-center">
                              <div className="text-[#666]">Order</div>
                              <div className={rec.components.order_book >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>{rec.components.order_book}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[#666]">Chain</div>
                              <div className={rec.components.on_chain >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>{rec.components.on_chain}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[#666]">Social</div>
                              <div className={rec.components.social >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>{rec.components.social}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[#666]">Cross</div>
                              <div className={rec.components.cross_asset >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>{rec.components.cross_asset}</div>
                            </div>
                            <div className="text-center">
                              <div className="text-[#666]">TA</div>
                              <div className={rec.components.advanced_ta >= 50 ? 'text-[#00FF94]' : 'text-[#FF4444]'}>{rec.components.advanced_ta}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                    
                    {recommendations.length === 0 && (
                      <div className="text-center py-8 text-[#666]">
                        <Brain size={32} className="mx-auto mb-2 opacity-50" />
                        <p>No recommendations available</p>
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
