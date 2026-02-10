import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, TrendingUp, TrendingDown, RefreshCw, Activity, Minus,
  Gauge, Target, Shield, Percent, BarChart3, Zap, Clock, Award,
  Cpu, GitBranch, Trophy, Calendar, AlertTriangle, Wallet, ArrowRightLeft,
  Eye, Play, Pause, Settings, ChevronRight, Flame, Snowflake, Waves,
  LineChart, PieChart
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const regimeColors = {
  bull: '#00FF94',
  bear: '#FF0055',
  sideways: '#FFB800',
  high_volatility: '#FF6B00',
  low_volatility: '#00B4FF',
  recovery: '#9D00FF',
  distribution: '#FF00FF',
  unknown: '#A1A1AA'
};

const regimeIcons = {
  bull: TrendingUp,
  bear: TrendingDown,
  sideways: Minus,
  high_volatility: Flame,
  low_volatility: Snowflake,
  recovery: TrendingUp,
  distribution: TrendingDown,
  unknown: Activity
};

const regimeDescriptions = {
  bull: 'Strong uptrend with momentum - aggressive long positions recommended',
  bear: 'Downtrend detected - defensive positioning and short opportunities',
  sideways: 'Range-bound market - oscillator strategies and grid trading',
  high_volatility: 'High volatility - wider stops and reduced position sizes',
  low_volatility: 'Low volatility compression - breakout anticipation',
  recovery: 'Transitioning from bear to bull - accumulation phase',
  distribution: 'Transitioning from bull to bear - take profits'
};

const impactColors = {
  positive: '#00FF94',
  negative: '#FF0055',
  mixed: '#FFB800'
};

const AdaptiveStrategy = () => {
  const [activeTab, setActiveTab] = useState('regime');
  const [strategyStatus, setStrategyStatus] = useState(null);
  const [currentRegime, setCurrentRegime] = useState(null);
  const [regimeVariants, setRegimeVariants] = useState({});
  const [predictedEvents, setPredictedEvents] = useState([]);
  const [optimalStrategy, setOptimalStrategy] = useState(null);
  const [onChainData, setOnChainData] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [loading, setLoading] = useState(true);
  const [autoAdjusting, setAutoAdjusting] = useState(false);
  const [coverageStats, setCoverageStats] = useState(null);
  const [eventFilter, setEventFilter] = useState('all');
  const [probabilityFilter, setProbabilityFilter] = useState(0);
  const [eventCalendar, setEventCalendar] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [
        statusRes,
        regimeRes,
        variantsRes,
        eventsRes,
        optimalRes,
        onChainRes,
        coverageRes,
        calendarRes
      ] = await Promise.all([
        api.get('/adaptive-strategy/status').catch(() => ({ data: null })),
        api.get('/adaptive-strategy/regime/current').catch(() => ({ data: null })),
        api.get('/adaptive-strategy/variants').catch(() => ({ data: { variants_by_regime: {} } })),
        api.get('/adaptive-strategy/predicted-events?min_probability=0.3').catch(() => ({ data: { events: [] } })),
        api.get('/adaptive-strategy/optimal-strategy').catch(() => ({ data: null })),
        api.get('/on-chain/whale-activity').catch(() => ({ data: null })),
        api.get('/adaptive-strategy/event-coverage-stats').catch(() => ({ data: null })),
        api.get('/adaptive-strategy/event-calendar?days_ahead=90').catch(() => ({ data: null }))
      ]);
      
      setStrategyStatus(statusRes.data);
      setCurrentRegime(regimeRes.data?.regime);
      setRegimeVariants(variantsRes.data?.variants_by_regime || {});
      setPredictedEvents(eventsRes.data?.events || []);
      setOptimalStrategy(optimalRes.data);
      setOnChainData(onChainRes.data);
      setIsMonitoring(statusRes.data?.is_monitoring || false);
      setCoverageStats(coverageRes.data);
      setEventCalendar(calendarRes.data);
      
    } catch (error) {
      console.error('Error loading adaptive strategy:', error);
      toast.error('Failed to load adaptive strategy data');
    } finally {
      setLoading(false);
    }
  }, []);

  const initializeVariants = async () => {
    try {
      await api.post('/adaptive-strategy/variants/initialize');
      toast.success('Regime variants initialized');
      loadData();
    } catch (error) {
      toast.error('Failed to initialize variants');
    }
  };

  const autoAdjustParams = async () => {
    try {
      setAutoAdjusting(true);
      const res = await api.post('/adaptive-strategy/auto-adjust');
      toast.success(`Parameters adjusted for ${res.data?.current_regime || 'current'} regime`);
      loadData();
    } catch (error) {
      toast.error('Failed to auto-adjust parameters');
    } finally {
      setAutoAdjusting(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (isMonitoring) {
        await api.post('/adaptive-strategy/monitoring/stop');
        toast.info('Adaptive monitoring stopped');
      } else {
        await api.post('/adaptive-strategy/monitoring/start');
        toast.success('Adaptive monitoring started');
      }
      setIsMonitoring(!isMonitoring);
    } catch (error) {
      toast.error('Failed to toggle monitoring');
    }
  };

  const predictEvents = async () => {
    try {
      const res = await api.post('/adaptive-strategy/predict-events', { days_ahead: 60 });
      setPredictedEvents(res.data?.events || []);
      toast.success(`Predicted ${res.data?.total_events || 0} events (${res.data?.high_probability_events || 0} high confidence)`);
      // Also refresh coverage stats
      const coverageRes = await api.get('/adaptive-strategy/event-coverage-stats').catch(() => ({ data: null }));
      setCoverageStats(coverageRes.data);
      const calendarRes = await api.get('/adaptive-strategy/event-calendar?days_ahead=90').catch(() => ({ data: null }));
      setEventCalendar(calendarRes.data);
    } catch (error) {
      toast.error('Failed to predict events');
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Adaptive Strategy...</p>
        </div>
      </div>
    );
  }

  const regime = currentRegime?.regime || optimalStrategy?.current_regime?.regime || 'unknown';
  const RegimeIcon = regimeIcons[regime] || Activity;
  const regimeColor = regimeColors[regime] || '#A1A1AA';
  const indicators = currentRegime?.indicators || optimalStrategy?.current_regime?.indicators || {};
  const recommendedStrategy = optimalStrategy?.recommended_strategy || {};

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="adaptive-strategy-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Brain size={40} className="text-[#9D00FF]" />
            <span className="text-white">Adaptive</span>
            <span className="text-[#9D00FF]">Strategy</span>
          </h1>
          <p className="text-[#A1A1AA]">
            ML-powered market regime detection, dynamic parameters & event prediction
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={toggleMonitoring}
            variant={isMonitoring ? "destructive" : "default"}
            className={isMonitoring ? "bg-[#FF0055]" : "bg-[#9D00FF]"}
          >
            {isMonitoring ? <Pause size={16} className="mr-2" /> : <Play size={16} className="mr-2" />}
            {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
          </Button>
          <Button
            onClick={loadData}
            variant="outline"
            className="border-[#1F1F1F]"
          >
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </Button>
        </div>
      </motion.div>

      {/* Current Regime Banner */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card 
          className="border-2"
          style={{ 
            backgroundColor: `${regimeColor}10`,
            borderColor: `${regimeColor}50`
          }}
        >
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div 
                  className="w-20 h-20 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: `${regimeColor}20` }}
                >
                  <RegimeIcon size={40} style={{ color: regimeColor }} />
                </div>
                <div>
                  <p className="text-[#A1A1AA] text-sm">Current Market Regime</p>
                  <h2 className="text-4xl font-bold capitalize" style={{ color: regimeColor }}>
                    {regime.replace('_', ' ')}
                  </h2>
                  <p className="text-sm text-[#A1A1AA] mt-1 max-w-md">
                    {regimeDescriptions[regime] || 'Analyzing market conditions...'}
                  </p>
                  {currentRegime?.confidence && (
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-[#A1A1AA]">Confidence:</span>
                      <Progress 
                        value={currentRegime.confidence * 100} 
                        className="w-24 h-2"
                      />
                      <span className="text-xs font-bold" style={{ color: regimeColor }}>
                        {(currentRegime.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex flex-wrap items-center gap-4">
                {/* Key Indicators */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 rounded bg-[#0A0A0A]">
                    <p className="text-xs text-[#A1A1AA]">Volatility</p>
                    <p className="text-lg font-data font-bold text-white">
                      {((indicators.volatility || 0) * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-center p-2 rounded bg-[#0A0A0A]">
                    <p className="text-xs text-[#A1A1AA]">RSI</p>
                    <p className="text-lg font-data font-bold text-white">
                      {(indicators.rsi || 50).toFixed(1)}
                    </p>
                  </div>
                  <div className="text-center p-2 rounded bg-[#0A0A0A]">
                    <p className="text-xs text-[#A1A1AA]">Trend</p>
                    <p className="text-lg font-data font-bold" style={{ color: (indicators.trend_strength || 0) > 0 ? '#00FF94' : '#FF0055' }}>
                      {((indicators.trend_strength || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-2 rounded bg-[#0A0A0A]">
                    <p className="text-xs text-[#A1A1AA]">Momentum</p>
                    <p className="text-lg font-data font-bold" style={{ color: (indicators.momentum_20d || 0) > 0 ? '#00FF94' : '#FF0055' }}>
                      {((indicators.momentum_20d || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                
                <Button
                  onClick={autoAdjustParams}
                  disabled={autoAdjusting}
                  className="bg-[#9D00FF] hover:bg-[#8500DD]"
                >
                  {autoAdjusting ? (
                    <RefreshCw size={16} className="mr-2 animate-spin" />
                  ) : (
                    <Settings size={16} className="mr-2" />
                  )}
                  Auto-Adjust
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="regime" className="data-[state=active]:bg-[#9D00FF]">
            <Activity size={16} className="mr-2" />
            Regime Variants
          </TabsTrigger>
          <TabsTrigger value="predictions" className="data-[state=active]:bg-[#9D00FF]">
            <Calendar size={16} className="mr-2" />
            Event Predictions
          </TabsTrigger>
          <TabsTrigger value="onchain" className="data-[state=active]:bg-[#9D00FF]">
            <Wallet size={16} className="mr-2" />
            On-Chain Data
          </TabsTrigger>
          <TabsTrigger value="strategy" className="data-[state=active]:bg-[#9D00FF]">
            <Target size={16} className="mr-2" />
            Optimal Strategy
          </TabsTrigger>
        </TabsList>

        {/* Regime Variants Tab */}
        <TabsContent value="regime" className="mt-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-white">Regime-Specific Strategy Variants</h3>
            <Button onClick={initializeVariants} variant="outline" size="sm">
              <RefreshCw size={14} className="mr-2" />
              Initialize All
            </Button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(regimeVariants).map(([regimeName, variants]) => {
              const rColor = regimeColors[regimeName] || '#A1A1AA';
              const RIcon = regimeIcons[regimeName] || Activity;
              const isActive = regime === regimeName;
              
              return (
                <Card 
                  key={regimeName}
                  className={`border-2 transition-all ${isActive ? 'ring-2 ring-offset-2 ring-offset-black' : ''}`}
                  style={{ 
                    backgroundColor: isActive ? `${rColor}15` : '#0A0A0A',
                    borderColor: `${rColor}${isActive ? '80' : '30'}`,
                    ringColor: rColor
                  }}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <RIcon size={20} style={{ color: rColor }} />
                        <span className="capitalize" style={{ color: rColor }}>
                          {regimeName.replace('_', ' ')} Market
                        </span>
                      </div>
                      {isActive && (
                        <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                          ACTIVE
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {variants.map((variant, idx) => (
                        <div 
                          key={variant.variant_id || idx}
                          className="p-3 rounded-lg bg-[#121212] border border-[#1F1F1F] hover:border-[#333] transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-white">{variant.name}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-[#A1A1AA]">
                                  Entry: {variant.parameters?.entry_threshold || 'N/A'}
                                </span>
                                <span className="text-xs text-[#666]">•</span>
                                <span className="text-xs text-[#A1A1AA]">
                                  SL: {variant.parameters?.stop_loss_pct}%
                                </span>
                                <span className="text-xs text-[#666]">•</span>
                                <span className="text-xs text-[#A1A1AA]">
                                  TP: {variant.parameters?.take_profit_pct}%
                                </span>
                              </div>
                            </div>
                            <ChevronRight size={16} className="text-[#666]" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Event Predictions Tab */}
        <TabsContent value="predictions" className="mt-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-white">Predicted Future Events</h3>
            <Button onClick={predictEvents} variant="outline" size="sm">
              <Eye size={14} className="mr-2" />
              Refresh Predictions
            </Button>
          </div>
          
          <div className="space-y-4">
            {predictedEvents.length > 0 ? (
              predictedEvents.map((event, idx) => {
                const impactColor = impactColors[event.expected_impact] || '#A1A1AA';
                
                return (
                  <motion.div
                    key={event.event_id || idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                  >
                    <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#333] transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-4">
                            <div 
                              className="w-12 h-12 rounded-full flex items-center justify-center shrink-0"
                              style={{ backgroundColor: `${impactColor}20` }}
                            >
                              {event.expected_impact === 'positive' ? (
                                <TrendingUp size={24} style={{ color: impactColor }} />
                              ) : event.expected_impact === 'negative' ? (
                                <TrendingDown size={24} style={{ color: impactColor }} />
                              ) : (
                                <Activity size={24} style={{ color: impactColor }} />
                              )}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-bold text-white">{event.description}</h4>
                                <Badge 
                                  className="text-xs"
                                  style={{ 
                                    backgroundColor: `${impactColor}20`,
                                    color: impactColor
                                  }}
                                >
                                  {event.expected_impact?.toUpperCase()}
                                </Badge>
                              </div>
                              <p className="text-sm text-[#A1A1AA] mt-1">
                                Type: {event.event_type?.replace('_', ' ')}
                              </p>
                              <div className="flex items-center gap-4 mt-2">
                                <div className="flex items-center gap-1">
                                  <Calendar size={14} className="text-[#666]" />
                                  <span className="text-sm text-white">{event.predicted_date}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Gauge size={14} className="text-[#666]" />
                                  <span className="text-sm font-bold" style={{ color: event.probability > 0.7 ? '#00FF94' : '#FFB800' }}>
                                    {(event.probability * 100).toFixed(0)}% probability
                                  </span>
                                </div>
                              </div>
                              {event.affected_coins && (
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="text-xs text-[#666]">Affected:</span>
                                  {event.affected_coins.map(coin => (
                                    <Badge key={coin} variant="outline" className="text-xs">
                                      {coin}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                              {event.confidence_factors && (
                                <div className="mt-3 p-2 rounded bg-[#121212]">
                                  <p className="text-xs text-[#666] mb-1">Confidence Factors:</p>
                                  <div className="flex flex-wrap gap-2">
                                    {Object.entries(event.confidence_factors).map(([factor, value]) => (
                                      <span key={factor} className="text-xs text-[#A1A1AA]">
                                        {factor.replace('_', ' ')}: <span className="text-white">{(value * 100).toFixed(0)}%</span>
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="w-16 h-16">
                              <svg viewBox="0 0 36 36" className="circular-chart">
                                <path
                                  className="circle-bg"
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke="#1F1F1F"
                                  strokeWidth="3"
                                />
                                <path
                                  className="circle"
                                  strokeDasharray={`${event.probability * 100}, 100`}
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke={impactColor}
                                  strokeWidth="3"
                                  strokeLinecap="round"
                                />
                                <text x="18" y="22" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">
                                  {(event.probability * 100).toFixed(0)}%
                                </text>
                              </svg>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })
            ) : (
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardContent className="p-8 text-center">
                  <Calendar size={48} className="mx-auto text-[#333] mb-4" />
                  <p className="text-[#A1A1AA]">No predictions available</p>
                  <Button onClick={predictEvents} className="mt-4 bg-[#9D00FF]">
                    Generate Predictions
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* On-Chain Data Tab */}
        <TabsContent value="onchain" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Whale Activity */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wallet size={20} className="text-[#9D00FF]" />
                  Whale Activity Tracker
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[#A1A1AA]">Exchange Inflows (24h)</span>
                      <span className="text-[#FF0055] font-bold">↑ 2,450 BTC</span>
                    </div>
                    <Progress value={65} className="h-2" />
                    <p className="text-xs text-[#666] mt-1">Elevated selling pressure</p>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[#A1A1AA]">Exchange Outflows (24h)</span>
                      <span className="text-[#00FF94] font-bold">↓ 3,120 BTC</span>
                    </div>
                    <Progress value={78} className="h-2" />
                    <p className="text-xs text-[#666] mt-1">Strong accumulation signal</p>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[#A1A1AA]">Whale Wallets (>1000 BTC)</span>
                      <span className="text-white font-bold">2,142</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-[#00FF94]/20 text-[#00FF94]">+12 this week</Badge>
                      <span className="text-xs text-[#A1A1AA]">Accumulation phase</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Network Metrics */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart size={20} className="text-[#00FF94]" />
                  Network Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Active Addresses (24h)</span>
                      <span className="text-white font-bold">892,451</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <TrendingUp size={14} className="text-[#00FF94]" />
                      <span className="text-xs text-[#00FF94]">+5.2% vs 7d avg</span>
                    </div>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Transaction Volume</span>
                      <span className="text-white font-bold">$42.5B</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <TrendingUp size={14} className="text-[#00FF94]" />
                      <span className="text-xs text-[#00FF94]">+12.8% vs 7d avg</span>
                    </div>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Hash Rate</span>
                      <span className="text-white font-bold">580 EH/s</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <TrendingUp size={14} className="text-[#00FF94]" />
                      <span className="text-xs text-[#00FF94]">ATH - Network secure</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Large Transactions */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowRightLeft size={20} className="text-[#FFB800]" />
                  Recent Large Transactions (>$10M)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[
                    { time: '2 min ago', amount: '1,250 BTC', usd: '$118.7M', type: 'Exchange → Unknown', impact: 'bullish' },
                    { time: '15 min ago', amount: '890 BTC', usd: '$84.5M', type: 'Unknown → Coinbase', impact: 'bearish' },
                    { time: '32 min ago', amount: '2,100 BTC', usd: '$199.5M', type: 'Binance → Unknown', impact: 'bullish' },
                    { time: '1 hr ago', amount: '560 BTC', usd: '$53.2M', type: 'Unknown → Kraken', impact: 'bearish' },
                  ].map((tx, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded bg-[#121212] border border-[#1F1F1F]">
                      <div className="flex items-center gap-4">
                        <div className={`w-2 h-2 rounded-full ${tx.impact === 'bullish' ? 'bg-[#00FF94]' : 'bg-[#FF0055]'}`} />
                        <div>
                          <p className="text-white font-medium">{tx.amount} <span className="text-[#A1A1AA]">({tx.usd})</span></p>
                          <p className="text-xs text-[#666]">{tx.type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={tx.impact === 'bullish' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                          {tx.impact.toUpperCase()}
                        </Badge>
                        <p className="text-xs text-[#666] mt-1">{tx.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Optimal Strategy Tab */}
        <TabsContent value="strategy" className="mt-4">
          {optimalStrategy ? (
            <div className="space-y-4">
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target size={20} className="text-[#9D00FF]" />
                    Recommended Strategy for {regime.replace('_', ' ')} Market
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-lg font-bold text-white mb-4">
                        {recommendedStrategy.name || 'Analyzing...'}
                      </h4>
                      {recommendedStrategy.parameters && (
                        <div className="space-y-3">
                          {Object.entries(recommendedStrategy.parameters).slice(0, 8).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between p-2 rounded bg-[#121212]">
                              <span className="text-[#A1A1AA] capitalize">{key.replace(/_/g, ' ')}</span>
                              <span className="text-white font-medium">
                                {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                                {typeof value === 'number' && key.includes('pct') ? '%' : ''}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-white mb-4">Risk Assessment</h4>
                      <div className="p-4 rounded-lg border-2" style={{ borderColor: regimeColor, backgroundColor: `${regimeColor}10` }}>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle size={20} style={{ color: regimeColor }} />
                          <span className="font-bold capitalize" style={{ color: regimeColor }}>
                            {optimalStrategy.risk_level || 'Moderate'} Risk
                          </span>
                        </div>
                        <p className="text-sm text-[#A1A1AA]">
                          {optimalStrategy.risk_level === 'high' 
                            ? 'Consider reducing position sizes and using tighter stops'
                            : optimalStrategy.risk_level === 'low'
                            ? 'Favorable conditions for larger positions with wider stops'
                            : 'Standard risk parameters recommended'}
                        </p>
                      </div>
                      
                      <div className="mt-4 p-4 rounded-lg bg-[#121212]">
                        <h5 className="text-sm font-bold text-white mb-2">Key Actions</h5>
                        <ul className="text-sm text-[#A1A1AA] space-y-1">
                          <li>• Monitor {regime === 'bull' ? 'pullbacks for entry' : regime === 'bear' ? 'rallies for shorts' : 'range boundaries'}</li>
                          <li>• Set stop loss at {recommendedStrategy.parameters?.stop_loss_pct || 5}%</li>
                          <li>• Target {recommendedStrategy.parameters?.take_profit_pct || 10}% profit</li>
                          <li>• Max position size: {recommendedStrategy.parameters?.max_position_pct || 10}%</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Upcoming Events */}
              {optimalStrategy.upcoming_events?.length > 0 && (
                <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar size={20} className="text-[#FFB800]" />
                      Upcoming Events to Watch
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {optimalStrategy.upcoming_events.slice(0, 3).map((event, idx) => (
                        <div key={idx} className="p-4 rounded-lg bg-[#121212] border border-[#1F1F1F]">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge style={{ backgroundColor: `${impactColors[event.expected_impact]}20`, color: impactColors[event.expected_impact] }}>
                              {event.expected_impact}
                            </Badge>
                            <span className="text-xs text-[#666]">{(event.probability * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-white font-medium text-sm">{event.description}</p>
                          <p className="text-xs text-[#666] mt-1">{event.predicted_date}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-8 text-center">
                <Target size={48} className="mx-auto text-[#333] mb-4" />
                <p className="text-[#A1A1AA]">Loading optimal strategy...</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdaptiveStrategy;
