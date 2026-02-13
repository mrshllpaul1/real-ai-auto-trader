import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { 
  Gem, Play, RefreshCw, History, TrendingUp, Target,
  Zap, Clock, CheckCircle, XCircle, BarChart3, Settings2,
  AlertTriangle, Award
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const GemBacktester = ({ embedded = false }) => {
  const [status, setStatus] = useState(null);
  const [backtestHistory, setBacktestHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [settings, setSettings] = useState({
    iterations: 10,
    target_accuracy: 60
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, historyRes] = await Promise.all([
        api.get('/gems/backtest/status').catch(() => ({ data: null })),
        api.get('/gems/backtest/history?limit=20').catch(() => ({ data: { history: [] } }))
      ]);

      setStatus(statusRes.data);
      setBacktestHistory(historyRes.data?.history || []);
      setIsRunning(statusRes.data?.is_running || false);
    } catch (error) {
      console.error('Error loading backtest data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s when running
    return () => clearInterval(interval);
  }, [loadData]);

  const handleStartBacktest = async () => {
    try {
      setIsRunning(true);
      toast.info('Starting gem prediction backtest...');
      const response = await api.post('/gems/backtest/start', {
        max_iterations: settings.iterations,
        target_accuracy: settings.target_accuracy
      });
      if (response.data.status === 'started') {
        toast.success('Backtest started! This may take several minutes.');
      } else {
        toast.info(response.data.message || 'Backtest initiated');
      }
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start backtest');
      setIsRunning(false);
    }
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 60) return 'text-[#00FF94]';
    if (accuracy >= 40) return 'text-[#FFB800]';
    return 'text-[#FF0055]';
  };

  const getAccuracyBadge = (accuracy) => {
    if (accuracy >= 60) return { color: 'bg-[#00FF94]/20 text-[#00FF94]', label: 'Good' };
    if (accuracy >= 40) return { color: 'bg-[#FFB800]/20 text-[#FFB800]', label: 'Fair' };
    return { color: 'bg-[#FF0055]/20 text-[#FF0055]', label: 'Improving' };
  };

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="gem-backtester-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Gem size={40} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Gem</span> Backtester
          </h1>
          <p className="text-[#A1A1AA]">
            Iteratively improve hidden gem prediction accuracy using historical data
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleStartBacktest}
            disabled={isRunning}
            className={`${isRunning ? 'bg-[#1F1F1F]' : 'bg-[#9D00FF] hover:bg-[#9D00FF]/80'}`}
            data-testid="start-backtest-btn"
          >
            {isRunning ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-white mr-2" />
                Running...
              </>
            ) : (
              <>
                <Play size={16} className="mr-2" />
                Start Backtest
              </>
            )}
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
      </motion.div>

      {/* Status Cards */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="current-accuracy-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Target size={20} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Current Accuracy</span>
            </div>
            <div className={`text-3xl font-data font-bold ${getAccuracyColor(status?.current_accuracy || 0)}`}>
              {(status?.current_accuracy || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="best-accuracy-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Award size={20} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Best Accuracy</span>
            </div>
            <div className={`text-3xl font-data font-bold ${getAccuracyColor(status?.best_accuracy || 0)}`}>
              {(status?.best_accuracy || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="iterations-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <RefreshCw size={20} className="text-[#007AFF]" />
              <span className="text-sm text-[#A1A1AA]">Total Iterations</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#007AFF]">
              {status?.total_iterations || 0}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="status-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Zap size={20} className={isRunning ? 'text-[#FFB800]' : 'text-[#A1A1AA]'} />
              <span className="text-sm text-[#A1A1AA]">Status</span>
            </div>
            <Badge className={isRunning ? 'bg-[#FFB800]/20 text-[#FFB800]' : 'bg-[#00FF94]/20 text-[#00FF94]'}>
              {isRunning ? 'Running' : 'Ready'}
            </Badge>
          </CardContent>
        </Card>
      </motion.div>

      {/* Progress Bar (when running) */}
      {isRunning && status?.progress && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Card className="bg-[#0A0A0A] border-[#FFB800]/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-medium">Backtest Progress</span>
                <span className="text-[#FFB800]">{status.progress.current_iteration}/{status.progress.total_iterations}</span>
              </div>
              <Progress value={(status.progress.current_iteration / status.progress.total_iterations) * 100} className="h-2" />
              <p className="text-sm text-[#A1A1AA] mt-2">
                Current accuracy: {(status.progress.current_accuracy || 0).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="overview" className="data-[state=active]:bg-[#9D00FF]">
            Overview
          </TabsTrigger>
          <TabsTrigger value="settings" className="data-[state=active]:bg-[#9D00FF]">
            Settings
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-[#9D00FF]">
            History ({backtestHistory.length})
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Current Weights */}
          {status?.current_weights && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="weights-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <BarChart3 className="text-[#9D00FF]" />
                    Current Prediction Weights
                  </CardTitle>
                  <CardDescription>Optimized weights from backtesting</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(status.current_weights).map(([factor, weight]) => (
                      <div key={factor} className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-[#A1A1AA] capitalize">
                            {factor.replace(/_/g, ' ')}
                          </span>
                          <span className="text-lg font-bold text-white">{(weight * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={weight * 100} className="h-1.5" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* How It Works */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>How Gem Backtesting Works</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#9D00FF]">
                    <div className="font-bold text-white mb-2">1. Load Historical Data</div>
                    <p className="text-sm text-[#A1A1AA]">Uses 282,000+ OHLCV records for 72+ coins dating back 10+ years.</p>
                  </div>
                  <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#007AFF]">
                    <div className="font-bold text-white mb-2">2. Test Predictions</div>
                    <p className="text-sm text-[#A1A1AA]">Makes gem predictions at 30%, 50%, 70% points in historical timeline.</p>
                  </div>
                  <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#00FF94]">
                    <div className="font-bold text-white mb-2">3. Verify Outcomes</div>
                    <p className="text-sm text-[#A1A1AA]">Compares predictions to actual 30-day gains (20%+ = gem hit).</p>
                  </div>
                  <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#FFB800]">
                    <div className="font-bold text-white mb-2">4. Adjust Weights</div>
                    <p className="text-sm text-[#A1A1AA]">Modifies prediction weights to reduce false positives/negatives.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Latest Result */}
          {status?.latest_result && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="latest-result-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <History className="text-[#007AFF]" />
                    Latest Backtest Result
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <p className="text-xs text-[#A1A1AA] mb-1">Accuracy</p>
                      <p className={`text-2xl font-bold ${getAccuracyColor(status.latest_result.accuracy)}`}>
                        {(status.latest_result.accuracy || 0).toFixed(1)}%
                      </p>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <p className="text-xs text-[#A1A1AA] mb-1">True Positives</p>
                      <p className="text-2xl font-bold text-[#00FF94]">
                        {status.latest_result.true_positives || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <p className="text-xs text-[#A1A1AA] mb-1">False Positives</p>
                      <p className="text-2xl font-bold text-[#FF0055]">
                        {status.latest_result.false_positives || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <p className="text-xs text-[#A1A1AA] mb-1">True Negatives</p>
                      <p className="text-2xl font-bold text-[#00FF94]">
                        {status.latest_result.true_negatives || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <p className="text-xs text-[#A1A1AA] mb-1">False Negatives</p>
                      <p className="text-2xl font-bold text-[#FF0055]">
                        {status.latest_result.false_negatives || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-6">
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Settings2 className="text-[#9D00FF]" />
                  Backtest Settings
                </CardTitle>
                <CardDescription>Configure backtest parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Max Iterations</label>
                    <Input
                      type="number"
                      min="1"
                      max="100"
                      value={settings.iterations}
                      onChange={(e) => setSettings({ ...settings, iterations: parseInt(e.target.value) || 10 })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                    <p className="text-xs text-[#A1A1AA] mt-1">Number of optimization iterations (1-100)</p>
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Target Accuracy (%)</label>
                    <Input
                      type="number"
                      min="30"
                      max="90"
                      value={settings.target_accuracy}
                      onChange={(e) => setSettings({ ...settings, target_accuracy: parseInt(e.target.value) || 60 })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                    <p className="text-xs text-[#A1A1AA] mt-1">Stop when this accuracy is reached (30-90%)</p>
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <h4 className="font-bold text-white mb-2">Estimated Time</h4>
                  <p className="text-sm text-[#A1A1AA]">
                    ~{settings.iterations * 2} minutes ({settings.iterations} iterations × ~2 min each)
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
            <Card className="bg-[#FFB800]/10 border-[#FFB800]/30">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="text-[#FFB800] flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-[#FFB800] mb-1">Resource Usage</h4>
                    <p className="text-sm text-[#A1A1AA]">
                      Backtesting is CPU-intensive and runs in the background. The app remains responsive during backtesting.
                      Progress is saved after each iteration, so you can safely navigate away.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {backtestHistory.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <History size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
                <p className="text-[#A1A1AA]">No backtest history yet. Run a backtest to start.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {backtestHistory.map((run, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`history-${index}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${run.accuracy >= 50 ? 'bg-[#00FF94]/20' : 'bg-[#FF0055]/20'}`}>
                            {run.accuracy >= 50 ? (
                              <CheckCircle size={20} className="text-[#00FF94]" />
                            ) : (
                              <XCircle size={20} className="text-[#FF0055]" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-bold text-white">Iteration #{run.iteration || index + 1}</h4>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge className={getAccuracyBadge(run.accuracy).color}>
                                {(run.accuracy || 0).toFixed(1)}% accuracy
                              </Badge>
                              <span className="text-xs text-[#A1A1AA]">
                                TP: {run.true_positives || 0} | FP: {run.false_positives || 0}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-[#A1A1AA]">
                            <Clock size={12} className="inline mr-1" />
                            {new Date(run.timestamp).toLocaleString()}
                          </p>
                          {run.weight_changes && (
                            <p className="text-xs text-[#9D00FF] mt-1">
                              {Object.keys(run.weight_changes).length} weights adjusted
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GemBacktester;
