import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  Brain, Newspaper, TrendingUp, TrendingDown, BarChart3, Star,
  Zap, RefreshCw, Play, Pause, Activity, Target, AlertTriangle,
  ChevronRight, ExternalLink, Clock, ThumbsUp, ThumbsDown, Layers,
  Globe, ArrowUpRight, ArrowDownRight, Minus, FlaskConical, Trophy,
  Users, PieChart
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api from '../services/api';

const AdvancedAI = () => {
  const [newsStatus, setNewsStatus] = useState(null);
  const [specialists, setSpecialists] = useState(null);
  const [rlhfStats, setRlhfStats] = useState(null);
  const [exchanges, setExchanges] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('specialists');
  
  // Advanced Features state
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [minScore, setMinScore] = useState(50);
  const [positionSize, setPositionSize] = useState(10);
  const [stopLoss, setStopLoss] = useState(10);
  const [takeProfit, setTakeProfit] = useState(30);
  const [rebalanceData, setRebalanceData] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  const userId = localStorage.getItem('user_id') || 'demo_user';

  const loadData = useCallback(async () => {
    try {
      const [newsRes, specialistsRes, rlhfRes, exchangesRes] = await Promise.all([
        api.get('/advanced-ai/news/status'),
        api.get('/advanced-ai/specialists/status'),
        api.get('/advanced-ai/rlhf/stats'),
        api.get('/advanced-ai/exchanges/status')
      ]);
      
      setNewsStatus(newsRes.data);
      setSpecialists(specialistsRes.data);
      setRlhfStats(rlhfRes.data);
      setExchanges(exchangesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    loadLeaderboard();
    loadRebalanceData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const loadLeaderboard = async () => {
    try {
      const res = await api.get('/social/leaderboard?limit=10');
      const traders = res.data.traders || [];
      setLeaderboard(traders);
    } catch (e) {
      console.error('Leaderboard error:', e);
    }
  };

  const loadRebalanceData = async () => {
    try {
      const res = await api.get('/rebalance/calculate/' + userId);
      setRebalanceData(res.data);
    } catch (e) {
      console.error('Rebalance error:', e);
    }
  };

  const runBacktest = async () => {
    try {
      setBacktestLoading(true);
      toast.loading('Running backtest...');
      
      const res = await api.post('/backtest/run', {
        strategy: {
          min_score: minScore,
          position_size_pct: positionSize,
          stop_loss_pct: stopLoss,
          take_profit_pct: takeProfit,
          max_positions: 3
        },
        coins: ['bitcoin', 'ethereum', 'solana'],
        days: 365,
        initial_capital: 10000
      });
      
      toast.dismiss();
      setBacktestResult(res.data);
      toast.success('Backtest complete!');
    } catch (e) {
      toast.dismiss();
      toast.error('Backtest failed');
      console.error('Backtest error:', e);
    } finally {
      setBacktestLoading(false);
    }
  };

  const executeRebalance = async () => {
    try {
      toast.loading('Executing rebalance...');
      await api.post('/rebalance/execute/' + userId);
      toast.dismiss();
      toast.success('Portfolio rebalanced!');
      await loadRebalanceData();
    } catch (e) {
      toast.dismiss();
      toast.error('Rebalance failed');
    }
  };

  const startNewsMonitor = async () => {
    try {
      await api.post('/advanced-ai/news/start', null, { params: { interval: 60 } });
      toast.success('News monitor started');
      loadData();
    } catch (error) {
      toast.error('Failed to start news monitor');
    }
  };

  const stopNewsMonitor = async () => {
    try {
      await api.post('/advanced-ai/news/stop');
      toast.success('News monitor stopped');
      loadData();
    } catch (error) {
      toast.error('Failed to stop news monitor');
    }
  };

  const getRegimeColor = (regime) => {
    const colors = {
      strong_bull: 'text-green-400',
      bull: 'text-green-300',
      sideways: 'text-yellow-400',
      bear: 'text-red-300',
      strong_bear: 'text-red-400',
      high_volatility: 'text-purple-400',
      unknown: 'text-gray-400'
    };
    return colors[regime] || 'text-gray-400';
  };

  const getRegimeIcon = (regime) => {
    if (regime?.includes('bull')) return <TrendingUp className="text-green-400" />;
    if (regime?.includes('bear')) return <TrendingDown className="text-red-400" />;
    if (regime === 'sideways') return <Minus className="text-yellow-400" />;
    if (regime === 'high_volatility') return <Activity className="text-purple-400" />;
    return <BarChart3 className="text-gray-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="animate-spin text-[#00FF94]" size={48} />
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="advanced-ai-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Brain size={40} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Advanced</span> AI Systems
          </h1>
          <p className="text-[#A1A1AA]">
            Market regime detection, specialist agents, RLHF, and multi-exchange trading
          </p>
        </div>
        <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[#A1A1AA]">Market Regime</p>
                <p className={`text-xl font-bold capitalize ${getRegimeColor(specialists?.current_regime)}`}>
                  {specialists?.current_regime?.replace('_', ' ') || 'Unknown'}
                </p>
              </div>
              {getRegimeIcon(specialists?.current_regime)}
            </div>
            <Progress value={specialists?.regime_confidence || 0} className="mt-2 h-1" />
            <p className="text-xs text-[#A1A1AA] mt-1">{(specialists?.regime_confidence || 0).toFixed(0)}% confidence</p>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[#A1A1AA]">News Monitor</p>
                <p className={`text-xl font-bold ${newsStatus?.is_running ? 'text-green-400' : 'text-gray-400'}`}>
                  {newsStatus?.is_running ? 'Active' : 'Inactive'}
                </p>
              </div>
              <Newspaper className={newsStatus?.is_running ? 'text-green-400' : 'text-gray-400'} />
            </div>
            <p className="text-xs text-[#A1A1AA] mt-2">
              {newsStatus?.stats?.news_processed || 0} articles processed
            </p>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[#A1A1AA]">RLHF Ratings</p>
                <p className="text-xl font-bold text-[#FFB800]">
                  {rlhfStats?.total_ratings || 0}
                </p>
              </div>
              <Star className="text-[#FFB800]" />
            </div>
            <p className="text-xs text-[#A1A1AA] mt-2">
              Avg: {(rlhfStats?.avg_rating || 0).toFixed(1)} / 5.0
            </p>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[#A1A1AA]">Exchanges</p>
                <p className="text-xl font-bold text-[#00FF94]">
                  {exchanges?.exchanges_count || 0} / 3
                </p>
              </div>
              <Globe className="text-[#00FF94]" />
            </div>
            <p className="text-xs text-[#A1A1AA] mt-2">
              {exchanges?.exchanges_configured?.join(', ') || 'None configured'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F] p-1">
          <TabsTrigger value="specialists" className="data-[state=active]:bg-[#9D00FF]">
            <Layers size={16} className="mr-2" />
            Specialist Agents
          </TabsTrigger>
          <TabsTrigger value="news" className="data-[state=active]:bg-[#9D00FF]">
            <Newspaper size={16} className="mr-2" />
            News Monitor
          </TabsTrigger>
          <TabsTrigger value="rlhf" className="data-[state=active]:bg-[#9D00FF]">
            <Star size={16} className="mr-2" />
            RLHF
          </TabsTrigger>
          <TabsTrigger value="exchanges" className="data-[state=active]:bg-[#9D00FF]">
            <Globe size={16} className="mr-2" />
            Multi-Exchange
          </TabsTrigger>
          <TabsTrigger value="features" className="data-[state=active]:bg-[#9D00FF]">
            <FlaskConical size={16} className="mr-2" />
            Features
          </TabsTrigger>
        </TabsList>

        {/* Specialist Agents Tab */}
        <TabsContent value="specialists" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Regime Detection */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="text-[#9D00FF]" />
                  Market Regime Detection
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-[#121212] rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[#A1A1AA]">Current Regime</span>
                    <span className={`font-bold capitalize ${getRegimeColor(specialists?.current_regime)}`}>
                      {specialists?.current_regime?.replace('_', ' ') || 'Unknown'}
                    </span>
                  </div>
                  <Progress value={specialists?.regime_confidence || 0} className="h-2" />
                  <p className="text-xs text-[#A1A1AA] mt-1 text-right">
                    {(specialists?.regime_confidence || 0).toFixed(1)}% confidence
                  </p>
                </div>

                <div className="space-y-2">
                  <p className="text-sm text-[#A1A1AA]">Regime Types:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {['strong_bull', 'bull', 'sideways', 'bear', 'strong_bear', 'high_volatility'].map(regime => (
                      <div key={regime} className={`p-2 rounded text-xs ${specialists?.current_regime === regime ? 'bg-[#9D00FF]/20 border border-[#9D00FF]' : 'bg-[#121212]'}`}>
                        <span className={`capitalize ${getRegimeColor(regime)}`}>
                          {regime.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Specialist Performance */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="text-[#00FF94]" />
                  Specialist Agent Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {specialists?.agent_performance && Object.entries(specialists.agent_performance).map(([key, agent]) => (
                    <div key={key} className="p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{agent.name}</span>
                        <span className="text-xs text-[#A1A1AA]">{agent.target_regime}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[#A1A1AA]">Win Rate</span>
                        <span className={agent.win_rate >= 0.5 ? 'text-green-400' : 'text-red-400'}>
                          {(agent.win_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[#A1A1AA]">Trades</span>
                        <span>{agent.total_trades}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* News Monitor Tab */}
        <TabsContent value="news" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Newspaper className="text-[#FFB800]" />
                  Real-Time News Monitor
                </div>
                <div className="flex gap-2">
                  {newsStatus?.is_running ? (
                    <Button onClick={stopNewsMonitor} variant="destructive" size="sm">
                      <Pause size={16} className="mr-2" />
                      Stop
                    </Button>
                  ) : (
                    <Button onClick={startNewsMonitor} className="bg-[#00FF94] text-black hover:bg-[#00FF94]/80" size="sm">
                      <Play size={16} className="mr-2" />
                      Start
                    </Button>
                  )}
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Status</p>
                  <p className={`text-lg font-bold ${newsStatus?.is_running ? 'text-green-400' : 'text-gray-400'}`}>
                    {newsStatus?.is_running ? 'Running' : 'Stopped'}
                  </p>
                </div>
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Articles Processed</p>
                  <p className="text-lg font-bold text-white">{newsStatus?.stats?.news_processed || 0}</p>
                </div>
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Alerts Triggered</p>
                  <p className="text-lg font-bold text-[#FFB800]">{newsStatus?.stats?.alerts_triggered || 0}</p>
                </div>
              </div>

              {/* Trending Topics */}
              <div className="p-4 bg-[#121212] rounded-lg">
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Zap className="text-[#FFB800]" size={16} />
                  Trending Topics
                </h4>
                {newsStatus?.trending?.top_keywords?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {newsStatus.trending.top_keywords.map((item, i) => (
                      <span key={i} className="px-2 py-1 bg-[#1F1F1F] rounded text-xs">
                        {item.keyword} ({item.count})
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-[#A1A1AA]">No trending topics yet. Start the monitor to track news.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* RLHF Tab */}
        <TabsContent value="rlhf" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="text-[#FFB800]" />
                Reinforcement Learning from Human Feedback
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Total Ratings</p>
                  <p className="text-2xl font-bold text-white">{rlhfStats?.total_ratings || 0}</p>
                </div>
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Average Rating</p>
                  <div className="flex items-center gap-2">
                    <p className="text-2xl font-bold text-[#FFB800]">{(rlhfStats?.avg_rating || 0).toFixed(1)}</p>
                    <div className="flex">
                      {[1,2,3,4,5].map(i => (
                        <Star key={i} size={14} className={i <= Math.round(rlhfStats?.avg_rating || 0) ? 'text-[#FFB800] fill-[#FFB800]' : 'text-gray-600'} />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-[#121212] rounded-lg">
                  <p className="text-xs text-[#A1A1AA]">Pending Feedback</p>
                  <p className="text-2xl font-bold text-[#9D00FF]">{rlhfStats?.pending_trades || 0}</p>
                </div>
              </div>

              {/* Reward Model Weights */}
              <div className="p-4 bg-[#121212] rounded-lg">
                <h4 className="text-sm font-medium mb-3">Learned Reward Model Weights</h4>
                <div className="space-y-2">
                  {rlhfStats?.reward_model_weights && Object.entries(rlhfStats.reward_model_weights).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-xs text-[#A1A1AA] capitalize">{key.replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-2">
                        <Progress value={Math.abs(value) * 100} className="w-20 h-1" />
                        <span className={`text-xs ${value >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {value >= 0 ? '+' : ''}{value.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Multi-Exchange Tab */}
        <TabsContent value="exchanges" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="text-[#00FF94]" />
                Multi-Exchange Trading
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {['kraken', 'binance', 'coinbase'].map(exchange => {
                  const isConfigured = exchanges?.exchanges_configured?.includes(exchange);
                  return (
                    <div key={exchange} className={`p-4 rounded-lg border ${isConfigured ? 'bg-[#00FF94]/10 border-[#00FF94]' : 'bg-[#121212] border-[#1F1F1F]'}`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium capitalize">{exchange}</span>
                        {isConfigured ? (
                          <span className="px-2 py-1 bg-[#00FF94]/20 text-[#00FF94] text-xs rounded">Connected</span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-600/20 text-gray-400 text-xs rounded">Not Configured</span>
                        )}
                      </div>
                      <p className="text-xs text-[#A1A1AA]">
                        {isConfigured ? 'Ready for trading' : 'Add API keys to enable'}
                      </p>
                    </div>
                  );
                })}
              </div>

              <div className="p-4 bg-[#121212] rounded-lg">
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <AlertTriangle className="text-[#FFB800]" size={16} />
                  Features Available
                </h4>
                <ul className="space-y-1 text-sm text-[#A1A1AA]">
                  <li>• Unified portfolio view across all exchanges</li>
                  <li>• Best price discovery for any trading pair</li>
                  <li>• Cross-exchange arbitrage detection</li>
                  <li>• Smart order routing to best exchange</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Features Tab */}
        <TabsContent value="features" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Backtest Panel */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="text-[#9D00FF]" />
                  Strategy Backtest
                </CardTitle>
                <CardDescription>Test AI strategies with historical data</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Min Score</Label>
                    <Input 
                      type="number" 
                      value={minScore} 
                      onChange={(e) => setMinScore(Number(e.target.value))} 
                      min="0" 
                      max="100"
                    />
                  </div>
                  <div>
                    <Label>Position Size %</Label>
                    <Input 
                      type="number" 
                      value={positionSize} 
                      onChange={(e) => setPositionSize(Number(e.target.value))} 
                      min="1" 
                      max="100"
                    />
                  </div>
                  <div>
                    <Label>Stop Loss %</Label>
                    <Input 
                      type="number" 
                      value={stopLoss} 
                      onChange={(e) => setStopLoss(Number(e.target.value))} 
                      min="1" 
                      max="50"
                    />
                  </div>
                  <div>
                    <Label>Take Profit %</Label>
                    <Input 
                      type="number" 
                      value={takeProfit} 
                      onChange={(e) => setTakeProfit(Number(e.target.value))} 
                      min="1" 
                      max="200"
                    />
                  </div>
                </div>

                <Button 
                  onClick={runBacktest} 
                  disabled={backtestLoading}
                  className="w-full"
                >
                  {backtestLoading ? (
                    <RefreshCw className="mr-2 animate-spin" size={16} />
                  ) : (
                    <Play className="mr-2" size={16} />
                  )}
                  {backtestLoading ? 'Running...' : 'Run Backtest'}
                </Button>

                {backtestResult && (
                  <div className="mt-4 space-y-2 p-4 bg-[#1F1F1F] rounded-lg">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-[#A1A1AA]">Total Trades:</span>
                        <span className="text-white ml-2">{backtestResult.total_trades}</span>
                      </div>
                      <div>
                        <span className="text-[#A1A1AA]">Win Rate:</span>
                        <span className="text-white ml-2">{backtestResult.win_rate?.toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-[#A1A1AA]">Final Value:</span>
                        <span className="text-white ml-2">${backtestResult.final_value?.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-[#A1A1AA]">Total Return:</span>
                        <span className={`ml-2 ${backtestResult.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {backtestResult.total_return >= 0 ? '+' : ''}{backtestResult.total_return?.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Portfolio Rebalance */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="text-[#00FF94]" />
                  Portfolio Rebalance
                </CardTitle>
                <CardDescription>AI-powered portfolio optimization</CardDescription>
              </CardHeader>
              <CardContent>
                {rebalanceData ? (
                  <div className="space-y-4">
                    <div className="text-sm text-[#A1A1AA]">
                      Suggested adjustments to optimize your portfolio allocation
                    </div>
                    {rebalanceData.recommendations?.length > 0 ? (
                      <div className="space-y-2">
                        {rebalanceData.recommendations.slice(0, 5).map((rec, idx) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-[#1F1F1F] rounded">
                            <span className="text-white">{rec.symbol}</span>
                            <div className="flex items-center gap-2">
                              {rec.action === 'buy' ? (
                                <TrendingUp className="text-green-400" size={16} />
                              ) : (
                                <TrendingDown className="text-red-400" size={16} />
                              )}
                              <span className={rec.action === 'buy' ? 'text-green-400' : 'text-red-400'}>
                                {rec.action.toUpperCase()} {rec.amount}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4 text-[#A1A1AA]">
                        Portfolio is optimally balanced
                      </div>
                    )}
                    <Button 
                      onClick={executeRebalance}
                      className="w-full mt-4"
                      disabled={!rebalanceData.recommendations?.length}
                    >
                      <RefreshCw className="mr-2" size={16} />
                      Execute Rebalance
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-[#A1A1AA]">
                    Loading rebalance data...
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Leaderboard */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="text-[#FFB800]" />
                  Top Traders Leaderboard
                </CardTitle>
                <CardDescription>Compare your performance with other traders</CardDescription>
              </CardHeader>
              <CardContent>
                {leaderboard.length > 0 ? (
                  <div className="space-y-2">
                    {leaderboard.map((trader, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-[#1F1F1F] rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                            idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                            idx === 1 ? 'bg-gray-400/20 text-gray-300' :
                            idx === 2 ? 'bg-orange-500/20 text-orange-400' :
                            'bg-[#333333] text-[#A1A1AA]'
                          }`}>
                            {idx + 1}
                          </div>
                          <div>
                            <div className="text-white font-medium">{trader.username || `Trader ${idx + 1}`}</div>
                            <div className="text-xs text-[#A1A1AA]">{trader.trades} trades</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold ${trader.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trader.pnl >= 0 ? '+' : ''}{trader.pnl?.toFixed(2)}%
                          </div>
                          <div className="text-xs text-[#A1A1AA]">
                            {trader.win_rate?.toFixed(1)}% WR
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-[#A1A1AA]">
                    <Users className="mx-auto mb-2" size={32} />
                    No leaderboard data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedAI;
