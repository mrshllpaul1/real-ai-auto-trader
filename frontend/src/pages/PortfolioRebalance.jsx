import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, PieChart, ArrowRight, Check, AlertTriangle, Info,
  Sliders, Zap, TrendingUp, TrendingDown, DollarSign, Target,
  ChevronRight, Play, Save
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, Tooltip } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const PortfolioRebalance = ({ embedded = false }) => {
  const [analysis, setAnalysis] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [drift, setDrift] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('analyze');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customAllocation, setCustomAllocation] = useState({});
  const [showExecuteModal, setShowExecuteModal] = useState(false);

  const COLORS = ['#00FF94', '#9D00FF', '#FF9500', '#00D1FF', '#FF5555', '#FFD700', '#00CED1'];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analysisRes, templatesRes, driftRes, configRes] = await Promise.all([
        fetch(`${API_URL}/api/rebalance/analyze`),
        fetch(`${API_URL}/api/rebalance/templates`),
        fetch(`${API_URL}/api/rebalance/drift`),
        fetch(`${API_URL}/api/rebalance/config`)
      ]);

      if (analysisRes.ok) setAnalysis(await analysisRes.json());
      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data.templates || []);
      }
      if (driftRes.ok) setDrift(await driftRes.json());
      if (configRes.ok) {
        const data = await configRes.json();
        setConfig(data.config);
        if (data.config?.target_allocation) {
          setCustomAllocation(data.config.target_allocation);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSuggestions = async (allocation = null) => {
    try {
      const res = await fetch(`${API_URL}/api/rebalance/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_allocation: allocation,
          risk_based: !allocation
        })
      });

      if (res.ok) {
        setSuggestions(await res.json());
        setActiveTab('rebalance');
        toast.success('Rebalancing suggestions generated');
      }
    } catch (err) {
      toast.error('Failed to get suggestions');
    }
  };

  const applyTemplate = (template) => {
    setSelectedTemplate(template.name);
    setCustomAllocation(template.allocation);
    getSuggestions(template.allocation);
  };

  const saveConfig = async () => {
    try {
      const res = await fetch(`${API_URL}/api/rebalance/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_allocation: customAllocation,
          rebalance_threshold: 5.0,
          min_trade_size: 50.0,
          auto_execute: false
        })
      });

      if (res.ok) {
        toast.success('Target allocation saved');
        fetchData();
      }
    } catch (err) {
      toast.error('Failed to save configuration');
    }
  };

  const executeRebalance = async () => {
    if (!suggestions?.suggested_trades?.length) return;

    try {
      const res = await fetch(`${API_URL}/api/rebalance/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(suggestions.suggested_trades)
      });

      if (res.ok) {
        toast.success('Rebalancing executed successfully');
        setShowExecuteModal(false);
        fetchData();
        setSuggestions(null);
      }
    } catch (err) {
      toast.error('Failed to execute rebalancing');
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'low': return 'text-[#00FF94] bg-[#00FF94]/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20';
      case 'high': return 'text-red-400 bg-red-500/20';
      default: return 'text-[#A1A1AA] bg-[#333]';
    }
  };

  const tabs = [
    { id: 'analyze', label: 'Current Allocation', icon: PieChart },
    { id: 'rebalance', label: 'Rebalance', icon: Sliders },
    { id: 'templates', label: 'Templates', icon: Target }
  ];

  const pieData = analysis ? Object.entries(analysis.current_allocation).map(([name, value]) => ({
    name,
    value: parseFloat(value)
  })) : [];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="rebalance-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <PieChart className="text-[#9D00FF]" />
            Portfolio Rebalancing
          </h1>
          <p className="text-[#A1A1AA] mt-1">Optimize your portfolio allocation</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => getSuggestions()}
            className="flex items-center gap-2 px-4 py-2 bg-[#9D00FF] text-white rounded-lg hover:bg-[#8D00EF] transition"
          >
            <Zap size={18} />
            AI Suggestions
          </button>
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a]"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Drift Alert */}
      {drift?.needs_rebalancing && (
        <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/50 rounded-xl">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-yellow-400" size={24} />
            <div>
              <p className="text-white font-medium">Portfolio Drift Detected</p>
              <p className="text-sm text-[#A1A1AA]">
                Your portfolio has drifted {drift.max_drift}% from target (threshold: {drift.threshold}%)
              </p>
            </div>
            <button
              onClick={() => getSuggestions()}
              className="ml-auto px-4 py-2 bg-yellow-500 text-black font-medium rounded-lg hover:bg-yellow-400"
            >
              Rebalance Now
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === tab.id
                ? 'bg-[#9D00FF]/20 text-[#9D00FF] border border-[#9D00FF]/50'
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
        {activeTab === 'analyze' && analysis && (
          <motion.div
            key="analyze"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Pie Chart */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Current Allocation</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="value"
                      label={({ name, value }) => `${name} ${value.toFixed(1)}%`}
                    >
                      {pieData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value) => `${value.toFixed(2)}%`}
                      contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }}
                    />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
              <div className="text-center mt-4">
                <p className="text-2xl font-bold text-white">${analysis.total_value?.toLocaleString()}</p>
                <p className="text-sm text-[#A1A1AA]">Total Portfolio Value</p>
              </div>
            </div>

            {/* Metrics */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Portfolio Metrics</h2>
              
              <div className="space-y-4">
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Number of Assets</span>
                    <span className="text-white font-bold">{analysis.metrics?.num_assets}</span>
                  </div>
                </div>
                
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Concentration Risk</span>
                    <span className={`px-2 py-1 rounded text-sm font-medium capitalize ${
                      analysis.metrics?.concentration_risk === 'low' ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                      analysis.metrics?.concentration_risk === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {analysis.metrics?.concentration_risk}
                    </span>
                  </div>
                </div>
                
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Diversification Score</span>
                    <span className="text-white font-bold">{analysis.metrics?.diversification_score}/100</span>
                  </div>
                  <div className="h-2 bg-[#333] rounded-full mt-2 overflow-hidden">
                    <div 
                      className="h-full bg-[#9D00FF]" 
                      style={{ width: `${analysis.metrics?.diversification_score}%` }}
                    />
                  </div>
                </div>
                
                <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Largest Position</span>
                    <span className="text-white font-bold">{analysis.metrics?.max_allocation}%</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => getSuggestions()}
                className="w-full mt-4 py-3 bg-[#9D00FF] text-white font-semibold rounded-lg hover:bg-[#8D00EF]"
              >
                Get Rebalancing Suggestions
              </button>
            </div>

            {/* Holdings Detail */}
            <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Holdings Detail</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(analysis.holdings_detail || {}).map(([asset, data], i) => (
                  <div key={asset} className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                      />
                      <span className="text-white font-medium">{asset}</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{data.percentage}%</p>
                    <p className="text-sm text-[#A1A1AA]">${data.total?.toLocaleString()}</p>
                    <div className="mt-2 text-xs text-[#A1A1AA]">
                      {data.spot > 0 && <span className="mr-2">Spot: ${data.spot.toLocaleString()}</span>}
                      {data.perp > 0 && <span className="mr-2">Perp: ${data.perp.toLocaleString()}</span>}
                      {data.yield > 0 && <span>Yield: ${data.yield.toLocaleString()}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'rebalance' && (
          <motion.div
            key="rebalance"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {suggestions ? (
              <>
                {/* Allocation Comparison */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4">Current → Target</h3>
                    <div className="space-y-3">
                      {Object.entries(suggestions.target_allocation || {}).map(([asset, target]) => {
                        const current = suggestions.current_allocation?.[asset] || 0;
                        const diff = target - current;
                        return (
                          <div key={asset} className="flex items-center gap-4">
                            <span className="w-16 text-white font-medium">{asset}</span>
                            <div className="flex-1 flex items-center gap-2">
                              <span className="text-[#A1A1AA] w-12 text-right">{current.toFixed(1)}%</span>
                              <ArrowRight size={16} className="text-[#A1A1AA]" />
                              <span className="text-white w-12">{target}%</span>
                              <span className={`text-sm ${diff >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                                ({diff >= 0 ? '+' : ''}{diff.toFixed(1)}%)
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4">Rebalance Summary</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                        <p className="text-sm text-[#A1A1AA]">Total Trades</p>
                        <p className="text-xl font-bold text-white">{suggestions.summary?.total_trades}</p>
                      </div>
                      <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                        <p className="text-sm text-[#A1A1AA]">Trade Volume</p>
                        <p className="text-xl font-bold text-white">${suggestions.summary?.total_volume?.toLocaleString()}</p>
                      </div>
                      <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                        <p className="text-sm text-[#A1A1AA]">Est. Fees</p>
                        <p className="text-xl font-bold text-[#A1A1AA]">${suggestions.summary?.estimated_fees?.toFixed(2)}</p>
                      </div>
                      <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                        <p className="text-sm text-[#A1A1AA]">Risk Impact</p>
                        <p className={`text-xl font-bold capitalize ${
                          suggestions.summary?.risk_impact === 'positive' ? 'text-[#00FF94]' : 'text-[#A1A1AA]'
                        }`}>
                          {suggestions.summary?.risk_impact}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Suggested Trades */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-white font-semibold">Suggested Trades</h3>
                    <button
                      onClick={() => setShowExecuteModal(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F]"
                    >
                      <Play size={16} />
                      Execute All
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    {suggestions.suggested_trades?.map((trade, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-4 bg-[#0A0A0A] border border-[#333] rounded-lg"
                      >
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${
                            trade.action === 'buy' ? 'bg-[#00FF94]/20' : 'bg-red-500/20'
                          }`}>
                            {trade.action === 'buy' ? (
                              <TrendingUp size={20} className="text-[#00FF94]" />
                            ) : (
                              <TrendingDown size={20} className="text-red-400" />
                            )}
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              {trade.action.toUpperCase()} {trade.asset}
                            </p>
                            <p className="text-sm text-[#A1A1AA]">
                              {trade.current_pct.toFixed(1)}% → {trade.target_pct.toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold ${trade.action === 'buy' ? 'text-[#00FF94]' : 'text-red-400'}`}>
                            ${trade.amount_usd.toLocaleString()}
                          </p>
                          <p className="text-sm text-[#A1A1AA]">
                            {trade.diff_pct >= 0 ? '+' : ''}{trade.diff_pct}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-12 text-center">
                <Sliders size={64} className="mx-auto text-[#333] mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No Suggestions Yet</h3>
                <p className="text-[#A1A1AA] mb-4">Click "AI Suggestions" or select a template to get started</p>
                <button
                  onClick={() => getSuggestions()}
                  className="px-6 py-2 bg-[#9D00FF] text-white font-semibold rounded-lg"
                >
                  Generate Suggestions
                </button>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'templates' && (
          <motion.div
            key="templates"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {templates.map((template) => (
              <div
                key={template.name}
                className={`bg-[#1F1F1F]/50 border rounded-xl p-4 cursor-pointer transition ${
                  selectedTemplate === template.name
                    ? 'border-[#9D00FF]'
                    : 'border-[#333] hover:border-[#555]'
                }`}
                onClick={() => applyTemplate(template)}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-semibold">{template.name}</h3>
                  <span className={`px-2 py-1 text-xs rounded ${getRiskColor(template.risk_level)}`}>
                    {template.risk_level}
                  </span>
                </div>
                <p className="text-sm text-[#A1A1AA] mb-4">{template.description}</p>
                
                <div className="space-y-2">
                  {Object.entries(template.allocation).map(([asset, pct]) => (
                    <div key={asset} className="flex items-center justify-between text-sm">
                      <span className="text-[#A1A1AA]">{asset}</span>
                      <span className="text-white">{pct}%</span>
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    applyTemplate(template);
                  }}
                  className="w-full mt-4 py-2 bg-[#333] text-white rounded-lg hover:bg-[#444] flex items-center justify-center gap-2"
                >
                  Apply Template
                  <ChevronRight size={16} />
                </button>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Execute Modal */}
      <AnimatePresence>
        {showExecuteModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowExecuteModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-white mb-4">Confirm Rebalancing</h2>
              
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4">
                <div className="flex items-start gap-2">
                  <AlertTriangle size={16} className="text-yellow-400 mt-0.5" />
                  <p className="text-sm text-yellow-400">
                    This will execute {suggestions?.suggested_trades?.length} trades totaling ${suggestions?.summary?.total_volume?.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="space-y-2 mb-6">
                {suggestions?.suggested_trades?.slice(0, 5).map((trade, i) => (
                  <div key={i} className="flex items-center justify-between text-sm p-2 bg-[#0A0A0A] rounded">
                    <span className={trade.action === 'buy' ? 'text-[#00FF94]' : 'text-red-400'}>
                      {trade.action.toUpperCase()} {trade.asset}
                    </span>
                    <span className="text-white">${trade.amount_usd.toLocaleString()}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowExecuteModal(false)}
                  className="flex-1 py-3 bg-[#333] text-white rounded-lg hover:bg-[#444]"
                >
                  Cancel
                </button>
                <button
                  onClick={executeRebalance}
                  className="flex-1 py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F]"
                >
                  Execute
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PortfolioRebalance;
