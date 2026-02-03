import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  Brain, RefreshCw, TrendingUp, TrendingDown, Minus, Zap,
  BarChart3, Target, Sparkles, Clock, CheckCircle2, AlertCircle,
  ArrowRight, ArrowUp, ArrowDown, Loader2, Play, Pause, Layers
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// Progress bar component
const ProgressBar = ({ progress, message }) => (
  <div className="w-full">
    <div className="flex justify-between text-sm mb-1">
      <span className="text-[#A1A1AA]">{message || 'Processing...'}</span>
      <span className="text-[#00FF94]">{progress}%</span>
    </div>
    <div className="w-full h-3 bg-[#1F1F1F] rounded-full overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${progress}%` }}
        className="h-full bg-gradient-to-r from-[#00FF94] to-[#9D00FF] rounded-full"
      />
    </div>
  </div>
);

// Signal badge component
const SignalBadge = ({ signal }) => {
  const config = {
    STRONG_BUY: { bg: 'bg-[#00FF94]/20', text: 'text-[#00FF94]', icon: TrendingUp },
    BUY: { bg: 'bg-[#00FF94]/10', text: 'text-[#00FF94]', icon: ArrowUp },
    HOLD: { bg: 'bg-[#FF9500]/10', text: 'text-[#FF9500]', icon: Minus },
    SELL: { bg: 'bg-[#FF0055]/10', text: 'text-[#FF0055]', icon: ArrowDown },
    STRONG_SELL: { bg: 'bg-[#FF0055]/20', text: 'text-[#FF0055]', icon: TrendingDown },
  };
  const c = config[signal] || config.HOLD;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${c.bg} ${c.text} text-xs font-bold`}>
      <Icon size={12} />
      {signal?.replace('_', ' ')}
    </span>
  );
};

// Gem badge
const GemBadge = ({ potential }) => {
  const colors = {
    HIGH: 'bg-[#FFD700]/20 text-[#FFD700] border-[#FFD700]/30',
    MEDIUM: 'bg-[#9D00FF]/20 text-[#9D00FF] border-[#9D00FF]/30',
    LOW: 'bg-[#A1A1AA]/20 text-[#A1A1AA] border-[#A1A1AA]/30'
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${colors[potential] || colors.LOW}`}>
      {potential === 'HIGH' && '💎 '}{potential}
    </span>
  );
};

const EnsembleAI = () => {
  const [status, setStatus] = useState(null);
  const [buildStatus, setBuildStatus] = useState(null);
  const [universe, setUniverse] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [hiddenGems, setHiddenGems] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rebuilding, setRebuilding] = useState(false);
  const [targetSize, setTargetSize] = useState(50);
  const [analyzeCount, setAnalyzeCount] = useState(500);
  
  // Polling interval for build status
  const [pollInterval, setPollInterval] = useState(null);

  // Fetch optimal universe
  const fetchUniverse = async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/optimal-universe`);
      const data = await res.json();
      setUniverse(data);
    } catch (err) {
      console.error('Error fetching universe:', err);
    }
  };

  // Fetch comparison
  const fetchComparison = async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/comparison`);
      const data = await res.json();
      setComparison(data);
    } catch (err) {
      console.error('Error fetching comparison:', err);
    }
  };

  // Fetch hidden gems
  const fetchHiddenGems = async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/hidden-gems`);
      const data = await res.json();
      setHiddenGems(data);
    } catch (err) {
      console.error('Error fetching hidden gems:', err);
    }
  };

  // Fetch build status - must be defined before fetchStatus
  const fetchBuildStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/build-status`);
      const data = await res.json();
      setBuildStatus(data);
      
      // Stop polling if complete
      if (!data.running && data.progress >= 100) {
        setRebuilding(false);
        toast.success('Universe rebuild complete!');
        // Refresh data
        fetchUniverse();
        fetchComparison();
        fetchHiddenGems();
        return true; // Signal to stop polling
      }
      return false;
    } catch (err) {
      console.error('Error fetching build status:', err);
      return false;
    }
  }, []);

  // Fetch ensemble status
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/status`);
      const data = await res.json();
      setStatus(data);
      setBuildStatus(data.universe_rebuild_status);
    } catch (err) {
      console.error('Error fetching status:', err);
    }
  }, []);
  const fetchComparison = async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/comparison`);
      const data = await res.json();
      setComparison(data);
    } catch (err) {
      console.error('Error fetching comparison:', err);
    }
  };

  // Fetch hidden gems
  const fetchHiddenGems = async () => {
    try {
      const res = await fetch(`${API}/api/ensemble/hidden-gems`);
      const data = await res.json();
      setHiddenGems(data);
    } catch (err) {
      console.error('Error fetching hidden gems:', err);
    }
  };

  // Start universe rebuild
  const startRebuild = async () => {
    setRebuilding(true);
    try {
      const res = await fetch(`${API}/api/ensemble/rebuild-universe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_size: targetSize, analyze_count: analyzeCount })
      });
      const data = await res.json();
      
      if (data.status === 'started') {
        toast.info(`Analyzing ${analyzeCount} coins... This may take a few minutes.`);
        // Start polling
        const interval = setInterval(fetchBuildStatus, 2000);
        setPollInterval(interval);
      } else if (data.status === 'already_running') {
        toast.warning('Rebuild already in progress');
      }
    } catch (err) {
      toast.error('Failed to start rebuild');
      setRebuilding(false);
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStatus(),
        fetchUniverse(),
        fetchComparison(),
        fetchHiddenGems()
      ]);
      setLoading(false);
    };
    loadData();
    
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#00FF94] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="ensemble-ai-page">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/20 border border-[#9D00FF]/30">
            <Layers className="text-[#9D00FF]" size={24} />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">Ensemble AI</h1>
            <p className="text-[#A1A1AA] text-sm">Combining all ML/DL models for optimal predictions</p>
          </div>
        </div>
      </motion.div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F]"
        >
          <div className="flex items-center gap-2 mb-2">
            <Brain className="text-[#9D00FF]" size={18} />
            <span className="text-[#A1A1AA] text-sm">Ensemble Status</span>
          </div>
          <div className="flex items-center gap-2">
            {status?.ensemble_initialized ? (
              <CheckCircle2 className="text-[#00FF94]" size={20} />
            ) : (
              <AlertCircle className="text-[#FF0055]" size={20} />
            )}
            <span className={`font-bold ${status?.ensemble_initialized ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {status?.ensemble_initialized ? 'Active' : 'Inactive'}
            </span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F]"
        >
          <div className="flex items-center gap-2 mb-2">
            <Target className="text-[#00FF94]" size={18} />
            <span className="text-[#A1A1AA] text-sm">Universe Size</span>
          </div>
          <span className="text-2xl font-bold text-white">{universe?.count || 0}</span>
          <span className="text-[#A1A1AA] text-sm ml-2">coins</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F]"
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="text-[#FFD700]" size={18} />
            <span className="text-[#A1A1AA] text-sm">Hidden Gems</span>
          </div>
          <span className="text-2xl font-bold text-[#FFD700]">{hiddenGems?.count || 0}</span>
          <span className="text-[#A1A1AA] text-sm ml-2">found</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F]"
        >
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="text-[#00B8FF]" size={18} />
            <span className="text-[#A1A1AA] text-sm">Avg Score</span>
          </div>
          <span className="text-2xl font-bold text-white">{universe?.avg_ensemble_score || 0}</span>
          <span className="text-[#A1A1AA] text-sm ml-2">/100</span>
        </motion.div>
      </div>

      {/* Rebuild Universe Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 rounded-xl border border-[#9D00FF]/30 mb-6"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <RefreshCw className={`text-[#9D00FF] ${rebuilding ? 'animate-spin' : ''}`} size={20} />
              Rebuild Universe
            </h2>
            <p className="text-[#A1A1AA] text-sm">Analyze top 1000 coins and optimize your trading universe</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-[#A1A1AA] block mb-1">Target Size</label>
              <input
                type="number"
                value={targetSize}
                onChange={(e) => setTargetSize(parseInt(e.target.value) || 50)}
                className="w-20 px-2 py-1 bg-[#1F1F1F] border border-[#333] rounded text-white text-sm"
                min={10}
                max={100}
                disabled={rebuilding}
              />
            </div>
            <div>
              <label className="text-xs text-[#A1A1AA] block mb-1">Analyze Count</label>
              <input
                type="number"
                value={analyzeCount}
                onChange={(e) => setAnalyzeCount(parseInt(e.target.value) || 500)}
                className="w-24 px-2 py-1 bg-[#1F1F1F] border border-[#333] rounded text-white text-sm"
                min={100}
                max={1000}
                step={100}
                disabled={rebuilding}
              />
            </div>
            <button
              onClick={startRebuild}
              disabled={rebuilding}
              className={`px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-all ${
                rebuilding
                  ? 'bg-[#333] text-[#A1A1AA] cursor-not-allowed'
                  : 'bg-gradient-to-r from-[#9D00FF] to-[#00FF94] text-black hover:shadow-lg hover:shadow-[#9D00FF]/30'
              }`}
              data-testid="rebuild-btn"
            >
              {rebuilding ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Building...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Start Rebuild
                </>
              )}
            </button>
          </div>
        </div>

        {/* Progress */}
        {(rebuilding || buildStatus?.running) && (
          <div className="mt-4">
            <ProgressBar 
              progress={buildStatus?.progress || 0} 
              message={buildStatus?.progress_message || 'Starting...'} 
            />
            <div className="flex justify-between text-xs text-[#A1A1AA] mt-2">
              <span>Coins analyzed: {buildStatus?.coins_analyzed || 0} / {buildStatus?.total_coins || analyzeCount}</span>
              <span>Started: {buildStatus?.started_at ? new Date(buildStatus.started_at).toLocaleTimeString() : '-'}</span>
            </div>
          </div>
        )}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Coins */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F]"
        >
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="text-[#00FF94]" size={20} />
            Top 10 by Ensemble Score
          </h3>
          <div className="space-y-2">
            {universe?.top_10?.slice(0, 10).map((coin, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-[#1F1F1F]/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-[#A1A1AA] text-sm w-6">#{i + 1}</span>
                  <span className="font-bold text-white">{coin.symbol || coin}</span>
                </div>
                <span className="text-[#00FF94] font-bold">{coin.score || '-'}</span>
              </div>
            ))}
            {(!universe?.top_10 || universe.top_10.length === 0) && (
              <p className="text-[#A1A1AA] text-center py-4">No data - run rebuild first</p>
            )}
          </div>
        </motion.div>

        {/* Hidden Gems */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card p-4 rounded-xl border border-[#FFD700]/30"
        >
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Sparkles className="text-[#FFD700]" size={20} />
            Hidden Gems (High Score + Low Cap)
          </h3>
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {hiddenGems?.hidden_gems?.map((gem, i) => (
              <div key={i} className="p-3 bg-[#1F1F1F]/50 rounded-lg border border-[#FFD700]/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white">{gem.symbol}</span>
                    <GemBadge potential={gem.gem_potential} />
                  </div>
                  <span className="text-[#00FF94] font-bold">{gem.ensemble_score}</span>
                </div>
                <div className="flex flex-wrap gap-2 text-xs text-[#A1A1AA]">
                  <span>MCap: ${(gem.market_cap / 1_000_000).toFixed(1)}M</span>
                  <span>24h: <span className={gem.price_change_24h > 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                    {gem.price_change_24h > 0 ? '+' : ''}{gem.price_change_24h?.toFixed(1)}%
                  </span></span>
                </div>
              </div>
            ))}
            {(!hiddenGems?.hidden_gems || hiddenGems.hidden_gems.length === 0) && (
              <p className="text-[#A1A1AA] text-center py-4">No hidden gems found - run rebuild first</p>
            )}
          </div>
        </motion.div>

        {/* Portfolio Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F] lg:col-span-2"
        >
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <ArrowRight className="text-[#00B8FF]" size={20} />
            Portfolio Comparison (Old vs New)
          </h3>
          
          {comparison?.comparison ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Retained */}
              <div className="p-4 bg-[#1F1F1F]/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="text-[#00B8FF]" size={18} />
                  <span className="text-[#A1A1AA]">Retained</span>
                  <span className="ml-auto text-white font-bold">{comparison.comparison.overlap_count}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {comparison.comparison.overlap?.slice(0, 10).map((c, i) => (
                    <span key={i} className="px-2 py-0.5 bg-[#00B8FF]/10 text-[#00B8FF] rounded text-xs">{c}</span>
                  ))}
                </div>
              </div>

              {/* Added */}
              <div className="p-4 bg-[#1F1F1F]/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowUp className="text-[#00FF94]" size={18} />
                  <span className="text-[#A1A1AA]">New Additions</span>
                  <span className="ml-auto text-white font-bold">{comparison.comparison.added_count}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {comparison.comparison.added?.slice(0, 10).map((c, i) => (
                    <span key={i} className="px-2 py-0.5 bg-[#00FF94]/10 text-[#00FF94] rounded text-xs">{c}</span>
                  ))}
                </div>
              </div>

              {/* Removed */}
              <div className="p-4 bg-[#1F1F1F]/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowDown className="text-[#FF0055]" size={18} />
                  <span className="text-[#A1A1AA]">Removed</span>
                  <span className="ml-auto text-white font-bold">{comparison.comparison.removed_count}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {comparison.comparison.removed?.slice(0, 10).map((c, i) => (
                    <span key={i} className="px-2 py-0.5 bg-[#FF0055]/10 text-[#FF0055] rounded text-xs">{c}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-[#A1A1AA] text-center py-4">
              {comparison?.message || 'No comparison available - run rebuild to compare old vs new portfolio'}
            </p>
          )}

          {comparison?.comparison && (
            <div className="mt-4 p-3 bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10 rounded-lg border border-[#9D00FF]/20">
              <div className="flex flex-wrap justify-between gap-4 text-sm">
                <div>
                  <span className="text-[#A1A1AA]">Avg Old Score:</span>
                  <span className="ml-2 text-white font-bold">{comparison.comparison.avg_existing_score}</span>
                </div>
                <div>
                  <span className="text-[#A1A1AA]">Avg New Score:</span>
                  <span className="ml-2 text-[#00FF94] font-bold">{comparison.comparison.avg_new_score}</span>
                </div>
                <div>
                  <span className="text-[#A1A1AA]">Improvement:</span>
                  <span className={`ml-2 font-bold ${
                    comparison.comparison.avg_new_score > comparison.comparison.avg_existing_score 
                      ? 'text-[#00FF94]' : 'text-[#FF0055]'
                  }`}>
                    {comparison.comparison.avg_new_score > comparison.comparison.avg_existing_score ? '+' : ''}
                    {(comparison.comparison.avg_new_score - comparison.comparison.avg_existing_score).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* Model Weights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 rounded-xl border border-[#1F1F1F] lg:col-span-2"
        >
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Brain className="text-[#9D00FF]" size={20} />
            Ensemble Model Weights
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {status?.model_weights && Object.entries(status.model_weights).map(([model, weight]) => (
              <div key={model} className="p-3 bg-[#1F1F1F]/50 rounded-lg text-center">
                <span className="text-[#A1A1AA] text-xs block mb-1 capitalize">{model}</span>
                <span className="text-white font-bold">{(weight * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Categories Breakdown */}
        {universe?.categories && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-4 rounded-xl border border-[#1F1F1F] lg:col-span-2"
          >
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="text-[#00B8FF]" size={20} />
              Universe Categories
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {Object.entries(universe.categories).map(([cat, count]) => (
                <div key={cat} className="p-3 bg-[#1F1F1F]/50 rounded-lg text-center">
                  <span className="text-[#A1A1AA] text-xs block mb-1 capitalize">{cat.replace('_', ' ')}</span>
                  <span className="text-white font-bold text-xl">{count}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default EnsembleAI;
