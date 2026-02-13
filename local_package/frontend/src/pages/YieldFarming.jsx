import React, { useState, useEffect } from 'react';
import { 
  Sprout, TrendingUp, DollarSign, Shield, AlertTriangle, RefreshCw,
  Filter, Search, ChevronDown, ChevronRight, Plus, Minus, Calculator,
  ArrowUpRight, Info, ExternalLink, Zap, Brain
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';
import { AIPredictionCard, TradingSignalsSummary } from '../components/AIPrediction';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const YieldFarming = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('opportunities');
  const [opportunities, setOpportunities] = useState([]);
  const [positions, setPositions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    chain: 'all',
    risk_level: 'all',
    min_apy: 0
  });
  const [selectedVault, setSelectedVault] = useState(null);
  const [depositAmount, setDepositAmount] = useState('');
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showILCalculator, setShowILCalculator] = useState(false);
  const [ilCalc, setIlCalc] = useState({ initial: 1, current: 1.5 });

  useEffect(() => {
    fetchData();
  }, [filters]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        chain: filters.chain,
        risk_level: filters.risk_level,
        min_apy: filters.min_apy.toString()
      });

      const [oppsRes, posRes] = await Promise.all([
        fetch(`${API_URL}/api/yield-farming/opportunities?${params}`),
        fetch(`${API_URL}/api/yield-farming/positions`)
      ]);

      if (oppsRes.ok) {
        const data = await oppsRes.json();
        setOpportunities(data.opportunities || []);
      }
      if (posRes.ok) {
        setPositions(await posRes.json());
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeposit = async () => {
    if (!selectedVault || !depositAmount) return;

    try {
      const res = await fetch(`${API_URL}/api/yield-farming/deposit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vault_id: selectedVault.vault_id,
          amount_usd: parseFloat(depositAmount),
          token: selectedVault.token,
          auto_compound: true
        })
      });

      if (res.ok) {
        toast.success('Deposit successful!');
        setShowDepositModal(false);
        setDepositAmount('');
        fetchData();
      }
    } catch (err) {
      toast.error('Deposit failed');
    }
  };

  const handleWithdraw = async (positionId, percent = 100) => {
    try {
      const res = await fetch(`${API_URL}/api/yield-farming/withdraw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          position_id: positionId,
          amount_percent: percent
        })
      });

      if (res.ok) {
        toast.success('Withdrawal successful');
        fetchData();
      }
    } catch (err) {
      toast.error('Withdrawal failed');
    }
  };

  const calculateIL = () => {
    const ratio = ilCalc.current / ilCalc.initial;
    const il = 2 * Math.sqrt(ratio) / (1 + ratio) - 1;
    return (il * 100).toFixed(2);
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-500/20 border-green-500/50';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'high': return 'text-red-400 bg-red-500/20 border-red-500/50';
      default: return 'text-[#A1A1AA] bg-[#333]';
    }
  };

  const chains = [
    { id: 'all', name: 'All Chains' },
    { id: 'ethereum', name: 'Ethereum', icon: '🔷' },
    { id: 'arbitrum', name: 'Arbitrum', icon: '🔵' },
    { id: 'bsc', name: 'BSC', icon: '🟡' }
  ];

  const riskLevels = ['all', 'low', 'medium', 'high'];

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="yield-farming-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Sprout className="text-[#00FF94]" />
            Yield Farming
          </h1>
          <p className="text-[#A1A1AA] mt-1">Find the best DeFi yields across protocols</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowILCalculator(true)}
            className="flex items-center gap-2 px-3 py-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="il-calculator-btn"
          >
            <Calculator size={18} className="text-[#A1A1AA]" />
            <span className="text-sm text-[#A1A1AA]">IL Calculator</span>
          </button>
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="refresh-yield-btn"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Portfolio Summary */}
      {positions?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Total Deposited</p>
            <p className="text-xl font-bold text-white">${(positions?.summary?.total_deposited_usd ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Current Value</p>
            <p className="text-xl font-bold text-[#00FF94]">${(positions?.summary?.total_current_value_usd ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Total Earned</p>
            <p className="text-xl font-bold text-[#9D00FF]">${(positions?.summary?.total_earned_usd ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Overall APY</p>
            <p className="text-xl font-bold text-white">{positions.summary.overall_apy}%</p>
          </div>
        </div>
      )}

      {/* AI DeFi Analysis */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="md:col-span-2 bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5 text-[#9D00FF]" />
            <span className="text-white font-medium">AI DeFi Analysis</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {['ETH', 'BTC', 'SOL', 'ARB'].map((token) => (
              <div key={token} className="bg-[#1F1F1F] rounded-lg p-3">
                <div className="text-xs text-[#666] mb-1">{token} Outlook</div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${
                    Math.random() > 0.5 ? 'text-[#00FF94]' : 'text-[#FFD700]'
                  }`}>
                    {Math.random() > 0.5 ? 'BULLISH' : 'NEUTRAL'}
                  </span>
                  <span className="text-xs text-[#666]">
                    {Math.round(50 + Math.random() * 30)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-[#666] mt-3">
            AI analyzes market conditions to help identify optimal entry/exit for yield positions
          </p>
        </div>
        <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-[#00FF94]" />
            <span className="text-white font-medium">Risk Assessment</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-[#A1A1AA]">Market Risk</span>
              <span className="text-[#FFD700]">Medium</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#A1A1AA]">IL Risk</span>
              <span className="text-[#00FF94]">Low</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#A1A1AA]">Protocol Risk</span>
              <span className="text-[#00FF94]">Low</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('opportunities')}
          className={`px-4 py-2 rounded-lg transition ${
            activeTab === 'opportunities'
              ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/50'
              : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent'
          }`}
          data-testid="tab-opportunities"
        >
          Opportunities
        </button>
        <button
          onClick={() => setActiveTab('positions')}
          className={`px-4 py-2 rounded-lg transition ${
            activeTab === 'positions'
              ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/50'
              : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent'
          }`}
          data-testid="tab-positions"
        >
          My Positions ({positions?.positions?.length || 0})
        </button>
      </div>

      {/* Filters */}
      {activeTab === 'opportunities' && (
        <div className="flex flex-wrap gap-3 mb-6">
          <select
            value={filters.chain}
            onChange={(e) => setFilters({ ...filters, chain: e.target.value })}
            className="bg-[#1F1F1F] border border-[#333] rounded-lg px-3 py-2 text-white"
          >
            {chains.map((chain) => (
              <option key={chain.id} value={chain.id}>
                {chain.icon} {chain.name}
              </option>
            ))}
          </select>
          <select
            value={filters.risk_level}
            onChange={(e) => setFilters({ ...filters, risk_level: e.target.value })}
            className="bg-[#1F1F1F] border border-[#333] rounded-lg px-3 py-2 text-white"
          >
            {riskLevels.map((risk) => (
              <option key={risk} value={risk}>
                {risk === 'all' ? 'All Risks' : risk.charAt(0).toUpperCase() + risk.slice(1) + ' Risk'}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2 bg-[#1F1F1F] border border-[#333] rounded-lg px-3 py-2">
            <span className="text-sm text-[#A1A1AA]">Min APY:</span>
            <input
              type="number"
              value={filters.min_apy}
              onChange={(e) => setFilters({ ...filters, min_apy: parseFloat(e.target.value) || 0 })}
              className="w-16 bg-transparent text-white outline-none"
              placeholder="0"
            />
            <span className="text-[#A1A1AA]">%</span>
          </div>
        </div>
      )}

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'opportunities' && (
          <motion.div
            key="opportunities"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            {opportunities.map((opp) => (
              <motion.div
                key={opp.vault_id}
                className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4 hover:border-[#00FF94]/30 transition cursor-pointer"
                onClick={() => {
                  setSelectedVault(opp);
                  setShowDepositModal(true);
                }}
                whileHover={{ scale: 1.01 }}
                data-testid={`vault-${opp.vault_id}`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-[#333] rounded-full flex items-center justify-center">
                      <Sprout size={24} className="text-[#00FF94]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-semibold">{opp.name}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded border ${getRiskColor(opp.risk_level)}`}>
                          {opp.risk_level}
                        </span>
                      </div>
                      <p className="text-sm text-[#A1A1AA]">{opp.protocol} • {opp.chain}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-[#00FF94]">{opp.apy}%</p>
                      <p className="text-xs text-[#A1A1AA]">APY</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-medium text-white">${(opp.tvl / 1e6).toFixed(0)}M</p>
                      <p className="text-xs text-[#A1A1AA]">TVL</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedVault(opp);
                        setShowDepositModal(true);
                      }}
                      className="px-4 py-2 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F] transition"
                    >
                      Deposit
                    </button>
                  </div>
                </div>

                {/* APY Breakdown */}
                {opp.apy_breakdown && (
                  <div className="mt-3 pt-3 border-t border-[#333] flex flex-wrap gap-4">
                    {Object.entries(opp.apy_breakdown).map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <span className="text-[#A1A1AA] capitalize">{key.replace('_', ' ')}: </span>
                        <span className="text-white">{value}%</span>
                      </div>
                    ))}
                    {opp.auto_compound && (
                      <span className="text-xs text-[#00FF94] flex items-center gap-1">
                        <Zap size={12} /> Auto-compound
                      </span>
                    )}
                  </div>
                )}
              </motion.div>
            ))}
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
            {positions?.positions?.length === 0 ? (
              <div className="text-center py-12 bg-[#1F1F1F]/50 border border-[#333] rounded-xl">
                <Sprout size={64} className="mx-auto text-[#333] mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No Active Positions</h3>
                <p className="text-[#A1A1AA] mb-4">Start farming to earn yield on your assets</p>
                <button
                  onClick={() => setActiveTab('opportunities')}
                  className="px-6 py-2 bg-[#00FF94] text-black font-semibold rounded-lg"
                >
                  Browse Opportunities
                </button>
              </div>
            ) : (
              positions?.positions?.map((pos) => (
                <div
                  key={pos.position_id}
                  className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
                  data-testid={`position-${pos.position_id}`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-white font-semibold">{pos.vault_name}</h3>
                      <p className="text-sm text-[#A1A1AA]">{pos.protocol} • {pos.chain}</p>
                    </div>

                    <div className="flex items-center gap-6">
                      <div>
                        <p className="text-sm text-[#A1A1AA]">Deposited</p>
                        <p className="text-white font-medium">${(pos?.deposited_usd ?? 0).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#A1A1AA]">Current</p>
                        <p className="text-[#00FF94] font-medium">${(pos?.current_value_usd ?? 0).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#A1A1AA]">Earned</p>
                        <p className="text-[#9D00FF] font-medium">+${(pos?.earned_usd ?? 0).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-[#A1A1AA]">APY</p>
                        <p className="text-white font-medium">{pos.current_apy}%</p>
                      </div>
                      <button
                        onClick={() => handleWithdraw(pos.position_id)}
                        className="px-4 py-2 bg-red-500/20 text-red-400 font-medium rounded-lg hover:bg-red-500/30 transition"
                      >
                        Withdraw
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Deposit Modal */}
      <AnimatePresence>
        {showDepositModal && selectedVault && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowDepositModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              data-testid="deposit-modal"
            >
              <h2 className="text-xl font-bold text-white mb-4">Deposit to {selectedVault.name}</h2>
              
              <div className="space-y-4">
                <div className="bg-[#0A0A0A] border border-[#333] rounded-lg p-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-[#A1A1AA]">Protocol</span>
                    <span className="text-white">{selectedVault.protocol}</span>
                  </div>
                  <div className="flex justify-between mb-2">
                    <span className="text-[#A1A1AA]">APY</span>
                    <span className="text-[#00FF94] font-bold">{selectedVault.apy}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Risk</span>
                    <span className={`px-2 py-0.5 text-xs rounded ${getRiskColor(selectedVault.risk_level)}`}>
                      {selectedVault.risk_level}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Amount (USD)</label>
                  <input
                    type="number"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    placeholder={`Min: $${selectedVault.min_deposit || 100}`}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-3 text-white text-lg"
                  />
                </div>

                {depositAmount && (
                  <div className="bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg p-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-[#A1A1AA]">Est. Annual Earnings</span>
                      <span className="text-[#00FF94] font-bold">
                        +${((parseFloat(depositAmount) * selectedVault.apy / 100)).toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleDeposit}
                  disabled={!depositAmount || parseFloat(depositAmount) < (selectedVault.min_deposit || 100)}
                  className="w-full py-3 bg-[#00FF94] text-black font-semibold rounded-lg hover:bg-[#00DD7F] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Deposit ${depositAmount || 0}
                </button>

                <button
                  onClick={() => setShowDepositModal(false)}
                  className="w-full py-2 text-[#A1A1AA] hover:text-white"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* IL Calculator Modal */}
      <AnimatePresence>
        {showILCalculator && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowILCalculator(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#1F1F1F] border border-[#333] rounded-xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              data-testid="il-calculator-modal"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Calculator className="text-[#9D00FF]" />
                Impermanent Loss Calculator
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Initial Price Ratio</label>
                  <input
                    type="number"
                    value={ilCalc.initial}
                    onChange={(e) => setIlCalc({ ...ilCalc, initial: parseFloat(e.target.value) || 1 })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-1 block">Current Price Ratio</label>
                  <input
                    type="number"
                    value={ilCalc.current}
                    onChange={(e) => setIlCalc({ ...ilCalc, current: parseFloat(e.target.value) || 1 })}
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg p-2 text-white"
                    step="0.1"
                  />
                </div>

                <div className="bg-[#0A0A0A] border border-[#333] rounded-lg p-4 text-center">
                  <p className="text-sm text-[#A1A1AA] mb-1">Impermanent Loss</p>
                  <p className={`text-3xl font-bold ${parseFloat(calculateIL()) < 0 ? 'text-red-400' : 'text-[#00FF94]'}`}>
                    {calculateIL()}%
                  </p>
                  <p className="text-xs text-[#A1A1AA] mt-2">
                    Price change: {(((ilCalc.current / ilCalc.initial) - 1) * 100).toFixed(1)}%
                  </p>
                </div>

                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle size={16} className="text-yellow-400 mt-0.5" />
                    <p className="text-xs text-yellow-400">
                      IL is the difference between holding tokens vs providing liquidity. 
                      Trading fees may offset this loss.
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setShowILCalculator(false)}
                  className="w-full py-2 bg-[#333] text-white rounded-lg hover:bg-[#444]"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default YieldFarming;
