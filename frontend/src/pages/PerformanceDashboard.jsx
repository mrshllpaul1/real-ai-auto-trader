import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Percent, Target, Award,
  RefreshCw, AlertTriangle, CheckCircle, XCircle, ArrowUpRight, 
  ArrowDownRight, Clock, BarChart3, PieChart, Activity, Wallet,
  History, Zap, LineChart as LineChartIcon, Edit3, Settings
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Area, AreaChart, ReferenceLine
} from 'recharts';
import EntryPriceManager from '../components/EntryPriceManager';

const API_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const PerformanceDashboard = ({ embedded = false }) => {
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [data, setData] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [pnlChartData, setPnlChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [isSampleData, setIsSampleData] = useState(false);
  const [showEntryManager, setShowEntryManager] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/portfolio-performance/dashboard');
      setData(res.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load performance data');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPnlChart = useCallback(async () => {
    try {
      setChartLoading(true);
      const res = await api.get('/portfolio-performance/pnl-chart?days=30');
      setPnlChartData(res.data.data || []);
      setIsSampleData(res.data.is_sample || false);
    } catch (error) {
      console.error('Error loading P&L chart:', error);
    } finally {
      setChartLoading(false);
    }
  }, []);

  const syncTradeHistory = async () => {
    try {
      setSyncing(true);
      toast.info('Syncing trade history from Kraken...');
      
      const res = await api.post('/spot/sync-trade-history?days_back=365');
      setSyncResult(res.data);
      toast.success(`Synced ${res.data.summary?.trades_processed || 0} trades!`);
      
      // Reload dashboard and chart
      await loadDashboard();
      await loadPnlChart();
    } catch (error) {
      console.error('Sync error:', error);
      toast.error('Failed to sync trade history');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    loadPnlChart();
  }, [loadDashboard, loadPnlChart]);

  const summary = data?.summary || {};
  const winLoss = data?.win_loss || {};
  const positions = data?.positions || [];
  const bestPerformer = data?.best_performer;
  const worstPerformer = data?.worst_performer;

  if (loading) {
    return (
      <div className={`${embedded ? '' : 'p-6'} flex items-center justify-center min-h-[400px]`}>
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-purple-500 mx-auto mb-4" />
          <p className="text-slate-400">Loading performance data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={embedded ? '' : 'p-6 space-y-6'}>
      {/* Header */}
      {!embedded && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Performance Dashboard</h1>
            <p className="text-slate-400 mt-1">Track your portfolio performance and P&L</p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={loadDashboard}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={syncTradeHistory}
              disabled={syncing}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <History className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Trades'}
            </Button>
          </div>
        </div>
      )}

      {/* Quick Actions for Embedded */}
      {embedded && (
        <div className="flex justify-end gap-2 mb-4">
          <Button 
            variant="outline" 
            size="sm"
            onClick={loadDashboard}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            size="sm"
            onClick={syncTradeHistory}
            disabled={syncing}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <History className={`w-4 h-4 mr-1 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Trades'}
          </Button>
        </div>
      )}

      {/* No Entry Data Warning */}
      {!data?.has_entry_data && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-400">No Entry Price Data</h3>
              <p className="text-sm text-slate-400 mt-1">
                Click "Sync Trades" to import your trade history from Kraken and see accurate P&L calculations.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Portfolio Value */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-slate-400">Portfolio Value</span>
          </div>
          <p className="text-2xl font-bold text-white">
            ${summary.total_portfolio_value?.toLocaleString() || '0.00'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Crypto: ${summary.current_portfolio_value?.toLocaleString()} | USD: ${summary.usd_balance?.toLocaleString()}
          </p>
        </motion.div>

        {/* Cost Basis */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-400">Cost Basis</span>
          </div>
          <p className="text-2xl font-bold text-white">
            ${summary.total_cost_basis?.toLocaleString() || '—'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {data?.positions_with_entry || 0} positions tracked
          </p>
        </motion.div>

        {/* Total P&L */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className={`p-4 rounded-xl border ${
            summary.total_pnl >= 0 
              ? 'bg-green-500/10 border-green-500/30' 
              : 'bg-red-500/10 border-red-500/30'
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            {summary.total_pnl >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-400" />
            )}
            <span className="text-sm text-slate-400">Total P&L</span>
          </div>
          <p className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl?.toFixed(2) || '0.00'}
          </p>
          <p className={`text-sm mt-1 ${summary.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {summary.total_pnl_percent >= 0 ? '+' : ''}{summary.total_pnl_percent?.toFixed(2) || '0.00'}%
          </p>
        </motion.div>

        {/* Win Rate */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-slate-400">Win Rate</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {winLoss.win_rate?.toFixed(0) || '0'}%
          </p>
          <p className="text-xs text-slate-500 mt-1">
            <span className="text-green-400">{winLoss.winning_positions || 0}W</span>
            {' / '}
            <span className="text-red-400">{winLoss.losing_positions || 0}L</span>
            {' of '}
            {winLoss.total_positions || 0} positions
          </p>
        </motion.div>
      </div>

      {/* P&L Chart */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        data-testid="pnl-chart-container"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-white flex items-center gap-2">
            <LineChartIcon className="w-4 h-4 text-cyan-400" />
            P&L Performance (30 Days)
          </h3>
          {isSampleData && (
            <Badge className="bg-amber-500/20 text-amber-400 text-xs">
              Sample Data - Sync trades for real P&L
            </Badge>
          )}
        </div>
        
        {chartLoading ? (
          <div className="h-64 flex items-center justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          </div>
        ) : pnlChartData.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={pnlChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="pnlGradientPos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="pnlGradientNeg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  tickFormatter={(value) => value.slice(5)} // Show only MM-DD
                  axisLine={{ stroke: '#374151' }}
                />
                <YAxis 
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  tickFormatter={(value) => `$${value}`}
                  axisLine={{ stroke: '#374151' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F9FAFB'
                  }}
                  formatter={(value, name) => [
                    `$${value.toFixed(2)}`,
                    name === 'cumulative_pnl' ? 'Cumulative P&L' : 'Daily P&L'
                  ]}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="cumulative_pnl"
                  stroke="#06B6D4"
                  strokeWidth={2}
                  fill="url(#pnlGradientPos)"
                />
                <Line
                  type="monotone"
                  dataKey="pnl"
                  stroke="#A78BFA"
                  strokeWidth={1.5}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex flex-col items-center justify-center text-slate-500">
            <LineChartIcon className="w-12 h-12 mb-3 opacity-50" />
            <p>No P&L data available</p>
            <p className="text-sm">Sync trade history to see your performance chart</p>
          </div>
        )}
        
        {/* Chart Legend */}
        {pnlChartData.length > 0 && (
          <div className="flex items-center justify-center gap-6 mt-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-400"></div>
              <span className="text-slate-400">Cumulative P&L</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-400"></div>
              <span className="text-slate-400">Daily P&L</span>
            </div>
          </div>
        )}
      </motion.div>

      {/* P&L Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Unrealized vs Realized */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <h3 className="font-medium text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            P&L Breakdown
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Unrealized P&L</span>
              <span className={`font-medium ${summary.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {summary.unrealized_pnl >= 0 ? '+' : ''}${summary.unrealized_pnl?.toFixed(2) || '0.00'}
                <span className="text-sm ml-1">
                  ({summary.unrealized_pnl_percent >= 0 ? '+' : ''}{summary.unrealized_pnl_percent?.toFixed(2) || '0'}%)
                </span>
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Realized P&L</span>
              <span className={`font-medium ${summary.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {summary.realized_pnl >= 0 ? '+' : ''}${summary.realized_pnl?.toFixed(2) || '0.00'}
              </span>
            </div>
            <div className="border-t border-slate-700 pt-3 flex justify-between items-center">
              <span className="text-white font-medium">Total P&L</span>
              <span className={`font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl?.toFixed(2) || '0.00'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Best & Worst */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <h3 className="font-medium text-white mb-4 flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            Top Performers
          </h3>
          <div className="space-y-3">
            {bestPerformer && (
              <div className="flex justify-between items-center p-2 bg-green-500/10 rounded-lg">
                <div className="flex items-center gap-2">
                  <ArrowUpRight className="w-4 h-4 text-green-400" />
                  <span className="text-white">{bestPerformer.symbol}</span>
                  <Badge className="bg-green-500/20 text-green-400">Best</Badge>
                </div>
                <span className="text-green-400 font-medium">
                  {bestPerformer.pnl_percent >= 0 ? '+' : ''}{bestPerformer.pnl_percent?.toFixed(2)}%
                </span>
              </div>
            )}
            {worstPerformer && (
              <div className="flex justify-between items-center p-2 bg-red-500/10 rounded-lg">
                <div className="flex items-center gap-2">
                  <ArrowDownRight className="w-4 h-4 text-red-400" />
                  <span className="text-white">{worstPerformer.symbol}</span>
                  <Badge className="bg-red-500/20 text-red-400">Worst</Badge>
                </div>
                <span className="text-red-400 font-medium">
                  {worstPerformer.pnl_percent?.toFixed(2)}%
                </span>
              </div>
            )}
            {!bestPerformer && !worstPerformer && (
              <p className="text-slate-500 text-sm text-center py-4">
                Sync trade history to see performance data
              </p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Position List */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden"
      >
        <div className="p-4 border-b border-slate-700">
          <h3 className="font-medium text-white flex items-center gap-2">
            <PieChart className="w-4 h-4 text-purple-400" />
            Position Performance
          </h3>
        </div>
        <div className="divide-y divide-slate-700/50">
          {positions.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              No positions found. Sync trade history to see P&L data.
            </div>
          ) : (
            positions.map((pos, idx) => (
              <div key={pos.symbol} className="p-4 flex items-center justify-between hover:bg-slate-700/20">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-medium">
                    {pos.symbol.substring(0, 2)}
                  </div>
                  <div>
                    <p className="font-medium text-white">{pos.symbol}</p>
                    <p className="text-xs text-slate-500">
                      {pos.entry_price ? (
                        <>Entry: ${pos.entry_price.toFixed(4)} → ${pos.current_price?.toFixed(4)}</>
                      ) : (
                        <>Current: ${pos.current_price?.toFixed(4)}</>
                      )}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {pos.pnl_percent !== null ? (
                    <>
                      <p className={`font-medium ${pos.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pos.pnl_percent >= 0 ? '+' : ''}{pos.pnl_percent?.toFixed(2)}%
                      </p>
                      <p className={`text-xs ${pos.pnl_usd >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pos.pnl_usd >= 0 ? '+' : ''}${pos.pnl_usd?.toFixed(2)}
                      </p>
                    </>
                  ) : (
                    <p className="text-slate-500 text-sm">No entry data</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </motion.div>

      {/* Sync Result */}
      {syncResult && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl"
        >
          <h3 className="font-medium text-purple-400 mb-2 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Trade History Synced
          </h3>
          <p className="text-sm text-slate-400">
            Processed {syncResult.summary?.trades_processed || 0} trades 
            ({syncResult.summary?.buys || 0} buys, {syncResult.summary?.sells || 0} sells) 
            from {syncResult.period?.days || 365} days of history.
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Positions updated: {syncResult.summary?.symbols_updated?.join(', ') || 'None'}
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default PerformanceDashboard;
