import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Activity, Brain, Shield, TrendingUp, TrendingDown, 
  AlertTriangle, Play, Pause, BarChart3, Zap, 
  RefreshCw, ChevronDown, ChevronUp, Waves, Wifi, WifiOff
} from 'lucide-react';
import { toast } from 'sonner';
import { useComponentState, ComponentType } from '../hooks/useSystemState';

const API_URL = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_BACKEND_URL;
const WS_URL = API_URL?.replace('https://', 'wss://').replace('http://', 'ws://');

// Mobile-optimized Tethys Dashboard for Galaxy S22 (1080x2340)
const TethysDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [tradingData, setTradingData] = useState(null);
  const [trainingData, setTrainingData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const pollingInitializedRef = useRef(false);

  // Use persisted state for Tethys trading
  const { 
    isRunning: tethysTradingPersisted, 
    setRunning: setTethysTradingState,
    refresh: refreshTethysState 
  } = useComponentState(ComponentType.TETHYS_TRADING, {
    pollInterval: 10000,
  });

  // WebSocket disabled - using HTTP polling for reliable updates in deployment
  // Kubernetes ingress doesn't support WebSocket protocol upgrade
  useEffect(() => {
    if (!pollingInitializedRef.current) {
      console.info('[TethysDashboard] Using HTTP polling mode for updates');
      pollingInitializedRef.current = true;
    }
    setWsConnected(false);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [dashboard, trading, training, newsData, mktSentiment] = await Promise.all([
        fetch(`${API_URL}/api/tethys/dashboard`).then(r => r.json()),
        fetch(`${API_URL}/api/tethys-trading/dashboard`).then(r => r.json()),
        fetch(`${API_URL}/api/tethys-train/dashboard`).then(r => r.json()),
        fetch(`${API_URL}/api/tethys/news?limit=5`).then(r => r.json()).catch(() => ({ news: [] })),
        fetch(`${API_URL}/api/tethys/sentiment`).then(r => r.json()).catch(() => null)
      ]);
      
      setDashboardData(dashboard);
      setTradingData(trading);
      setTrainingData(training);
      setSentimentData(newsData);
      setMarketSentiment(mktSentiment);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const startTrading = async () => {
    try {
      const res = await fetch(`${API_URL}/api/tethys-trading/start?interval=60`, {
        method: 'POST'
      });
      const data = await res.json();
      await setTethysTradingState(true, { interval: 60 });
      toast.success('Trading loop started');
      fetchData();
      refreshTethysState();
    } catch (error) {
      toast.error('Failed to start trading');
    }
  };

  const stopTrading = async () => {
    try {
      await fetch(`${API_URL}/api/tethys-trading/stop`, { method: 'POST' });
      await setTethysTradingState(false);
      toast.success('Trading stopped');
      fetchData();
      refreshTethysState();
    } catch (error) {
      toast.error('Failed to stop trading');
    }
  };

  const runTick = async () => {
    try {
      const res = await fetch(`${API_URL}/api/tethys-trading/full-cycle?symbol=BTC/USD`, {
        method: 'POST'
      });
      const data = await res.json();
      toast.success(`Action: ${data.action || 'none'}`);
      fetchData();
    } catch (error) {
      toast.error('Tick failed');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Waves className="w-16 h-16 text-cyan-400 animate-pulse mx-auto mb-4" />
          <p className="text-cyan-300 text-lg">Loading Tethys...</p>
        </div>
      </div>
    );
  }

  const riskState = dashboardData?.risk?.state || {};
  const isTrading = tradingData?.trading_loop?.is_running;
  const isTraining = trainingData?.training?.is_training;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900 pb-20">
      {/* Mobile Header - Optimized for S22 */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-lg border-b border-cyan-500/20 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Waves className="w-7 h-7 text-cyan-400" />
            <div>
              <h1 className="text-lg font-bold text-white">Tethys</h1>
              <p className="text-[10px] text-cyan-400/70">Rainbow DQN Agent</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* WebSocket Status */}
            <div className="flex items-center gap-1" title={wsConnected ? 'Live updates connected' : 'Reconnecting...'}>
              {wsConnected ? (
                <Wifi className="w-3.5 h-3.5 text-green-400" />
              ) : (
                <WifiOff className="w-3.5 h-3.5 text-slate-500" />
              )}
            </div>
            <Badge 
              variant={isTrading ? "default" : "secondary"}
              className={`text-xs ${isTrading ? 'bg-green-500/20 text-green-400 border-green-500/50' : 'bg-slate-700'}`}
            >
              {isTrading ? 'LIVE' : 'IDLE'}
            </Badge>
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={fetchData}
              className="p-2"
            >
              <RefreshCw className="w-4 h-4 text-cyan-400" />
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Stats Row - Mobile Optimized */}
      <div className="px-4 py-3 grid grid-cols-3 gap-2">
        <StatCard 
          label="Portfolio"
          value={`$${(riskState.portfolio_value || 0).toLocaleString()}`}
          trend={riskState.daily_pnl_pct > 0 ? 'up' : 'down'}
          small
        />
        <StatCard 
          label="Daily P&L"
          value={`${((riskState.daily_pnl_pct || 0) * 100).toFixed(2)}%`}
          trend={riskState.daily_pnl_pct > 0 ? 'up' : 'down'}
          small
        />
        <StatCard 
          label="Drawdown"
          value={`${((riskState.current_drawdown_pct || 0) * 100).toFixed(1)}%`}
          trend="neutral"
          warning={riskState.current_drawdown_pct > 0.1}
          small
        />
      </div>

      {/* Main Action Buttons - Touch Optimized */}
      <div className="px-4 py-2 flex gap-2">
        <Button
          onClick={isTrading ? stopTrading : startTrading}
          className={`flex-1 h-12 ${isTrading 
            ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/50' 
            : 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/50'
          }`}
        >
          {isTrading ? <Pause className="w-5 h-5 mr-2" /> : <Play className="w-5 h-5 mr-2" />}
          {isTrading ? 'Stop' : 'Start'} Trading
        </Button>
        <Button
          onClick={runTick}
          variant="outline"
          className="h-12 px-4 border-cyan-500/50 text-cyan-400"
        >
          <Zap className="w-5 h-5" />
        </Button>
      </div>

      {/* Tabs - Mobile Friendly */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="px-4 mt-2">
        <TabsList className="w-full bg-slate-800/50 p-1 h-10">
          <TabsTrigger value="overview" className="flex-1 text-xs data-[state=active]:bg-cyan-500/20">
            Overview
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex-1 text-xs data-[state=active]:bg-cyan-500/20">
            AI
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex-1 text-xs data-[state=active]:bg-cyan-500/20">
            Risk
          </TabsTrigger>
          <TabsTrigger value="train" className="flex-1 text-xs data-[state=active]:bg-cyan-500/20">
            Train
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-3 space-y-3">
          {/* Latest Decision Card */}
          <ExpandableCard
            title="Latest Decision"
            icon={<Brain className="w-4 h-4 text-cyan-400" />}
            expanded={expandedCard === 'decision'}
            onToggle={() => setExpandedCard(expandedCard === 'decision' ? null : 'decision')}
          >
            {tradingData?.explainability?.top_features ? (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Action</span>
                  <Badge className="bg-blue-500/20 text-blue-400">
                    {tradingData.explainability.top_features[0]?.feature || 'N/A'}
                  </Badge>
                </div>
                <div className="space-y-1">
                  {tradingData.explainability.top_features.slice(0, 3).map((f, i) => (
                    <div key={i} className="flex justify-between text-xs">
                      <span className="text-slate-500">{f.feature}</span>
                      <span className={f.avg_contribution > 0 ? 'text-green-400' : 'text-red-400'}>
                        {f.avg_contribution?.toFixed(3)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No decisions yet</p>
            )}
          </ExpandableCard>

          {/* Uncertainty Card */}
          <ExpandableCard
            title="Model Confidence"
            icon={<Activity className="w-4 h-4 text-purple-400" />}
            expanded={expandedCard === 'confidence'}
            onToggle={() => setExpandedCard(expandedCard === 'confidence' ? null : 'confidence')}
          >
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Confidence</span>
                  <span className="text-cyan-400">
                    {((dashboardData?.uncertainty?.avg_confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress 
                  value={(dashboardData?.uncertainty?.avg_confidence || 0) * 100} 
                  className="h-2 bg-slate-700"
                />
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Uncertainty</span>
                  <span className="text-orange-400">
                    {((dashboardData?.uncertainty?.avg_uncertainty || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress 
                  value={(dashboardData?.uncertainty?.avg_uncertainty || 0) * 100} 
                  className="h-2 bg-slate-700"
                />
              </div>
            </div>
          </ExpandableCard>

          {/* Evolution Card */}
          {tradingData?.evolution?.generation > 0 && (
            <ExpandableCard
              title="Genetic Evolution"
              icon={<BarChart3 className="w-4 h-4 text-green-400" />}
              expanded={expandedCard === 'evolution'}
              onToggle={() => setExpandedCard(expandedCard === 'evolution' ? null : 'evolution')}
            >
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Generation</span>
                  <span className="text-white font-mono">{tradingData.evolution.generation}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Best Fitness</span>
                  <span className="text-green-400 font-mono">
                    {tradingData.evolution.fitness?.toFixed(4)}
                  </span>
                </div>
              </div>
            </ExpandableCard>
          )}

          {/* Market Sentiment Card */}
          <ExpandableCard
            title="Market Sentiment"
            icon={<Activity className="w-4 h-4 text-orange-400" />}
            expanded={expandedCard === 'sentiment'}
            onToggle={() => setExpandedCard(expandedCard === 'sentiment' ? null : 'sentiment')}
          >
            <div className="space-y-3">
              {/* Fear & Greed Index - Primary Indicator */}
              {marketSentiment?.fear_greed_index !== undefined && (
                <div className="p-3 rounded-lg bg-gradient-to-r from-red-500/10 via-yellow-500/10 to-green-500/10 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400">Fear & Greed Index</span>
                    <Badge className={`text-[10px] ${
                      marketSentiment.fear_greed_index <= 24 ? 'bg-red-500/20 text-red-400' :
                      marketSentiment.fear_greed_index <= 44 ? 'bg-orange-500/20 text-orange-400' :
                      marketSentiment.fear_greed_index <= 55 ? 'bg-yellow-500/20 text-yellow-400' :
                      marketSentiment.fear_greed_index <= 74 ? 'bg-lime-500/20 text-lime-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {marketSentiment.fear_greed_classification}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-2xl font-bold ${
                      marketSentiment.fear_greed_index <= 24 ? 'text-red-400' :
                      marketSentiment.fear_greed_index <= 44 ? 'text-orange-400' :
                      marketSentiment.fear_greed_index <= 55 ? 'text-yellow-400' :
                      marketSentiment.fear_greed_index <= 74 ? 'text-lime-400' :
                      'text-green-400'
                    }`}>
                      {marketSentiment.fear_greed_index}
                    </span>
                    <div className="flex-1 h-2 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 relative">
                      <div 
                        className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-slate-900 shadow-lg"
                        style={{ left: `${marketSentiment.fear_greed_index}%` }}
                      />
                    </div>
                  </div>
                  {marketSentiment.fear_greed_recommendation && (
                    <p className="text-[10px] text-slate-500 mt-2">
                      Recommendation: <span className="text-slate-300">{marketSentiment.fear_greed_recommendation}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Aggregated Sentiment Score */}
              {marketSentiment && (
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/50">
                  <div className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${
                      marketSentiment.signal === 'BULLISH' ? 'bg-green-400' :
                      marketSentiment.signal === 'BEARISH' ? 'bg-red-400' : 'bg-yellow-400'
                    }`} />
                    <span className="text-xs text-slate-400">Combined Score</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-mono ${
                      marketSentiment.signal === 'BULLISH' ? 'text-green-400' :
                      marketSentiment.signal === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      {(marketSentiment.overall_score * 100).toFixed(0)}%
                    </span>
                    <Badge className={`text-[10px] ${
                      marketSentiment.signal === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      marketSentiment.signal === 'BEARISH' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {marketSentiment.signal}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Coin Breakdown */}
              {marketSentiment?.breakdown && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(marketSentiment.breakdown).map(([coin, signal]) => (
                    <span key={coin} className={`text-[10px] px-2 py-1 rounded-full ${
                      signal === 'BULLISH' ? 'bg-green-500/10 text-green-400' :
                      signal === 'BEARISH' ? 'bg-red-500/10 text-red-400' : 'bg-slate-700 text-slate-400'
                    }`}>
                      {coin}: {signal.charAt(0)}
                    </span>
                  ))}
                </div>
              )}

              {/* News Feed */}
              <div className="space-y-2 pt-2 border-t border-slate-700/50">
                <p className="text-[10px] text-slate-500 uppercase">Latest News ({sentimentData?.source || 'coinstats'})</p>
                {sentimentData?.news?.slice(0, 3).map((item, i) => (
                  <div key={i} className="flex items-start gap-2 pb-2 border-b border-slate-700/50 last:border-0">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                      item.sentiment?.label === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      item.sentiment?.label === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {item.sentiment?.label?.charAt(0) || 'N'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <a 
                        href={item.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-slate-300 line-clamp-2 hover:text-cyan-400 transition-colors"
                      >
                        {item.title}
                      </a>
                      <div className="flex items-center gap-2 mt-1">
                        {item.related_coins?.slice(0, 2).map((coin, j) => (
                          <span key={j} className="text-[10px] text-cyan-400">{coin}</span>
                        ))}
                        <span className="text-[10px] text-slate-500">
                          {item.source} • {new Date(item.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
                {(!sentimentData?.news || sentimentData.news.length === 0) && (
                  <p className="text-xs text-slate-500">No recent news</p>
                )}
              </div>
            </div>
          </ExpandableCard>
        </TabsContent>

        {/* AI Tab */}
        <TabsContent value="ai" className="mt-3 space-y-3">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <Brain className="w-4 h-4 text-cyan-400" />
                Rainbow DQN Status
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
              <InfoRow label="Model Type" value="C51 + Transformer" />
              <InfoRow label="Sequence Length" value="168 timesteps" />
              <InfoRow label="Atoms" value="51" />
              <InfoRow label="N-Step" value="3" />
              <InfoRow 
                label="Components" 
                value={Object.values(tradingData?.trading_loop?.components || {}).filter(Boolean).length + '/4'} 
              />
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-400" />
                Session Stats
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
              <InfoRow label="Total Ticks" value={tradingData?.trading_loop?.total_ticks || 0} />
              <InfoRow label="Executed Trades" value={tradingData?.trading_loop?.executed_trades || 0} />
              <InfoRow 
                label="Session Duration" 
                value={tradingData?.trading_loop?.session_duration?.split('.')[0] || '0:00:00'} 
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Tab */}
        <TabsContent value="risk" className="mt-3 space-y-3">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="w-4 h-4 text-cyan-400" />
                Risk Limits
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
              <InfoRow 
                label="Max Position" 
                value={`${((dashboardData?.risk?.limits?.max_position_pct || 0.25) * 100).toFixed(0)}%`} 
              />
              <InfoRow 
                label="Max Daily Loss" 
                value={`${((dashboardData?.risk?.limits?.max_daily_loss_pct || 0.05) * 100).toFixed(0)}%`} 
              />
              <InfoRow 
                label="Circuit Breaker" 
                value={`${((dashboardData?.risk?.limits?.circuit_breaker_loss_pct || 0.1) * 100).toFixed(0)}%`} 
              />
              <InfoRow 
                label="Max Drawdown" 
                value={`${((dashboardData?.risk?.limits?.max_drawdown_pct || 0.15) * 100).toFixed(0)}%`} 
              />
            </CardContent>
          </Card>

          {/* Circuit Breaker Status */}
          <Card className={`border ${riskState.circuit_breaker_active 
            ? 'bg-red-500/10 border-red-500/50' 
            : 'bg-slate-800/50 border-slate-700'}`}
          >
            <CardContent className="py-4 px-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`w-5 h-5 ${riskState.circuit_breaker_active ? 'text-red-400' : 'text-slate-500'}`} />
                  <span className="text-sm">Circuit Breaker</span>
                </div>
                <Badge className={riskState.circuit_breaker_active 
                  ? 'bg-red-500/20 text-red-400' 
                  : 'bg-green-500/20 text-green-400'
                }>
                  {riskState.circuit_breaker_active ? 'ACTIVE' : 'OK'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Loss Streak */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="py-4 px-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Consecutive Losses</span>
                <span className={`font-mono ${riskState.consecutive_losses > 3 ? 'text-red-400' : 'text-white'}`}>
                  {riskState.consecutive_losses || 0} / 5
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Training Tab */}
        <TabsContent value="train" className="mt-3 space-y-3">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-green-400" />
                Training Status
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">Status</span>
                <Badge className={isTraining 
                  ? 'bg-yellow-500/20 text-yellow-400' 
                  : 'bg-slate-700 text-slate-400'
                }>
                  {isTraining ? 'Training...' : 'Idle'}
                </Badge>
              </div>
              
              {isTraining && (
                <>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Progress</span>
                      <span className="text-cyan-400">
                        {trainingData?.training?.current_episode || 0} / {trainingData?.training?.total_episodes || 0}
                      </span>
                    </div>
                    <Progress 
                      value={trainingData?.training?.progress_pct || 0} 
                      className="h-2 bg-slate-700"
                    />
                  </div>
                  <InfoRow 
                    label="Best Sharpe" 
                    value={trainingData?.training?.best_sharpe?.toFixed(4) || 'N/A'} 
                  />
                </>
              )}

              {/* Live Training Chart */}
              {trainingData?.training?.recent_history?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-slate-500 mb-2">Episode Rewards</p>
                  <div className="h-20 flex items-end gap-0.5">
                    {trainingData.training.recent_history.slice(-20).map((h, i) => {
                      const reward = h.episode_reward || 0;
                      const maxReward = Math.max(...trainingData.training.recent_history.map(x => Math.abs(x.episode_reward || 0)), 1);
                      const height = Math.abs(reward) / maxReward * 100;
                      return (
                        <div
                          key={i}
                          className={`flex-1 rounded-t ${reward >= 0 ? 'bg-green-500/60' : 'bg-red-500/60'}`}
                          style={{ height: `${Math.max(height, 5)}%` }}
                          title={`Episode ${h.episode || i}: ${reward.toFixed(4)}`}
                        />
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* MLflow Registry with Promotion */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                📊 Model Registry
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
              <InfoRow 
                label="Experiment" 
                value={trainingData?.registry?.experiment_name || 'N/A'} 
              />
              <InfoRow 
                label="Registered Models" 
                value={trainingData?.registry?.registered_models?.length || 0} 
              />
              
              {/* Model Versions List */}
              {trainingData?.registry?.registered_models?.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs text-slate-500">Model Versions</p>
                  {trainingData.registry.registered_models.slice(0, 3).map((model, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded bg-slate-900/50">
                      <div>
                        <span className="text-xs text-white">v{model.version}</span>
                        <Badge className={`ml-2 text-[10px] ${
                          model.stage === 'Production' ? 'bg-green-500/20 text-green-400' :
                          model.stage === 'Staging' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-slate-700 text-slate-400'
                        }`}>
                          {model.stage || 'None'}
                        </Badge>
                      </div>
                      {model.stage !== 'Production' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 text-[10px] text-cyan-400 hover:text-cyan-300"
                          onClick={async () => {
                            try {
                              await fetch(`${API_URL}/api/tethys-train/registry/promote?model_name=tethys_rainbow_dqn&version=${model.version}&stage=Production`, {
                                method: 'POST'
                              });
                              toast.success(`Model v${model.version} promoted to Production`);
                              fetchData();
                            } catch (e) {
                              toast.error('Failed to promote model');
                            }
                          }}
                        >
                          Promote
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Start Training Button */}
          <Button
            onClick={async () => {
              try {
                await fetch(`${API_URL}/api/tethys-train/start`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ episodes: 50, symbol: 'BTC/USD' })
                });
                toast.success('Training started');
                fetchData();
              } catch (e) {
                toast.error('Failed to start training');
              }
            }}
            disabled={isTraining}
            className="w-full h-12 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50"
          >
            <Brain className="w-5 h-5 mr-2" />
            {isTraining ? 'Training in Progress...' : 'Start Training (50 episodes)'}
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Helper Components
const StatCard = ({ label, value, trend, warning, small }) => (
  <div className={`bg-slate-800/50 rounded-lg p-2 border ${warning ? 'border-red-500/50' : 'border-slate-700'}`}>
    <p className="text-[10px] text-slate-500 uppercase">{label}</p>
    <div className="flex items-center gap-1">
      <span className={`font-mono ${small ? 'text-sm' : 'text-base'} ${
        warning ? 'text-red-400' : 
        trend === 'up' ? 'text-green-400' : 
        trend === 'down' ? 'text-red-400' : 'text-white'
      }`}>
        {value}
      </span>
      {trend === 'up' && <TrendingUp className="w-3 h-3 text-green-400" />}
      {trend === 'down' && <TrendingDown className="w-3 h-3 text-red-400" />}
    </div>
  </div>
);

const ExpandableCard = ({ title, icon, children, expanded, onToggle }) => (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardHeader 
      className="py-3 px-4 cursor-pointer" 
      onClick={onToggle}
    >
      <CardTitle className="text-sm flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon}
          {title}
        </div>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </CardTitle>
    </CardHeader>
    {expanded && (
      <CardContent className="px-4 pb-4 pt-0">
        {children}
      </CardContent>
    )}
  </Card>
);

const InfoRow = ({ label, value }) => (
  <div className="flex justify-between items-center">
    <span className="text-slate-400 text-xs">{label}</span>
    <span className="text-white text-sm font-mono">{value}</span>
  </div>
);

export default TethysDashboard;
