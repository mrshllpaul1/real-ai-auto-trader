import React, { useState, useEffect } from 'react';
import { 
  TrendingDown, TrendingUp, DollarSign, Clock, Target, 
  Layers, Plus, Play, Pause, Trash2, RefreshCw, AlertTriangle,
  ChevronDown, ChevronUp, Zap, BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import useTradingPairs from '../hooks/useTradingPairs';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const AdvancedOrders = ({ embedded = false }) => {
  const { pairs: tradingPairs } = useTradingPairs();
  const [activeTab, setActiveTab] = useState('trailing');
  const [trailingStops, setTrailingStops] = useState([]);
  const [dcaBots, setDcaBots] = useState([]);
  const [ocoOrders, setOcoOrders] = useState([]);
  const [ordersSummary, setOrdersSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [trailingForm, setTrailingForm] = useState({
    symbol: 'BTC/USD',
    side: 'sell',
    quantity: 0.1,
    trail_percent: 5
  });

  const [dcaForm, setDcaForm] = useState({
    name: '',
    symbol: 'BTC/USD',
    amount_per_order: 100,
    frequency: 'daily',
    total_investment: null,
    num_orders: null
  });

  const [ocoForm, setOcoForm] = useState({
    symbol: 'BTC/USD',
    quantity: 0.1,
    take_profit_price: 50000,
    stop_loss_price: 40000
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, trailingRes, dcaRes, ocoRes] = await Promise.all([
        fetch(`${API_URL}/api/advanced-orders/summary`),
        fetch(`${API_URL}/api/advanced-orders/trailing-stop/list`),
        fetch(`${API_URL}/api/advanced-orders/dca/list`),
        fetch(`${API_URL}/api/advanced-orders/oco/list`)
      ]);

      if (summaryRes.ok) setOrdersSummary(await summaryRes.json());
      if (trailingRes.ok) {
        const data = await trailingRes.json();
        setTrailingStops(data.orders || []);
      }
      if (dcaRes.ok) {
        const data = await dcaRes.json();
        setDcaBots(data.bots || []);
      }
      if (ocoRes.ok) {
        const data = await ocoRes.json();
        setOcoOrders(data.orders || []);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createTrailingStop = async () => {
    try {
      const res = await fetch(`${API_URL}/api/advanced-orders/trailing-stop/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trailingForm)
      });
      if (res.ok) {
        toast.success('Trailing stop created');
        setShowCreateModal(false);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to create trailing stop');
    }
  };

  const createDCABot = async () => {
    try {
      const res = await fetch(`${API_URL}/api/advanced-orders/dca/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...dcaForm,
          start_immediately: true
        })
      });
      if (res.ok) {
        toast.success('DCA bot created');
        setShowCreateModal(false);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to create DCA bot');
    }
  };

  const createOCO = async () => {
    try {
      const res = await fetch(`${API_URL}/api/advanced-orders/oco/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ocoForm)
      });
      if (res.ok) {
        toast.success('OCO order created');
        setShowCreateModal(false);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to create OCO order');
    }
  };

  const executeDCA = async (botId) => {
    try {
      const res = await fetch(`${API_URL}/api/advanced-orders/dca/execute/${botId}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`DCA executed: $${data.execution?.amount_usd || 0}`);
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to execute DCA');
    }
  };

  const pauseDCA = async (botId) => {
    try {
      await fetch(`${API_URL}/api/advanced-orders/dca/pause/${botId}`, { method: 'POST' });
      toast.success('Bot paused');
      fetchData();
    } catch (err) {
      toast.error('Failed to pause bot');
    }
  };

  const resumeDCA = async (botId) => {
    try {
      await fetch(`${API_URL}/api/advanced-orders/dca/resume/${botId}`, { method: 'POST' });
      toast.success('Bot resumed');
      fetchData();
    } catch (err) {
      toast.error('Failed to resume bot');
    }
  };

  const cancelOrder = async (type, orderId) => {
    try {
      let endpoint = '';
      if (type === 'trailing') endpoint = `/api/advanced-orders/trailing-stop/${orderId}`;
      else if (type === 'oco') endpoint = `/api/advanced-orders/oco/${orderId}`;
      else if (type === 'dca') endpoint = `/api/advanced-orders/dca/${orderId}`;

      await fetch(`${API_URL}${endpoint}`, { method: 'DELETE' });
      toast.success('Order cancelled');
      fetchData();
    } catch (err) {
      toast.error('Failed to cancel order');
    }
  };

  const tabs = [
    { id: 'trailing', label: 'Trailing Stop', icon: TrendingDown, count: ordersSummary?.active_orders?.trailing_stops || 0 },
    { id: 'dca', label: 'DCA Bots', icon: DollarSign, count: ordersSummary?.active_orders?.dca_bots || 0 },
    { id: 'oco', label: 'OCO Orders', icon: Target, count: ordersSummary?.active_orders?.oco_orders || 0 },
    { id: 'iceberg', label: 'Iceberg', icon: Layers, count: ordersSummary?.active_orders?.iceberg_orders || 0 }
  ];

  const symbols = tradingPairs.length > 0 
    ? tradingPairs.map(p => `${p.symbol}/USD`)
    : ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ARB/USD', 'DOGE/USD'];
  const frequencies = ['hourly', 'daily', 'weekly', 'monthly'];

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="advanced-orders-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Advanced Orders</h1>
          <p className="text-[#A1A1AA] mt-1">Trailing stops, DCA bots, OCO orders</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="refresh-orders-btn"
          >
            <RefreshCw size={18} className="text-[#A1A1AA]" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F] transition"
            data-testid="create-order-btn"
          >
            <Plus size={18} />
            Create Order
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {tabs.map((tab) => (
          <motion.div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              activeTab === tab.id
                ? 'bg-[#00FF94]/10 border-[#00FF94]/50'
                : 'bg-[#1F1F1F]/50 border-[#333] hover:border-[#555]'
            }`}
            whileHover={{ scale: 1.02 }}
            data-testid={`tab-${tab.id}`}
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${activeTab === tab.id ? 'bg-[#00FF94]/20' : 'bg-[#333]'}`}>
                <tab.icon size={20} className={activeTab === tab.id ? 'text-[#00FF94]' : 'text-[#A1A1AA]'} />
              </div>
              <div>
                <p className="text-xs text-[#A1A1AA]">{tab.label}</p>
                <p className="text-xl font-bold text-white">{tab.count}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Content */}
      <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 md:p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'trailing' && (
            <motion.div
              key="trailing"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <h2 className="text-lg font-semibold text-white mb-4">Trailing Stop Orders</h2>
              {trailingStops.length === 0 ? (
                <div className="text-center py-12">
                  <TrendingDown size={48} className="mx-auto text-[#333] mb-4" />
                  <p className="text-[#A1A1AA]">No trailing stops active</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 px-4 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30"
                  >
                    Create Your First
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {trailingStops.map((order) => (
                    <div
                      key={order.order_id}
                      className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg"
                      data-testid={`trailing-order-${order.order_id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-white">{order.symbol}</span>
                          <span className={`ml-2 px-2 py-0.5 text-xs rounded ${
                            order.side === 'sell' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                          }`}>
                            {order.side.toUpperCase()}
                          </span>
                        </div>
                        <button
                          onClick={() => cancelOrder('trailing', order.order_id)}
                          className="p-1.5 text-red-400 hover:bg-red-500/20 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                        <div>
                          <p className="text-[#A1A1AA]">Trail %</p>
                          <p className="text-white font-medium">{order.trail_percent}%</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Stop Price</p>
                          <p className="text-[#FF5555] font-medium">${(order?.current_stop_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Quantity</p>
                          <p className="text-white font-medium">{order.quantity}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'dca' && (
            <motion.div
              key="dca"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <h2 className="text-lg font-semibold text-white mb-4">DCA Bots</h2>
              {dcaBots.length === 0 ? (
                <div className="text-center py-12">
                  <DollarSign size={48} className="mx-auto text-[#333] mb-4" />
                  <p className="text-[#A1A1AA]">No DCA bots running</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 px-4 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30"
                  >
                    Create DCA Bot
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {dcaBots.map((bot) => (
                    <div
                      key={bot.bot_id}
                      className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg"
                      data-testid={`dca-bot-${bot.bot_id}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <span className="font-bold text-white">{bot.name || bot.symbol}</span>
                          <span className={`ml-2 px-2 py-0.5 text-xs rounded ${
                            bot.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {bot.status?.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => executeDCA(bot.bot_id)}
                            className="p-1.5 text-[#00FF94] hover:bg-[#00FF94]/20 rounded"
                            title="Execute Now"
                          >
                            <Zap size={16} />
                          </button>
                          {bot.status === 'active' ? (
                            <button
                              onClick={() => pauseDCA(bot.bot_id)}
                              className="p-1.5 text-yellow-400 hover:bg-yellow-500/20 rounded"
                            >
                              <Pause size={16} />
                            </button>
                          ) : (
                            <button
                              onClick={() => resumeDCA(bot.bot_id)}
                              className="p-1.5 text-green-400 hover:bg-green-500/20 rounded"
                            >
                              <Play size={16} />
                            </button>
                          )}
                          <button
                            onClick={() => cancelOrder('dca', bot.bot_id)}
                            className="p-1.5 text-red-400 hover:bg-red-500/20 rounded"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-[#A1A1AA]">Amount</p>
                          <p className="text-white font-medium">${bot.amount_per_order}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Frequency</p>
                          <p className="text-white font-medium capitalize">{bot.frequency}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Invested</p>
                          <p className="text-[#00FF94] font-medium">${(bot?.total_invested ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Avg Price</p>
                          <p className="text-white font-medium">${(bot?.average_price ?? 0).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'oco' && (
            <motion.div
              key="oco"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <h2 className="text-lg font-semibold text-white mb-4">OCO Orders (One-Cancels-Other)</h2>
              {ocoOrders.length === 0 ? (
                <div className="text-center py-12">
                  <Target size={48} className="mx-auto text-[#333] mb-4" />
                  <p className="text-[#A1A1AA]">No OCO orders active</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 px-4 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30"
                  >
                    Create OCO Order
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {ocoOrders.map((order) => (
                    <div
                      key={order.order_id}
                      className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg"
                      data-testid={`oco-order-${order.order_id}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-bold text-white">{order.symbol}</span>
                        <button
                          onClick={() => cancelOrder('oco', order.order_id)}
                          className="p-1.5 text-red-400 hover:bg-red-500/20 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-[#A1A1AA]">Entry</p>
                          <p className="text-white font-medium">${(order?.entry_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Take Profit</p>
                          <p className="text-green-400 font-medium">${(order?.take_profit_price ?? 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-[#A1A1AA]">Stop Loss</p>
                          <p className="text-red-400 font-medium">${(order?.stop_loss_price ?? 0).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'iceberg' && (
            <motion.div
              key="iceberg"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <h2 className="text-lg font-semibold text-white mb-4">Iceberg Orders</h2>
              <div className="text-center py-12">
                <Layers size={48} className="mx-auto text-[#333] mb-4" />
                <p className="text-[#A1A1AA]">Iceberg orders help you execute large orders without moving the market</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="mt-4 px-4 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30"
                >
                  Create Iceberg Order
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              data-testid="create-order-modal"
            >
              <h2 className="text-xl font-bold text-white mb-4">Create {tabs.find(t => t.id === activeTab)?.label}</h2>

              {activeTab === 'trailing' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Symbol</label>
                    <select
                      value={trailingForm.symbol}
                      onChange={(e) => setTrailingForm({ ...trailingForm, symbol: e.target.value })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    >
                      {symbols.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Trail %</label>
                    <input
                      type="number"
                      value={trailingForm.trail_percent}
                      onChange={(e) => setTrailingForm({ ...trailingForm, trail_percent: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Quantity</label>
                    <input
                      type="number"
                      value={trailingForm.quantity}
                      onChange={(e) => setTrailingForm({ ...trailingForm, quantity: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <button
                    onClick={createTrailingStop}
                    className="w-full py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F]"
                  >
                    Create Trailing Stop
                  </button>
                </div>
              )}

              {activeTab === 'dca' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Bot Name</label>
                    <input
                      type="text"
                      value={dcaForm.name}
                      onChange={(e) => setDcaForm({ ...dcaForm, name: e.target.value })}
                      placeholder="My BTC DCA"
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Symbol</label>
                    <select
                      value={dcaForm.symbol}
                      onChange={(e) => setDcaForm({ ...dcaForm, symbol: e.target.value })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    >
                      {symbols.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Amount per Order ($)</label>
                    <input
                      type="number"
                      value={dcaForm.amount_per_order}
                      onChange={(e) => setDcaForm({ ...dcaForm, amount_per_order: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Frequency</label>
                    <select
                      value={dcaForm.frequency}
                      onChange={(e) => setDcaForm({ ...dcaForm, frequency: e.target.value })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    >
                      {frequencies.map(f => <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>)}
                    </select>
                  </div>
                  <button
                    onClick={createDCABot}
                    className="w-full py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F]"
                  >
                    Create DCA Bot
                  </button>
                </div>
              )}

              {activeTab === 'oco' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Symbol</label>
                    <select
                      value={ocoForm.symbol}
                      onChange={(e) => setOcoForm({ ...ocoForm, symbol: e.target.value })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    >
                      {symbols.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Quantity</label>
                    <input
                      type="number"
                      value={ocoForm.quantity}
                      onChange={(e) => setOcoForm({ ...ocoForm, quantity: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Take Profit Price</label>
                    <input
                      type="number"
                      value={ocoForm.take_profit_price}
                      onChange={(e) => setOcoForm({ ...ocoForm, take_profit_price: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-1 block">Stop Loss Price</label>
                    <input
                      type="number"
                      value={ocoForm.stop_loss_price}
                      onChange={(e) => setOcoForm({ ...ocoForm, stop_loss_price: parseFloat(e.target.value) })}
                      className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    />
                  </div>
                  <button
                    onClick={createOCO}
                    className="w-full py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F]"
                  >
                    Create OCO Order
                  </button>
                </div>
              )}

              <button
                onClick={() => setShowCreateModal(false)}
                className="w-full mt-3 py-2 text-[#A1A1AA] hover:text-white"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdvancedOrders;
