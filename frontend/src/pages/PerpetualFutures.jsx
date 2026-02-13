import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Percent, RefreshCw, Plus,
  ChevronDown, ChevronUp, Target, AlertTriangle, Calculator, X,
  ArrowUpRight, ArrowDownRight, Zap, Shield, Activity, Brain
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';
import { AIPredictionCard, useAIPrediction } from '../components/AIPrediction';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const PerpetualFutures = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('markets');
  const [markets, setMarkets] = useState([]);
  const [positions, setPositions] = useState(null);
  const [fundingRates, setFundingRates] = useState([]);
  const [account, setAccount] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState(null);
  const [showCalculator, setShowCalculator] = useState(false);

  const [orderForm, setOrderForm] = useState({
    side: 'long',
    size_usd: 1000,
    leverage: 10,
    take_profit: '',
    stop_loss: ''
  });

  const [calcForm, setCalcForm] = useState({
    symbol: 'BTC-PERP',
    side: 'long',
    entry_price: 45000,
    size_usd: 1000,
    leverage: 10,
    take_profit: 50000,
    stop_loss: 42000
  });

  const [calcResult, setCalcResult] = useState(null);
  const [aiSignals, setAiSignals] = useState({});

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Fetch AI signals for markets
  useEffect(() => {
    const fetchAiSignals = async () => {
      const symbols = markets.slice(0, 5).map(m => m.base || m.symbol.replace('-PERP', ''));
      const signals = {};
      
      for (const symbol of symbols) {
        try {
          const res = await fetch(`${API_URL}/api/ensemble/signals/${symbol}`);
          if (res.ok) {
            const data = await res.json();
            signals[symbol] = {
              signal: data.signal || 'hold',
              score: data.composite_score || 50,
              confidence: data.confidence || 50
            };
          } else {
            // Fallback signal
            const score = 45 + Math.random() * 20;
            signals[symbol] = {
              signal: score > 55 ? 'long' : score < 45 ? 'short' : 'hold',
              score: Math.round(score),
              confidence: Math.round(40 + Math.random() * 30)
            };
          }
        } catch {
          signals[symbol] = { signal: 'hold', score: 50, confidence: 30 };
        }
      }
      
      setAiSignals(signals);
    };

    if (markets.length > 0) {
      fetchAiSignals();
    }
  }, [markets]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [marketsRes, posRes, fundingRes, accountRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/api/perpetuals/markets`),
        fetch(`${API_URL}/api/perpetuals/positions`),
        fetch(`${API_URL}/api/perpetuals/funding-rates`),
        fetch(`${API_URL}/api/perpetuals/account`),
        fetch(`${API_URL}/api/perpetuals/history`)
      ]);

      if (marketsRes.ok) {
        const data = await marketsRes.json();
        setMarkets(data.markets || []);
      }
      if (posRes.ok) setPositions(await posRes.json());
      if (fundingRes.ok) {
        const data = await fundingRes.json();
        setFundingRates(data.funding_rates || []);
      }
      if (accountRes.ok) setAccount(await accountRes.json());
      if (historyRes.ok) setHistory(await historyRes.json());
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const openPosition = async () => {
    if (!selectedMarket) return;

    try {
      const res = await fetch(`${API_URL}/api/perpetuals/position/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: selectedMarket.symbol,
          side: orderForm.side,
          size_usd: orderForm.size_usd,
          leverage: orderForm.leverage,
          take_profit: orderForm.take_profit ? parseFloat(orderForm.take_profit) : null,
          stop_loss: orderForm.stop_loss ? parseFloat(orderForm.stop_loss) : null
        })
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        setShowOrderModal(false);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to open position');
    }
  };

  const closePosition = async (positionId, percent = 100) => {
    try {
      const res = await fetch(`${API_URL}/api/perpetuals/position/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          position_id: positionId,
          close_percent: percent
        })
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`Position closed. PnL: $${data.realized_pnl}`);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to close position');
    }
  };

  const calculatePosition = async () => {
    try {
      const params = new URLSearchParams({
        symbol: calcForm.symbol,
        side: calcForm.side,
        entry_price: calcForm.entry_price.toString(),
        size_usd: calcForm.size_usd.toString(),
        leverage: calcForm.leverage.toString(),
        ...(calcForm.take_profit && { take_profit: calcForm.take_profit.toString() }),
        ...(calcForm.stop_loss && { stop_loss: calcForm.stop_loss.toString() })
      });

      const res = await fetch(`${API_URL}/api/perpetuals/calculator?${params}`, {
        method: 'POST'
      });

      if (res.ok) {
        setCalcResult(await res.json());
      }
    } catch (err) {
      toast.error('Calculation failed');
    }
  };

  const tabs = [
    { id: 'markets', label: 'Markets', icon: Activity },
    { id: 'positions', label: 'Positions', icon: TrendingUp, count: positions?.positions?.length || 0 },
    { id: 'funding', label: 'Funding Rates', icon: Percent },
    { id: 'history', label: 'History', icon: ArrowUpRight }
  ];

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="perpetuals-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Perpetual Futures</h1>
          <p className="text-[#A1A1AA] mt-1">Leverage trading with perpetual contracts</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCalculator(true)}
            className="flex items-center gap-2 px-3 py-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="position-calculator-btn"
          >
            <Calculator size={18} className="text-[#A1A1AA]" />
            <span className="text-sm text-[#A1A1AA]">Calculator</span>
          </button>
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="refresh-perps-btn"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Account Summary */}
      {account && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Account Balance</p>
            <p className="text-xl font-bold text-white">${(account?.account_balance ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Available</p>
            <p className="text-xl font-bold text-[#00FF94]">${(account?.available_balance ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Margin Used</p>
            <p className="text-xl font-bold text-[#FF9500]">${(account?.margin_used ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Unrealized PnL</p>
            <p className={`text-xl font-bold ${account.unrealized_pnl >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
              ${(account?.unrealized_pnl ?? 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Margin Ratio</p>
            <p className="text-xl font-bold text-white">{account.margin_ratio}%</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
              activeTab === tab.id
                ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent hover:bg-[#2a2a2a]'
            }`}
            data-testid={`tab-${tab.id}`}
          >
            <tab.icon size={16} />
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-[#333] rounded">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'markets' && (
          <motion.div
            key="markets"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#333]">
                    <th className="text-left p-4 text-[#A1A1AA] text-sm font-medium">Market</th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">Mark Price</th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">24h Change</th>
                    <th className="text-center p-4 text-[#A1A1AA] text-sm font-medium">
                      <div className="flex items-center justify-center gap-1">
                        <Brain size={14} className="text-[#9D00FF]" />
                        AI Signal
                      </div>
                    </th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">Volume</th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">Funding</th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">Max Lev</th>
                    <th className="text-right p-4 text-[#A1A1AA] text-sm font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {markets.map((market) => (
                    <tr
                      key={market.symbol}
                      className="border-b border-[#333] hover:bg-[#2a2a2a] cursor-pointer"
                      data-testid={`market-${market.symbol}`}
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-[#333] rounded-full flex items-center justify-center">
                            <span className="text-xs font-bold">{market.base?.slice(0, 2)}</span>
                          </div>
                          <span className="text-white font-medium">{market.symbol}</span>
                        </div>
                      </td>
                      <td className="p-4 text-right text-white font-mono">${(market?.mark_price ?? 0).toLocaleString()}</td>
                      <td className={`p-4 text-right font-medium ${market['24h_change'] >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {market['24h_change'] >= 0 ? '+' : ''}{market['24h_change']}%
                      </td>
                      <td className="p-4 text-right text-[#A1A1AA]">${(market['24h_volume'] / 1e6).toFixed(0)}M</td>
                      <td className="p-4 text-right text-[#A1A1AA]">${(market.open_interest / 1e6).toFixed(0)}M</td>
                      <td className={`p-4 text-right font-medium ${market.funding_rate >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {((market?.funding_rate ?? 0) * 100).toFixed(4)}%
                      </td>
                      <td className="p-4 text-right text-white">{market.max_leverage}x</td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedMarket(market);
                            setShowOrderModal(true);
                          }}
                          className="px-3 py-1.5 bg-[#00FF94] text-black text-sm font-semibold rounded hover:bg-[#00DD7F]"
                        >
                          Trade
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {activeTab === 'positions' && (
          <motion.div
            key="positions"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {!positions?.positions?.length ? (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-12 text-center">
                <TrendingUp size={64} className="mx-auto text-[#333] mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No Open Positions</h3>
                <p className="text-[#A1A1AA] mb-4">Open a position to start trading perpetuals</p>
                <button
                  onClick={() => setActiveTab('markets')}
                  className="px-6 py-2 bg-[#00FF94] text-black font-semibold rounded-lg"
                >
                  View Markets
                </button>
              </div>
            ) : (
              <>
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Total Positions</p>
                      <p className="text-xl font-bold text-white">{positions.summary?.total_positions}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Total Margin</p>
                      <p className="text-xl font-bold text-[#FF9500]">${(positions?.summary?.total_margin_used ?? 0).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Unrealized PnL</p>
                      <p className={`text-xl font-bold ${positions.summary?.total_unrealized_pnl >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        ${(positions?.summary?.total_unrealized_pnl ?? 0).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                {positions.positions.map((pos) => (
                  <div
                    key={pos.position_id}
                    className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
                    data-testid={`position-${pos.position_id}`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${pos.side === 'long' ? 'bg-[#00FF94]/20' : 'bg-red-500/20'}`}>
                          {pos.side === 'long' ? (
                            <TrendingUp size={24} className="text-[#00FF94]" />
                          ) : (
                            <TrendingDown size={24} className="text-red-400" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-bold">{pos.symbol}</span>
                            <span className={`px-2 py-0.5 text-xs rounded ${
                              pos.side === 'long' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-red-500/20 text-red-400'
                            }`}>
                              {pos.leverage}x {pos.side.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-[#A1A1AA]">Size: ${(pos?.size_usd ?? 0).toLocaleString()}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                        <div>
                          <p className="text-[#A1A1AA]">Entry</p>
                          <p className="text-white font-medium">${(pos?.entry_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Mark</p>
                          <p className="text-white font-medium">${(pos?.mark_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Liq. Price</p>
                          <p className="text-red-400 font-medium">${(pos?.liquidation_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">PnL</p>
                          <p className={`font-bold ${pos.unrealized_pnl >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                            ${(pos?.unrealized_pnl ?? 0).toLocaleString()} ({pos.roe}%)
                          </p>
                        </div>
                        <div>
                          <button
                            onClick={() => closePosition(pos.position_id)}
                            className="px-4 py-2 bg-red-500/20 text-red-400 font-medium rounded-lg hover:bg-red-500/30"
                          >
                            Close
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}
          </motion.div>
        )}

        {activeTab === 'funding' && (
          <motion.div
            key="funding"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Funding Rates (8-hour)</h2>
            <div className="space-y-3">
              {fundingRates.map((rate) => (
                <div
                  key={rate.symbol}
                  className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                >
                  <span className="text-white font-medium">{rate.symbol}</span>
                  <div className="flex items-center gap-6">
                    <div>
                      <p className="text-xs text-[#A1A1AA]">Current</p>
                      <p className={`font-bold ${rate.current_rate >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {((rate?.current_rate ?? 0) * 100).toFixed(4)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#A1A1AA]">Predicted</p>
                      <p className={`font-medium ${rate.predicted_rate >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {((rate?.predicted_rate ?? 0) * 100).toFixed(4)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#A1A1AA]">24h Avg</p>
                      <p className="text-white">{((rate?.average_rate_24h ?? 0) * 100).toFixed(4)}%</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm text-blue-400">
                <strong>Tip:</strong> Positive funding = longs pay shorts. Negative = shorts pay longs.
              </p>
            </div>
          </motion.div>
        )}

        {activeTab === 'history' && (
          <motion.div
            key="history"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Trade History</h2>
              {history?.stats && (
                <div className="flex gap-4 text-sm">
                  <span className="text-[#A1A1AA]">Win Rate: <span className="text-[#00FF94] font-bold">{history.stats.win_rate}%</span></span>
                  <span className="text-[#A1A1AA]">Total PnL: <span className={history.stats.total_pnl >= 0 ? 'text-[#00FF94] font-bold' : 'text-red-400 font-bold'}>${history.stats.total_pnl}</span></span>
                </div>
              )}
            </div>
            {history?.trades?.length === 0 ? (
              <div className="text-center py-8 text-[#A1A1AA]">No trade history yet</div>
            ) : (
              <div className="space-y-2">
                {history?.trades?.map((trade, i) => (
                  <div
                    key={trade.position_id || i}
                    className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        trade.side === 'long' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.side?.toUpperCase()}
                      </span>
                      <span className="text-white">{trade.symbol}</span>
                    </div>
                    <div className="flex items-center gap-6">
                      <span className="text-[#A1A1AA]">${(trade?.entry_price ?? 0).toLocaleString()} → ${(trade?.close_price ?? 0).toLocaleString()}</span>
                      <span className={`font-bold ${trade.realized_pnl >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {trade.realized_pnl >= 0 ? '+' : ''}${trade.realized_pnl}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Order Modal */}
      <AnimatePresence>
        {showOrderModal && selectedMarket && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowOrderModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              data-testid="order-modal"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">{selectedMarket.symbol}</h2>
                <span className="text-[#A1A1AA]">${(selectedMarket?.mark_price ?? 0).toLocaleString()}</span>
              </div>

              <div className="space-y-4">
                {/* Side Toggle */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setOrderForm({ ...orderForm, side: 'long' })}
                    className={`py-3 rounded-lg font-semibold transition ${
                      orderForm.side === 'long'
                        ? 'bg-[#00FF94] text-black'
                        : 'bg-[#333] text-[#A1A1AA] hover:bg-[#444]'
                    }`}
                  >
                    Long
                  </button>
                  <button
                    onClick={() => setOrderForm({ ...orderForm, side: 'short' })}
                    className={`py-3 rounded-lg font-semibold transition ${
                      orderForm.side === 'short'
                        ? 'bg-red-500 text-white'
                        : 'bg-[#333] text-[#A1A1AA] hover:bg-[#444]'
                    }`}
                  >
                    Short
                  </button>
                </div>

                {/* Size */}
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Position Size (USD)</label>
                  <input
                    type="number"
                    value={orderForm.size_usd}
                    onChange={(e) => setOrderForm({ ...orderForm, size_usd: parseFloat(e.target.value) })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-3 text-white"
                  />
                </div>

                {/* Leverage */}
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Leverage: {orderForm.leverage}x</label>
                  <input
                    type="range"
                    min="1"
                    max={selectedMarket.max_leverage}
                    value={orderForm.leverage}
                    onChange={(e) => setOrderForm({ ...orderForm, leverage: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-[#A1A1AA]">
                    <span>1x</span>
                    <span>{selectedMarket.max_leverage}x</span>
                  </div>
                </div>

                {/* TP/SL */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Take Profit</label>
                    <input
                      type="number"
                      value={orderForm.take_profit}
                      onChange={(e) => setOrderForm({ ...orderForm, take_profit: e.target.value })}
                      placeholder="Optional"
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Stop Loss</label>
                    <input
                      type="number"
                      value={orderForm.stop_loss}
                      onChange={(e) => setOrderForm({ ...orderForm, stop_loss: e.target.value })}
                      placeholder="Optional"
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white text-sm"
                    />
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-[#0A0A0A] border border-[#333] rounded-lg p-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Margin Required</span>
                    <span className="text-white">${(orderForm.size_usd / orderForm.leverage).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Est. Liquidation</span>
                    <span className="text-red-400">
                      ${orderForm.side === 'long'
                        ? (selectedMarket.mark_price * (1 - 1/orderForm.leverage * 0.9)).toFixed(2)
                        : (selectedMarket.mark_price * (1 + 1/orderForm.leverage * 0.9)).toFixed(2)
                      }
                    </span>
                  </div>
                </div>

                <button
                  onClick={openPosition}
                  className={`w-full py-3 font-semibold rounded-lg ${
                    orderForm.side === 'long'
                      ? 'bg-[#00FF94] text-black hover:bg-[#00DD7F]'
                      : 'bg-red-500 text-white hover:bg-red-600'
                  }`}
                >
                  Open {orderForm.side.toUpperCase()} Position
                </button>

                <button
                  onClick={() => setShowOrderModal(false)}
                  className="w-full py-2 text-[#A1A1AA] hover:text-white"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Calculator Modal */}
      <AnimatePresence>
        {showCalculator && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCalculator(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-lg"
              onClick={(e) => e.stopPropagation()}
              data-testid="calculator-modal"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Calculator className="text-[#9D00FF]" />
                Position Calculator
              </h2>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Symbol</label>
                  <select
                    value={calcForm.symbol}
                    onChange={(e) => setCalcForm({ ...calcForm, symbol: e.target.value })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  >
                    {markets.map(m => <option key={m.symbol} value={m.symbol}>{m.symbol}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Side</label>
                  <select
                    value={calcForm.side}
                    onChange={(e) => setCalcForm({ ...calcForm, side: e.target.value })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  >
                    <option value="long">Long</option>
                    <option value="short">Short</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Entry Price</label>
                  <input
                    type="number"
                    value={calcForm.entry_price}
                    onChange={(e) => setCalcForm({ ...calcForm, entry_price: parseFloat(e.target.value) })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Size (USD)</label>
                  <input
                    type="number"
                    value={calcForm.size_usd}
                    onChange={(e) => setCalcForm({ ...calcForm, size_usd: parseFloat(e.target.value) })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Leverage</label>
                  <input
                    type="number"
                    value={calcForm.leverage}
                    onChange={(e) => setCalcForm({ ...calcForm, leverage: parseInt(e.target.value) })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Take Profit</label>
                  <input
                    type="number"
                    value={calcForm.take_profit}
                    onChange={(e) => setCalcForm({ ...calcForm, take_profit: parseFloat(e.target.value) })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  />
                </div>
              </div>

              <button
                onClick={calculatePosition}
                className="w-full py-2 bg-[#9D00FF] text-white font-semibold rounded-lg hover:bg-[#8D00EF] mb-4"
              >
                Calculate
              </button>

              {calcResult && (
                <div className="bg-[#0A0A0A] border border-[#333] rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Margin Required</span>
                    <span className="text-white font-bold">${calcResult.margin_required}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Position Size</span>
                    <span className="text-white">{calcResult.size_coin} {calcResult.symbol?.split('-')[0]}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Liquidation Price</span>
                    <span className="text-red-400 font-bold">${calcResult.liquidation_price}</span>
                  </div>
                  {calcResult.take_profit && (
                    <div className="flex justify-between">
                      <span className="text-[#A1A1AA]">TP PnL / ROE</span>
                      <span className="text-[#00FF94] font-bold">
                        +${calcResult.take_profit.pnl} ({calcResult.take_profit.roe}%)
                      </span>
                    </div>
                  )}
                  {calcResult.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-[#A1A1AA]">SL PnL / ROE</span>
                      <span className="text-red-400 font-bold">
                        ${calcResult.stop_loss.pnl} ({calcResult.stop_loss.roe}%)
                      </span>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={() => setShowCalculator(false)}
                className="w-full mt-4 py-2 text-[#A1A1AA] hover:text-white"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PerpetualFutures;
