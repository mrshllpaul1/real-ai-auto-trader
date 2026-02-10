import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, TrendingUp, TrendingDown, Target, Activity, 
  CheckCircle, XCircle, Clock, Zap, BarChart3, 
  AlertTriangle, Award, RefreshCw, Database, LineChart,
  Gauge, Layers, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

// Simple chart components for accuracy visualization
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
        <div className="absolute bottom-0 left-1/2 w-4 h-4 -translate-x-1/2 translate-y-1/2 rounded-full bg-white" />
      </div>
      <div className="text-2xl font-data font-bold mt-2" style={{ color }}>
        {value?.toFixed(1)}%
      </div>
      <div className="text-xs text-[#A1A1AA]">{label}</div>
    </div>
  );
};

const AILearningLoop = () => {
  const [status, setStatus] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [insights, setInsights] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [recentPredictions, setRecentPredictions] = useState([]);
  const [unverifiedPredictions, setUnverifiedPredictions] = useState([]);
  const [backtestStatus, setBacktestStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Default status object to prevent null errors
  const safeStatus = status || {
    total_predictions: 0,
    verified_predictions: 0,
    verification_rate: 0,
    accuracy_rate: 0,
    model_accuracy: {},
    learning_rate: 0,
    last_training: null
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, perfRes, insightsRes, feedbackRes, recentRes, unverifiedRes, backtestRes] = await Promise.all([
        api.get('/ai-learning/status').catch(() => ({ data: null })),
        api.get('/ai-learning/model-performance?days=30').catch(() => ({ data: null })),
        api.get('/ai-learning/insights').catch(() => ({ data: null })),
        api.get('/ai-learning/training-feedback').catch(() => ({ data: null })),
        api.get('/ai-learning/predictions/recent?limit=20').catch(() => ({ data: { predictions: [] } })),
        api.get('/ai-learning/predictions/unverified?limit=20').catch(() => ({ data: { predictions: [] } })),
        api.get('/gems/backtest/status').catch(() => ({ data: null }))
      ]);

      setStatus(statusRes.data);
      setPerformance(perfRes.data?.performance || {});
      setInsights(insightsRes.data);
      setFeedback(feedbackRes.data);
      setRecentPredictions(recentRes.data?.predictions || []);
      setUnverifiedPredictions(unverifiedRes.data?.predictions || []);
      setBacktestStatus(backtestRes.data);
    } catch (error) {
      console.error('Error loading AI learning data:', error);
      toast.error('Failed to load AI learning data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [loadData]);

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 70) return 'text-[#00FF94]';
    if (accuracy >= 50) return 'text-[#FFB800]';
    return 'text-[#FF0055]';
  };

  const getAccuracyBadge = (accuracy) => {
    if (accuracy >= 70) return { color: 'bg-[#00FF94]/20 text-[#00FF94]', label: 'Excellent' };
    if (accuracy >= 50) return { color: 'bg-[#FFB800]/20 text-[#FFB800]', label: 'Good' };
    return { color: 'bg-[#FF0055]/20 text-[#FF0055]', label: 'Needs Improvement' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading AI Learning Loop data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="ai-learning-loop">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Brain size={40} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">AI</span> Learning Loop
          </h1>
          <p className="text-[#A1A1AA]">
            Continuous learning from predictions to improve AI accuracy over time
          </p>
        </div>
        <Button
          onClick={loadData}
          variant="outline"
          className="border-[#9D00FF] text-[#9D00FF] hover:bg-[#9D00FF]/10"
          data-testid="refresh-btn"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh Data
        </Button>
      </motion.div>

      {/* Status Overview Cards */}
      {status && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="total-predictions-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Database size={20} className="text-[#9D00FF]" />
                <span className="text-sm text-[#A1A1AA]">Total Predictions</span>
              </div>
              <div className="text-3xl font-data font-bold text-white">
                {safeStatus.total_predictions || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="verified-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle size={20} className="text-[#00FF94]" />
                <span className="text-sm text-[#A1A1AA]">Verified</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#00FF94]">
                {safeStatus.verified_predictions || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="pending-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Clock size={20} className="text-[#FFB800]" />
                <span className="text-sm text-[#A1A1AA]">Pending</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#FFB800]">
                {(safeStatus.total_predictions || 0) - (safeStatus.verified_predictions || 0)}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="verification-rate-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Activity size={20} className="text-[#007AFF]" />
                <span className="text-sm text-[#A1A1AA]">Verification Rate</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#007AFF]">
                {(safeStatus.verification_rate || 0).toFixed(1)}%
              </div>
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
          <TabsTrigger value="charts" className="data-[state=active]:bg-[#9D00FF]">
            Charts
          </TabsTrigger>
          <TabsTrigger value="models" className="data-[state=active]:bg-[#9D00FF]">
            Model Performance
          </TabsTrigger>
          <TabsTrigger value="insights" className="data-[state=active]:bg-[#9D00FF]">
            Insights
          </TabsTrigger>
          <TabsTrigger value="predictions" className="data-[state=active]:bg-[#9D00FF]">
            Predictions
          </TabsTrigger>
        </TabsList>

        {/* Charts Tab - NEW */}
        <TabsContent value="charts" className="space-y-6">
          {/* Backtest Accuracy Card */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="backtest-accuracy-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <LineChart className="text-[#00FF94]" />
                  Gem Prediction Accuracy (Backtesting)
                </CardTitle>
                <CardDescription>
                  Accuracy improvement over iterations using OHLCV historical data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {backtestStatus?.result?.iterations ? (
                  <>
                    {/* Accuracy Gauge */}
                    <div className="flex justify-around items-center py-4">
                      <AccuracyGauge 
                        value={backtestStatus.result?.final_accuracy || 0} 
                        label="Final Accuracy" 
                      />
                      <div className="text-center">
                        <div className="text-4xl font-data font-bold text-[#9D00FF]">
                          {backtestStatus.result?.iterations?.length || 0}
                        </div>
                        <div className="text-xs text-[#A1A1AA]">Iterations</div>
                      </div>
                      <AccuracyGauge 
                        value={backtestStatus.result?.best_threshold * 100 || 70} 
                        label="Optimal Threshold" 
                      />
                    </div>
                    
                    {/* Accuracy Trend Chart */}
                    <AccuracyTrendChart 
                      data={backtestStatus.result.iterations} 
                      title="Accuracy per Iteration"
                    />
                    
                    {/* Optimized Weights */}
                    {backtestStatus.result?.best_weights && (
                      <div className="mt-6">
                        <h4 className="text-sm font-medium text-[#A1A1AA] mb-3">Optimized Prediction Weights</h4>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                          {Object.entries(backtestStatus.result.best_weights)
                            .sort((a, b) => b[1] - a[1])
                            .map(([factor, weight]) => (
                              <div key={factor} className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                                <div className="text-xs text-[#A1A1AA] mb-1 capitalize">
                                  {factor.replace(/_/g, ' ')}
                                </div>
                                <div className="text-lg font-data font-bold text-white">
                                  {((weight || 0) * 100).toFixed(0)}%
                                </div>
                                <Progress value={weight * 100} className="h-1 mt-1" />
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <Gauge size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
                    <p className="text-[#A1A1AA] mb-4">No backtest data yet</p>
                    <p className="text-xs text-[#A1A1AA]">
                      Run a backtest from the Gem Backtester page to see accuracy charts
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Model Performance Comparison */}
          {insights?.model_rankings && insights.model_rankings.length > 0 && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="model-comparison-chart">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Layers className="text-[#007AFF]" />
                    Model Performance Comparison
                  </CardTitle>
                  <CardDescription>Accuracy comparison across all AI models</CardDescription>
                </CardHeader>
                <CardContent>
                  <ModelComparisonChart models={insights.model_rankings} />
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Prediction Stats Grid */}
          <motion.div 
            initial={{ y: 20, opacity: 0 }} 
            animate={{ y: 0, opacity: 1 }} 
            transition={{ delay: 0.2 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4"
          >
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4 text-center">
                <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-[#00FF94]/20 flex items-center justify-center">
                  <ArrowUpRight className="text-[#00FF94]" />
                </div>
                <div className="text-2xl font-data font-bold text-[#00FF94]">
                  {insights?.strong_areas?.length || 0}
                </div>
                <div className="text-xs text-[#A1A1AA]">Strong Areas</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4 text-center">
                <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-[#FF0055]/20 flex items-center justify-center">
                  <ArrowDownRight className="text-[#FF0055]" />
                </div>
                <div className="text-2xl font-data font-bold text-[#FF0055]">
                  {insights?.weak_areas?.length || 0}
                </div>
                <div className="text-xs text-[#A1A1AA]">Weak Areas</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4 text-center">
                <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-[#9D00FF]/20 flex items-center justify-center">
                  <Brain className="text-[#9D00FF]" />
                </div>
                <div className="text-2xl font-data font-bold text-[#9D00FF]">
                  {Object.keys(performance || {}).length}
                </div>
                <div className="text-xs text-[#A1A1AA]">Active Models</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4 text-center">
                <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-[#FFB800]/20 flex items-center justify-center">
                  <Target className="text-[#FFB800]" />
                </div>
                <div className="text-2xl font-data font-bold text-[#FFB800]">
                  {backtestStatus?.result?.final_accuracy?.toFixed(0) || 0}%
                </div>
                <div className="text-xs text-[#A1A1AA]">Gem Accuracy</div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Model Rankings */}
          {insights?.model_rankings && insights.model_rankings.length > 0 && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="model-rankings-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Award className="text-[#FFB800]" />
                    Model Rankings (Last 30 Days)
                  </CardTitle>
                  <CardDescription>AI models ranked by prediction accuracy</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {insights.model_rankings.map((model, index) => {
                      const badge = getAccuracyBadge(model.accuracy);
                      return (
                        <div
                          key={model.model}
                          className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                          data-testid={`model-rank-${index}`}
                        >
                          <div className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                              index === 0 ? 'bg-[#FFB800]/20' : 'bg-[#1F1F1F]'
                            }`}>
                              <span className={`font-bold ${index === 0 ? 'text-[#FFB800]' : 'text-[#A1A1AA]'}`}>
                                #{index + 1}
                              </span>
                            </div>
                            <div>
                              <h3 className="font-bold text-white uppercase">{model.model}</h3>
                              <p className="text-sm text-[#A1A1AA]">{model.predictions} predictions</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <div className={`text-2xl font-data font-bold ${getAccuracyColor(model?.accuracy || 0)}`}>
                                {(model?.accuracy || 0).toFixed(1)}%
                              </div>
                              <Badge className={badge.color}>{badge.label}</Badge>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Weak & Strong Areas */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Strong Areas */}
            {insights?.strong_areas && insights.strong_areas.length > 0 && (
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
                <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="strong-areas-card">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3 text-[#00FF94]">
                      <TrendingUp />
                      Strong Areas
                    </CardTitle>
                    <CardDescription>Prediction types with high accuracy</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {insights.strong_areas.slice(0, 5).map((area, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-[#00FF94]/5 rounded-lg border border-[#00FF94]/20">
                          <div>
                            <span className="font-medium text-white">{area.model}</span>
                            <span className="text-[#A1A1AA] mx-2">→</span>
                            <span className="text-[#A1A1AA]">{area.type}</span>
                          </div>
                          <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                            {(area?.accuracy || 0).toFixed(1)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Weak Areas */}
            {insights?.weak_areas && insights.weak_areas.length > 0 && (
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
                <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="weak-areas-card">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3 text-[#FF0055]">
                      <TrendingDown />
                      Areas for Improvement
                    </CardTitle>
                    <CardDescription>Prediction types needing optimization</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {insights.weak_areas.slice(0, 5).map((area, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-[#FF0055]/5 rounded-lg border border-[#FF0055]/20">
                          <div>
                            <span className="font-medium text-white">{area.model}</span>
                            <span className="text-[#A1A1AA] mx-2">→</span>
                            <span className="text-[#A1A1AA]">{area.type}</span>
                          </div>
                          <Badge className="bg-[#FF0055]/20 text-[#FF0055]">
                            {(area?.accuracy || 0).toFixed(1)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>

          {/* Weight Adjustments */}
          {insights?.recommended_weight_adjustments && Object.keys(insights.recommended_weight_adjustments).length > 0 && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="weight-adjustments-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Zap className="text-[#9D00FF]" />
                    Recommended Weight Adjustments
                  </CardTitle>
                  <CardDescription>AI suggestions for model optimization</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(insights.recommended_weight_adjustments).map(([model, adjustment]) => (
                      <div key={model} className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/20">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-white uppercase">{model}</span>
                          <Badge className={adjustment.recommendation === 'increase_weight' 
                            ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                            : 'bg-[#FF0055]/20 text-[#FF0055]'
                          }>
                            {adjustment.recommendation === 'increase_weight' ? '↑ Increase' : '↓ Decrease'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-[#A1A1AA]">
                          <span>Current Performance: {(adjustment.current_performance || 0).toFixed(1)}%</span>
                          <span>•</span>
                          <span>Suggested Change: {adjustment.suggested_boost || adjustment.suggested_reduction || 0}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </TabsContent>

        {/* Model Performance Tab */}
        <TabsContent value="models" className="space-y-6">
          {performance && Object.keys(performance).length > 0 ? (
            Object.entries(performance).map(([model, stats]) => (
              <motion.div key={model} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
                <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`model-${model}-card`}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="uppercase">{model}</span>
                      <Badge className={getAccuracyBadge(stats?.accuracy_rate || 0).color}>
                        {(stats?.accuracy_rate || 0).toFixed(1)}% Accuracy
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {stats.total_predictions} predictions | {stats.correct_predictions} correct
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Accuracy Progress Bar */}
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-[#A1A1AA]">Overall Accuracy</span>
                        <span className={getAccuracyColor(stats?.accuracy_rate || 0)}>{(stats?.accuracy_rate || 0).toFixed(1)}%</span>
                      </div>
                      <Progress value={stats?.accuracy_rate || 0} className="h-2" />
                    </div>

                    {/* By Type */}
                    {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-[#A1A1AA] mb-3">By Prediction Type</h4>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                          {Object.entries(stats.by_type).map(([type, typeStats]) => (
                            <div key={type} className="p-3 bg-[#121212] rounded-lg">
                              <div className="text-xs text-[#A1A1AA] mb-1">{type}</div>
                              <div className={`text-lg font-bold ${getAccuracyColor(typeStats?.accuracy || 0)}`}>
                                {(typeStats?.accuracy || 0).toFixed(1)}%
                              </div>
                              <div className="text-xs text-[#A1A1AA]">{typeStats?.total || 0} predictions</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* By Confidence */}
                    {stats?.by_confidence && (
                      <div>
                        <h4 className="text-sm font-medium text-[#A1A1AA] mb-3">By Confidence Level</h4>
                        <div className="grid grid-cols-3 gap-3">
                          <div className="p-3 bg-[#121212] rounded-lg border-l-4 border-[#00FF94]">
                            <div className="text-xs text-[#A1A1AA] mb-1">High Confidence (80%+)</div>
                            <div className={`text-lg font-bold ${getAccuracyColor(stats.by_confidence?.high || 0)}`}>
                              {(stats.by_confidence?.high || 0).toFixed(1)}%
                            </div>
                          </div>
                          <div className="p-3 bg-[#121212] rounded-lg border-l-4 border-[#FFB800]">
                            <div className="text-xs text-[#A1A1AA] mb-1">Medium (50-80%)</div>
                            <div className={`text-lg font-bold ${getAccuracyColor(stats.by_confidence?.medium || 0)}`}>
                              {(stats.by_confidence?.medium || 0).toFixed(1)}%
                            </div>
                          </div>
                          <div className="p-3 bg-[#121212] rounded-lg border-l-4 border-[#FF0055]">
                            <div className="text-xs text-[#A1A1AA] mb-1">Low (&lt;50%)</div>
                            <div className={`text-lg font-bold ${getAccuracyColor(stats.by_confidence?.low || 0)}`}>
                              {(stats.by_confidence?.low || 0).toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))
          ) : (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <Brain size={48} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
                <p className="text-[#A1A1AA]">No model performance data yet. Store predictions and record outcomes to start tracking.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          {/* Training Feedback */}
          {feedback && (
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="training-feedback-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <BarChart3 className="text-[#007AFF]" />
                    Training Feedback Summary
                  </CardTitle>
                  <CardDescription>Last 60 days of prediction data for retraining</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-sm text-[#A1A1AA] mb-1">Total Verified</div>
                      <div className="text-2xl font-bold text-white">{feedback.total_verified || 0}</div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-sm text-[#A1A1AA] mb-1">Successful Patterns</div>
                      <div className="text-2xl font-bold text-[#00FF94]">{feedback.successful_patterns?.length || 0}</div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-sm text-[#A1A1AA] mb-1">Failed Patterns</div>
                      <div className="text-2xl font-bold text-[#FF0055]">{feedback.failed_patterns?.length || 0}</div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-sm text-[#A1A1AA] mb-1">Coins Analyzed</div>
                      <div className="text-2xl font-bold text-[#9D00FF]">{Object.keys(feedback.by_coin || {}).length}</div>
                    </div>
                  </div>

                  {/* By Coin Performance */}
                  {feedback?.by_coin && Object.keys(feedback.by_coin).length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-[#A1A1AA] mb-3">Performance by Coin</h4>
                      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 max-h-60 overflow-y-auto">
                        {Object.entries(feedback.by_coin)
                          .sort((a, b) => (b[1]?.accuracy_rate || 0) - (a[1]?.accuracy_rate || 0))
                          .slice(0, 20)
                          .map(([coin, stats]) => (
                            <div key={coin} className="p-3 bg-[#121212] rounded-lg">
                              <div className="font-bold text-white">{coin}</div>
                              <div className={`text-lg font-data ${getAccuracyColor(stats?.accuracy_rate || 0)}`}>
                                {(stats?.accuracy_rate || 0).toFixed(1)}%
                              </div>
                              <div className="text-xs text-[#A1A1AA]">{stats?.total || 0} predictions</div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions" className="space-y-6">
          {/* Unverified Predictions */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="unverified-predictions-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Clock className="text-[#FFB800]" />
                  Pending Verification ({unverifiedPredictions.length})
                </CardTitle>
                <CardDescription>Predictions awaiting outcome verification</CardDescription>
              </CardHeader>
              <CardContent>
                {unverifiedPredictions.length === 0 ? (
                  <div className="text-center py-8 text-[#A1A1AA]">
                    No pending predictions
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {unverifiedPredictions.map((pred, index) => (
                      <div 
                        key={index} 
                        className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-[#FFB800]/20 flex items-center justify-center">
                            <Target size={20} className="text-[#FFB800]" />
                          </div>
                          <div>
                            <div className="font-bold text-white">{pred.coin}</div>
                            <div className="text-sm text-[#A1A1AA]">{pred.type} • {pred.source_model}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge className="bg-[#FFB800]/20 text-[#FFB800]">
                            {pred.confidence}% confidence
                          </Badge>
                          <div className="text-xs text-[#A1A1AA] mt-1">
                            {new Date(pred.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Verified Predictions */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="recent-predictions-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <CheckCircle className="text-[#00FF94]" />
                  Recent Predictions
                </CardTitle>
                <CardDescription>Latest prediction outcomes</CardDescription>
              </CardHeader>
              <CardContent>
                {recentPredictions.length === 0 ? (
                  <div className="text-center py-8 text-[#A1A1AA]">
                    No recent predictions
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {recentPredictions.map((pred, index) => (
                      <div 
                        key={index} 
                        className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            pred.verified && pred.accuracy_score >= 0.5 
                              ? 'bg-[#00FF94]/20' 
                              : pred.verified 
                                ? 'bg-[#FF0055]/20' 
                                : 'bg-[#1F1F1F]'
                          }`}>
                            {pred.verified ? (
                              (pred.accuracy_score || 0) >= 0.5 
                                ? <CheckCircle size={20} className="text-[#00FF94]" />
                                : <XCircle size={20} className="text-[#FF0055]" />
                            ) : (
                              <Clock size={20} className="text-[#A1A1AA]" />
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-white">{pred.coin}</div>
                            <div className="text-sm text-[#A1A1AA]">{pred.type} • {pred.source_model}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          {pred.verified ? (
                            <div className={`text-lg font-bold ${
                              (pred.accuracy_score || 0) >= 0.5 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                            }`}>
                              {((pred.accuracy_score || 0) * 100).toFixed(0)}%
                            </div>
                          ) : (
                            <Badge className="bg-[#1F1F1F] text-[#A1A1AA]">Pending</Badge>
                          )}
                          <div className="text-xs text-[#A1A1AA]">
                            {new Date(pred.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* How Learning Loop Works */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}>
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="how-it-works">
          <CardHeader>
            <CardTitle>How the Learning Loop Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#9D00FF]">
                <div className="font-bold text-white mb-2">1. Store Predictions</div>
                <p className="text-sm text-[#A1A1AA]">AI models generate predictions with confidence scores and store them for tracking.</p>
              </div>
              <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#007AFF]">
                <div className="font-bold text-white mb-2">2. Record Outcomes</div>
                <p className="text-sm text-[#A1A1AA]">When predictions can be verified, actual outcomes are recorded and accuracy calculated.</p>
              </div>
              <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#00FF94]">
                <div className="font-bold text-white mb-2">3. Analyze Performance</div>
                <p className="text-sm text-[#A1A1AA]">System identifies which models, types, and coins have highest/lowest accuracy.</p>
              </div>
              <div className="p-4 bg-[#121212] rounded-lg border-l-4 border-[#FFB800]">
                <div className="font-bold text-white mb-2">4. Weekly Retraining</div>
                <p className="text-sm text-[#A1A1AA]">Feedback is used in weekly retraining to adjust model weights and improve accuracy.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default AILearningLoop;
