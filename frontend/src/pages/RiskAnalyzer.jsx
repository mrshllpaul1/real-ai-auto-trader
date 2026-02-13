import React, { useState, useEffect } from 'react';
import { 
  Shield, AlertTriangle, TrendingUp, TrendingDown, Activity, RefreshCw,
  PieChart, BarChart3, Zap, Target, AlertCircle, CheckCircle, Info,
  ChevronDown, ChevronRight, Layers, DollarSign, Percent
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { 
  ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, 
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const RiskAnalyzer = ({ embedded = false }) => {
  const [overview, setOverview] = useState(null);
  const [exposure, setExposure] = useState(null);
  const [varData, setVarData] = useState(null);
  const [stressTest, setStressTest] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedScenario, setSelectedScenario] = useState('market_crash');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewRes, exposureRes, varRes, corrRes] = await Promise.all([
        fetch(`${API_URL}/api/risk-analyzer/overview`),
        fetch(`${API_URL}/api/risk-analyzer/exposure`),
        fetch(`${API_URL}/api/risk-analyzer/var`),
        fetch(`${API_URL}/api/risk-analyzer/correlations`)
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (exposureRes.ok) setExposure(await exposureRes.json());
      if (varRes.ok) setVarData(await varRes.json());
      if (corrRes.ok) setCorrelations(await corrRes.json());
    } catch (err) {
      console.error('Error fetching risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runStressTest = async (scenario) => {
    try {
      const res = await fetch(`${API_URL}/api/risk-analyzer/stress-test?scenario=${scenario}`, {
        method: 'POST'
      });
      if (res.ok) {
        setStressTest(await res.json());
        toast.success(`Stress test complete: ${scenario}`);
      }
    } catch (err) {
      toast.error('Stress test failed');
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-500';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-[#00FF94]';
      default: return 'text-[#A1A1AA]';
    }
  };

  const getRiskBg = (level) => {
    switch (level) {
      case 'critical': return 'bg-red-500/20 border-red-500/50';
      case 'high': return 'bg-orange-500/20 border-orange-500/50';
      case 'medium': return 'bg-yellow-500/20 border-yellow-500/50';
      case 'low': return 'bg-[#00FF94]/20 border-[#00FF94]/50';
      default: return 'bg-[#333]';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical': return <AlertCircle className="text-red-500" size={16} />;
      case 'high': return <AlertTriangle className="text-orange-400" size={16} />;
      case 'medium': return <Info className="text-yellow-400" size={16} />;
      case 'low': return <CheckCircle className="text-[#00FF94]" size={16} />;
      default: return <Info className="text-[#A1A1AA]" size={16} />;
    }
  };

  const COLORS = ['#00FF94', '#9D00FF', '#FF9500', '#00D1FF', '#FF5555'];

  const tabs = [
    { id: 'overview', label: 'Risk Overview', icon: Shield },
    { id: 'exposure', label: 'Exposure', icon: PieChart },
    { id: 'var', label: 'Value at Risk', icon: BarChart3 },
    { id: 'stress', label: 'Stress Test', icon: Zap }
  ];

  const stressScenarios = [
    { id: 'market_crash', name: 'Market Crash', desc: 'BTC -30%, ETH -35%' },
    { id: 'flash_crash', name: 'Flash Crash', desc: 'BTC -15%, quick recovery' },
    { id: 'bull_run', name: 'Bull Run', desc: 'BTC +25%, ETH +35%' },
    { id: 'black_swan', name: 'Black Swan', desc: 'BTC -50%, extreme volatility' }
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="risk-analyzer-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Shield className="text-[#9D00FF]" />
            Portfolio Risk Analyzer
          </h1>
          <p className="text-[#A1A1AA] mt-1">Unified risk analysis across all positions</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
          data-testid="refresh-risk-btn"
        >
          <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          <span className="text-[#A1A1AA]">Refresh</span>
        </button>
      </div>

      {/* Risk Score Card */}
      {overview && (
        <div className={`mb-6 p-6 rounded-xl border ${getRiskBg(overview.risk_level)}`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="text-center md:text-left">
              <p className="text-sm text-[#A1A1AA] mb-1">Overall Risk Score</p>
              <div className="flex items-center gap-4">
                <span className={`text-6xl font-bold ${getRiskColor(overview.risk_level)}`}>
                  {overview.overall_risk_score}
                </span>
                <div>
                  <p className={`text-2xl font-semibold capitalize ${getRiskColor(overview.risk_level)}`}>
                    {overview.risk_level}
                  </p>
                  <p className="text-sm text-[#A1A1AA]">
                    Portfolio: ${(overview?.total_portfolio_value ?? 0).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Risk Gauge Visualization */}
            <div className="flex-1 max-w-md">
              <div className="h-4 bg-[#1F1F1F] rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    overview.risk_level === 'critical' ? 'bg-red-500' :
                    overview.risk_level === 'high' ? 'bg-orange-400' :
                    overview.risk_level === 'medium' ? 'bg-yellow-400' :
                    'bg-[#00FF94]'
                  }`}
                  style={{ width: `${overview.overall_risk_score}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-xs text-[#A1A1AA]">
                <span>Low</span>
                <span>Medium</span>
                <span>High</span>
                <span>Critical</span>
              </div>
            </div>
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
                ? 'bg-[#9D00FF]/20 text-[#9D00FF] border border-[#9D00FF]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent hover:bg-[#2a2a2a]'
            }`}
            data-testid={`tab-${tab.id}`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && overview && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Risk Breakdown */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Breakdown by Position Type</h2>
              <div className="space-y-4">
                {/* Perpetuals */}
                <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium flex items-center gap-2">
                      <TrendingUp size={16} className="text-[#00FF94]" />
                      Perpetual Futures
                    </span>
                    <span className="text-[#00FF94] font-bold">
                      ${overview.risk_breakdown?.(perpetuals?.total_exposure ?? 0).toLocaleString() || 0}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-[#A1A1AA]">Avg Leverage</p>
                      <p className="text-white">{overview.risk_breakdown?.perpetuals?.avg_leverage || 0}x</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">Long/Short</p>
                      <p className="text-white">
                        ${overview.risk_breakdown?.(perpetuals?.long_exposure ?? 0).toLocaleString() || 0} / 
                        ${overview.risk_breakdown?.(perpetuals?.short_exposure ?? 0).toLocaleString() || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">Near Liq</p>
                      <p className={`${(overview.risk_breakdown?.perpetuals?.positions_at_risk || 0) > 0 ? 'text-red-400' : 'text-white'}`}>
                        {overview.risk_breakdown?.perpetuals?.positions_at_risk || 0}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Yield Farming */}
                <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium flex items-center gap-2">
                      <Layers size={16} className="text-[#9D00FF]" />
                      Yield Farming
                    </span>
                    <span className="text-[#9D00FF] font-bold">
                      ${overview.risk_breakdown?.(yield_farming?.total_exposure ?? 0).toLocaleString() || 0}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-[#A1A1AA]">Avg APY</p>
                      <p className="text-white">{overview.risk_breakdown?.yield_farming?.avg_apy || 0}%</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">IL Exposure</p>
                      <p className="text-white">${overview.risk_breakdown?.(yield_farming?.il_exposure ?? 0).toLocaleString() || 0}</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">High Risk</p>
                      <p className="text-white">${overview.risk_breakdown?.(yield_farming?.high_risk_exposure ?? 0).toLocaleString() || 0}</p>
                    </div>
                  </div>
                </div>

                {/* Options */}
                <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium flex items-center gap-2">
                      <Target size={16} className="text-[#FF9500]" />
                      Options
                    </span>
                    <span className="text-[#FF9500] font-bold">
                      ${overview.risk_breakdown?.(options?.total_exposure ?? 0).toLocaleString() || 0}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-sm">
                    <div>
                      <p className="text-[#A1A1AA]">Delta</p>
                      <p className="text-white">{overview.risk_breakdown?.(options?.net_delta ?? 0).toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">Gamma</p>
                      <p className="text-white">{overview.risk_breakdown?.(options?.net_gamma ?? 0).toFixed(4)}</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">Theta</p>
                      <p className="text-red-400">${overview.risk_breakdown?.options?.total_theta || 0}/day</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">Vega</p>
                      <p className="text-white">{overview.risk_breakdown?.options?.total_vega || 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Recommendations</h2>
              {overview.recommendations?.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle size={48} className="mx-auto text-[#00FF94] mb-3" />
                  <p className="text-white font-medium">Portfolio looks healthy!</p>
                  <p className="text-sm text-[#A1A1AA]">No immediate risk concerns identified.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {overview.recommendations?.map((rec, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg border ${
                        rec.priority === 'critical' ? 'bg-red-500/10 border-red-500/30' :
                        rec.priority === 'high' ? 'bg-orange-500/10 border-orange-500/30' :
                        rec.priority === 'medium' ? 'bg-yellow-500/10 border-yellow-500/30' :
                        'bg-[#1F1F1F] border-[#333]'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {getPriorityIcon(rec.priority)}
                        <div>
                          <p className="text-white text-sm">{rec.message}</p>
                          <p className="text-xs text-[#A1A1AA] mt-1 capitalize">{rec.category}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Risk Factors Chart */}
            {overview.risk_factors?.length > 0 && (
              <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <h2 className="text-lg font-semibold text-white mb-4">Risk Factor Analysis</h2>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={overview.risk_factors} layout="vertical">
                      <XAxis type="number" domain={[0, 100]} stroke="#A1A1AA" />
                      <YAxis dataKey="name" type="category" width={120} stroke="#A1A1AA" />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Bar dataKey="score" fill="#9D00FF" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'exposure' && exposure && (
          <motion.div
            key="exposure"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Exposure by Type Pie */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Exposure by Position Type</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={[
                        { name: 'Perpetuals', value: exposure.by_type?.perpetuals || 0 },
                        { name: 'Yield Farming', value: exposure.by_type?.yield_farming || 0 },
                        { name: 'Options', value: exposure.by_type?.options || 0 }
                      ].filter(d => d.value > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {COLORS.map((color, index) => (
                        <Cell key={`cell-${index}`} fill={color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value) => `$${value.toLocaleString()}`}
                      contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }}
                    />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#00FF94]" />
                  <span className="text-sm text-[#A1A1AA]">Perpetuals</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#9D00FF]" />
                  <span className="text-sm text-[#A1A1AA]">Yield</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#FF9500]" />
                  <span className="text-sm text-[#A1A1AA]">Options</span>
                </div>
              </div>
            </div>

            {/* Exposure by Asset */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Exposure by Asset</h2>
              <div className="space-y-3">
                {exposure.by_asset?.slice(0, 8).map((asset, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-[#333] rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold">{asset.asset?.slice(0, 3)}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between mb-1">
                        <span className="text-white font-medium">{asset.asset}</span>
                        <span className="text-[#A1A1AA]">${(asset?.total ?? 0).toLocaleString()}</span>
                      </div>
                      <div className="h-2 bg-[#333] rounded-full overflow-hidden flex">
                        {asset.perpetuals > 0 && (
                          <div 
                            className="h-full bg-[#00FF94]" 
                            style={{ width: `${(asset.perpetuals / asset.total) * 100}%` }}
                          />
                        )}
                        {asset.yield > 0 && (
                          <div 
                            className="h-full bg-[#9D00FF]" 
                            style={{ width: `${(asset.yield / asset.total) * 100}%` }}
                          />
                        )}
                        {asset.options > 0 && (
                          <div 
                            className="h-full bg-[#FF9500]" 
                            style={{ width: `${(asset.options / asset.total) * 100}%` }}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {exposure.concentration && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <p className="text-sm text-yellow-400">
                    <AlertTriangle size={14} className="inline mr-1" />
                    Top concentration: {exposure.concentration.top_asset} ({exposure.concentration.top_asset_pct}%)
                  </p>
                </div>
              )}
            </div>

            {/* Summary Stats */}
            <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 text-center">
                <p className="text-sm text-[#A1A1AA]">Total Exposure</p>
                <p className="text-2xl font-bold text-white">${(exposure?.total_exposure ?? 0).toLocaleString()}</p>
              </div>
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 text-center">
                <p className="text-sm text-[#A1A1AA]">Perpetuals</p>
                <p className="text-2xl font-bold text-[#00FF94]">${(exposure?.by_type?.perpetuals ?? 0).toLocaleString() || 0}</p>
              </div>
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 text-center">
                <p className="text-sm text-[#A1A1AA]">Yield Farming</p>
                <p className="text-2xl font-bold text-[#9D00FF]">${(exposure?.by_type?.yield_farming ?? 0).toLocaleString() || 0}</p>
              </div>
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 text-center">
                <p className="text-sm text-[#A1A1AA]">Options</p>
                <p className="text-2xl font-bold text-[#FF9500]">${(exposure?.by_type?.options ?? 0).toLocaleString() || 0}</p>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'var' && varData && (
          <motion.div
            key="var"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* VaR Cards */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Value at Risk (VaR)</h2>
              <div className="space-y-4">
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <p className="text-sm text-[#A1A1AA] mb-1">95% VaR (1-day)</p>
                  <p className="text-3xl font-bold text-red-400">${(varData?.var_95 ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    5% chance of losing more than this amount in one day
                  </p>
                </div>
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <p className="text-sm text-[#A1A1AA] mb-1">99% VaR (1-day)</p>
                  <p className="text-3xl font-bold text-red-500">${(varData?.var_99 ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    1% chance of losing more than this amount in one day
                  </p>
                </div>
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <p className="text-sm text-[#A1A1AA] mb-1">Expected Shortfall (CVaR)</p>
                  <p className="text-3xl font-bold text-red-600">${(varData?.expected_shortfall ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-[#A1A1AA] mt-1">
                    Average loss when VaR is exceeded
                  </p>
                </div>
              </div>
            </div>

            {/* VaR Parameters */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Parameters</h2>
              <div className="space-y-4">
                <div className="flex justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <span className="text-[#A1A1AA]">Portfolio Value</span>
                  <span className="text-white font-bold">${(varData?.portfolio_value ?? 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <span className="text-[#A1A1AA]">Effective Leverage</span>
                  <span className="text-white font-bold">{varData.effective_leverage}x</span>
                </div>
                <div className="flex justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <span className="text-[#A1A1AA]">Daily Volatility</span>
                  <span className="text-white font-bold">{varData.daily_volatility}</span>
                </div>
                <div className="flex justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <span className="text-[#A1A1AA]">Time Horizon</span>
                  <span className="text-white font-bold">{varData.time_horizon_days} day(s)</span>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-xs text-blue-400">
                  <Info size={14} className="inline mr-1" />
                  Methodology: {varData.methodology}
                </p>
              </div>
            </div>

            {/* Risk Visualization */}
            <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Loss Distribution</h2>
              <div className="relative h-32 bg-[#0A0A0A] rounded-lg overflow-hidden">
                <div className="absolute inset-0 flex items-end">
                  {/* Distribution curve approximation */}
                  {Array.from({ length: 50 }).map((_, i) => {
                    const x = (i / 50) * 100;
                    const height = Math.exp(-Math.pow((x - 50) / 15, 2) / 2) * 100;
                    return (
                      <div
                        key={i}
                        className={`flex-1 ${
                          i < 5 ? 'bg-red-500' : 
                          i < 10 ? 'bg-orange-400' : 
                          'bg-[#00FF94]'
                        }`}
                        style={{ height: `${height}%`, opacity: 0.7 }}
                      />
                    );
                  })}
                </div>
                <div className="absolute bottom-2 left-4 text-xs text-white">
                  99% VaR: ${(varData?.var_99 ?? 0).toLocaleString()}
                </div>
                <div className="absolute bottom-2 left-24 text-xs text-white">
                  95% VaR: ${(varData?.var_95 ?? 0).toLocaleString()}
                </div>
              </div>
              <div className="flex justify-between mt-2 text-xs text-[#A1A1AA]">
                <span>Worst Case</span>
                <span>Expected</span>
                <span>Best Case</span>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'stress' && (
          <motion.div
            key="stress"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Scenario Selection */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Select Stress Scenario</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {stressScenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => {
                      setSelectedScenario(scenario.id);
                      runStressTest(scenario.id);
                    }}
                    className={`p-4 rounded-lg border transition text-left ${
                      selectedScenario === scenario.id
                        ? 'bg-[#9D00FF]/20 border-[#9D00FF]/50'
                        : 'bg-[#0A0A0A] border-[#333] hover:border-[#555]'
                    }`}
                    data-testid={`scenario-${scenario.id}`}
                  >
                    <p className="text-white font-medium">{scenario.name}</p>
                    <p className="text-xs text-[#A1A1AA] mt-1">{scenario.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Stress Test Results */}
            {stressTest && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Impact Summary */}
                <div className={`p-6 rounded-xl border ${
                  stressTest.survival ? 'bg-[#00FF94]/10 border-[#00FF94]/50' : 'bg-red-500/10 border-red-500/50'
                }`}>
                  <div className="flex items-center gap-3 mb-4">
                    {stressTest.survival ? (
                      <CheckCircle className="text-[#00FF94]" size={32} />
                    ) : (
                      <AlertCircle className="text-red-500" size={32} />
                    )}
                    <div>
                      <p className="text-white font-semibold">
                        {stressTest.survival ? 'Portfolio Survives' : 'Portfolio at Risk'}
                      </p>
                      <p className="text-sm text-[#A1A1AA] capitalize">{stressTest.scenario?.replace('_', ' ')}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Current Value</p>
                      <p className="text-xl font-bold text-white">${(stressTest?.current_portfolio_value ?? 0).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Projected Value</p>
                      <p className={`text-xl font-bold ${stressTest.total_impact >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        ${(stressTest?.projected_portfolio_value ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Total Impact</p>
                      <p className={`text-xl font-bold ${stressTest.total_impact >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {stressTest.total_impact >= 0 ? '+' : ''}${(stressTest?.total_impact ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Liquidations</p>
                      <p className={`text-xl font-bold ${stressTest.liquidations_triggered > 0 ? 'text-red-400' : 'text-white'}`}>
                        {stressTest.liquidations_triggered}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Impact Breakdown */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-4">Impact by Position Type</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <span className="text-[#A1A1AA] flex items-center gap-2">
                        <TrendingUp size={16} className="text-[#00FF94]" />
                        Perpetuals
                      </span>
                      <span className={`font-bold ${stressTest.impact_breakdown?.perpetuals >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {stressTest.impact_breakdown?.perpetuals >= 0 ? '+' : ''}${(stressTest?.impact_breakdown?.perpetuals ?? 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <span className="text-[#A1A1AA] flex items-center gap-2">
                        <Layers size={16} className="text-[#9D00FF]" />
                        Yield Farming
                      </span>
                      <span className={`font-bold ${stressTest.impact_breakdown?.yield_farming >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {stressTest.impact_breakdown?.yield_farming >= 0 ? '+' : ''}${(stressTest?.impact_breakdown?.yield_farming ?? 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <span className="text-[#A1A1AA] flex items-center gap-2">
                        <Target size={16} className="text-[#FF9500]" />
                        Options
                      </span>
                      <span className={`font-bold ${stressTest.impact_breakdown?.options >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        {stressTest.impact_breakdown?.options >= 0 ? '+' : ''}${(stressTest?.impact_breakdown?.options ?? 0).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Scenario Parameters */}
                  <div className="mt-4 p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <p className="text-sm text-[#A1A1AA] mb-2">Scenario Parameters</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <span className="text-white">BTC: {stressTest.scenario_params?.btc_move > 0 ? '+' : ''}{stressTest.scenario_params?.btc_move}%</span>
                      <span className="text-white">ETH: {stressTest.scenario_params?.eth_move > 0 ? '+' : ''}{stressTest.scenario_params?.eth_move}%</span>
                      <span className="text-white">Alts: {stressTest.scenario_params?.alt_move > 0 ? '+' : ''}{stressTest.scenario_params?.alt_move}%</span>
                      <span className="text-white">Vol Spike: +{stressTest.scenario_params?.vol_spike}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!stressTest && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-12 text-center">
                <Zap size={64} className="mx-auto text-[#333] mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Run a Stress Test</h3>
                <p className="text-[#A1A1AA] max-w-md mx-auto">
                  Select a scenario above to see how your portfolio would perform under different market conditions.
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RiskAnalyzer;
