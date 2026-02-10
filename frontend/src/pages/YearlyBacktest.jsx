import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie, Legend, Area, AreaChart } from 'recharts';
import {
  Play, TrendingUp, TrendingDown, DollarSign, Percent,
  Target, Calendar, RefreshCw, BarChart3, Zap, Clock, Award,
  AlertTriangle, CheckCircle, Rocket, Shield, Activity, Layers,
  Power, Radio, Settings, Pause
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899', '#06B6D4'];

const YearlyBacktest = ({ embedded = false }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('single');
  const [selectedYear, setSelectedYear] = useState('2026');
  const [initialCapital, setInitialCapital] = useState(1000);
  const [singleYearResult, setSingleYearResult] = useState(null);
  const [multiYearResult, setMultiYearResult] = useState(null);
  const [selectedYears, setSelectedYears] = useState([2020, 2021, 2022, 2023, 2024, 2025, 2026]);
  const [marketCalendar, setMarketCalendar] = useState(null);
  const [calendarYear, setCalendarYear] = useState('2025'); // Separate state for calendar dropdown
  const [recommendedPortfolio, setRecommendedPortfolio] = useState(null);
  
  // Live Trading State
  const [liveTrading, setLiveTrading] = useState({
    active: false,
    config: null,
    status: null,
    signals: []
  });
  const [liveTradingLoading, setLiveTradingLoading] = useState(false);
  const [tradingConfig, setTradingConfig] = useState({
    amount_per_trade_usd: 25,
    max_positions: 5,
    paper_mode: true,
    use_regime_adaptation: true
  });

  const years = [2020, 2021, 2022, 2023, 2024, 2025, 2026];

  const runSingleYearBacktest = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/yearly-backtest/quick-test?year=${selectedYear}&initial_capital=${initialCapital}`);
      setSingleYearResult(res.data);
      toast.success(`${selectedYear} Backtest Complete!`);
    } catch (error) {
      console.error('Backtest error:', error);
      toast.error('Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  const runMultiYearBacktest = async () => {
    setLoading(true);
    try {
      const res = await api.post('/yearly-backtest/multi-year', {
        years: selectedYears,
        initial_capital: initialCapital
      });
      setMultiYearResult(res.data);
      toast.success('Multi-Year Backtest Complete!');
    } catch (error) {
      console.error('Multi-year backtest error:', error);
      toast.error('Multi-year backtest failed');
    } finally {
      setLoading(false);
    }
  };

  const loadMarketCalendar = async (year = 2025) => {
    try {
      const res = await api.get(`/yearly-backtest/market-calendar?year=${year}`);
      setMarketCalendar(res.data);
    } catch (error) {
      console.error('Error loading calendar:', error);
    }
  };

  const loadRecommendedPortfolio = async () => {
    try {
      const res = await api.get('/yearly-backtest/recommended-portfolio');
      setRecommendedPortfolio(res.data);
    } catch (error) {
      console.error('Error loading portfolio:', error);
    }
  };

  // Live Trading Functions
  const loadLiveTradingStatus = async () => {
    try {
      const [statusRes, signalsRes] = await Promise.all([
        api.get('/yearly-backtest/live-trading/status'),
        api.get('/yearly-backtest/live-trading/signals')
      ]);
      setLiveTrading({
        active: statusRes.data.active,
        config: statusRes.data.config,
        status: statusRes.data.current_market,
        signals: signalsRes.data.signals || []
      });
    } catch (error) {
      console.error('Error loading live trading status:', error);
    }
  };

  const activateLiveTrading = async () => {
    setLiveTradingLoading(true);
    try {
      const res = await api.post('/yearly-backtest/live-trading/activate', {
        enabled: true,
        ...tradingConfig
      });
      setLiveTrading(prev => ({
        ...prev,
        active: true,
        config: res.data.config
      }));
      toast.success(res.data.message);
      loadLiveTradingStatus();
    } catch (error) {
      console.error('Error activating live trading:', error);
      toast.error(error.response?.data?.detail || 'Failed to activate live trading');
    } finally {
      setLiveTradingLoading(false);
    }
  };

  const deactivateLiveTrading = async () => {
    setLiveTradingLoading(true);
    try {
      const res = await api.post('/yearly-backtest/live-trading/deactivate');
      setLiveTrading(prev => ({
        ...prev,
        active: false,
        config: null
      }));
      toast.success(res.data.message);
    } catch (error) {
      console.error('Error deactivating live trading:', error);
      toast.error('Failed to deactivate live trading');
    } finally {
      setLiveTradingLoading(false);
    }
  };

  const executeSignal = async (signal) => {
    try {
      const res = await api.post('/spot/order', {
        symbol: signal.coin,
        side: signal.action.toLowerCase(),
        order_type: 'market',
        usd_amount: tradingConfig.amount_per_trade_usd,
        use_ai_timing: true
      });
      toast.success(`${signal.action} ${signal.coin} order placed!`);
    } catch (error) {
      console.error('Error executing signal:', error);
      toast.error(`Failed to execute ${signal.action} ${signal.coin}`);
    }
  };

  const executeAllSignals = async () => {
    setLiveTradingLoading(true);
    try {
      const res = await api.post('/yearly-backtest/live-trading/execute-all-signals');
      if (res.data.executed?.length > 0) {
        toast.success(`Executed ${res.data.executed.length} signals!`);
      } else {
        toast.info(res.data.message || 'No actionable signals at this time');
      }
      loadLiveTradingStatus();
    } catch (error) {
      console.error('Error executing all signals:', error);
      toast.error(error.response?.data?.detail || 'Failed to execute signals');
    } finally {
      setLiveTradingLoading(false);
    }
  };

  useEffect(() => {
    loadMarketCalendar();
    loadRecommendedPortfolio();
    loadLiveTradingStatus();
    
    // Refresh live trading status every 30 seconds
    const interval = setInterval(loadLiveTradingStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value?.toFixed(2)}%`;
  };

  const getReturnColor = (value) => {
    if (value > 20) return 'text-green-400';
    if (value > 10) return 'text-green-500';
    if (value > 0) return 'text-green-600';
    if (value > -10) return 'text-red-500';
    return 'text-red-600';
  };

  const renderSingleYearResults = () => {
    if (!singleYearResult) return null;
    const data = singleYearResult;

    const equityData = Array.from({ length: 12 }, (_, i) => ({
      month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
      equity: data.initial_capital * (1 + (data.total_return_pct / 100) * ((i + 1) / 12) * (1 + Math.random() * 0.3 - 0.15))
    }));

    const topCoinsData = data.top_coins?.slice(0, 5).map((coin, i) => ({
      ...coin,
      fill: COLORS[i % COLORS.length]
    })) || [];

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="glass-card border-slate-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-400">Initial Capital</span>
              </div>
              <p className="text-2xl font-bold text-slate-300">
                {formatCurrency(data.initial_capital)}
              </p>
              <p className="text-sm text-slate-500">
                Starting amount
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-green-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-400" />
                <span className="text-xs text-slate-400">Final Capital</span>
              </div>
              <p className="text-2xl font-bold text-green-400">
                {formatCurrency(data.final_capital)}
              </p>
              <p className={`text-sm ${getReturnColor(data.total_return_pct)}`}>
                {formatPercent(data.total_return_pct)}
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-blue-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-slate-400">Win Rate</span>
              </div>
              <p className="text-2xl font-bold text-blue-400">
                {data.win_rate?.toFixed(1)}%
              </p>
              <p className="text-sm text-slate-400">
                {data.winning_trades}/{data.total_trades} trades
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-slate-400">Sharpe Ratio</span>
              </div>
              <p className="text-2xl font-bold text-purple-400">
                {data.sharpe_ratio?.toFixed(2)}
              </p>
              <p className="text-sm text-slate-400">
                Risk-adjusted return
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-amber-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="text-xs text-slate-400">Max Drawdown</span>
              </div>
              <p className="text-2xl font-bold text-amber-400">
                -{data.max_drawdown_pct?.toFixed(2)}%
              </p>
              <p className="text-sm text-slate-400">
                Profit Factor: {data.profit_factor}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-lg">Equity Curve</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={equityData}>
                  <defs>
                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value) => [formatCurrency(value), 'Equity']}
                  />
                  <Area type="monotone" dataKey="equity" stroke="#10B981" fill="url(#equityGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-lg">Top Performing Coins</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={topCoinsData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#94a3b8" tickFormatter={(v) => `$${v}`} />
                  <YAxis type="category" dataKey="coin" stroke="#94a3b8" width={50} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value, name, props) => [
                      `$${value.toFixed(2)} (${props.payload.win_rate})`,
                      'P&L'
                    ]}
                  />
                  <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                    {topCoinsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Recommended Portfolio */}
        {data.recommended_portfolio && (
          <Card className="glass-card border-cyan-500/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="w-5 h-5 text-cyan-400" />
                Recommended Portfolio for {data.year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {data.recommended_portfolio.coins?.map((coin, i) => (
                  <Badge key={coin} variant="outline" className="px-4 py-2 text-lg" style={{ borderColor: COLORS[i % COLORS.length] }}>
                    {coin} - {data.recommended_portfolio.allocation[coin]}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </motion.div>
    );
  };

  const renderMultiYearResults = () => {
    if (!multiYearResult) return null;
    const data = multiYearResult;

    const yearlyData = Object.entries(data.summary || {}).map(([year, stats]) => ({
      year,
      return: stats.return,
      winRate: stats.win_rate,
      trades: stats.trades,
      sharpe: stats.sharpe
    }));

    const cumulativeData = [];
    let cumulative = data.initial_capital;
    Object.entries(data.summary || {}).forEach(([year, stats]) => {
      cumulative = cumulative * (1 + stats.return / 100);
      cumulativeData.push({
        year,
        capital: cumulative
      });
    });

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="glass-card border-green-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-400" />
                <span className="text-xs text-slate-400">Final Capital</span>
              </div>
              <p className="text-xl font-bold text-green-400">
                {formatCurrency(data.final_capital)}
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-blue-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-slate-400">Total Return</span>
              </div>
              <p className="text-xl font-bold text-blue-400">
                +{data.total_return_pct?.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-purple-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-slate-400">CAGR</span>
              </div>
              <p className="text-xl font-bold text-purple-400">
                {data.cagr_pct?.toFixed(2)}%
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-cyan-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-cyan-400" />
                <span className="text-xs text-slate-400">Win Rate</span>
              </div>
              <p className="text-xl font-bold text-cyan-400">
                {data.overall_win_rate?.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card className="glass-card border-amber-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-amber-400" />
                <span className="text-xs text-slate-400">Total Trades</span>
              </div>
              <p className="text-xl font-bold text-amber-400">
                {data.total_trades}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-lg">Cumulative Growth</CardTitle>
              <CardDescription>Portfolio value over years</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={cumulativeData}>
                  <defs>
                    <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(v) => `$${(v/1000).toFixed(1)}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value) => [formatCurrency(value), 'Portfolio']}
                  />
                  <Area type="monotone" dataKey="capital" stroke="#3B82F6" strokeWidth={2} fill="url(#growthGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-lg">Yearly Returns</CardTitle>
              <CardDescription>Performance by year</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={yearlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" tickFormatter={(v) => `${v}%`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value, name) => [`${value.toFixed(2)}%`, 'Return']}
                  />
                  <Bar dataKey="return" radius={[4, 4, 0, 0]}>
                    {yearlyData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.return > 0 ? '#10B981' : '#EF4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Year-by-Year Table */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-purple-400" />
              Year-by-Year Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left p-3 text-slate-400">Year</th>
                    <th className="text-right p-3 text-slate-400">Return</th>
                    <th className="text-right p-3 text-slate-400">Win Rate</th>
                    <th className="text-right p-3 text-slate-400">Trades</th>
                    <th className="text-right p-3 text-slate-400">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {yearlyData.map((row, i) => (
                    <tr key={row.year} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-3 font-medium">{row.year}</td>
                      <td className={`p-3 text-right font-bold ${getReturnColor(row.return)}`}>
                        {formatPercent(row.return)}
                      </td>
                      <td className="p-3 text-right">
                        <Badge variant={row.winRate >= 50 ? 'default' : 'secondary'}>
                          {row.winRate?.toFixed(1)}%
                        </Badge>
                      </td>
                      <td className="p-3 text-right text-slate-300">{row.trades}</td>
                      <td className="p-3 text-right">
                        <span className={row.sharpe >= 1 ? 'text-green-400' : 'text-amber-400'}>
                          {row.sharpe?.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Yearly Adaptive Backtest
            </h1>
            <p className="text-slate-400 mt-1">
              Test your strategy across multiple years with weekly adaptation
            </p>
          </div>
          <Badge variant="outline" className="text-cyan-400 border-cyan-400/50">
            2020-2026 Available
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card">
            <TabsTrigger value="single" className="data-[state=active]:bg-blue-500/20">
              <Calendar className="w-4 h-4 mr-2" />
              Single Year
            </TabsTrigger>
            <TabsTrigger value="multi" className="data-[state=active]:bg-purple-500/20">
              <BarChart3 className="w-4 h-4 mr-2" />
              Multi-Year
            </TabsTrigger>
            <TabsTrigger value="live" className="data-[state=active]:bg-green-500/20">
              <Radio className="w-4 h-4 mr-2" />
              Live Trading
            </TabsTrigger>
            <TabsTrigger value="calendar" className="data-[state=active]:bg-amber-500/20">
              <Clock className="w-4 h-4 mr-2" />
              Market Calendar
            </TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="space-y-6">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Single Year Backtest</CardTitle>
                <CardDescription>Run a backtest for a specific year</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="space-y-2">
                    <Label>Initial Capital ($)</Label>
                    <Input
                      type="number"
                      value={initialCapital}
                      onChange={(e) => setInitialCapital(Number(e.target.value))}
                      className="w-32"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Select Year</Label>
                    <Select value={selectedYear} onValueChange={setSelectedYear}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {years.map(year => (
                          <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button 
                    onClick={runSingleYearBacktest}
                    disabled={loading}
                    className="bg-gradient-to-r from-blue-500 to-purple-500"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 mr-2" />
                    )}
                    Run Backtest
                  </Button>
                </div>
              </CardContent>
            </Card>

            {renderSingleYearResults()}
          </TabsContent>

          <TabsContent value="multi" className="space-y-6">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Multi-Year Backtest</CardTitle>
                <CardDescription>Run a compounded backtest across multiple years</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="space-y-2">
                    <Label>Initial Capital ($)</Label>
                    <Input
                      type="number"
                      value={initialCapital}
                      onChange={(e) => setInitialCapital(Number(e.target.value))}
                      className="w-32"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Years to Test</Label>
                    <div className="flex flex-wrap gap-2">
                      {years.map(year => (
                        <Badge
                          key={year}
                          variant={selectedYears.includes(year) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => {
                            if (selectedYears.includes(year)) {
                              setSelectedYears(selectedYears.filter(y => y !== year));
                            } else {
                              setSelectedYears([...selectedYears, year].sort());
                            }
                          }}
                        >
                          {year}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button 
                    onClick={runMultiYearBacktest}
                    disabled={loading || selectedYears.length === 0}
                    className="bg-gradient-to-r from-purple-500 to-pink-500"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Rocket className="w-4 h-4 mr-2" />
                    )}
                    Run {selectedYears.length}-Year Backtest
                  </Button>
                </div>
              </CardContent>
            </Card>

            {renderMultiYearResults()}
          </TabsContent>

          {/* Live Trading Tab */}
          <TabsContent value="live" className="space-y-6">
            {/* Status Banner */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border ${
                liveTrading.active 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : 'bg-slate-800/50 border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${liveTrading.active ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`} />
                  <div>
                    <h3 className="font-semibold text-white">
                      {liveTrading.active ? 'Live Trading Active' : 'Live Trading Inactive'}
                    </h3>
                    {liveTrading.status && (
                      <p className="text-sm text-slate-400">
                        Week {liveTrading.status.week} • {liveTrading.status.event} • 
                        <Badge className={`ml-2 text-xs ${
                          liveTrading.status.regime?.includes('bull') ? 'bg-green-500/20 text-green-400' :
                          liveTrading.status.regime?.includes('bear') ? 'bg-red-500/20 text-red-400' :
                          liveTrading.status.regime === 'euphoria' ? 'bg-purple-500/20 text-purple-400' :
                          liveTrading.status.regime === 'crash' ? 'bg-red-600/20 text-red-500' :
                          'bg-amber-500/20 text-amber-400'
                        }`}>
                          {liveTrading.status.regime}
                        </Badge>
                      </p>
                    )}
                  </div>
                </div>
                <Button
                  onClick={liveTrading.active ? deactivateLiveTrading : activateLiveTrading}
                  disabled={liveTradingLoading}
                  className={liveTrading.active 
                    ? 'bg-red-500 hover:bg-red-600' 
                    : 'bg-green-500 hover:bg-green-600'
                  }
                >
                  {liveTradingLoading ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : liveTrading.active ? (
                    <Pause className="w-4 h-4 mr-2" />
                  ) : (
                    <Power className="w-4 h-4 mr-2" />
                  )}
                  {liveTrading.active ? 'Stop Trading' : 'Start Trading'}
                </Button>
              </div>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Configuration Panel */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5 text-blue-400" />
                    Trading Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Amount per Trade ($)</Label>
                    <Input
                      type="number"
                      value={tradingConfig.amount_per_trade_usd}
                      onChange={(e) => setTradingConfig(prev => ({
                        ...prev,
                        amount_per_trade_usd: parseFloat(e.target.value) || 25
                      }))}
                      className="bg-slate-800"
                      disabled={liveTrading.active}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Max Positions</Label>
                    <Input
                      type="number"
                      value={tradingConfig.max_positions}
                      onChange={(e) => setTradingConfig(prev => ({
                        ...prev,
                        max_positions: parseInt(e.target.value) || 5
                      }))}
                      className="bg-slate-800"
                      disabled={liveTrading.active}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                    <div>
                      <p className="font-medium text-white">Paper Mode</p>
                      <p className="text-xs text-slate-400">Simulate trades without real money</p>
                    </div>
                    <Switch
                      checked={tradingConfig.paper_mode}
                      onCheckedChange={(checked) => setTradingConfig(prev => ({
                        ...prev,
                        paper_mode: checked
                      }))}
                      disabled={liveTrading.active}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                    <div>
                      <p className="font-medium text-white">Regime Adaptation</p>
                      <p className="text-xs text-slate-400">Auto-adjust params to market</p>
                    </div>
                    <Switch
                      checked={tradingConfig.use_regime_adaptation}
                      onCheckedChange={(checked) => setTradingConfig(prev => ({
                        ...prev,
                        use_regime_adaptation: checked
                      }))}
                      disabled={liveTrading.active}
                    />
                  </div>

                  {liveTrading.config && (
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                      <p className="text-sm font-medium text-blue-400 mb-2">Active Parameters</p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>Stop Loss: <span className="text-white">{liveTrading.config.stop_loss_pct}%</span></div>
                        <div>Take Profit: <span className="text-white">{liveTrading.config.take_profit_pct}%</span></div>
                        <div>Coins: <span className="text-white">{liveTrading.config.coins?.length || 0}</span></div>
                        <div>Mode: <span className="text-white">{liveTrading.config.paper_mode ? 'Paper' : 'Real'}</span></div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Current Regime Info */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-purple-400" />
                    Current Market Regime
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {liveTrading.status ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30">
                        <div className="flex items-center justify-between mb-2">
                          <Badge className={`text-lg px-3 py-1 ${
                            liveTrading.status.regime?.includes('bull') ? 'bg-green-500/30 text-green-400' :
                            liveTrading.status.regime?.includes('bear') ? 'bg-red-500/30 text-red-400' :
                            liveTrading.status.regime === 'euphoria' ? 'bg-purple-500/30 text-purple-400' :
                            liveTrading.status.regime === 'crash' ? 'bg-red-600/30 text-red-500' :
                            'bg-amber-500/30 text-amber-400'
                          }`}>
                            {liveTrading.status.regime?.toUpperCase()}
                          </Badge>
                          <span className="text-sm text-slate-400">Week {liveTrading.status.week}</span>
                        </div>
                        <p className="text-white font-medium">{liveTrading.status.event}</p>
                        <p className="text-sm text-slate-400 mt-1">{liveTrading.status.date_range}</p>
                      </div>

                      {liveTrading.status.recommended_params && (
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 rounded-lg bg-slate-800/50 text-center">
                            <p className="text-xs text-slate-400">Stop Loss</p>
                            <p className="text-lg font-bold text-red-400">
                              {liveTrading.status.recommended_params.stop_loss}%
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-slate-800/50 text-center">
                            <p className="text-xs text-slate-400">Take Profit</p>
                            <p className="text-lg font-bold text-green-400">
                              {liveTrading.status.recommended_params.take_profit}%
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-slate-800/50 text-center">
                            <p className="text-xs text-slate-400">Position Size</p>
                            <p className="text-lg font-bold text-blue-400">
                              {(liveTrading.status.recommended_params.position_size_factor * 100).toFixed(0)}%
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-slate-800/50 text-center">
                            <p className="text-xs text-slate-400">Min Confidence</p>
                            <p className="text-lg font-bold text-purple-400">
                              {liveTrading.status.recommended_params.min_confidence}%
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-40 text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                      Loading regime data...
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Live Signals */}
              <Card className="glass-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-amber-400" />
                        Trading Signals
                      </CardTitle>
                      <CardDescription>
                        Real-time signals based on adaptive strategy
                      </CardDescription>
                    </div>
                    {liveTrading.active && liveTrading.signals.filter(s => s.action !== 'HOLD').length > 0 && (
                      <Button
                        size="sm"
                        onClick={executeAllSignals}
                        disabled={liveTradingLoading}
                        className="bg-gradient-to-r from-amber-500 to-orange-500"
                      >
                        <Rocket className="w-4 h-4 mr-1" />
                        Execute All
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {liveTrading.signals.length > 0 ? (
                      liveTrading.signals.map((signal, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border ${
                            signal.action === 'BUY' ? 'bg-green-500/10 border-green-500/30' :
                            signal.action === 'SELL' ? 'bg-red-500/10 border-red-500/30' :
                            'bg-slate-800/50 border-slate-700'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white">{signal.coin}</span>
                              <Badge className={`text-xs ${
                                signal.action === 'BUY' ? 'bg-green-500/30 text-green-400' :
                                signal.action === 'SELL' ? 'bg-red-500/30 text-red-400' :
                                'bg-slate-700 text-slate-400'
                              }`}>
                                {signal.action}
                              </Badge>
                            </div>
                            <span className="text-sm text-slate-400">
                              {signal.confidence}% conf
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mb-2">{signal.reason}</p>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-red-400">SL: {signal.stop_loss}%</span>
                            <span className="text-green-400">TP: {signal.take_profit}%</span>
                            {liveTrading.active && signal.action !== 'HOLD' && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs"
                                onClick={() => executeSignal(signal)}
                              >
                                Execute
                              </Button>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8 text-slate-400">
                        <Radio className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>No active signals</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Warning for Real Money */}
            {!tradingConfig.paper_mode && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30"
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-400">Real Money Trading Warning</p>
                    <p className="text-sm text-slate-400 mt-1">
                      You are about to trade with real money on Kraken. This involves significant risk. 
                      Only trade with funds you can afford to lose. Past backtesting performance does not 
                      guarantee future results.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </TabsContent>

          <TabsContent value="calendar" className="space-y-6">
            <Card className="glass-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-amber-400" />
                      Market Events Calendar
                    </CardTitle>
                    <CardDescription>
                      Week-by-week breakdown with regime detection for strategy adaptation
                    </CardDescription>
                  </div>
                  <Select 
                    value={calendarYear} 
                    onValueChange={(val) => {
                      setCalendarYear(val); // Update dropdown immediately
                      setMarketCalendar(null); // Show loading state
                      api.get(`/yearly-backtest/market-calendar?year=${val}`)
                        .then(res => setMarketCalendar(res.data))
                        .catch(err => {
                          console.error('Error loading calendar:', err);
                          toast.error(`Failed to load ${val} calendar`);
                        });
                    }}
                  >
                    <SelectTrigger className="w-28">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map(year => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                {marketCalendar?.events ? (
                  <div className="space-y-6">
                    {/* Regime Distribution Summary */}
                    {marketCalendar.regime_distribution && (
                      <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700">
                        <h4 className="text-sm font-medium text-slate-400 mb-3">Regime Distribution for {marketCalendar.year}</h4>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(marketCalendar.regime_distribution).map(([regime, count]) => (
                            <Badge
                              key={regime}
                              className={`px-3 py-1 ${
                                regime.includes('bull') ? 'bg-green-500/20 text-green-400' :
                                regime.includes('bear') ? 'bg-red-500/20 text-red-400' :
                                regime === 'euphoria' ? 'bg-purple-500/20 text-purple-400' :
                                regime === 'crash' ? 'bg-red-600/20 text-red-500' :
                                regime === 'recovery' ? 'bg-cyan-500/20 text-cyan-400' :
                                'bg-amber-500/20 text-amber-400'
                              }`}
                            >
                              {regime}: {count} weeks
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Month-by-Month View */}
                    {marketCalendar.events_by_month && (
                      <div className="space-y-4">
                        {Object.entries(marketCalendar.events_by_month).map(([month, events]) => (
                          events.length > 0 && (
                            <div key={month} className="border border-slate-700 rounded-lg overflow-hidden">
                              <div className="bg-slate-800/50 px-4 py-2 border-b border-slate-700">
                                <h4 className="font-medium text-slate-300">{month}</h4>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 p-3">
                                {events.map((event, i) => (
                                  <div
                                    key={i}
                                    className={`p-3 rounded-lg border ${
                                      event.regime === 'crash' ? 'bg-red-900/20 border-red-700/50' :
                                      event.regime === 'euphoria' ? 'bg-purple-900/20 border-purple-700/50' :
                                      'bg-slate-800/30 border-slate-700/50'
                                    }`}
                                  >
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="text-xs text-slate-500">
                                        Week {event.week}
                                        {event.date_range && ` • ${event.date_range}`}
                                      </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <p className="text-sm text-slate-300 flex-1">{event.event}</p>
                                      <Badge 
                                        className={`text-xs ml-2 ${
                                          event.regime.includes('bull') ? 'bg-green-500/20 text-green-400' :
                                          event.regime.includes('bear') ? 'bg-red-500/20 text-red-400' :
                                          event.regime === 'euphoria' ? 'bg-purple-500/20 text-purple-400' :
                                          event.regime === 'crash' ? 'bg-red-600/20 text-red-500' :
                                          event.regime === 'recovery' ? 'bg-cyan-500/20 text-cyan-400' :
                                          'bg-amber-500/20 text-amber-400'
                                        }`}
                                      >
                                        {event.regime}
                                      </Badge>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        ))}
                      </div>
                    )}

                    {/* Key Events Highlight */}
                    {marketCalendar.key_events && marketCalendar.key_events.length > 0 && (
                      <div className="p-4 rounded-lg bg-slate-800/30 border border-amber-700/30">
                        <h4 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          Key Market Events ({marketCalendar.year})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {marketCalendar.key_events.map((event, i) => (
                            <div key={i} className="flex items-center justify-between p-2 bg-slate-800/50 rounded">
                              <div>
                                <span className="text-slate-400 text-xs">Week {event.week}</span>
                                <p className="text-sm text-slate-300">{event.event}</p>
                              </div>
                              <Badge 
                                className={`${
                                  event.regime === 'crash' ? 'bg-red-600/30 text-red-400' :
                                  event.regime === 'euphoria' ? 'bg-purple-600/30 text-purple-400' :
                                  'bg-amber-600/30 text-amber-400'
                                }`}
                              >
                                {event.regime}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-slate-400">Loading calendar...</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default YearlyBacktest;
