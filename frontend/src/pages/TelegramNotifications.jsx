import React, { useState, useEffect } from 'react';
import { 
  Send, Bell, BellOff, Settings, RefreshCw, Plus, Trash2,
  MessageSquare, AlertTriangle, TrendingUp, DollarSign, Clock,
  Check, X, ChevronRight, TestTube, Volume2, VolumeX
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const TelegramNotifications = ({ embedded = false }) => {
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  const [priceAlerts, setPriceAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('setup');
  const [chatId, setChatId] = useState('');
  const [showAlertModal, setShowAlertModal] = useState(false);

  const [alertForm, setAlertForm] = useState({
    symbol: 'BTC/USD',
    target_price: '',
    direction: 'above'
  });

  const [preferences, setPreferences] = useState({
    trade: true,
    price: true,
    risk: true,
    portfolio: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statusRes, configRes, alertsRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/api/telegram/status`),
        fetch(`${API_URL}/api/telegram/config`),
        fetch(`${API_URL}/api/telegram/price-alerts`),
        fetch(`${API_URL}/api/telegram/history?limit=20`)
      ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(data.config);
        if (data.config?.chat_id) setChatId(data.config.chat_id);
        if (data.config?.alert_types) {
          setPreferences({
            trade: data.config.alert_types.includes('trade'),
            price: data.config.alert_types.includes('price'),
            risk: data.config.alert_types.includes('risk'),
            portfolio: data.config.alert_types.includes('portfolio')
          });
        }
      }
      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setPriceAlerts(data.alerts || []);
      }
      if (historyRes.ok) {
        const data = await historyRes.json();
        setHistory(data.messages || []);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    if (!chatId) {
      toast.error('Please enter your Chat ID');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/telegram/test?chat_id=${chatId}`, {
        method: 'POST'
      });
      
      if (res.ok) {
        toast.success('Test message sent! Check your Telegram.');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to send test message');
      }
    } catch (err) {
      toast.error('Connection failed');
    }
  };

  const saveConfig = async () => {
    const alertTypes = Object.entries(preferences)
      .filter(([_, enabled]) => enabled)
      .map(([type]) => type);

    try {
      const res = await fetch(`${API_URL}/api/telegram/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          enabled: true,
          alert_types: alertTypes
        })
      });

      if (res.ok) {
        toast.success('Configuration saved');
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to save configuration');
    }
  };

  const createPriceAlert = async () => {
    if (!alertForm.target_price) {
      toast.error('Please enter a target price');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/telegram/price-alert/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...alertForm,
          target_price: parseFloat(alertForm.target_price),
          chat_id: chatId
        })
      });

      if (res.ok) {
        toast.success('Price alert created');
        setShowAlertModal(false);
        setAlertForm({ symbol: 'BTC/USD', target_price: '', direction: 'above' });
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to create alert');
    }
  };

  const deleteAlert = async (alertId) => {
    try {
      await fetch(`${API_URL}/api/telegram/price-alert/${alertId}`, {
        method: 'DELETE'
      });
      toast.success('Alert deleted');
      fetchData();
    } catch (err) {
      toast.error('Failed to delete alert');
    }
  };

  const sendDailySummary = async () => {
    try {
      const res = await fetch(`${API_URL}/api/telegram/notify/daily-summary`, {
        method: 'POST'
      });
      if (res.ok) {
        toast.success('Daily summary sent');
      }
    } catch (err) {
      toast.error('Failed to send summary');
    }
  };

  const tabs = [
    { id: 'setup', label: 'Setup', icon: Settings },
    { id: 'alerts', label: 'Price Alerts', icon: Bell },
    { id: 'history', label: 'History', icon: MessageSquare }
  ];

  const symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ARB/USD', 'DOGE/USD'];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="telegram-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Send className="text-[#0088CC]" />
            Telegram Notifications
          </h1>
          <p className="text-[#A1A1AA] mt-1">Get trading alerts via Telegram</p>
        </div>
        <div className="flex gap-3">
          {status?.user_configured && (
            <button
              onClick={sendDailySummary}
              className="flex items-center gap-2 px-4 py-2 bg-[#0088CC] text-white rounded-lg hover:bg-[#0077B5] transition"
            >
              <Send size={16} />
              Send Summary
            </button>
          )}
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a]"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Status Banner */}
      <div className={`mb-6 p-4 rounded-xl border ${
        status?.enabled 
          ? 'bg-[#00FF94]/10 border-[#00FF94]/50' 
          : 'bg-yellow-500/10 border-yellow-500/50'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {status?.enabled ? (
              <Bell className="text-[#00FF94]" size={24} />
            ) : (
              <BellOff className="text-yellow-400" size={24} />
            )}
            <div>
              <p className="text-white font-medium">
                {status?.enabled ? 'Notifications Active' : 'Notifications Not Configured'}
              </p>
              <p className="text-sm text-[#A1A1AA]">
                {status?.enabled 
                  ? `Chat ID: ${status?.chat_id}` 
                  : 'Set up your Telegram to receive alerts'}
              </p>
            </div>
          </div>
          {status?.enabled && (
            <div className="flex gap-2">
              {status?.alert_types?.map((type) => (
                <span key={type} className="px-2 py-1 text-xs bg-[#333] text-white rounded capitalize">
                  {type}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === tab.id
                ? 'bg-[#0088CC]/20 text-[#0088CC] border border-[#0088CC]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'setup' && (
          <motion.div
            key="setup"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Setup Instructions */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Setup Instructions</h2>
              <ol className="space-y-4">
                <li className="flex gap-3">
                  <span className="w-6 h-6 bg-[#0088CC] text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
                  <div>
                    <p className="text-white">Open Telegram and search for <code className="bg-[#333] px-1 rounded">@TethysTradingBot</code></p>
                    <p className="text-sm text-[#A1A1AA]">Or click: <a href="https://t.me/TethysTradingBot" target="_blank" rel="noopener" className="text-[#0088CC] hover:underline">t.me/TethysTradingBot</a></p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="w-6 h-6 bg-[#0088CC] text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                  <div>
                    <p className="text-white">Send <code className="bg-[#333] px-1 rounded">/start</code> to the bot</p>
                    <p className="text-sm text-[#A1A1AA]">The bot will reply with your Chat ID</p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="w-6 h-6 bg-[#0088CC] text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
                  <div>
                    <p className="text-white">Enter your Chat ID below and test the connection</p>
                  </div>
                </li>
              </ol>
            </div>

            {/* Configuration */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Configuration</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Your Telegram Chat ID</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={chatId}
                      onChange={(e) => setChatId(e.target.value)}
                      placeholder="e.g., 123456789"
                      className="flex-1 bg-[#0A0A0A] border border-[#333] rounded-lg p-3 text-white"
                    />
                    <button
                      onClick={testConnection}
                      className="px-4 py-2 bg-[#0088CC] text-white rounded-lg hover:bg-[#0077B5] flex items-center gap-2"
                    >
                      <TestTube size={16} />
                      Test
                    </button>
                  </div>
                </div>

                <div className="border-t border-[#333] pt-4">
                  <p className="text-sm text-[#A1A1AA] mb-3">Alert Types</p>
                  <div className="space-y-2">
                    {[
                      { key: 'trade', label: 'Trade Executions', icon: TrendingUp },
                      { key: 'price', label: 'Price Alerts', icon: Bell },
                      { key: 'risk', label: 'Risk Warnings', icon: AlertTriangle },
                      { key: 'portfolio', label: 'Portfolio Updates', icon: DollarSign }
                    ].map((item) => (
                      <label key={item.key} className="flex items-center justify-between p-2 bg-[#0A0A0A] border border-[#333] rounded-lg cursor-pointer">
                        <div className="flex items-center gap-2">
                          <item.icon size={16} className="text-[#A1A1AA]" />
                          <span className="text-white">{item.label}</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={preferences[item.key]}
                          onChange={(e) => setPreferences({ ...preferences, [item.key]: e.target.checked })}
                          className="w-4 h-4 accent-[#0088CC]"
                        />
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={saveConfig}
                  disabled={!chatId}
                  className="w-full py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F] disabled:opacity-50"
                >
                  Save Configuration
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'alerts' && (
          <motion.div
            key="alerts"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Price Alerts</h2>
              <button
                onClick={() => setShowAlertModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-[#0088CC] text-white rounded-lg hover:bg-[#0077B5]"
              >
                <Plus size={16} />
                New Alert
              </button>
            </div>

            {priceAlerts.length === 0 ? (
              <div className="text-center py-12">
                <Bell size={48} className="mx-auto text-[#333] mb-4" />
                <p className="text-[#A1A1AA]">No price alerts set</p>
                <button
                  onClick={() => setShowAlertModal(true)}
                  className="mt-4 px-4 py-2 bg-[#0088CC]/20 text-[#0088CC] rounded-lg"
                >
                  Create Your First Alert
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {priceAlerts.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className="flex items-center justify-between p-4 bg-[#0A0A0A] border border-[#333] rounded-lg"
                  >
                    <div>
                      <p className="text-white font-medium">{alert.symbol}</p>
                      <p className="text-sm text-[#A1A1AA]">
                        Alert when price goes <span className={alert.direction === 'above' ? 'text-[#00FF94]' : 'text-red-400'}>{alert.direction}</span> ${alert.target_price?.toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteAlert(alert.alert_id)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'history' && (
          <motion.div
            key="history"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Notification History</h2>
            
            {history.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare size={48} className="mx-auto text-[#333] mb-4" />
                <p className="text-[#A1A1AA]">No notifications sent yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((msg, i) => (
                  <div
                    key={i}
                    className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        msg.success ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {msg.success ? 'Sent' : 'Failed'}
                      </span>
                      <span className="text-xs text-[#A1A1AA]">
                        {new Date(msg.sent_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-white line-clamp-2">{msg.message?.replace(/<[^>]*>/g, '')}</p>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* New Alert Modal */}
      <AnimatePresence>
        {showAlertModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowAlertModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-white mb-4">Create Price Alert</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Symbol</label>
                  <select
                    value={alertForm.symbol}
                    onChange={(e) => setAlertForm({ ...alertForm, symbol: e.target.value })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  >
                    {symbols.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Target Price ($)</label>
                  <input
                    type="number"
                    value={alertForm.target_price}
                    onChange={(e) => setAlertForm({ ...alertForm, target_price: e.target.value })}
                    placeholder="e.g., 50000"
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                  />
                </div>

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Direction</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setAlertForm({ ...alertForm, direction: 'above' })}
                      className={`py-2 rounded-lg font-medium ${
                        alertForm.direction === 'above'
                          ? 'bg-[#00FF94] text-black'
                          : 'bg-[#333] text-white'
                      }`}
                    >
                      Above
                    </button>
                    <button
                      onClick={() => setAlertForm({ ...alertForm, direction: 'below' })}
                      className={`py-2 rounded-lg font-medium ${
                        alertForm.direction === 'below'
                          ? 'bg-red-500 text-white'
                          : 'bg-[#333] text-white'
                      }`}
                    >
                      Below
                    </button>
                  </div>
                </div>

                <button
                  onClick={createPriceAlert}
                  className="w-full py-3 bg-[#0088CC] text-white font-semibold rounded-lg hover:bg-[#0077B5]"
                >
                  Create Alert
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TelegramNotifications;
