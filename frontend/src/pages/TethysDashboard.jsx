import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Activity, Brain, Shield, TrendingUp, TrendingDown, 
  AlertTriangle, Play, Pause, BarChart3, Zap, 
  RefreshCw, ChevronDown, ChevronUp, Waves
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

// Mobile-optimized Tethys Dashboard for Galaxy S22 (1080x2340)
const TethysDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [tradingData, setTradingData] = useState(null);
  const [trainingData, setTrainingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [dashboard, trading, training] = await Promise.all([
        fetch(`${API_URL}/api/tethys/dashboard`).then(r => r.json()),
        fetch(`${API_URL}/api/tethys-trading/dashboard`).then(r => r.json()),
        fetch(`${API_URL}/api/tethys-train/dashboard`).then(r => r.json())
      ]);
      
      setDashboardData(dashboard);
      setTradingData(trading);
      setTrainingData(training);
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
      toast.success('Trading loop started');
      fetchData();
    } catch (error) {
      toast.error('Failed to start trading');
    }
  };

  const stopTrading = async () => {
    try {
      await fetch(`${API_URL}/api/tethys-trading/stop`, { method: 'POST' });
      toast.success('Trading stopped');
      fetchData();
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
