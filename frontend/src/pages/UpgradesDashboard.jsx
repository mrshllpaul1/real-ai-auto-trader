import React, { useState, useEffect, useCallback } from 'react';
import { 
  Bell, TrendingUp, RefreshCw, Target, Activity, 
  Play, Square, Settings, DollarSign, Percent,
  AlertTriangle, CheckCircle, XCircle, Zap,
  PieChart, ArrowUpDown, Shield, Smartphone, Waves,
  ExternalLink, Copy, MessageCircle, BarChart3, LineChart
} from 'lucide-react';
import api from '../services/api';

const UpgradesDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [arbitrageData, setArbitrageData] = useState({ opportunities: [], prices: {} });
  const [rebalanceData, setRebalanceData] = useState(null);
  const [trailingStops, setTrailingStops] = useState([]);
  const [notifications, setNotifications] = useState([]);

  // Fetch all status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await api.get('/upgrades/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Tabs configuration
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'whale', label: 'Whale Tracker', icon: Waves },
    { id: 'sentiment', label: 'Sentiment', icon: MessageCircle },
    { id: 'backtest', label: 'Backtest', icon: LineChart },
    { id: 'arbitrage', label: 'Arbitrage', icon: Zap },
    { id: 'rebalancer', label: 'Rebalancer', icon: PieChart },
    { id: 'trailing', label: 'Trailing Stops', icon: Target },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="upgrades-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Upgrades Dashboard</h1>
          <p className="text-gray-400 text-sm">P0, P1 & P3 Features</p>
        </div>
        <button
          onClick={fetchStatus}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-cyan-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab status={status} />}
      {activeTab === 'whale' && <WhaleTab />}
      {activeTab === 'sentiment' && <SentimentTab />}
      {activeTab === 'backtest' && <BacktestTab />}
      {activeTab === 'notifications' && <NotificationsTab />}
      {activeTab === 'arbitrage' && <ArbitrageTab />}
      {activeTab === 'rebalancer' && <RebalancerTab />}
      {activeTab === 'trailing' && <TrailingStopsTab />}
    </div>
  );
};

// Overview Tab
const OverviewTab = ({ status }) => {
  const features = status?.features || {};

  const featureCards = [
    {
      name: 'Whale Tracker',
      icon: Waves,
      status: features.whale_tracking?.is_monitoring,
      stats: `${features.whale_tracking?.wallets_watched || 0} wallets`,
      color: 'blue'
    },
    {
      name: 'Push Notifications',
      icon: Bell,
      status: features.push_notifications?.active,
      stats: `${features.push_notifications?.total_subscriptions || 0} subscriptions`,
      color: 'cyan'
    },
    {
      name: 'Arbitrage Monitor',
      icon: Zap,
      status: features.arbitrage?.is_monitoring,
      stats: `${features.arbitrage?.active_opportunities || 0} opportunities`,
      color: 'yellow'
    },
    {
      name: 'Portfolio Rebalancer',
      icon: PieChart,
      status: features.rebalancer?.enabled,
      stats: `${Object.keys(features.rebalancer?.target_allocations || {}).length} targets`,
      color: 'green'
    },
    {
      name: 'Trailing Stops',
      icon: Target,
      status: features.trailing_stops?.is_monitoring,
      stats: `${features.trailing_stops?.active_stops || 0} active`,
      color: 'purple'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {featureCards.map((feature, idx) => (
          <div
            key={idx}
            className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
          >
            <div className="flex items-center justify-between mb-3">
              <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                feature.status 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-gray-600/20 text-gray-400'
              }`}>
                {feature.status ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <h3 className="text-white font-medium">{feature.name}</h3>
            <p className="text-gray-400 text-sm mt-1">{feature.stats}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickActionButton 
            icon={Bell} 
            label="Test Notification" 
            onClick={() => alert('Test notification sent!')}
          />
          <QuickActionButton 
            icon={Zap} 
            label="Scan Arbitrage" 
            onClick={async () => {
              try {
                await api.post('/upgrades/arbitrage/start');
                alert('Arbitrage scanning started!');
              } catch (e) {
                alert('Failed to start');
              }
            }}
          />
          <QuickActionButton 
            icon={PieChart} 
            label="Analyze Portfolio" 
            onClick={async () => {
              const res = await api.get('/upgrades/rebalancer/analyze');
              alert(`Needs rebalance: ${res.data.needs_rebalance}`);
            }}
          />
          <QuickActionButton 
            icon={Smartphone} 
            label="Install PWA" 
            onClick={() => {
              if ('serviceWorker' in navigator) {
                alert('PWA can be installed from browser menu');
              }
            }}
          />
        </div>
      </div>

      {/* P3 Advanced Features */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">P3 Advanced Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AdvancedFeatureCard 
            title="DeFi Yield Farming"
            description="Auto-stake idle assets in DeFi protocols"
            status="Coming Soon"
            icon={DollarSign}
          />
          <AdvancedFeatureCard 
            title="Options Trading"
            description="Crypto options strategies (covered calls, puts)"
            status="Coming Soon"
            icon={ArrowUpDown}
          />
          <AdvancedFeatureCard 
            title="Copy Trading"
            description="Share/follow successful trader strategies"
            status="Coming Soon"
            icon={TrendingUp}
          />
          <AdvancedFeatureCard 
            title="Market Maker Mode"
            description="Provide liquidity and earn spreads"
            status="Coming Soon"
            icon={Shield}
          />
        </div>
      </div>
    </div>
  );
};

// Notifications Tab
const NotificationsTab = () => {
  const [notifications, setNotifications] = useState([]);
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const [historyRes, pendingRes] = await Promise.all([
        api.get('/upgrades/notifications/history?limit=20'),
        api.get('/upgrades/notifications/pending')
      ]);
      setNotifications([...pendingRes.data, ...historyRes.data]);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const notificationTypes = [
    { key: 'trade_pending', label: 'Trade Pending', icon: AlertTriangle },
    { key: 'trade_executed', label: 'Trade Executed', icon: CheckCircle },
    { key: 'stop_loss_triggered', label: 'Stop-Loss', icon: XCircle },
    { key: 'arbitrage_opportunity', label: 'Arbitrage', icon: Zap },
    { key: 'whale_alert', label: 'Whale Alerts', icon: Activity },
  ];

  return (
    <div className="space-y-6">
      {/* Notification Preferences */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Notification Preferences</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {notificationTypes.map(type => (
            <label 
              key={type.key}
              className="flex items-center gap-2 p-3 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700"
            >
              <input 
                type="checkbox" 
                defaultChecked 
                className="rounded border-gray-600"
              />
              <type.icon className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-300">{type.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Recent Notifications */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Recent Notifications</h3>
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading...</div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-8 text-gray-400">No notifications yet</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {notifications.map((notif, idx) => (
              <div 
                key={idx}
                className="flex items-start gap-3 p-3 bg-gray-700/30 rounded-lg"
              >
                <Bell className="w-5 h-5 text-cyan-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-white font-medium text-sm">{notif.title}</p>
                  <p className="text-gray-400 text-sm">{notif.body}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    {new Date(notif.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Arbitrage Tab
const ArbitrageTab = () => {
  const [status, setStatus] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [prices, setPrices] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, oppRes, pricesRes] = await Promise.all([
        api.get('/upgrades/arbitrage/status'),
        api.get('/upgrades/arbitrage/opportunities'),
        api.get('/upgrades/arbitrage/prices')
      ]);
      setStatus(statusRes.data);
      setOpportunities(oppRes.data);
      setPrices(pricesRes.data);
    } catch (error) {
      console.error('Failed to fetch arbitrage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (status?.is_monitoring) {
        await api.post('/upgrades/arbitrage/stop');
      } else {
        await api.post('/upgrades/arbitrage/start');
      }
      fetchData();
    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white">Arbitrage Monitor</h3>
            <p className="text-gray-400 text-sm">
              {status?.tracked_pairs || 0} pairs across {status?.enabled_exchanges?.length || 0} exchanges
            </p>
          </div>
          <button
            onClick={toggleMonitoring}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
              status?.is_monitoring
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {status?.is_monitoring ? (
              <>
                <Square className="w-4 h-4" /> Stop
              </>
            ) : (
              <>
                <Play className="w-4 h-4" /> Start
              </>
            )}
          </button>
        </div>
      </div>

      {/* Opportunities */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">
          Active Opportunities ({opportunities.length})
        </h3>
        {opportunities.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            {status?.is_monitoring ? 'Scanning for opportunities...' : 'Start monitoring to find opportunities'}
          </div>
        ) : (
          <div className="space-y-3">
            {opportunities.map((opp, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-500/10 to-transparent border border-yellow-500/20 rounded-lg"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    <span className="text-white font-medium">{opp.symbol}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1">
                    Buy on {opp.buy_exchange} @ ${opp.buy_price?.toFixed(2)} → 
                    Sell on {opp.sell_exchange} @ ${opp.sell_price?.toFixed(2)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-green-400 font-medium">+{opp.spread_pct?.toFixed(2)}%</p>
                  <p className="text-sm text-gray-400">${opp.potential_profit?.toFixed(2)} profit</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Price Comparison */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Exchange Prices</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-2">Pair</th>
                <th className="text-right py-2">Kraken</th>
                <th className="text-right py-2">Binance</th>
                <th className="text-right py-2">Coinbase</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(prices).slice(0, 10).map(([symbol, exchanges]) => (
                <tr key={symbol} className="border-b border-gray-700/50">
                  <td className="py-2 text-white">{symbol}</td>
                  <td className="py-2 text-right text-gray-300">
                    ${exchanges?.kraken?.last?.toFixed(2) || '-'}
                  </td>
                  <td className="py-2 text-right text-gray-300">
                    ${exchanges?.binance?.last?.toFixed(2) || '-'}
                  </td>
                  <td className="py-2 text-right text-gray-300">
                    ${exchanges?.coinbase?.last?.toFixed(2) || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Rebalancer Tab
const RebalancerTab = () => {
  const [status, setStatus] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, analysisRes] = await Promise.all([
        api.get('/upgrades/rebalancer/status'),
        api.get('/upgrades/rebalancer/analyze')
      ]);
      setStatus(statusRes.data);
      setAnalysis(analysisRes.data);
    } catch (error) {
      console.error('Failed to fetch rebalancer data:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyTemplate = async (template) => {
    try {
      await api.post(`/upgrades/rebalancer/template/${template}`);
      fetchData();
    } catch (error) {
      console.error('Failed to apply template:', error);
    }
  };

  const executeRebalance = async (dryRun = true) => {
    try {
      const res = await api.post(`/upgrades/rebalancer/execute?dry_run=${dryRun}`);
      alert(dryRun ? 'Dry run complete!' : 'Rebalance executed!');
      fetchData();
    } catch (error) {
      console.error('Failed to execute rebalance:', error);
    }
  };

  const templates = status?.available_templates || ['conservative', 'balanced', 'aggressive', 'altcoin_heavy'];

  return (
    <div className="space-y-6">
      {/* Templates */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Allocation Templates</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {templates.map(template => (
            <button
              key={template}
              onClick={() => applyTemplate(template)}
              className="p-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-center transition-colors"
            >
              <PieChart className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
              <span className="text-white text-sm capitalize">{template.replace('_', ' ')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Current vs Target */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Portfolio Allocation</h3>
          {analysis?.needs_rebalance && (
            <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm">
              Rebalance Needed
            </span>
          )}
        </div>
        
        {analysis?.current_allocations && (
          <div className="space-y-3">
            {Object.entries(analysis.current_allocations).map(([symbol, data]) => (
              <div key={symbol} className="flex items-center gap-4">
                <span className="w-16 text-white font-medium">{symbol}</span>
                <div className="flex-1">
                  <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-cyan-500"
                      style={{ width: `${Math.min(data.current_pct, 100)}%` }}
                    />
                  </div>
                </div>
                <span className="w-20 text-right text-gray-300">{data.current_pct?.toFixed(1)}%</span>
                <span className="w-20 text-right text-gray-500">→ {data.target_pct || 0}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended Actions */}
      {analysis?.recommended_actions?.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="text-lg font-medium text-white mb-4">Recommended Actions</h3>
          <div className="space-y-2 mb-4">
            {analysis.recommended_actions.map((action, idx) => (
              <div 
                key={idx}
                className={`flex items-center justify-between p-3 rounded-lg ${
                  action.action === 'buy' ? 'bg-green-500/10 border border-green-500/20' : 'bg-red-500/10 border border-red-500/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    action.action === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {action.action.toUpperCase()}
                  </span>
                  <span className="text-white">{action.symbol}</span>
                </div>
                <span className="text-gray-300">${action.amount_usd?.toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => executeRebalance(true)}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
            >
              Dry Run
            </button>
            <button
              onClick={() => executeRebalance(false)}
              className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg"
            >
              Execute Rebalance
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Trailing Stops Tab
const TrailingStopsTab = () => {
  const [status, setStatus] = useState(null);
  const [activeStops, setActiveStops] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, activeRes, historyRes] = await Promise.all([
        api.get('/upgrades/trailing-stops/status'),
        api.get('/upgrades/trailing-stops/active'),
        api.get('/upgrades/trailing-stops/history?limit=10')
      ]);
      setStatus(statusRes.data);
      setActiveStops(activeRes.data);
      setHistory(historyRes.data);
    } catch (error) {
      console.error('Failed to fetch trailing stops data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (status?.is_monitoring) {
        await api.post('/upgrades/trailing-stops/stop');
      } else {
        await api.post('/upgrades/trailing-stops/start');
      }
      fetchData();
    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white">Trailing Stop Monitor</h3>
            <p className="text-gray-400 text-sm">{activeStops.length} active trailing stops</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg"
            >
              + Create Stop
            </button>
            <button
              onClick={toggleMonitoring}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
                status?.is_monitoring
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {status?.is_monitoring ? (
                <>
                  <Square className="w-4 h-4" /> Stop
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Start
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Create Form */}
      {showCreate && <CreateTrailingStopForm onCreated={() => { setShowCreate(false); fetchData(); }} />}

      {/* Active Stops */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Active Trailing Stops</h3>
        {activeStops.length === 0 ? (
          <div className="text-center py-8 text-gray-400">No active trailing stops</div>
        ) : (
          <div className="space-y-3">
            {activeStops.map((stop, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-purple-400" />
                    <span className="text-white font-medium">{stop.symbol}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      stop.side === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {stop.side.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1">
                    Entry: ${stop.entry_price?.toFixed(2)} | Current: ${stop.current_price?.toFixed(2)} | Stop: ${stop.stop_price?.toFixed(2)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-cyan-400 font-medium">{stop.trail_pct}% trail</p>
                  <p className="text-sm text-gray-400">{stop.quantity} units</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Triggered History</h3>
        {history.length === 0 ? (
          <div className="text-center py-8 text-gray-400">No triggered stops yet</div>
        ) : (
          <div className="space-y-2">
            {history.map((stop, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-3 bg-gray-700/20 rounded-lg"
              >
                <div>
                  <span className="text-white">{stop.symbol}</span>
                  <span className="text-gray-400 text-sm ml-2">@ ${stop.current_price?.toFixed(2)}</span>
                </div>
                <div className={`font-medium ${stop.pnl_usd >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${stop.pnl_usd?.toFixed(2)} ({stop.pnl_pct?.toFixed(1)}%)
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Create Trailing Stop Form
const CreateTrailingStopForm = ({ onCreated }) => {
  const [formData, setFormData] = useState({
    symbol: 'BTC',
    side: 'long',
    entry_price: '',
    quantity: '',
    trail_pct: 5
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/upgrades/trailing-stops/create', {
        ...formData,
        entry_price: parseFloat(formData.entry_price),
        quantity: parseFloat(formData.quantity),
        trail_pct: parseFloat(formData.trail_pct)
      });
      onCreated();
    } catch (error) {
      console.error('Failed to create trailing stop:', error);
      alert('Failed to create trailing stop');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
      <h3 className="text-lg font-medium text-white mb-4">Create Trailing Stop</h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div>
          <label className="block text-gray-400 text-sm mb-1">Symbol</label>
          <input
            type="text"
            value={formData.symbol}
            onChange={e => setFormData({...formData, symbol: e.target.value.toUpperCase()})}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Side</label>
          <select
            value={formData.side}
            onChange={e => setFormData({...formData, side: e.target.value})}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Entry Price</label>
          <input
            type="number"
            step="0.01"
            value={formData.entry_price}
            onChange={e => setFormData({...formData, entry_price: e.target.value})}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Quantity</label>
          <input
            type="number"
            step="0.0001"
            value={formData.quantity}
            onChange={e => setFormData({...formData, quantity: e.target.value})}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Trail %</label>
          <input
            type="number"
            step="0.5"
            min="1"
            max="25"
            value={formData.trail_pct}
            onChange={e => setFormData({...formData, trail_pct: e.target.value})}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            required
          />
        </div>
      </div>
      <div className="flex justify-end mt-4">
        <button
          type="submit"
          className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
        >
          Create Trailing Stop
        </button>
      </div>
    </form>
  );
};

// Whale Tracking Tab
const WhaleTab = () => {
  const [status, setStatus] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [wallets, setWallets] = useState([]);
  const [flows, setFlows] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newWallet, setNewWallet] = useState({ address: '', label: '' });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, txRes, walletsRes, flowsRes] = await Promise.all([
        api.get('/upgrades/whale/status'),
        api.get('/upgrades/whale/transactions?limit=20'),
        api.get('/upgrades/whale/wallets'),
        api.get('/upgrades/whale/flows?hours=24')
      ]);
      setStatus(statusRes.data);
      setTransactions(txRes.data);
      setWallets(walletsRes.data);
      setFlows(flowsRes.data);
    } catch (error) {
      console.error('Failed to fetch whale data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (status?.is_monitoring) {
        await api.post('/upgrades/whale/stop');
      } else {
        await api.post('/upgrades/whale/start');
      }
      fetchData();
    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  const addWallet = async (e) => {
    e.preventDefault();
    if (!newWallet.address || !newWallet.label) return;
    try {
      await api.post('/upgrades/whale/wallets', newWallet);
      setNewWallet({ address: '', label: '' });
      fetchData();
    } catch (error) {
      alert('Failed to add wallet');
    }
  };

  const shortenAddress = (addr) => addr ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : '';

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white flex items-center gap-2">
              <Waves className="w-5 h-5 text-blue-400" />
              Whale Tracker
            </h3>
            <p className="text-gray-400 text-sm">
              {status?.wallets_watched || 0} wallets • ETH: ${status?.eth_price_usd?.toLocaleString() || '---'}
            </p>
          </div>
          <button
            onClick={toggleMonitoring}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium ${
              status?.is_monitoring
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            {status?.is_monitoring ? (
              <>
                <Square className="w-4 h-4" /> Stop
              </>
            ) : (
              <>
                <Play className="w-4 h-4" /> Start
              </>
            )}
          </button>
        </div>
      </div>

      {/* Exchange Flows */}
      {flows && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="text-lg font-medium text-white mb-4">24h Exchange Flows</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-green-500/10 rounded-lg">
              <p className="text-green-400 text-xl font-bold">{flows.outflows_eth?.toFixed(2)} ETH</p>
              <p className="text-gray-400 text-sm">Outflows (Bullish)</p>
            </div>
            <div className="text-center p-3 bg-red-500/10 rounded-lg">
              <p className="text-red-400 text-xl font-bold">{flows.inflows_eth?.toFixed(2)} ETH</p>
              <p className="text-gray-400 text-sm">Inflows (Bearish)</p>
            </div>
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <p className={`text-xl font-bold ${flows.net_flow_eth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {flows.net_flow_eth >= 0 ? '+' : ''}{flows.net_flow_eth?.toFixed(2)} ETH
              </p>
              <p className="text-gray-400 text-sm">Net Flow</p>
            </div>
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <p className={`text-xl font-bold ${
                flows.signal === 'bullish' ? 'text-green-400' : 
                flows.signal === 'bearish' ? 'text-red-400' : 'text-gray-400'
              }`}>
                {flows.signal?.toUpperCase()}
              </p>
              <p className="text-gray-400 text-sm">Signal</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Whale Transactions */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">
          Recent Whale Transactions ({transactions.length})
        </h3>
        {transactions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            {status?.is_monitoring ? 'Scanning for whale movements...' : 'Start monitoring to detect whales'}
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {transactions.map((tx, idx) => (
              <div 
                key={idx}
                className={`flex items-center justify-between p-3 rounded-lg ${
                  tx.direction === 'out' ? 'bg-green-500/10 border-l-4 border-green-500' :
                  tx.direction === 'in' ? 'bg-red-500/10 border-l-4 border-red-500' :
                  'bg-gray-700/30'
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Waves className="w-4 h-4 text-blue-400" />
                    <span className="text-white font-medium">{tx.value_eth?.toFixed(2)} ETH</span>
                    <span className="text-gray-400">(${tx.value_usd?.toLocaleString()})</span>
                    {tx.exchange_name && (
                      <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                        {tx.exchange_name}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-400 mt-1">
                    <span>{shortenAddress(tx.from_address)}</span>
                    <span>→</span>
                    <span>{shortenAddress(tx.to_address)}</span>
                    <a 
                      href={`https://etherscan.io/tx/${tx.hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    tx.direction === 'out' ? 'bg-green-500/20 text-green-400' :
                    tx.direction === 'in' ? 'bg-red-500/20 text-red-400' :
                    'bg-gray-600/20 text-gray-400'
                  }`}>
                    {tx.direction === 'out' ? '↑ OUT' : tx.direction === 'in' ? '↓ IN' : 'TRANSFER'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Wallet Form */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Add Wallet to Watch</h3>
        <form onSubmit={addWallet} className="flex gap-3">
          <input
            type="text"
            placeholder="0x... (Ethereum address)"
            value={newWallet.address}
            onChange={e => setNewWallet({...newWallet, address: e.target.value})}
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          />
          <input
            type="text"
            placeholder="Label"
            value={newWallet.label}
            onChange={e => setNewWallet({...newWallet, label: e.target.value})}
            className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Add
          </button>
        </form>
      </div>

      {/* Watched Wallets */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-medium text-white mb-4">Watched Wallets ({wallets.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
          {wallets.slice(0, 20).map((wallet, idx) => (
            <div 
              key={idx}
              className="flex items-center justify-between p-2 bg-gray-700/30 rounded"
            >
              <div>
                <span className="text-white text-sm">{wallet.label}</span>
                <p className="text-gray-500 text-xs font-mono">{shortenAddress(wallet.address)}</p>
              </div>
              <div className="text-right">
                <span className="text-gray-300 text-sm">{wallet.last_balance_eth?.toFixed(2)} ETH</span>
                {wallet.is_exchange && (
                  <span className="ml-2 px-1 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                    Exchange
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Helper Components
const QuickActionButton = ({ icon: Icon, label, onClick }) => (
  <button
    onClick={onClick}
    className="flex flex-col items-center gap-2 p-4 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-colors"
  >
    <Icon className="w-6 h-6 text-cyan-400" />
    <span className="text-sm text-gray-300">{label}</span>
  </button>
);

const AdvancedFeatureCard = ({ title, description, status, icon: Icon }) => (
  <div className="flex items-start gap-4 p-4 bg-gray-700/30 rounded-lg">
    <Icon className="w-8 h-8 text-gray-500" />
    <div className="flex-1">
      <h4 className="text-white font-medium">{title}</h4>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
    <span className="px-2 py-1 bg-gray-600/50 text-gray-400 rounded text-xs">
      {status}
    </span>
  </div>
);

export default UpgradesDashboard;
