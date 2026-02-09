import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, TrendingUp, TrendingDown, Target, Activity, 
  CheckCircle, XCircle, Clock, Zap, BarChart3, 
  AlertTriangle, Award, RefreshCw, Database, LineChart,
  Gauge, Layers, ArrowUpRight, ArrowDownRight, Shield,
  Play, Pause, Waves, Wifi, WifiOff, ChevronDown, ChevronUp
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const API_URL = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const WS_URL = API_URL?.replace('https://', 'wss://').replace('http://', 'ws://');

// Chart Components
const AccuracyTrendChart = ({ data, title }) => {
  if (!data || data.length === 0) return null;
  
  const maxValue = Math.max(...data.map(d => d.accuracy || 0), 100);
  const minValue = Math.min(...data.map(d => d.accuracy || 0), 0);
  
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-[#A1A1AA]">{title}</h4>
      <div className="flex items-end gap-1 h-32 bg-[#121212] rounded-lg p-3">
        {data.slice(-20).map((item, index) => {
          const height = ((item.accuracy - minValue) / (maxValue - minValue || 1)) * 100;
          const color = item.accuracy >= 70 ? '#00FF94' : item.accuracy >= 50 ? '#FFB800' : '#FF0055';
          return (
            <div
              key={index}
              className="flex-1 flex flex-col items-center justify-end group relative"
            >
              <div
                className="w-full rounded-t transition-all duration-300 hover:opacity-80"
                style={{ height: `${Math.max(height, 5)}%`, backgroundColor: color }}
              />
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black/90 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                {item.accuracy?.toFixed(1)}%
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-[#A1A1AA]">
        <span>Older</span>
        <span>Recent</span>
      </div>
    </div>
  );
};

const ModelComparisonChart = ({ models }) => {
  if (!models || models.length === 0) return null;
  
  return (
    <div className="space-y-3">
      {models.map((model, index) => (
        <div key={model.model || index} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-white font-medium uppercase">{model.model}</span>
            <span className={`font-data ${
              model.accuracy >= 70 ? 'text-[#00FF94]' : 
              model.accuracy >= 50 ? 'text-[#FFB800]' : 'text-[#FF0055]'
            }`}>
              {model.accuracy?.toFixed(1)}%
            </span>
          </div>
          <div className="h-3 bg-[#1F1F1F] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${model.accuracy}%` }}
              transition={{ duration: 0.8, delay: index * 0.1 }}
              className="h-full rounded-full"
              style={{
                backgroundColor: model.accuracy >= 70 ? '#00FF94' : 
                  model.accuracy >= 50 ? '#FFB800' : '#FF0055'
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const AccuracyGauge = ({ value, label }) => {
  const rotation = (value / 100) * 180 - 90;
  const color = value >= 70 ? '#00FF94' : value >= 50 ? '#FFB800' : '#FF0055';
  
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-16 overflow-hidden">
        <div className="absolute inset-0 border-8 border-[#1F1F1F] rounded-t-full" />
        <div 
          className="absolute bottom-0 left-1/2 w-1 h-14 origin-bottom transition-transform duration-700"
          style={{ 
            transform: `translateX(-50%) rotate(${rotation}deg)`,
            backgroundColor: color
          }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#1F1F1F]" />
      </div>
      <div className="text-3xl font-data font-black mt-2" style={{ color }}>
        {value?.toFixed(1)}%
      </div>
      <div className="text-sm text-[#A1A1AA]">{label}</div>
    </div>
  );
};

const AITraining = () => {
  const [activeTab, setActiveTab] = useState('training');
  
  // Training tab state
  const [learningReport, setLearningReport] = useState(null);
  const [indicators, setIndicators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  
  // Learning Loop tab state
  const [loopStatus, setLoopStatus] = useState(null);
  const [loopMetrics, setLoopMetrics] = useState(null);
  const [loopLoading, setLoopLoading] = useState(true);
  
  // Tethys tab state
  const [dashboardData, setDashboardData] = useState(null);
  const [tradingData, setTradingData] = useState(null);
  const [trainingData, setTrainingData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [tethysLoading, setTethysLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // Training tab functions
  const timeoutPromise = (promise, ms = 10000) => {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), ms))
    ]);
  };

  const loadLearningData = async () => {
    try {
      setLoading(true);
      const [reportRes, indicatorsRes] = await Promise.all([
        timeoutPromise(api.get('/learning/report'), 8000).catch(() => ({ data: null })),
        timeoutPromise(api.get('/learning/indicators/performance'), 8000).catch(() => ({ data: { indicators: [] } }))
      ]);

      setLearningReport(reportRes.data);
      setIndicators(indicatorsRes.data?.indicators || []);
    } catch (error) {
      console.error('Error loading learning data:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerTraining = async () => {
    try {
      setTraining(true);
      toast.loading('Training AI with latest data...');
      
      await api.post('/learning/train');
      
      toast.dismiss();
      toast.success('AI training completed! Intelligence enhanced.');
      await loadLearningData();
    } catch (error) {
      toast.dismiss();
      toast.error('Training failed');
    } finally {
      setTraining(false);
    }
  };

  // Learning Loop functions
  const loadLoopData = async () => {
    try {
      setLoopLoading(true);
      const [statusRes, metricsRes] = await Promise.all([
        timeoutPromise(api.get('/learning/loop/status'), 8000).catch(() => ({ data: null })),
        timeoutPromise(api.get('/learning/loop/metrics'), 8000).catch(() => ({ data: null }))
      ]);

      setLoopStatus(statusRes.data);
      setLoopMetrics(metricsRes.data);
    } catch (error) {
      console.error('Error loading loop data:', error);
    } finally {
      setLoopLoading(false);
    }
  };

  const toggleLoop = async () => {
    try {
      const endpoint = loopStatus?.is_running ? '/learning/loop/stop' : '/learning/loop/start';
      await api.post(endpoint);
      toast.success(loopStatus?.is_running ? 'Learning loop stopped' : 'Learning loop started');
      await loadLoopData();
    } catch (error) {
      toast.error('Failed to toggle learning loop');
    }
  };

  // Tethys functions
  const fetchTethysData = useCallback(async () => {
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
      setTethysLoading(false);
    }
  }, []);

  // WebSocket for Tethys
  useEffect(() => {
    if (activeTab !== 'tethys') return;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${WS_URL}/api/tethys-train/ws/progress`);
        
        ws.onopen = () => {
          setWsConnected(true);
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'episode' || data.type === 'status') {
            setTrainingData(prev => ({
              ...prev,
              training: {
                ...prev?.training,
                ...data.data,
                recent_history: data.type === 'episode' 
                  ? [...(prev?.training?.recent_history || []).slice(-19), data.data]
                  : prev?.training?.recent_history
              }
            }));
          }
        };
        
        ws.onclose = () => {
          setWsConnected(false);
          setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = () => {
          setWsConnected(false);
        };
        
        wsRef.current = ws;
      } catch (e) {
        console.log('WebSocket not available');
      }
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [activeTab]);

  // Load data based on active tab
  useEffect(() => {
    if (activeTab === 'training') {
      loadLearningData();
    } else if (activeTab === 'loop') {
      loadLoopData();
    } else if (activeTab === 'tethys') {
      fetchTethysData();
    }
  }, [activeTab, fetchTethysData]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#00FF94';
      case 'initializing': return '#007AFF';
      default: return '#9D00FF';
    }
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
            <Brain size={48} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">AI</span> Training System
          </h1>
          <p className="text-[#A1A1AA]">
            Train, monitor, and optimize AI models for superior trading performance
          </p>
        </div>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-[#1F1F1F]">
          <TabsTrigger value="training" className="data-[state=active]:bg-[#9D00FF]">
            <Brain className="w-4 h-4 mr-2" />
            Training Models
          </TabsTrigger>
          <TabsTrigger value="loop" className="data-[state=active]:bg-[#9D00FF]">
            <RefreshCw className="w-4 h-4 mr-2" />
            Learning Loop
          </TabsTrigger>
          <TabsTrigger value="tethys" className="data-[state=active]:bg-[#9D00FF]">
            <Shield className="w-4 h-4 mr-2" />
            Tethys System
          </TabsTrigger>
        </TabsList>

        {/* Training Tab */}
        <TabsContent value="training" className="space-y-6 mt-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Training Controls */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="text-[#9D00FF]" />
                    Training Controls
                  </CardTitle>
                  <CardDescription>
                    Train AI models with the latest market data
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={triggerTraining}
                    className="w-full bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
                    disabled={training}
                  >
                    {training ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Training in Progress...
                      </>
                    ) : (
                      <>
                        <Zap className="mr-2 h-4 w-4" />
                        Start Training Session
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Learning Report */}
              {learningReport && (
                <>
                  <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                    <CardHeader>
                      <CardTitle>Overall Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <AccuracyGauge 
                          value={learningReport.overall_accuracy || 0} 
                          label="Overall Accuracy" 
                        />
                        <AccuracyGauge 
                          value={learningReport.prediction_confidence || 0} 
                          label="Confidence" 
                        />
                        <AccuracyGauge 
                          value={learningReport.improvement_rate || 0} 
                          label="Improvement" 
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Model Performance */}
                  {learningReport.models && (
                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle>Model Performance Comparison</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ModelComparisonChart models={learningReport.models} />
                      </CardContent>
                    </Card>
                  )}

                  {/* Accuracy Trends */}
                  {learningReport.accuracy_history && (
                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle>Accuracy Trends</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <AccuracyTrendChart 
                          data={learningReport.accuracy_history} 
                          title="Historical Accuracy" 
                        />
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

              {/* Indicators Performance */}
              {indicators.length > 0 && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Top Performing Indicators</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {indicators.slice(0, 10).map((indicator, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                          <span className="font-medium">{indicator.name}</span>
                          <div className="flex items-center gap-4">
                            <Badge variant={indicator.accuracy >= 70 ? "success" : "secondary"}>
                              {indicator.accuracy?.toFixed(1)}% accuracy
                            </Badge>
                            <Badge variant="outline">
                              {indicator.trades} trades
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* Learning Loop Tab */}
        <TabsContent value="loop" className="space-y-6 mt-6">
          {loopLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Loop Status */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <RefreshCw className={`text-[#9D00FF] ${loopStatus?.is_running ? 'animate-spin' : ''}`} />
                    Continuous Learning Loop
                  </CardTitle>
                  <CardDescription>
                    Automatically learn from every trade in real-time
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${loopStatus?.is_running ? 'bg-[#00FF94] animate-pulse' : 'bg-[#FF0055]'}`} />
                      <span className="font-medium">
                        Status: {loopStatus?.is_running ? 'Active' : 'Stopped'}
                      </span>
                    </div>
                    <Button
                      onClick={toggleLoop}
                      variant={loopStatus?.is_running ? "destructive" : "default"}
                      className={loopStatus?.is_running ? '' : 'bg-[#9D00FF] hover:bg-[#8B00E6]'}
                    >
                      {loopStatus?.is_running ? (
                        <>
                          <Pause className="mr-2 h-4 w-4" />
                          Stop Loop
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-4 w-4" />
                          Start Loop
                        </>
                      )}
                    </Button>
                  </div>

                  {loopStatus?.last_update && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Last Update</p>
                        <p className="text-lg font-data font-bold">
                          {new Date(loopStatus.last_update).toLocaleTimeString()}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Cycle Time</p>
                        <p className="text-lg font-data font-bold text-[#9D00FF]">
                          {loopStatus.cycle_time_seconds || 0}s
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Total Cycles</p>
                        <p className="text-lg font-data font-bold text-[#00FF94]">
                          {loopStatus.total_cycles || 0}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Improvements</p>
                        <p className="text-lg font-data font-bold text-[#FFB800]">
                          {loopStatus.improvements || 0}
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Loop Metrics */}
              {loopMetrics && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle className="text-lg">Trades Analyzed</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-data font-black text-[#9D00FF]">
                          {loopMetrics.trades_analyzed || 0}
                        </div>
                        <p className="text-sm text-[#A1A1AA] mt-2">
                          +{loopMetrics.recent_trades || 0} in last hour
                        </p>
                      </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle className="text-lg">Model Updates</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-data font-black text-[#00FF94]">
                          {loopMetrics.model_updates || 0}
                        </div>
                        <p className="text-sm text-[#A1A1AA] mt-2">
                          Last: {loopMetrics.last_update_time || 'N/A'}
                        </p>
                      </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle className="text-lg">Accuracy Gain</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-data font-black text-[#FFB800]">
                          +{loopMetrics.accuracy_improvement || 0}%
                        </div>
                        <p className="text-sm text-[#A1A1AA] mt-2">
                          Since loop started
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Recent Learning Events */}
                  {loopMetrics.recent_events && loopMetrics.recent_events.length > 0 && (
                    <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                      <CardHeader>
                        <CardTitle>Recent Learning Events</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {loopMetrics.recent_events.map((event, index) => (
                            <div key={index} className="flex items-center gap-3 p-3 bg-[#121212] rounded-lg">
                              <Clock className="w-4 h-4 text-[#A1A1AA]" />
                              <div className="flex-1">
                                <p className="text-sm font-medium">{event.description}</p>
                                <p className="text-xs text-[#A1A1AA]">{event.timestamp}</p>
                              </div>
                              <Badge variant={event.type === 'improvement' ? 'success' : 'secondary'}>
                                {event.type}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </>
          )}
        </TabsContent>

        {/* Tethys Tab */}
        <TabsContent value="tethys" className="space-y-6 mt-6">
          {tethysLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
            </div>
          ) : (
            <>
              {/* Tethys Status */}
              <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Shield className="text-[#9D00FF]" />
                      Tethys AI System
                    </div>
                    <div className="flex items-center gap-2">
                      {wsConnected ? (
                        <Badge className="bg-[#00FF94] text-black">
                          <Wifi className="w-3 h-3 mr-1" />
                          Live
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <WifiOff className="w-3 h-3 mr-1" />
                          Offline
                        </Badge>
                      )}
                    </div>
                  </CardTitle>
                  <CardDescription>
                    Advanced reinforcement learning trading system
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboardData && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Status</p>
                        <Badge variant={dashboardData.status === 'active' ? 'success' : 'secondary'}>
                          {dashboardData.status || 'unknown'}
                        </Badge>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Total Trades</p>
                        <p className="text-lg font-data font-bold">
                          {dashboardData.total_trades || 0}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Win Rate</p>
                        <p className="text-lg font-data font-bold text-[#00FF94]">
                          {dashboardData.win_rate?.toFixed(1) || 0}%
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Total P&L</p>
                        <p className={`text-lg font-data font-bold ${
                          (dashboardData.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                        }`}>
                          ${dashboardData.total_pnl?.toFixed(2) || 0}
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Training Progress */}
              {trainingData?.training && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Training Progress</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Episode</p>
                        <p className="text-2xl font-data font-bold text-[#9D00FF]">
                          {trainingData.training.episode || 0}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Reward</p>
                        <p className={`text-2xl font-data font-bold ${
                          (trainingData.training.reward || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                        }`}>
                          {trainingData.training.reward?.toFixed(2) || 0}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Epsilon</p>
                        <p className="text-2xl font-data font-bold text-[#FFB800]">
                          {trainingData.training.epsilon?.toFixed(3) || 0}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-[#A1A1AA]">Loss</p>
                        <p className="text-2xl font-data font-bold">
                          {trainingData.training.loss?.toFixed(4) || 0}
                        </p>
                      </div>
                    </div>

                    {trainingData.training.progress !== undefined && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-[#A1A1AA]">Progress</span>
                          <span className="font-data font-bold">{trainingData.training.progress}%</span>
                        </div>
                        <Progress value={trainingData.training.progress} className="h-2" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Trading Performance */}
              {tradingData && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Trading Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <p className="text-sm text-[#A1A1AA]">Total Profit</p>
                        <p className={`text-3xl font-data font-black ${
                          (tradingData.total_profit || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                        }`}>
                          ${tradingData.total_profit?.toFixed(2) || 0}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-[#A1A1AA]">Active Positions</p>
                        <p className="text-3xl font-data font-black text-[#9D00FF]">
                          {tradingData.active_positions || 0}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-[#A1A1AA]">24h Trades</p>
                        <p className="text-3xl font-data font-black text-[#FFB800]">
                          {tradingData.trades_24h || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Market Sentiment */}
              {marketSentiment && (
                <Card className="bg-gradient-to-br from-[#1F1F1F] to-[#121212] border-[#2A2A2A]">
                  <CardHeader>
                    <CardTitle>Market Sentiment</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-center">
                      <AccuracyGauge 
                        value={marketSentiment.overall_sentiment || 50} 
                        label="Overall Sentiment" 
                      />
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

export default AITraining;
