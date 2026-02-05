import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { 
  Brain, Activity, TrendingUp, TrendingDown, Clock, 
  Play, Pause, RefreshCw, Shield, Zap, Target,
  CheckCircle, XCircle, AlertTriangle, BarChart3
} from 'lucide-react';
import api from '../services/api';

const SRDDQNDashboard = () => {
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [tradingStatus, setTradingStatus] = useState(null);
  const [lastSignal, setLastSignal] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [pipeline, trading, perf] = await Promise.all([
        api.get('/srddqn-pipeline/status').catch(() => ({ data: null })),
        api.get('/srddqn-trading/status').catch(() => ({ data: null })),
        api.get('/srddqn-trading/performance').catch(() => ({ data: null }))
      ]);
      
      setPipelineStatus(pipeline.data);
      setTradingStatus(trading.data);
      setPerformance(perf.data);
      
      if (trading.data?.last_signal) {
        setLastSignal(trading.data.last_signal);
      }
    } catch (error) {
      console.error('Error fetching SRDDQN data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleGenerateSignal = async () => {
    setGenerating(true);
    try {
      const response = await api.post('/srddqn-trading/signal', { symbol: 'BTC' });
      setLastSignal(response.data);
    } catch (error) {
      console.error('Error generating signal:', error);
    } finally {
      setGenerating(false);
    }
  };

  const handleStartTraining = async () => {
    try {
      await api.post('/srddqn-pipeline/run-all', {
        phase_1_epochs: 10,
        phase_2_episodes: 50,
        phase_3_test_episodes: 5
      });
      fetchData();
    } catch (error) {
      console.error('Error starting training:', error);
    }
  };

  const handleRunBacktest = async () => {
    try {
      await api.post('/srddqn-trading/backtest');
      fetchData();
    } catch (error) {
      console.error('Error running backtest:', error);
    }
  };

  const getPhaseColor = (phase) => {
    if (phase >= 6) return 'text-green-400';
    if (phase >= 3) return 'text-yellow-400';
    if (phase >= 1) return 'text-cyan-400';
    return 'text-gray-400';
  };

  const getSignalColor = (signal) => {
    if (signal === 'strong_buy' || signal === 'buy') return 'text-green-400';
    if (signal === 'strong_sell' || signal === 'sell') return 'text-red-400';
    return 'text-gray-400';
  };

  const getSignalIcon = (signal) => {
    if (signal === 'strong_buy' || signal === 'buy') return <TrendingUp className="w-6 h-6" />;
    if (signal === 'strong_sell' || signal === 'sell') return <TrendingDown className="w-6 h-6" />;
    return <Activity className="w-6 h-6" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="srddqn-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-400" />
            SRDDQN Trading Agent
          </h2>
          <p className="text-gray-400 mt-1">Self-Rewarding Double Deep Q-Network</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={fetchData} 
            variant="outline" 
            className="border-gray-700"
            data-testid="refresh-btn"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Pipeline Status */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Training Phase</p>
                <p className={`text-3xl font-bold ${getPhaseColor(pipelineStatus?.current_phase || 0)}`}>
                  {pipelineStatus?.current_phase || 0}/6
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                pipelineStatus?.training_complete ? 'bg-green-500/20' : 'bg-cyan-500/20'
              }`}>
                {pipelineStatus?.training_complete ? (
                  <CheckCircle className="w-6 h-6 text-green-400" />
                ) : (
                  <Clock className="w-6 h-6 text-cyan-400" />
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {pipelineStatus?.training_complete ? 'Training Complete' : 'Training in Progress...'}
            </p>
          </CardContent>
        </Card>

        {/* Trading Status */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Trading Status</p>
                <p className={`text-xl font-bold ${tradingStatus?.is_active ? 'text-green-400' : 'text-yellow-400'}`}>
                  {tradingStatus?.is_active ? 'Active' : 'Standby'}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                tradingStatus?.is_active ? 'bg-green-500/20' : 'bg-yellow-500/20'
              }`}>
                {tradingStatus?.is_active ? (
                  <Play className="w-6 h-6 text-green-400" />
                ) : (
                  <Pause className="w-6 h-6 text-yellow-400" />
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {tradingStatus?.total_trades || 0} trades executed
            </p>
          </CardContent>
        </Card>

        {/* Backtest Status */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Backtest Status</p>
                <p className={`text-xl font-bold ${
                  tradingStatus?.backtest_passed ? 'text-green-400' : 'text-red-400'
                }`}>
                  {tradingStatus?.backtest_passed ? 'Passed' : 'Pending'}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                tradingStatus?.backtest_passed ? 'bg-green-500/20' : 'bg-red-500/20'
              }`}>
                {tradingStatus?.backtest_passed ? (
                  <CheckCircle className="w-6 h-6 text-green-400" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Sharpe threshold: {tradingStatus?.min_sharpe_threshold || 0.5}
            </p>
          </CardContent>
        </Card>

        {/* Performance */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Avg Sharpe Ratio</p>
                <p className={`text-2xl font-bold ${
                  (performance?.avg_sharpe_ratio || 0) > 0.5 ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {(performance?.avg_sharpe_ratio || 0).toFixed(2)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              From {performance?.backtest_count || 0} backtests
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Signal Generation */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              Signal Generation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button 
                onClick={handleGenerateSignal}
                disabled={generating || !pipelineStatus?.current_phase}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                data-testid="generate-signal-btn"
              >
                {generating ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4 mr-2" />
                )}
                Generate Signal
              </Button>

              {lastSignal && (
                <div className="p-4 bg-[#1a1a2e] rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-400">Latest Signal</span>
                    <span className={`flex items-center gap-2 font-bold ${getSignalColor(lastSignal.signal)}`}>
                      {getSignalIcon(lastSignal.signal)}
                      {lastSignal.signal?.toUpperCase()}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Confidence</p>
                      <p className="text-white">{((lastSignal.confidence || 0) * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Position</p>
                      <p className="text-white">{((lastSignal.position || 0) * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Symbol</p>
                      <p className="text-white">{lastSignal.symbol || 'BTC'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Sentiment Adj.</p>
                      <p className="text-white">{((lastSignal.sentiment_adjustment || 0) * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Training Controls */}
        <Card className="bg-[#12121A] border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-400" />
              Training & Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Phase Progress */}
              <div className="p-4 bg-[#1a1a2e] rounded-lg">
                <p className="text-gray-400 text-sm mb-3">6-Phase Pipeline Progress</p>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5, 6].map((phase) => (
                    <div
                      key={phase}
                      className={`flex-1 h-2 rounded ${
                        phase <= (pipelineStatus?.current_phase || 0)
                          ? 'bg-gradient-to-r from-cyan-500 to-purple-500'
                          : 'bg-gray-700'
                      }`}
                    />
                  ))}
                </div>
                <div className="flex justify-between mt-2 text-xs text-gray-500">
                  <span>Reward</span>
                  <span>RL</span>
                  <span>Valid</span>
                  <span>Deploy</span>
                  <span>Adv</span>
                  <span>XAI</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Button 
                  onClick={handleStartTraining}
                  variant="outline"
                  className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10"
                  data-testid="start-training-btn"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Training
                </Button>
                <Button 
                  onClick={handleRunBacktest}
                  variant="outline"
                  className="border-purple-500/50 text-purple-400 hover:bg-purple-500/10"
                  data-testid="run-backtest-btn"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Run Backtest
                </Button>
              </div>

              {/* Reward Components */}
              <div className="p-4 bg-[#1a1a2e] rounded-lg">
                <p className="text-gray-400 text-sm mb-3">Reward Components</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Sharpe Ratio</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-700 rounded overflow-hidden">
                        <div className="h-full bg-cyan-500" style={{ width: '50%' }} />
                      </div>
                      <span className="text-cyan-400 text-sm">50%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Self-Reward</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-700 rounded overflow-hidden">
                        <div className="h-full bg-purple-500" style={{ width: '30%' }} />
                      </div>
                      <span className="text-purple-400 text-sm">30%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Curiosity</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-700 rounded overflow-hidden">
                        <div className="h-full bg-pink-500" style={{ width: '20%' }} />
                      </div>
                      <span className="text-pink-400 text-sm">20%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Safety Guards */}
      <Card className="bg-[#12121A] border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-400" />
            Safety Guards & Risk Limits
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-3 bg-[#1a1a2e] rounded-lg text-center">
              <p className="text-gray-400 text-xs">Max Position</p>
              <p className="text-white font-bold text-lg">25%</p>
            </div>
            <div className="p-3 bg-[#1a1a2e] rounded-lg text-center">
              <p className="text-gray-400 text-xs">Daily Loss Limit</p>
              <p className="text-red-400 font-bold text-lg">5%</p>
            </div>
            <div className="p-3 bg-[#1a1a2e] rounded-lg text-center">
              <p className="text-gray-400 text-xs">Max Drawdown</p>
              <p className="text-red-400 font-bold text-lg">15%</p>
            </div>
            <div className="p-3 bg-[#1a1a2e] rounded-lg text-center">
              <p className="text-gray-400 text-xs">Volatility Limit</p>
              <p className="text-yellow-400 font-bold text-lg">5%</p>
            </div>
            <div className="p-3 bg-[#1a1a2e] rounded-lg text-center">
              <p className="text-gray-400 text-xs">Sentiment Weight</p>
              <p className="text-purple-400 font-bold text-lg">{((tradingStatus?.sentiment_weight || 0.2) * 100).toFixed(0)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SRDDQNDashboard;
