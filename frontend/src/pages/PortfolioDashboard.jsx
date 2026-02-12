import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar
} from 'recharts';
import { 
  Wallet, TrendingUp, TrendingDown, RefreshCw, DollarSign,
  Activity, PieChart as PieIcon, BarChart3, Sparkles, Trophy,
  Calendar, Target, Shield, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import toast from '../utils/toast';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const COLORS = ['#9D00FF', '#00FF94', '#FFB800', '#FF0055', '#007AFF', '#FF6B00', '#00D4FF', '#FF00FF'];

const PortfolioDashboard = ({ embedded = false }) => {
  const [summary, setSummary] = useState(null);
  const [composition, setComposition] = useState(null);
  const [history, setHistory] = useState(null);
  const [topPerformers, setTopPerformers] = useState([]);
  const [worstPerformers, setWorstPerformers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState('30d');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sumRes, compRes, histRes, topRes, worstRes] = await Promise.all([
        api.get('/portfolio/visualization/summary').catch(() => ({ data: null })),
        api.get('/portfolio/visualization/composition').catch(() => ({ data: null })),
        api.get(`/portfolio/visualization/performance-history?range=${selectedRange}`).catch(() => ({ data: null })),
        api.get('/portfolio/visualization/top-performers?limit=5').catch(() => ({ data: { top_performers: [] } })),
        api.get('/portfolio/visualization/worst-performers?limit=5').catch(() => ({ data: { worst_performers: [] } }))
      ]);
      
      setSummary(sumRes.data);
      setComposition(compRes.data);
      setHistory(histRes.data);
      setTopPerformers(topRes.data?.top_performers || []);
      setWorstPerformers(worstRes.data?.worst_performers || []);
      
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load portfolio data', {
        description: 'Please check your connection and try again',
      });
    } finally {
      setLoading(false);
    }
  }, [selectedRange]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCreateSnapshot = async () => {
    const loadingToast = toast.loading('Creating portfolio snapshot...');
    try {
      await api.post('/portfolio/visualization/snapshot');
      toast.dismiss(loadingToast);
      toast.success('Portfolio snapshot saved', {
        description: 'Snapshot created successfully',
        duration: 4000,
      });
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to create snapshot', {
        description: error.response?.data?.detail || 'Please try again',
      });
    }
  };

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  const isAllocated = summary?.allocated;
  const pnlPositive = (summary?.total_pnl || 0) >= 0;

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="portfolio-dashboard">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/20 border border-[#9D00FF]/30">
                <PieIcon size={32} className="text-[#9D00FF]" />
              </div>
              <span className="text-white">Portfolio</span>
              <span className="bg-gradient-to-r from-[#9D00FF] to-[#00FF94] bg-clip-text text-transparent">Dashboard</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Visualize your AI trading portfolio performance and composition
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleCreateSnapshot}
              variant="outline"
              className="border-[#1F1F1F] hover:border-[#9D00FF]/50"
              data-testid="snapshot-btn"
            >
              <Calendar size={16} className="mr-2" />
              Snapshot
            </Button>
            <Button
              onClick={loadData}
              variant="outline"
              className="border-[#1F1F1F]"
              data-testid="refresh-btn"
            >
              <RefreshCw size={16} />
            </Button>
          </div>
        </div>
      </motion.div>

      {!isAllocated ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-[#1F1F1F] flex items-center justify-center">
            <Wallet size={40} className="text-[#A1A1AA]" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">No Budget Allocated</h3>
          <p className="text-[#A1A1AA] max-w-md mx-auto mb-4">
            Allocate a trading budget to start seeing portfolio visualizations.
          </p>
          <Button
            onClick={() => window.location.href = '/budget'}
            className="bg-[#9D00FF] hover:bg-[#9D00FF]/80"
          >
            Go to Trading Budget
          </Button>
        </motion.div>
      ) : (
        <>
          {/* Summary Cards */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          >
            <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
              <div className="absolute top-0 right-0 w-20 h-20 bg-[#9D00FF]/10 rounded-full blur-2xl" />
              <CardContent className="p-4 relative">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign size={18} className="text-[#9D00FF]" />
                  <span className="text-sm text-[#A1A1AA]">Initial Budget</span>
                </div>
                <div className="text-3xl font-data font-bold text-white">
                  ${summary?.initial_budget?.toLocaleString() || 0}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
              <div className="absolute top-0 right-0 w-20 h-20 bg-[#00FF94]/10 rounded-full blur-2xl" />
              <CardContent className="p-4 relative">
                <div className="flex items-center gap-2 mb-2">
                  <Wallet size={18} className="text-[#00FF94]" />
                  <span className="text-sm text-[#A1A1AA]">Current Value</span>
                </div>
                <div className="text-3xl font-data font-bold text-white">
                  ${summary?.current_value?.toLocaleString() || 0}
                </div>
              </CardContent>
            </Card>

            <Card className={`bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative`}>
              <div className={`absolute top-0 right-0 w-20 h-20 ${pnlPositive ? 'bg-[#00FF94]/10' : 'bg-[#FF0055]/10'} rounded-full blur-2xl`} />
              <CardContent className="p-4 relative">
                <div className="flex items-center gap-2 mb-2">
                  {pnlPositive ? (
                    <TrendingUp size={18} className="text-[#00FF94]" />
                  ) : (
                    <TrendingDown size={18} className="text-[#FF0055]" />
                  )}
                  <span className="text-sm text-[#A1A1AA]">Total P&L</span>
                </div>
                <div className={`text-3xl font-data font-bold ${pnlPositive ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                  {pnlPositive ? '+' : ''}${summary?.total_pnl?.toFixed(2) || 0}
                </div>
                <p className={`text-sm ${pnlPositive ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                  {pnlPositive ? '+' : ''}{summary?.total_pnl_pct?.toFixed(2) || 0}%
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
              <div className="absolute top-0 right-0 w-20 h-20 bg-[#FFB800]/10 rounded-full blur-2xl" />
              <CardContent className="p-4 relative">
                <div className="flex items-center gap-2 mb-2">
                  <Activity size={18} className="text-[#FFB800]" />
                  <span className="text-sm text-[#A1A1AA]">Positions</span>
                </div>
                <div className="text-3xl font-data font-bold text-white">
                  {summary?.positions_count || 0}
                </div>
                <p className="text-sm text-[#A1A1AA]">
                  {summary?.gems_count || 0} gems
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Portfolio Composition Pie Chart */}
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <PieIcon className="text-[#9D00FF]" size={20} />
                    Portfolio Composition
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {composition?.composition?.length > 0 ? (
                    <div className="h-[300px] min-h-[300px] w-full">
                      <ResponsiveContainer width="100%" height={300} minWidth={200}>
                        <PieChart>
                          <Pie
                            data={composition.composition}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={2}
                            dataKey="value"
                            nameKey="name"
                          >
                            {composition.composition.map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS[index % COLORS.length]}
                                stroke="#0A0A0A"
                                strokeWidth={2}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload[0]) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-[#1F1F1F] border border-[#333] p-3 rounded-lg shadow-xl">
                                    <p className="text-white font-bold">{data.name}</p>
                                    <p className="text-[#A1A1AA]">${data.value?.toFixed(2)}</p>
                                    <p className="text-[#9D00FF]">{data.percentage?.toFixed(1)}%</p>
                                    {data.pnl_pct !== 0 && (
                                      <p className={data.pnl_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                                        P&L: {data.pnl_pct >= 0 ? '+' : ''}{data.pnl_pct?.toFixed(2)}%
                                      </p>
                                    )}
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-[#A1A1AA]">
                      No positions to display
                    </div>
                  )}}
                  
                  {/* Legend */}
                  <div className="flex flex-wrap gap-3 mt-4 justify-center">
                    {composition?.composition?.slice(0, 6).map((item, idx) => (
                      <div key={item.name} className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        <span className="text-sm text-[#A1A1AA]">{item.name}</span>
                        <span className="text-sm text-white">{item.percentage?.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Performance History Line Chart */}
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-white">
                      <BarChart3 className="text-[#00FF94]" size={20} />
                      Performance History
                    </CardTitle>
                    <div className="flex gap-1">
                      {['1d', '7d', '30d', '90d', 'all'].map((range) => (
                        <Button
                          key={range}
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedRange(range)}
                          className={`text-xs px-2 py-1 ${
                            selectedRange === range 
                              ? 'bg-[#9D00FF]/20 text-[#9D00FF]' 
                              : 'text-[#A1A1AA] hover:text-white'
                          }`}
                          data-testid={`range-${range}`}
                        >
                          {range.toUpperCase()}
                        </Button>
                      ))}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {history?.history?.length > 0 ? (
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={history.history}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#A1A1AA"
                            tick={{ fill: '#A1A1AA', fontSize: 11 }}
                            tickFormatter={(value) => {
                              if (!value) return '';
                              const parts = value.split('-');
                              return `${parts[1]}/${parts[2]}`;
                            }}
                          />
                          <YAxis 
                            stroke="#A1A1AA"
                            tick={{ fill: '#A1A1AA', fontSize: 11 }}
                            tickFormatter={(value) => `$${value}`}
                          />
                          <Tooltip
                            content={({ active, payload, label }) => {
                              if (active && payload && payload[0]) {
                                return (
                                  <div className="bg-[#1F1F1F] border border-[#333] p-3 rounded-lg shadow-xl">
                                    <p className="text-[#A1A1AA] text-sm">{label}</p>
                                    <p className="text-white font-bold">
                                      Value: ${payload[0].value?.toFixed(2)}
                                    </p>
                                    {payload[0].payload.pnl !== undefined && (
                                      <p className={payload[0].payload.pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                                        P&L: {payload[0].payload.pnl >= 0 ? '+' : ''}${payload[0].payload.pnl?.toFixed(2)}
                                      </p>
                                    )}
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#9D00FF" 
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6, fill: '#9D00FF', stroke: '#fff' }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-[#A1A1AA]">
                      No history data available
                    </div>
                  )}
                  
                  {/* Stats */}
                  {history?.stats && (
                    <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-[#1F1F1F]">
                      <div className="text-center">
                        <p className="text-xs text-[#A1A1AA]">Period Return</p>
                        <p className={`font-data font-bold ${history.stats.period_return >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {history.stats.period_return >= 0 ? '+' : ''}{history.stats.period_return}%
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-[#A1A1AA]">High</p>
                        <p className="font-data font-bold text-white">${history.stats.high}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-[#A1A1AA]">Low</p>
                        <p className="font-data font-bold text-white">${history.stats.low}</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Top & Worst Performers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Top Performers */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-[#00FF94]">
                    <Trophy className="text-[#FFB800]" size={20} />
                    Top Performers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {topPerformers.length > 0 ? (
                    <div className="space-y-3">
                      {topPerformers.map((pos, idx) => (
                        <div 
                          key={pos.coin_id} 
                          className="flex items-center justify-between p-3 rounded-lg bg-[#111] border border-[#1F1F1F]"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                              idx === 0 ? 'bg-[#FFB800]/20 text-[#FFB800]' : 'bg-[#00FF94]/20 text-[#00FF94]'
                            }`}>
                              #{idx + 1}
                            </div>
                            <div>
                              <p className="text-white font-medium">{pos.coin_id}</p>
                              <p className="text-xs text-[#A1A1AA]">${pos.current_value?.toFixed(2)}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center gap-1 text-[#00FF94]">
                              <ArrowUpRight size={14} />
                              <span className="font-data font-bold">+{pos.pnl_pct?.toFixed(2)}%</span>
                            </div>
                            <p className="text-xs text-[#00FF94]">+${pos.pnl_usd?.toFixed(2)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[#A1A1AA] text-center py-4">No positions yet</p>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* Worst Performers */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-[#FF0055]">
                    <Shield className="text-[#FF0055]" size={20} />
                    Underperformers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {worstPerformers.length > 0 ? (
                    <div className="space-y-3">
                      {worstPerformers.map((pos, idx) => (
                        <div 
                          key={pos.coin_id} 
                          className="flex items-center justify-between p-3 rounded-lg bg-[#111] border border-[#1F1F1F]"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold bg-[#FF0055]/20 text-[#FF0055]">
                              #{idx + 1}
                            </div>
                            <div>
                              <p className="text-white font-medium">{pos.coin_id}</p>
                              <p className="text-xs text-[#A1A1AA]">${pos.current_value?.toFixed(2)}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center gap-1 text-[#FF0055]">
                              <ArrowDownRight size={14} />
                              <span className="font-data font-bold">{pos.pnl_pct?.toFixed(2)}%</span>
                            </div>
                            <p className="text-xs text-[#FF0055]">${pos.pnl_usd?.toFixed(2)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[#A1A1AA] text-center py-4">No positions yet</p>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Cash vs Invested Bar */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Target className="text-[#007AFF]" size={20} />
                  Allocation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[#A1A1AA]">Invested</span>
                      <span className="text-white font-data">
                        ${(summary?.current_value - summary?.cash_available)?.toFixed(2) || 0} 
                        <span className="text-[#A1A1AA] ml-1">({composition?.invested_pct?.toFixed(1) || 0}%)</span>
                      </span>
                    </div>
                    <div className="h-4 bg-[#1F1F1F] rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-[#9D00FF] to-[#00FF94] rounded-full transition-all duration-500"
                        style={{ width: `${composition?.invested_pct || 0}%` }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[#A1A1AA]">Cash Available</span>
                      <span className="text-white font-data">
                        ${summary?.cash_available?.toFixed(2) || 0}
                        <span className="text-[#A1A1AA] ml-1">({composition?.cash_pct?.toFixed(1) || 0}%)</span>
                      </span>
                    </div>
                    <div className="h-4 bg-[#1F1F1F] rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#FFB800] rounded-full transition-all duration-500"
                        style={{ width: `${composition?.cash_pct || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
                
                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-[#1F1F1F]">
                  <div className="text-center">
                    <p className="text-xs text-[#A1A1AA]">Trades Executed</p>
                    <p className="text-lg font-data font-bold text-white">{summary?.trades_executed || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-[#A1A1AA]">Avg Position Size</p>
                    <p className="text-lg font-data font-bold text-white">${summary?.avg_position_size?.toFixed(2) || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-[#A1A1AA]">Real Trading</p>
                    <Badge className={summary?.real_trading_enabled ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                      {summary?.real_trading_enabled ? 'ENABLED' : 'PAPER'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </div>
  );
};

export default PortfolioDashboard;
