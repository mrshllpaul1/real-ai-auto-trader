// AdaptiveStrategy-b3b8bcc5
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
import { StatsGridSkeleton, ChartSkeleton, CardSkeleton, AIInsightSkeleton } from '../components/LoadingSkeletons';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';
import { useComponentState, ComponentType } from '../hooks/useSystemState';

// Inline fallback for PageLoadingSkeleton in case of import issues
const PageLoadingSkeletonFallback = () => (
  <div className="min-h-screen bg-[#0A0A0A] p-6">
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="h-8 w-48 bg-[#1F1F1F] rounded-lg animate-pulse mb-2" />
          <div className="h-4 w-32 bg-[#1F1F1F] rounded animate-pulse" />
        </div>
      </div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
            <div className="h-4 w-20 bg-[#1F1F1F] rounded animate-pulse mb-2" />
            <div className="h-8 w-24 bg-[#1F1F1F] rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  </div>
);

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

const AdaptiveStrategy = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('regime');
  const [strategyStatus, setStrategyStatus] = useState(null);
  const [currentRegime, setCurrentRegime] = useState(null);
  const [regimeVariants, setRegimeVariants] = useState({});
  const [predictedEvents, setPredictedEvents] = useState([]);
  const [optimalStrategy, setOptimalStrategy] = useState(null);
  const [onChainData, setOnChainData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoAdjusting, setAutoAdjusting] = useState(false);
  const [coverageStats, setCoverageStats] = useState(null);
  const [eventFilter, setEventFilter] = useState('all');
  const [probabilityFilter, setProbabilityFilter] = useState(0);
  const [eventCalendar, setEventCalendar] = useState(null);

  // Use persisted state for monitoring
  const { 
    isRunning: isMonitoring, 
    setRunning: setMonitoringState,
    loading: monitoringLoading 
  } = useComponentState(ComponentType.ADAPTIVE_MONITORING, {
    pollInterval: 30000, // Check every 30 seconds
  });

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
      // Don't override monitoring state from local status - use persisted state
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
        await setMonitoringState(false);
        toast.info('Adaptive monitoring stopped');
      } else {
        await api.post('/adaptive-strategy/monitoring/start');
        await setMonitoringState(true);
        toast.success('Adaptive monitoring started');
      }
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
    return <PageLoadingSkeleton />;
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
                        {((currentRegime?.confidence ?? 0) * 100).toFixed(0)}%
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
          {/* Coverage Stats Bar */}
          {coverageStats && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] mb-4">
              <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <PieChart size={18} className="text-[#9D00FF]" />
                      <span className="text-sm text-[#A1A1AA]">Event Coverage:</span>
                      <span className="text-lg font-bold" style={{ color: coverageStats.coverage_percentage >= 70 ? '#00FF94' : coverageStats.coverage_percentage >= 50 ? '#FFB800' : '#FF0055' }}>
                        {coverageStats.coverage_percentage}%
                      </span>
                    </div>
                    <div className="h-4 w-px bg-[#333] hidden lg:block" />
                    <div className="flex items-center gap-2">
                      <Target size={14} className="text-[#00B4FF]" />
                      <span className="text-xs text-[#A1A1AA]">
                        {coverageStats.event_types_with_predictions}/{coverageStats.total_event_types_defined} types active
                      </span>
                    </div>
                    <div className="h-4 w-px bg-[#333] hidden lg:block" />
                    <div className="flex items-center gap-2">
                      <Calendar size={14} className="text-[#FFB800]" />
                      <span className="text-xs text-[#A1A1AA]">
                        Upcoming: <span className="text-white">{coverageStats.upcoming_events?.next_30_days || 0}</span> (30d) · <span className="text-white">{coverageStats.upcoming_events?.next_60_days || 0}</span> (60d) · <span className="text-white">{coverageStats.upcoming_events?.next_90_days || 0}</span> (90d)
                      </span>
                    </div>
                  </div>
                  <div className="w-full lg:w-48">
                    <Progress value={coverageStats.coverage_percentage} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters and Actions */}
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-4 gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-[#A1A1AA]">Filter:</span>
              {['all', 'scheduled', 'derivatives', 'regulatory', 'protocol', 'on_chain', 'macro', 'defi', 'institutional', 'risk'].map(f => (
                <Button
                  key={f}
                  size="sm"
                  variant={eventFilter === f ? "default" : "outline"}
                  onClick={() => setEventFilter(f)}
                  className={`text-xs h-7 ${eventFilter === f ? 'bg-[#9D00FF] text-white' : 'text-[#A1A1AA] border-[#333]'}`}
                >
                  {f === 'all' ? 'All' : f === 'on_chain' ? 'On-Chain' : f.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <select
                value={probabilityFilter}
                onChange={(e) => setProbabilityFilter(Number(e.target.value))}
                className="text-xs bg-[#0A0A0A] border border-[#333] rounded px-2 py-1 text-white h-7"
              >
                <option value={0}>All probabilities</option>
                <option value={0.3}>30%+</option>
                <option value={0.5}>50%+</option>
                <option value={0.7}>70%+</option>
                <option value={0.9}>90%+</option>
              </select>
              <Button onClick={predictEvents} variant="outline" size="sm" className="h-7">
                <RefreshCw size={12} className="mr-1" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Scheduled Events Timeline */}
          {eventCalendar?.scheduled_events_raw?.length > 0 && eventFilter === 'all' && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] mb-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock size={14} className="text-[#00B4FF]" />
                  <span className="text-[#00B4FF]">Upcoming Scheduled Events</span>
                  <Badge variant="outline" className="text-xs ml-2">{eventCalendar.scheduled_events_raw.length} events</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {eventCalendar.scheduled_events_raw.slice(0, 9).map((ev, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 rounded bg-[#121212] border border-[#1F1F1F]">
                      <div className="text-center shrink-0 w-12">
                        <div className="text-[10px] text-[#666] uppercase">
                          {new Date(ev.date + 'T00:00:00Z').toLocaleDateString('en-US', { month: 'short' })}
                        </div>
                        <div className="text-lg font-bold text-white leading-none">
                          {new Date(ev.date + 'T00:00:00Z').getUTCDate()}
                        </div>
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs text-white truncate">{ev.description}</p>
                        <div className="flex items-center gap-1 mt-0.5">
                          <Badge variant="outline" className="text-[9px] h-4 px-1">{ev.calendar_category?.replace('_', ' ')}</Badge>
                          <span className="text-[10px] text-[#666]">{ev.days_until}d away</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Event Predictions List */}
          <div className="space-y-3">
            {(() => {
              const categoryMap = {
                fomc_meeting: 'macro', options_expiry: 'derivatives', futures_expiry: 'derivatives',
                bitcoin_halving: 'protocol', ethereum_upgrade: 'protocol', network_upgrade: 'protocol',
                mining_difficulty_adjustment: 'protocol', sec_deadline: 'regulatory', regulatory_action: 'regulatory',
                etf_launch: 'regulatory', cbdc_announcement: 'regulatory', whale_accumulation: 'on_chain',
                whale_distribution: 'on_chain', token_unlock: 'scheduled', quarterly_earnings: 'scheduled',
                institutional_buy: 'institutional', exchange_listing: 'market', governance_vote: 'defi',
                airdrop_event: 'defi', defi_exploit: 'defi', layer2_milestone: 'protocol',
                protocol_launch: 'protocol', celebrity_endorsement: 'social', macro_crisis: 'macro',
                geopolitical_event: 'macro', stablecoin_depeg: 'risk', tax_deadline: 'scheduled',
                regime_shift: 'risk', volatility_event: 'risk', trend_exhaustion: 'risk',
                correlation_shift: 'risk', liquidity_event: 'risk', aggregate_sell_pressure: 'risk',
              };

              const filtered = predictedEvents.filter(event => {
                const cat = categoryMap[event.event_type] || 'other';
                const passCategory = eventFilter === 'all' || cat === eventFilter;
                const passProb = event.probability >= probabilityFilter;
                return passCategory && passProb;
              });

              if (filtered.length === 0) {
                return (
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-8 text-center">
                      <Calendar size={48} className="mx-auto text-[#333] mb-4" />
                      <p className="text-[#A1A1AA]">{predictedEvents.length === 0 ? 'No predictions available' : 'No events match current filters'}</p>
                      {predictedEvents.length === 0 && (
                        <Button onClick={predictEvents} className="mt-4 bg-[#9D00FF]">
                          Generate Predictions
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                );
              }

              return filtered.map((event, idx) => {
                const impactColor = impactColors[event.expected_impact] || '#A1A1AA';
                const cat = categoryMap[event.event_type] || 'other';
                const catColors = {
                  macro: '#FF6B00', derivatives: '#00B4FF', protocol: '#9D00FF', regulatory: '#FFB800',
                  on_chain: '#00FF94', scheduled: '#FF00FF', defi: '#00B4FF', institutional: '#FFB800',
                  risk: '#FF0055', market: '#00FF94', social: '#FF6B00', other: '#A1A1AA'
                };
                
                return (
                  <motion.div
                    key={event.event_id || idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(idx * 0.05, 0.5) }}
                  >
                    <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#333] transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 min-w-0">
                            <div 
                              className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                              style={{ backgroundColor: `${impactColor}20` }}
                            >
                              {event.expected_impact === 'positive' ? (
                                <TrendingUp size={20} style={{ color: impactColor }} />
                              ) : event.expected_impact === 'negative' ? (
                                <TrendingDown size={20} style={{ color: impactColor }} />
                              ) : (
                                <Activity size={20} style={{ color: impactColor }} />
                              )}
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-bold text-white text-sm">{event.description}</h4>
                              </div>
                              <div className="flex items-center gap-2 mt-1 flex-wrap">
                                <Badge 
                                  className="text-[10px] h-5"
                                  style={{ backgroundColor: `${impactColor}20`, color: impactColor }}
                                >
                                  {event.expected_impact?.toUpperCase()}
                                </Badge>
                                <Badge 
                                  variant="outline" 
                                  className="text-[10px] h-5"
                                  style={{ borderColor: catColors[cat], color: catColors[cat] }}
                                >
                                  {event.event_type?.replace(/_/g, ' ')}
                                </Badge>
                                <Badge variant="outline" className="text-[10px] h-5 text-[#666]">
                                  {cat}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-4 mt-2 flex-wrap">
                                <div className="flex items-center gap-1">
                                  <Calendar size={12} className="text-[#666]" />
                                  <span className="text-xs text-white">{event.predicted_date}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Gauge size={12} className="text-[#666]" />
                                  <span className="text-xs font-bold" style={{ color: event.probability >= 0.9 ? '#00FF94' : event.probability >= 0.7 ? '#00B4FF' : event.probability >= 0.5 ? '#FFB800' : '#FF6B00' }}>
                                    {((event?.probability ?? 0) * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                              {event.affected_coins && (
                                <div className="flex items-center gap-1 mt-1.5 flex-wrap">
                                  <span className="text-[10px] text-[#666]">Coins:</span>
                                  {event.affected_coins.slice(0, 6).map(coin => (
                                    <Badge key={coin} variant="outline" className="text-[10px] h-4 px-1">
                                      {coin}
                                    </Badge>
                                  ))}
                                  {event.affected_coins.length > 6 && (
                                    <span className="text-[10px] text-[#666]">+{event.affected_coins.length - 6}</span>
                                  )}
                                </div>
                              )}
                              {event.confidence_factors && (
                                <div className="mt-2 p-2 rounded bg-[#121212]">
                                  <p className="text-[10px] text-[#666] mb-1">Confidence Factors:</p>
                                  <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                                    {Object.entries(event.confidence_factors).map(([factor, value]) => (
                                      <span key={factor} className="text-[10px] text-[#A1A1AA]">
                                        {factor.replace(/_/g, ' ')}: <span className="text-white">{(value * 100).toFixed(0)}%</span>
                                      </span>
                                    ))}
                                  </div>
                                  {event.prediction_basis && (
                                    <p className="text-[10px] text-[#555] mt-1 italic">Basis: {event.prediction_basis}</p>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-right shrink-0 ml-2">
                            <div className="w-14 h-14">
                              <svg viewBox="0 0 36 36" className="circular-chart">
                                <path
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke="#1F1F1F"
                                  strokeWidth="3"
                                />
                                <path
                                  strokeDasharray={`${event.probability * 100}, 100`}
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke={event.probability >= 0.9 ? '#00FF94' : event.probability >= 0.7 ? '#00B4FF' : event.probability >= 0.5 ? '#FFB800' : '#FF6B00'}
                                  strokeWidth="3"
                                  strokeLinecap="round"
                                />
                                <text x="18" y="22" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">
                                  {((event?.probability ?? 0) * 100).toFixed(0)}%
                                </text>
                              </svg>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              });
            })()}
          </div>

          {/* Event Type Coverage Grid */}
          {coverageStats?.type_details && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] mt-6">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 size={14} className="text-[#9D00FF]" />
                  <span className="text-[#9D00FF]">Event Type Coverage</span>
                  <Badge variant="outline" className="text-xs ml-2">
                    {coverageStats.event_types_with_predictions}/{coverageStats.total_event_types_defined} types
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                  {coverageStats.type_details.map((td, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-2 p-2 rounded border ${
                        td.is_predicted ? 'bg-[#121212] border-[#1F1F1F]' : 'bg-[#0A0A0A] border-[#1A1A1A] opacity-60'
                      }`}
                    >
                      <div className={`w-2 h-2 rounded-full shrink-0 ${td.is_predicted ? 'bg-[#00FF94]' : 'bg-[#333]'}`} />
                      <div className="min-w-0 flex-1">
                        <p className="text-[11px] text-white truncate">{td.event_type?.replace(/_/g, ' ')}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-[9px] text-[#666]">
                            {td.is_predicted ? `${td.active_predictions} active` : 'inactive'}
                          </span>
                          {td.avg_probability > 0 && (
                            <span className="text-[9px]" style={{ color: td.avg_probability >= 0.7 ? '#00FF94' : '#FFB800' }}>
                              {((td?.avg_probability ?? 0) * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                      <Badge 
                        variant="outline" 
                        className="text-[8px] h-4 px-1 shrink-0"
                        style={{ 
                          color: td.impact === 'positive' ? '#00FF94' : td.impact === 'negative' ? '#FF0055' : '#FFB800',
                          borderColor: td.impact === 'positive' ? '#00FF9430' : td.impact === 'negative' ? '#FF005530' : '#FFB80030',
                        }}
                      >
                        {td.impact}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
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
                      <span className="text-[#A1A1AA]">Whale Wallets (&gt;1000 BTC)</span>
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
                  Recent Large Transactions (&gt;$10M)
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
                            <span className="text-xs text-[#666]">{((event?.probability ?? 0) * 100).toFixed(0)}%</span>
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
