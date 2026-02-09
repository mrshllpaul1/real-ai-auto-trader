import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { 
  Gem, Radar, Play, Square, RefreshCw, TrendingUp, AlertTriangle, 
  Zap, Target, Activity, Clock, ArrowUpRight, Brain, Cpu, Sparkles,
  Trophy, Layers, Award, ChevronRight, Loader2, History, BarChart3,
  Settings2, CheckCircle, XCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const GemAnalysis = () => {
  const [activeTab, setActiveTab] = useState('scanner');
  
  // Scanner tab state
  const [isRunning, setIsRunning] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [scannerStatus, setScannerStatus] = useState(null);
  const [scannerLoading, setScannerLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastScan, setLastScan] = useState(null);
  
  // Backtester tab state
  const [backtestStatus, setBacktestStatus] = useState(null);
  const [backtestHistory, setBacktestHistory] = useState([]);
  const [backtestLoading, setBacktestLoading] = useState(true);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [backtestSettings, setBacktestSettings] = useState({
    iterations: 10,
    target_accuracy: 60
  });
  
  // ML/DL Comparison tab state
  const [comparison, setComparison] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [scanResults, setScanResults] = useState(null);
  const [mlLoading, setMlLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [mlScanning, setMlScanning] = useState(false);

  // Scanner functions
  const loadScannerStatus = useCallback(async () => {
    try {
      const response = await api.get('/scanner/status');
      setScannerStatus(response.data);
      setIsRunning(response.data.running);
    } catch (error) {
      console.error('Error loading scanner status:', error);
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      const response = await api.get('/scanner/alerts');
      setAlerts(response.data.alerts || []);
      if (response.data.alerts?.length > 0) {
        setLastScan(response.data.alerts[0].scanned_at);
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setScannerLoading(false);
    }
  }, []);

  const startScanner = async () => {
    try {
      toast.loading('Starting scanner...');
      await api.post('/scanner/start', { interval_seconds: 300 });
      toast.dismiss();
      toast.success('Hidden gem scanner started! Scanning every 5 minutes.');
      setIsRunning(true);
      await scanNow();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to start scanner');
    }
  };

  const stopScanner = async () => {
    try {
      await api.post('/scanner/stop');
      toast.success('Scanner stopped');
      setIsRunning(false);
      loadScannerStatus();
    } catch (error) {
      toast.error('Failed to stop scanner');
    }
  };

  const scanNow = async () => {
    try {
      setScanning(true);
      toast.info('Scanning for hidden gems...');
      const response = await api.post('/scanner/scan');
      toast.dismiss();
      
      const newAlerts = response.data.new_alerts || 0;
      if (newAlerts > 0) {
        toast.success(`Found ${newAlerts} potential gem${newAlerts !== 1 ? 's' : ''}!`);
      } else {
        toast.info('No new gems found in this scan');
      }
      
      await loadAlerts();
    } catch (error) {
      toast.dismiss();
      toast.error('Scan failed');
    } finally {
      setScanning(false);
    }
  };

  // Backtester functions
  const loadBacktestData = useCallback(async () => {
    try {
      setBacktestLoading(true);
      const [statusRes, historyRes] = await Promise.all([
        api.get('/gems/backtest/status').catch(() => ({ data: null })),
        api.get('/gems/backtest/history?limit=20').catch(() => ({ data: { history: [] } }))
      ]);

      setBacktestStatus(statusRes.data);
      setBacktestHistory(historyRes.data?.history || []);
      setIsBacktesting(statusRes.data?.is_running || false);
    } catch (error) {
      console.error('Error loading backtest data:', error);
    } finally {
      setBacktestLoading(false);
    }
  }, []);

  const handleStartBacktest = async () => {
    try {
      setIsBacktesting(true);
      toast.info('Starting gem prediction backtest...');
      const response = await api.post('/gems/backtest/start', {
        max_iterations: backtestSettings.iterations,
        target_accuracy: backtestSettings.target_accuracy
      });
      if (response.data.status === 'started') {
        toast.success('Backtest started! This may take several minutes.');
      } else {
        toast.info(response.data.message || 'Backtest initiated');
      }
      loadBacktestData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start backtest');
      setIsBacktesting(false);
    }
  };

  // ML/DL Comparison functions
  const loadMLData = useCallback(async () => {
    try {
      setMlLoading(true);
      const [compRes, infoRes, statusRes] = await Promise.all([
        api.get('/gems/ml-dl/compare').catch(() => ({ data: null })),
        api.get('/gems/ml-dl/model-info').catch(() => ({ data: null })),
        api.get('/gems/ml-dl/status').catch(() => ({ data: null }))
      ]);
      
      setComparison(compRes.data);
      setModelInfo(infoRes.data);
      setTrainingStatus(statusRes.data);
    } catch (error) {
      console.error('Error loading ML/DL data:', error);
    } finally {
      setMlLoading(false);
    }
  }, []);

  const handleTrain = async () => {
    try {
      setTraining(true);
      await api.post('/gems/ml-dl/train', {});
      toast.success('Training started! This may take a few minutes.');
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const res = await api.get('/gems/ml-dl/status');
          setTrainingStatus(res.data);
          
          if (!res.data.running) {
            clearInterval(pollInterval);
            setTraining(false);
            loadMLData();
            toast.success('Training complete!');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setTraining(false);
        }
      }, 5000);
    } catch (error) {
      toast.error('Failed to start training');
      setTraining(false);
    }
  };

  const handleMLScan = async () => {
    try {
      setMlScanning(true);
      toast.info('Scanning with ML/DL models...');
      const response = await api.post('/gems/ml-dl/scan', {});
      setScanResults(response.data);
      toast.success(`Found ${response.data.gems?.length || 0} potential gems!`);
    } catch (error) {
      toast.error('ML/DL scan failed');
    } finally {
      setMlScanning(false);
    }
  };

  const handleViewGemDetails = (symbol) => {
    // Navigate to spot trading page with the selected symbol
    window.location.href = `/spot?symbol=${symbol}`;
    toast.info(`Opening ${symbol} trading view...`);
  };

  // Load data based on active tab
  useEffect(() => {
    if (activeTab === 'scanner') {
      loadScannerStatus();
      loadAlerts();
    } else if (activeTab === 'backtester') {
      loadBacktestData();
    } else if (activeTab === 'comparison') {
      loadMLData();
    }
  }, [activeTab, loadScannerStatus, loadAlerts, loadBacktestData, loadMLData]);

  // Auto-refresh scanner
  useEffect(() => {
    if (activeTab === 'scanner' && autoRefresh) {
      const interval = setInterval(() => {
        loadAlerts();
        loadScannerStatus();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [activeTab, autoRefresh, loadAlerts, loadScannerStatus]);

  // Auto-refresh backtester when running
  useEffect(() => {
    if (activeTab === 'backtester' && isBacktesting) {
      const interval = setInterval(loadBacktestData, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab, isBacktesting, loadBacktestData]);

  // Auto-refresh ML/DL
  useEffect(() => {
    if (activeTab === 'comparison') {
      const interval = setInterval(loadMLData, 30000);
      return () => clearInterval(interval);
    }
  }, [activeTab, loadMLData]);

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 60) return 'text-[#00FF94]';
    if (accuracy >= 40) return 'text-[#FFB800]';
    return 'text-[#FF0055]';
  };

  const getAccuracyBadge = (accuracy) => {
    if (accuracy >= 60) return { color: 'bg-[#00FF94]/20 text-[#00FF94]', label: 'Good' };
    if (accuracy >= 40) return { color: 'bg-[#FFB800]/20 text-[#FFB800]', label: 'Fair' };
    return { color: 'bg-[#FF0055]/20 text-[#FF0055]', label: 'Poor' };
  };

  const getPotentialColor = (potential) => {
    if (potential >= 50) return '#00FF94';
    if (potential >= 25) return '#FFB800';
    return '#FF0055';
  };

  return (
    <div className="p-6 lg:p-12 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2 flex items-center gap-4">
            <Gem size={48} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Gem</span> Analysis
          </h1>
          <p className="text-[#A1A1AA]">
            Discover hidden crypto gems before they explode
          </p>
        </div>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-[#1F1F1F]">
          <TabsTrigger value="scanner" className="data-[state=active]:bg-[#9D00FF]">
            <Radar className="w-4 h-4 mr-2" />
            Scanner
          </TabsTrigger>
          <TabsTrigger value="backtester" className="data-[state=active]:bg-[#9D00FF]">
            <History className="w-4 h-4 mr-2" />
            Backtester
          </TabsTrigger>
          <TabsTrigger value="comparison" className="data-[state=active]:bg-[#9D00FF]">
            <Brain className="w-4 h-4 mr-2" />
            ML/DL Comparison
          </TabsTrigger>
        </TabsList>

        {/* Scanner Tab */}
        <TabsContent value="scanner" className="space-y-6 mt-6">
          {scannerLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Scanner Controls */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Radar className="text-[#9D00FF]" />
                      Scanner Controls
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <Switch
                          id="auto-refresh"
                          checked={autoRefresh}
                          onCheckedChange={setAutoRefresh}
                        />
                        <Label htmlFor="auto-refresh" className="text-sm">Auto Refresh</Label>
                      </div>
                      <Badge variant={isRunning ? "success" : "secondary"}>
                        {isRunning ? 'Running' : 'Stopped'}
                      </Badge>
                    </div>
                  </CardTitle>
                  <CardDescription>
                    {scannerStatus?.next_scan && (
                      <span>Next scan: {new Date(scannerStatus.next_scan).toLocaleTimeString()}</span>
                    )}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-3">
                    {!isRunning ? (
                      <Button
                        onClick={startScanner}
                        className="flex-1 bg-[#9D00FF] hover:bg-[#8B00E6]"
                      >
                        <Play className="mr-2 h-4 w-4" />
                        Start Scanner
                      </Button>
                    ) : (
                      <Button
                        onClick={stopScanner}
                        variant="destructive"
                        className="flex-1"
                      >
                        <Square className="mr-2 h-4 w-4" />
                        Stop Scanner
                      </Button>
                    )}
                    <Button
                      onClick={scanNow}
                      disabled={scanning}
                      variant="outline"
                      className="flex-1"
                    >
                      {scanning ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Scanning...
                        </>
                      ) : (
                        <>
                          <Zap className="mr-2 h-4 w-4" />
                          Scan Now
                        </>
                      )}
                    </Button>
                  </div>

                  {lastScan && (
                    <div className="text-sm text-[#A1A1AA]">
                      Last scan: {new Date(lastScan).toLocaleString()}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Scanner Stats */}
              {scannerStatus && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Total Scans</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-data font-black text-[#9D00FF]">
                        {scannerStatus.total_scans || 0}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Gems Found</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-data font-black text-[#00FF94]">
                        {scannerStatus.total_gems_found || 0}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">High Priority</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-data font-black text-[#FFB800]">
                        {alerts.filter(a => a.confidence >= 80).length}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Success Rate</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-data font-black text-[#00FF94]">
                        {scannerStatus.success_rate?.toFixed(1) || 0}%
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Alerts */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle>Detected Gems ({alerts.length})</CardTitle>
                  <CardDescription>
                    Potential hidden gems detected by the AI scanner
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {alerts.length === 0 ? (
                    <div className="text-center py-12">
                      <Gem className="mx-auto h-12 w-12 text-[#A1A1AA] mb-4" />
                      <p className="text-[#A1A1AA]">No gems detected yet. Start scanning!</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <AnimatePresence>
                        {alerts.slice(0, 20).map((alert, index) => (
                          <motion.div
                            key={alert.symbol || index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 bg-[#121212] rounded-lg border border-[#2A2A2A] hover:border-[#9D00FF] transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <Gem className="text-[#9D00FF]" size={24} />
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-heading font-bold text-lg">{alert.symbol}</span>
                                    <Badge variant={alert.confidence >= 80 ? "success" : "secondary"}>
                                      {alert.confidence}% confidence
                                    </Badge>
                                  </div>
                                  <p className="text-sm text-[#A1A1AA]">{alert.reason}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <div className="text-right">
                                  <div className="text-2xl font-data font-black" style={{ color: getPotentialColor(alert.potential_gain || 0) }}>
                                    +{alert.potential_gain?.toFixed(1) || 0}%
                                  </div>
                                  <div className="text-xs text-[#A1A1AA]">Potential</div>
                                </div>
                                <Button 
                                  size="sm" 
                                  className="bg-[#9D00FF] hover:bg-[#8B00E6]"
                                  onClick={() => handleViewGemDetails(alert.symbol)}
                                  title="View trading details"
                                >
                                  <ArrowUpRight className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Backtester Tab */}
        <TabsContent value="backtester" className="space-y-6 mt-6">
          {backtestLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Backtest Controls */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="text-[#9D00FF]" />
                    Backtest Configuration
                  </CardTitle>
                  <CardDescription>
                    Test gem prediction accuracy against historical data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Iterations</Label>
                      <Input
                        type="number"
                        value={backtestSettings.iterations}
                        onChange={(e) => setBacktestSettings({...backtestSettings, iterations: parseInt(e.target.value)})}
                        min="1"
                        max="100"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Target Accuracy %</Label>
                      <Input
                        type="number"
                        value={backtestSettings.target_accuracy}
                        onChange={(e) => setBacktestSettings({...backtestSettings, target_accuracy: parseInt(e.target.value)})}
                        min="1"
                        max="100"
                      />
                    </div>
                  </div>
                  <Button
                    onClick={handleStartBacktest}
                    disabled={isBacktesting}
                    className="w-full bg-[#9D00FF] hover:bg-[#8B00E6]"
                  >
                    {isBacktesting ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Backtesting in Progress...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Start Backtest
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Current Backtest Status */}
              {backtestStatus && backtestStatus.is_running && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Backtest Progress</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Iteration</p>
                        <p className="text-2xl font-data font-bold text-[#9D00FF]">
                          {backtestStatus.current_iteration}/{backtestStatus.max_iterations}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Accuracy</p>
                        <p className={`text-2xl font-data font-bold ${getAccuracyColor(backtestStatus.current_accuracy)}`}>
                          {backtestStatus.current_accuracy?.toFixed(1) || 0}%
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Status</p>
                        <Badge className="bg-[#00FF94] text-black">Running</Badge>
                      </div>
                    </div>
                    <Progress value={(backtestStatus.current_iteration / backtestStatus.max_iterations) * 100} />
                  </CardContent>
                </Card>
              )}

              {/* Backtest History */}
              {backtestHistory.length > 0 && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Backtest History</CardTitle>
                    <CardDescription>Previous backtest results</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {backtestHistory.map((test, index) => {
                        const badge = getAccuracyBadge(test.accuracy);
                        return (
                          <div key={index} className="p-4 bg-[#121212] rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                {test.accuracy >= 60 ? (
                                  <CheckCircle className="text-[#00FF94]" />
                                ) : (
                                  <XCircle className="text-[#FF0055]" />
                                )}
                                <div>
                                  <div className="font-medium">
                                    {new Date(test.completed_at).toLocaleDateString()}
                                  </div>
                                  <div className="text-sm text-[#A1A1AA]">
                                    {test.iterations} iterations • {test.trades_tested} trades
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <Badge className={badge.color}>
                                  {badge.label}
                                </Badge>
                                <div className={`text-2xl font-data font-bold ${getAccuracyColor(test.accuracy)}`}>
                                  {test.accuracy?.toFixed(1)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* ML/DL Comparison Tab */}
        <TabsContent value="comparison" className="space-y-6 mt-6">
          {mlLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Model Controls */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="text-[#9D00FF]" />
                    Model Controls
                  </CardTitle>
                  <CardDescription>
                    Train and compare ML vs DL model performance
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-3">
                    <Button
                      onClick={handleTrain}
                      disabled={training}
                      className="flex-1 bg-[#9D00FF] hover:bg-[#8B00E6]"
                    >
                      {training ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Training Models...
                        </>
                      ) : (
                        <>
                          <Zap className="mr-2 h-4 w-4" />
                          Train Both Models
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleMLScan}
                      disabled={mlScanning}
                      variant="outline"
                      className="flex-1"
                    >
                      {mlScanning ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          Scanning...
                        </>
                      ) : (
                        <>
                          <Radar className="mr-2 h-4 w-4" />
                          Scan with Models
                        </>
                      )}
                    </Button>
                  </div>

                  {trainingStatus?.running && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-[#A1A1AA]">Training Progress</span>
                        <span className="font-data">{trainingStatus.progress || 0}%</span>
                      </div>
                      <Progress value={trainingStatus.progress || 0} />
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Model Comparison */}
              {comparison && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Model Performance Comparison</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* ML Model */}
                      <div className="space-y-4 p-4 bg-[#121212] rounded-lg">
                        <div className="flex items-center gap-3">
                          <Cpu className="text-[#00FF94]" size={32} />
                          <div>
                            <h3 className="text-xl font-heading font-bold">Machine Learning</h3>
                            <p className="text-sm text-[#A1A1AA]">Random Forest</p>
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Accuracy</span>
                            <span className={`font-data font-bold ${getAccuracyColor(comparison.ml_accuracy)}`}>
                              {comparison.ml_accuracy?.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Precision</span>
                            <span className="font-data font-bold">{comparison.ml_precision?.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Recall</span>
                            <span className="font-data font-bold">{comparison.ml_recall?.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">F1 Score</span>
                            <span className="font-data font-bold">{comparison.ml_f1?.toFixed(3)}</span>
                          </div>
                        </div>
                      </div>

                      {/* DL Model */}
                      <div className="space-y-4 p-4 bg-[#121212] rounded-lg">
                        <div className="flex items-center gap-3">
                          <Brain className="text-[#9D00FF]" size={32} />
                          <div>
                            <h3 className="text-xl font-heading font-bold">Deep Learning</h3>
                            <p className="text-sm text-[#A1A1AA]">Neural Network</p>
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Accuracy</span>
                            <span className={`font-data font-bold ${getAccuracyColor(comparison.dl_accuracy)}`}>
                              {comparison.dl_accuracy?.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Precision</span>
                            <span className="font-data font-bold">{comparison.dl_precision?.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">Recall</span>
                            <span className="font-data font-bold">{comparison.dl_recall?.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-[#A1A1AA]">F1 Score</span>
                            <span className="font-data font-bold">{comparison.dl_f1?.toFixed(3)}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Winner */}
                    {comparison.winner && (
                      <div className="mt-6 p-4 bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 rounded-lg border border-[#9D00FF]">
                        <div className="flex items-center justify-center gap-3">
                          <Trophy className="text-[#FFB800]" size={32} />
                          <div className="text-center">
                            <div className="text-sm text-[#A1A1AA]">Best Performer</div>
                            <div className="text-2xl font-heading font-bold">
                              {comparison.winner === 'ml' ? 'Machine Learning' : 'Deep Learning'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Scan Results */}
              {scanResults && scanResults.gems && scanResults.gems.length > 0 && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>ML/DL Scan Results</CardTitle>
                    <CardDescription>Gems detected by both models</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {scanResults.gems.slice(0, 10).map((gem, index) => (
                        <div key={index} className="p-4 bg-[#121212] rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <Gem className="text-[#9D00FF]" />
                              <div>
                                <div className="font-heading font-bold">{gem.symbol}</div>
                                <div className="text-sm text-[#A1A1AA]">
                                  ML: {gem.ml_score?.toFixed(1)} | DL: {gem.dl_score?.toFixed(1)}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl font-data font-black text-[#00FF94]">
                                {gem.combined_score?.toFixed(1)}
                              </div>
                              <div className="text-xs text-[#A1A1AA]">Combined Score</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Model Info */}
              {modelInfo && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Model Information</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <h4 className="font-medium">ML Model</h4>
                        <div className="text-sm text-[#A1A1AA]">
                          <p>Last trained: {modelInfo.ml_last_trained ? new Date(modelInfo.ml_last_trained).toLocaleDateString() : 'Never'}</p>
                          <p>Training samples: {modelInfo.ml_samples || 0}</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <h4 className="font-medium">DL Model</h4>
                        <div className="text-sm text-[#A1A1AA]">
                          <p>Last trained: {modelInfo.dl_last_trained ? new Date(modelInfo.dl_last_trained).toLocaleDateString() : 'Never'}</p>
                          <p>Training samples: {modelInfo.dl_samples || 0}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GemAnalysis;
