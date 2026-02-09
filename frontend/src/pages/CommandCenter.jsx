import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Activity, Wallet, Target,
  Play, Square, Settings, Zap, PieChart, Bell, Waves, LineChart,
  RefreshCw, ArrowUpDown, Shield, MessageCircle, FlaskConical,
  Rocket, Brain, BarChart3, AlertTriangle, CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import api, { tradingAPI, marketAPI } from '../services/api';
import { toast } from 'sonner';
import MarketOverview from '../components/MarketOverview';

// Tab components
const DashboardTab = ({ portfolio, krakenPortfolio, prices }) => (
  <div className="space-y-6">
    {/* Portfolio Cards */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
            <Wallet className="w-4 h-4" /> Kraken Portfolio
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            ${krakenPortfolio?.total_usd?.toFixed(2) || '0.00'}
          </div>
          <div className="text-sm text-gray-400">
            {krakenPortfolio?.holdings?.length || 0} assets
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" /> 24h Change
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${(krakenPortfolio?.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {krakenPortfolio?.change_24h >= 0 ? '+' : ''}{krakenPortfolio?.change_24h?.toFixed(2) || '0.00'}%
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
            <Activity className="w-4 h-4" /> AI Budget
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            ${portfolio?.current_value?.toFixed(2) || '700.00'}
          </div>
          <div className="text-sm text-gray-400">Isolated trading budget</div>
        </CardContent>
      </Card>
    </div>

    {/* Market Overview */}
    <MarketOverview />

    {/* Holdings Table */}
    {krakenPortfolio?.holdings?.length > 0 && (
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-800">
                  <th className="text-left py-2">Asset</th>
                  <th className="text-right py-2">Amount</th>
                  <th className="text-right py-2">Value</th>
                  <th className="text-right py-2">24h</th>
                </tr>
              </thead>
              <tbody>
                {krakenPortfolio.holdings.slice(0, 10).map((h, i) => (
                  <tr key={i} className="border-b border-gray-800/50">
                    <td className="py-2 text-white font-medium">{h.symbol}</td>
                    <td className="py-2 text-right text-gray-300">{h.amount?.toFixed(4)}</td>
                    <td className="py-2 text-right text-white">${h.value_usd?.toFixed(2)}</td>
                    <td className={`py-2 text-right ${(h.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {h.change_24h?.toFixed(2) || '0.00'}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    )}
  </div>
);

const GrowthTab = ({ growthStatus, onToggleAutopilot }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400">
            <Rocket className="w-4 h-4 inline mr-2" />Goal: $500 → $100K
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-400">
            {((growthStatus?.current_value || 500) / 100000 * 100).toFixed(2)}%
          </div>
          <div className="text-sm text-gray-400">Progress to goal</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Current Value</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            ${growthStatus?.current_value?.toFixed(2) || '500.00'}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Total P/L</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${(growthStatus?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {growthStatus?.total_pnl >= 0 ? '+' : ''}${growthStatus?.total_pnl?.toFixed(2) || '0.00'}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Autopilot</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={onToggleAutopilot}
            className={growthStatus?.autopilot_active 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'}
          >
            {growthStatus?.autopilot_active ? <Square className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            {growthStatus?.autopilot_active ? 'Stop' : 'Start'}
          </Button>
        </CardContent>
      </Card>
    </div>

    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Target className="w-5 h-5 text-cyan-400" />
          Growth Strategy
        </CardTitle>
      </CardHeader>
      <CardContent className="text-gray-300 space-y-2">
        <p>• Target: 200x returns ($500 → $100,000)</p>
        <p>• Strategy: AI-powered gem hunting + momentum trading</p>
        <p>• Risk: Aggressive (high reward potential)</p>
        <p>• Auto-rebalancing enabled when autopilot is active</p>
      </CardContent>
    </Card>
  </div>
);

const MasterTab = ({ orchestratorStatus, onToggleOrchestrator }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">
            <Brain className="w-4 h-4 inline mr-2" />Master Orchestrator
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Badge className={orchestratorStatus?.is_running ? 'bg-green-500' : 'bg-gray-600'}>
            {orchestratorStatus?.is_running ? 'ACTIVE' : 'STOPPED'}
          </Badge>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Active Strategies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-cyan-400">
            {orchestratorStatus?.active_strategies || 0}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Today's Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            {orchestratorStatus?.trades_today || 0}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Control</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={onToggleOrchestrator}
            className={orchestratorStatus?.is_running 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-cyan-600 hover:bg-cyan-700'}
          >
            {orchestratorStatus?.is_running ? 'Stop' : 'Start'} Orchestrator
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
);

const UpgradesTab = ({ upgradesStatus }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[
        { name: 'Whale Tracker', icon: Waves, status: upgradesStatus?.features?.whale_tracking?.is_monitoring },
        { name: 'Sentiment', icon: MessageCircle, status: upgradesStatus?.features?.sentiment?.is_monitoring },
        { name: 'Arbitrage', icon: Zap, status: upgradesStatus?.features?.arbitrage?.is_monitoring },
        { name: 'Trailing Stops', icon: Target, status: upgradesStatus?.features?.trailing_stops?.is_monitoring },
        { name: 'Rebalancer', icon: PieChart, status: upgradesStatus?.features?.rebalancer?.enabled },
        { name: 'A/B Testing', icon: FlaskConical, status: upgradesStatus?.features?.ab_testing?.is_monitoring },
        { name: 'Backtest', icon: LineChart, status: upgradesStatus?.features?.backtest?.available },
        { name: 'Notifications', icon: Bell, status: upgradesStatus?.features?.push_notifications?.active },
      ].map((feature, idx) => (
        <Card key={idx} className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4 text-center">
            <feature.icon className={`w-8 h-8 mx-auto mb-2 ${feature.status ? 'text-green-400' : 'text-gray-500'}`} />
            <div className="text-sm text-white">{feature.name}</div>
            <Badge className={`mt-2 ${feature.status ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}`}>
              {feature.status ? 'Active' : 'Inactive'}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>

    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-3">
        <Button onClick={() => window.location.href = '/upgrades'} variant="outline" className="border-cyan-500 text-cyan-400">
          <Settings className="w-4 h-4 mr-2" /> Manage Upgrades
        </Button>
        <Button onClick={() => window.location.href = '/spot-trading'} variant="outline" className="border-green-500 text-green-400">
          <ArrowUpDown className="w-4 h-4 mr-2" /> Spot Trading
        </Button>
        <Button onClick={() => window.location.href = '/model-performance'} variant="outline" className="border-purple-500 text-purple-400">
          <BarChart3 className="w-4 h-4 mr-2" /> Model Performance
        </Button>
      </CardContent>
    </Card>
  </div>
);

const CommandCenter = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [portfolio, setPortfolio] = useState(null);
  const [krakenPortfolio, setKrakenPortfolio] = useState(null);
  const [prices, setPrices] = useState({});
  const [growthStatus, setGrowthStatus] = useState(null);
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);
  const [upgradesStatus, setUpgradesStatus] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [portfolioRes, krakenRes, pricesRes, growthRes, orchRes, upgradesRes] = await Promise.allSettled([
        tradingAPI.getPortfolio(),
        tradingAPI.getKrakenPortfolio(),
        marketAPI.getPrices('bitcoin,ethereum,solana'),
        api.get('/growth/status'),
        api.get('/master-orchestrator/status'),
        api.get('/upgrades/status')
      ]);

      if (portfolioRes.status === 'fulfilled') setPortfolio(portfolioRes.value.data);
      if (krakenRes.status === 'fulfilled') setKrakenPortfolio(krakenRes.value.data);
      if (pricesRes.status === 'fulfilled') setPrices(pricesRes.value.data);
      if (growthRes.status === 'fulfilled') setGrowthStatus(growthRes.value.data);
      if (orchRes.status === 'fulfilled') setOrchestratorStatus(orchRes.value.data);
      if (upgradesRes.status === 'fulfilled') setUpgradesStatus(upgradesRes.value.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleAutopilot = async () => {
    try {
      if (growthStatus?.autopilot_active) {
        await api.post('/growth/stop');
      } else {
        await api.post('/growth/start');
      }
      fetchData();
      toast.success(growthStatus?.autopilot_active ? 'Autopilot stopped' : 'Autopilot started');
    } catch (error) {
      toast.error('Failed to toggle autopilot');
    }
  };

  const toggleOrchestrator = async () => {
    try {
      if (orchestratorStatus?.is_running) {
        await api.post('/master-orchestrator/stop');
      } else {
        await api.post('/master-orchestrator/start');
      }
      fetchData();
      toast.success(orchestratorStatus?.is_running ? 'Orchestrator stopped' : 'Orchestrator started');
    } catch (error) {
      toast.error('Failed to toggle orchestrator');
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'growth', label: '$500→$100K', icon: Rocket },
    { id: 'master', label: 'Master Control', icon: Brain },
    { id: 'upgrades', label: 'Upgrades', icon: Zap },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="command-center">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-gray-400">Unified trading control panel</p>
        </div>
        <Button onClick={fetchData} variant="outline" className="border-gray-700">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-800 pb-2 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-cyan-500/20 text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'dashboard' && (
          <DashboardTab portfolio={portfolio} krakenPortfolio={krakenPortfolio} prices={prices} />
        )}
        {activeTab === 'growth' && (
          <GrowthTab growthStatus={growthStatus} onToggleAutopilot={toggleAutopilot} />
        )}
        {activeTab === 'master' && (
          <MasterTab orchestratorStatus={orchestratorStatus} onToggleOrchestrator={toggleOrchestrator} />
        )}
        {activeTab === 'upgrades' && (
          <UpgradesTab upgradesStatus={upgradesStatus} />
        )}
      </motion.div>
    </div>
  );
};

export default CommandCenter;
