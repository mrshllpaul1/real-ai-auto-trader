import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Activity, 
  BarChart3, 
  LineChart,
  AlertTriangle,
  CheckCircle,
  Cpu,
  Target,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const DeepLearningAI = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [multiSignals, setMultiSignals] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [detectingPatterns, setDetectingPatterns] = useState(false);
  const [fetchingSignals, setFetchingSignals] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const coins = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
    { id: 'avalanche-2', name: 'Avalanche', symbol: 'AVAX' },
  ];

  // Timeout wrapper
  const timeoutPromise = (promise, ms = 15000) => {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('Request timed out')), ms))
    ]);
  };

  const loadAIStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await timeoutPromise(api.get('/deep-learning/status'), 10000);
      setAiStatus(response.data);
    } catch (error) {
      console.error('Error loading AI status:', error);
      toast.error('Failed to load AI status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAIStatus();
  }, [loadAIStatus]);

  const getPrediction = async () => {
    try {
      setPredicting(true);
      setPrediction(null);
      toast.loading('Analyzing market data with deep learning...');
      
      const response = await timeoutPromise(
        api.post(`/deep-learning/predict/${selectedCoin}?include_news=true`),
        120000 // 2 minute timeout for training
      );
      
      toast.dismiss();
      setPrediction(response.data);
      toast.success('AI prediction generated!');
    } catch (error) {
      toast.dismiss();
      if (error.message === 'Request timed out') {
        toast.error('Prediction is taking too long. The AI model may be training.');
      } else {
        toast.error('Failed to generate prediction');
      }
      console.error('Prediction error:', error);
    } finally {
      setPredicting(false);
    }
  };

  const detectPatterns = async () => {
    try {
      setDetectingPatterns(true);
      setPatterns(null);
      toast.loading('Detecting chart patterns...');
      
      const response = await timeoutPromise(
        api.post(`/deep-learning/detect-patterns/${selectedCoin}?window_days=30`),
        30000
      );
      
      toast.dismiss();
      setPatterns(response.data);
      toast.success('Patterns detected!');
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to detect patterns');
      console.error('Pattern detection error:', error);
    } finally {
      setDetectingPatterns(false);
    }
  };

  const getMultiSignals = async () => {
    try {
      setFetchingSignals(true);
      setMultiSignals(null);
      toast.loading('Getting AI signals for multiple coins...');
      
      const response = await timeoutPromise(
        api.post('/deep-learning/multi-signal', {
          coin_ids: ['bitcoin', 'ethereum', 'solana', 'cardano', 'avalanche-2']
        }),
        180000 // 3 minute timeout
      );
      
      toast.dismiss();
      setMultiSignals(response.data);
      toast.success(`Generated signals for ${response.data.count} coins!`);
    } catch (error) {
      toast.dismiss();
      if (error.message === 'Request timed out') {
        toast.error('Signal generation timed out. AI models may be training.');
      } else {
        toast.error('Failed to get multi-coin signals');
      }
      console.error('Multi-signal error:', error);
    } finally {
      setFetchingSignals(false);
    }
  };

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'STRONG_BUY': return '#00FF94';
      case 'BUY': return '#00CC77';
      case 'STRONG_SELL': return '#FF0055';
      case 'SELL': return '#FF4444';
      case 'HOLD': return '#007AFF';
      default: return '#A1A1AA';
    }
  };

  const getSignalBg = (signal) => {
    switch (signal) {
      case 'STRONG_BUY': return 'bg-[#00FF94]/10 border-[#00FF94]/30';
      case 'BUY': return 'bg-[#00CC77]/10 border-[#00CC77]/30';
      case 'STRONG_SELL': return 'bg-[#FF0055]/10 border-[#FF0055]/30';
      case 'SELL': return 'bg-[#FF4444]/10 border-[#FF4444]/30';
      case 'HOLD': return 'bg-[#007AFF]/10 border-[#007AFF]/30';
      default: return 'bg-[#1F1F1F] border-[#1F1F1F]';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Initializing Deep Learning AI...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="deep-learning-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2 flex items-center gap-4" data-testid="page-title">
            <Cpu size={48} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Deep Learning</span> AI
          </h1>
          <p className="text-[#A1A1AA]">
            Neural network-powered price predictions and pattern recognition
          </p>
        </div>
        <Button
          onClick={loadAIStatus}
          variant="outline"
          className="border-[#9D00FF] text-[#9D00FF] hover:bg-[#9D00FF]/10 rounded-full"
          data-testid="refresh-status-btn"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh Status
        </Button>
      </motion.div>

      {/* AI Status Overview */}
      {aiStatus && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="ai-status-card">
            <CardHeader>
              <CardTitle className="text-2xl font-heading flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#00FF94] animate-pulse" />
                AI System Status: {aiStatus.status}
              </CardTitle>
              <CardDescription>TensorFlow {aiStatus.models?.tensorflow_version} • Ensemble AI Active</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain size={18} className="text-[#9D00FF]" />
                    <span className="text-sm text-[#A1A1AA]">LSTM Model</span>
                  </div>
                  <div className="text-xl font-bold text-white">
                    {aiStatus.models?.lstm_price_predictor?.trained ? 'Trained' : 'Ready'}
                  </div>
                  <div className="text-xs text-[#A1A1AA] mt-1">
                    {aiStatus.models?.lstm_price_predictor?.sequence_length}-day lookback
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#00FF94]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity size={18} className="text-[#00FF94]" />
                    <span className="text-sm text-[#A1A1AA]">Sentiment</span>
                  </div>
                  <div className="text-xl font-bold text-white">
                    Active
                  </div>
                  <div className="text-xs text-[#A1A1AA] mt-1">
                    {aiStatus.models?.sentiment_analyzer?.bullish_keywords + aiStatus.models?.sentiment_analyzer?.bearish_keywords} keywords
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#007AFF]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <LineChart size={18} className="text-[#007AFF]" />
                    <span className="text-sm text-[#A1A1AA]">Pattern CNN</span>
                  </div>
                  <div className="text-xl font-bold text-white">
                    Active
                  </div>
                  <div className="text-xs text-[#A1A1AA] mt-1">
                    {aiStatus.models?.pattern_recognizer?.patterns_supported?.length} patterns
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#FF9500]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap size={18} className="text-[#FF9500]" />
                    <span className="text-sm text-[#A1A1AA]">Ensemble</span>
                  </div>
                  <div className="text-xl font-bold text-white">
                    {aiStatus.models?.ensemble_ready ? 'Ready' : 'Initializing'}
                  </div>
                  <div className="text-xs text-[#A1A1AA] mt-1">
                    All models combined
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="overview" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            Overview
          </TabsTrigger>
          <TabsTrigger value="prediction" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            Price Prediction
          </TabsTrigger>
          <TabsTrigger value="patterns" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            Pattern Detection
          </TabsTrigger>
          <TabsTrigger value="signals" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            Multi-Coin Signals
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="lstm-info-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Brain className="text-[#9D00FF]" />
                  LSTM Price Predictor
                </CardTitle>
                <CardDescription>Long Short-Term Memory neural network</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-[#A1A1AA] text-sm">
                  Uses 60 days of historical price data to predict future prices. The LSTM model
                  captures temporal patterns and trends in cryptocurrency markets.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Architecture</div>
                    <div className="text-sm font-bold text-white">3-Layer LSTM</div>
                  </div>
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Prediction</div>
                    <div className="text-sm font-bold text-white">5-Day Horizon</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="sentiment-info-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Activity className="text-[#00FF94]" />
                  Sentiment Analyzer
                </CardTitle>
                <CardDescription>News and social sentiment analysis</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-[#A1A1AA] text-sm">
                  Analyzes crypto news headlines to determine market sentiment. Uses keyword
                  matching and neural networks for classification.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Bullish Keywords</div>
                    <div className="text-sm font-bold text-[#00FF94]">
                      {aiStatus?.models?.sentiment_analyzer?.bullish_keywords || 20}
                    </div>
                  </div>
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Bearish Keywords</div>
                    <div className="text-sm font-bold text-[#FF0055]">
                      {aiStatus?.models?.sentiment_analyzer?.bearish_keywords || 20}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="pattern-info-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <BarChart3 className="text-[#007AFF]" />
                  Pattern Recognizer
                </CardTitle>
                <CardDescription>CNN-based chart pattern detection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-[#A1A1AA] text-sm">
                  Identifies technical chart patterns like double tops, triangles, and flags
                  using convolutional neural networks.
                </p>
                <div className="flex flex-wrap gap-2">
                  {aiStatus?.models?.pattern_recognizer?.patterns_supported?.slice(0, 6).map((pattern) => (
                    <Badge 
                      key={pattern} 
                      variant="outline" 
                      className="border-[#007AFF]/30 text-[#007AFF] text-xs"
                    >
                      {pattern.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="ensemble-info-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Zap className="text-[#FF9500]" />
                  Ensemble Trading AI
                </CardTitle>
                <CardDescription>Combined AI for trading signals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-[#A1A1AA] text-sm">
                  Combines all AI models with weighted scoring: Price prediction (40%),
                  Sentiment (25%), Patterns (20%), Technical (15%).
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Signal Types</div>
                    <div className="text-sm font-bold text-white">BUY/SELL/HOLD</div>
                  </div>
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">Confidence</div>
                    <div className="text-sm font-bold text-white">50-95%</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Price Prediction Tab */}
        <TabsContent value="prediction">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="prediction-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Target className="text-[#9D00FF]" />
                AI Price Prediction
              </CardTitle>
              <CardDescription>
                Get deep learning-powered price predictions with sentiment analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                  <SelectTrigger className="w-full sm:w-[200px] bg-[#121212] border-[#1F1F1F]" data-testid="coin-selector">
                    <SelectValue placeholder="Select coin" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                    {coins.map((coin) => (
                      <SelectItem key={coin.id} value={coin.id}>
                        {coin.name} ({coin.symbol})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={getPrediction}
                  className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full"
                  disabled={predicting}
                  data-testid="get-prediction-btn"
                >
                  {predicting ? (
                    <>
                      <Loader2 size={16} className="mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain size={16} className="mr-2" />
                      Get AI Prediction
                    </>
                  )}
                </Button>
              </div>

              {predicting && (
                <div className="p-6 bg-[#121212] rounded-lg border border-[#9D00FF]/20 text-center">
                  <Loader2 size={48} className="mx-auto mb-4 animate-spin text-[#9D00FF]" />
                  <p className="text-[#A1A1AA]">
                    Deep learning model is analyzing {coins.find(c => c.id === selectedCoin)?.name}...
                  </p>
                  <p className="text-xs text-[#666] mt-2">
                    This may take 1-2 minutes if the model needs training
                  </p>
                </div>
              )}

              {prediction && !predicting && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                  data-testid="prediction-result"
                >
                  {/* Main Signal */}
                  <div className={`p-6 rounded-lg border ${getSignalBg(prediction.final_signal)}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {prediction.action === 'BUY' ? (
                          <TrendingUp size={32} style={{ color: getSignalColor(prediction.final_signal) }} />
                        ) : prediction.action === 'SELL' ? (
                          <TrendingDown size={32} style={{ color: getSignalColor(prediction.final_signal) }} />
                        ) : (
                          <Activity size={32} style={{ color: getSignalColor(prediction.final_signal) }} />
                        )}
                        <div>
                          <h3 className="text-2xl font-bold" style={{ color: getSignalColor(prediction.final_signal) }}>
                            {prediction.final_signal?.replace(/_/g, ' ')}
                          </h3>
                          <p className="text-[#A1A1AA]">
                            {coins.find(c => c.id === prediction.coin_id)?.name || prediction.coin_id}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-[#A1A1AA]">Confidence</div>
                        <div className="text-3xl font-bold font-data" style={{ color: getSignalColor(prediction.final_signal) }}>
                          {prediction.confidence?.toFixed(0)}%
                        </div>
                      </div>
                    </div>

                    {/* Price Info */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="p-3 bg-black/30 rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Current Price</div>
                        <div className="text-lg font-bold text-white font-data">
                          ${prediction.current_price?.toLocaleString()}
                        </div>
                      </div>
                      {prediction.components?.price_prediction?.predicted_prices && (
                        <div className="p-3 bg-black/30 rounded-lg">
                          <div className="text-xs text-[#A1A1AA]">Predicted (5 days)</div>
                          <div className={`text-lg font-bold font-data ${
                            prediction.components.price_prediction.predicted_change_pct > 0 
                              ? 'text-[#00FF94]' 
                              : 'text-[#FF0055]'
                          }`}>
                            ${prediction.components.price_prediction.predicted_prices[4]?.toLocaleString()}
                            <span className="text-sm ml-2">
                              ({prediction.components.price_prediction.predicted_change_pct > 0 ? '+' : ''}
                              {prediction.components.price_prediction.predicted_change_pct?.toFixed(2)}%)
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* AI Reasoning */}
                    {prediction.reasoning?.length > 0 && (
                      <div className="p-3 bg-black/30 rounded-lg">
                        <div className="text-xs text-[#A1A1AA] mb-2">AI Reasoning</div>
                        <ul className="space-y-1">
                          {prediction.reasoning.map((reason, i) => (
                            <li key={i} className="text-sm text-white flex items-center gap-2">
                              <CheckCircle size={14} className="text-[#9D00FF]" />
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Components Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Price Prediction Component */}
                    {prediction.components?.price_prediction && (
                      <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                          <Brain size={16} className="text-[#9D00FF]" />
                          LSTM Prediction
                        </h4>
                        <div className={`text-lg font-bold ${
                          prediction.components.price_prediction.trend === 'bullish' 
                            ? 'text-[#00FF94]' 
                            : prediction.components.price_prediction.trend === 'bearish'
                            ? 'text-[#FF0055]'
                            : 'text-[#A1A1AA]'
                        }`}>
                          {prediction.components.price_prediction.trend?.toUpperCase()}
                        </div>
                        <div className="text-sm text-[#A1A1AA]">
                          {prediction.components.price_prediction.prediction_horizon_days}-day forecast
                        </div>
                      </div>
                    )}

                    {/* Sentiment Component */}
                    {prediction.components?.sentiment && (
                      <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                          <Activity size={16} className="text-[#00FF94]" />
                          Sentiment Analysis
                        </h4>
                        <div className={`text-lg font-bold ${
                          prediction.components.sentiment.overall_sentiment === 'bullish' 
                            ? 'text-[#00FF94]' 
                            : prediction.components.sentiment.overall_sentiment === 'bearish'
                            ? 'text-[#FF0055]'
                            : 'text-[#A1A1AA]'
                        }`}>
                          {prediction.components.sentiment.overall_sentiment?.toUpperCase()}
                        </div>
                        <div className="text-sm text-[#A1A1AA]">
                          {prediction.components.sentiment.news_analyzed || 0} news analyzed
                        </div>
                      </div>
                    )}

                    {/* Pattern Component */}
                    {prediction.components?.pattern && (
                      <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                          <BarChart3 size={16} className="text-[#007AFF]" />
                          Pattern Detected
                        </h4>
                        <div className="text-lg font-bold text-[#007AFF]">
                          {prediction.components.pattern.pattern?.replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div className="text-sm text-[#A1A1AA]">
                          {prediction.components.pattern.confidence?.toFixed(0)}% confidence
                        </div>
                      </div>
                    )}

                    {/* Technical Component */}
                    {prediction.components?.technical && (
                      <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                          <LineChart size={16} className="text-[#FF9500]" />
                          Technical Analysis
                        </h4>
                        <div className={`text-lg font-bold ${
                          prediction.components.technical.signal === 'bullish' 
                            ? 'text-[#00FF94]' 
                            : prediction.components.technical.signal === 'bearish'
                            ? 'text-[#FF0055]'
                            : 'text-[#A1A1AA]'
                        }`}>
                          RSI: {prediction.components.technical.rsi?.toFixed(0)}
                        </div>
                        <div className="text-sm text-[#A1A1AA]">
                          Price {prediction.components.technical.price_vs_sma} SMA
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pattern Detection Tab */}
        <TabsContent value="patterns">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="patterns-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <BarChart3 className="text-[#007AFF]" />
                Chart Pattern Detection
              </CardTitle>
              <CardDescription>
                AI identifies technical chart patterns from price data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                  <SelectTrigger className="w-full sm:w-[200px] bg-[#121212] border-[#1F1F1F]">
                    <SelectValue placeholder="Select coin" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                    {coins.map((coin) => (
                      <SelectItem key={coin.id} value={coin.id}>
                        {coin.name} ({coin.symbol})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={detectPatterns}
                  className="bg-[#007AFF] hover:bg-[#0066DD] text-white rounded-full"
                  disabled={detectingPatterns}
                  data-testid="detect-patterns-btn"
                >
                  {detectingPatterns ? (
                    <>
                      <Loader2 size={16} className="mr-2 animate-spin" />
                      Detecting...
                    </>
                  ) : (
                    <>
                      <BarChart3 size={16} className="mr-2" />
                      Detect Patterns
                    </>
                  )}
                </Button>
              </div>

              {patterns && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                  data-testid="patterns-result"
                >
                  <div className={`p-6 rounded-lg border ${
                    patterns.patterns?.is_bullish 
                      ? 'bg-[#00FF94]/10 border-[#00FF94]/30' 
                      : patterns.patterns?.is_bearish
                      ? 'bg-[#FF0055]/10 border-[#FF0055]/30'
                      : 'bg-[#121212] border-[#1F1F1F]'
                  }`}>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-white">
                          {patterns.patterns?.pattern?.replace(/_/g, ' ').toUpperCase() || 'No Pattern'}
                        </h3>
                        <p className="text-[#A1A1AA]">
                          {coins.find(c => c.id === patterns.coin_id)?.name} • {patterns.prices_analyzed} prices analyzed
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-[#A1A1AA]">Confidence</div>
                        <div className={`text-3xl font-bold font-data ${
                          patterns.patterns?.is_bullish ? 'text-[#00FF94]' : 
                          patterns.patterns?.is_bearish ? 'text-[#FF0055]' : 'text-[#A1A1AA]'
                        }`}>
                          {patterns.patterns?.confidence?.toFixed(0)}%
                        </div>
                      </div>
                    </div>

                    {patterns.patterns?.all_patterns?.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-sm text-[#A1A1AA]">All Patterns Detected:</div>
                        <div className="flex flex-wrap gap-2">
                          {patterns.patterns.all_patterns.map((p, i) => (
                            <Badge 
                              key={i}
                              className={`${
                                p.name.includes('bullish') || p.name.includes('bottom') || p.name.includes('ascending')
                                  ? 'bg-[#00FF94]/20 text-[#00FF94]'
                                  : 'bg-[#FF0055]/20 text-[#FF0055]'
                              }`}
                            >
                              {p.name.replace(/_/g, ' ')} ({p.confidence}%)
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Multi-Coin Signals Tab */}
        <TabsContent value="signals">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="signals-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-3">
                    <Zap className="text-[#FF9500]" />
                    Multi-Coin AI Signals
                  </CardTitle>
                  <CardDescription>
                    Get ensemble AI trading signals for top cryptocurrencies
                  </CardDescription>
                </div>
                <Button
                  onClick={getMultiSignals}
                  className="bg-[#FF9500] hover:bg-[#E68600] text-white rounded-full"
                  disabled={fetchingSignals}
                  data-testid="get-signals-btn"
                >
                  {fetchingSignals ? (
                    <>
                      <Loader2 size={16} className="mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Zap size={16} className="mr-2" />
                      Get All Signals
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {fetchingSignals && (
                <div className="p-6 bg-[#121212] rounded-lg border border-[#FF9500]/20 text-center">
                  <Loader2 size={48} className="mx-auto mb-4 animate-spin text-[#FF9500]" />
                  <p className="text-[#A1A1AA]">
                    Analyzing multiple coins with deep learning...
                  </p>
                  <p className="text-xs text-[#666] mt-2">
                    This may take 2-3 minutes for all coins
                  </p>
                </div>
              )}

              {multiSignals && !fetchingSignals && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-4"
                  data-testid="signals-result"
                >
                  {/* Top Pick */}
                  {multiSignals.top_pick && (
                    <div className={`p-6 rounded-lg border ${getSignalBg(multiSignals.top_pick.final_signal)}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle size={20} style={{ color: getSignalColor(multiSignals.top_pick.final_signal) }} />
                        <span className="text-sm font-bold text-white">TOP PICK</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-2xl font-bold" style={{ color: getSignalColor(multiSignals.top_pick.final_signal) }}>
                            {coins.find(c => c.id === multiSignals.top_pick.coin_id)?.name || multiSignals.top_pick.coin_id}
                          </h3>
                          <p className="text-lg font-bold" style={{ color: getSignalColor(multiSignals.top_pick.final_signal) }}>
                            {multiSignals.top_pick.final_signal?.replace(/_/g, ' ')}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-[#A1A1AA]">Confidence</div>
                          <div className="text-3xl font-bold font-data" style={{ color: getSignalColor(multiSignals.top_pick.final_signal) }}>
                            {multiSignals.top_pick.confidence?.toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* All Signals */}
                  <div className="space-y-3">
                    {multiSignals.signals?.map((signal, i) => (
                      <div
                        key={signal.coin_id}
                        className={`p-4 rounded-lg border ${getSignalBg(signal.final_signal)} flex items-center justify-between`}
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-[#1F1F1F] flex items-center justify-center">
                            <span className="font-bold text-white">#{i + 1}</span>
                          </div>
                          <div>
                            <h4 className="font-bold text-white">
                              {coins.find(c => c.id === signal.coin_id)?.name || signal.coin_id}
                            </h4>
                            <p className="text-sm" style={{ color: getSignalColor(signal.final_signal) }}>
                              {signal.final_signal?.replace(/_/g, ' ')}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold font-data" style={{ color: getSignalColor(signal.final_signal) }}>
                            {signal.confidence?.toFixed(0)}%
                          </div>
                          {signal.score !== undefined && (
                            <div className="text-xs text-[#A1A1AA]">
                              Score: {signal.score?.toFixed(1)}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {!multiSignals && !fetchingSignals && (
                <div className="text-center py-12">
                  <Zap size={48} className="mx-auto mb-4 text-[#FF9500] opacity-50" />
                  <p className="text-[#A1A1AA]">
                    Click "Get All Signals" to analyze multiple coins with deep learning
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Warning Notice */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#FF9500]/5 border-[#FF9500]/20" data-testid="warning-card">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-[#FF9500] mt-1 flex-shrink-0" size={20} />
              <div>
                <h4 className="font-bold text-[#FF9500] mb-1">AI Model Training Notice</h4>
                <p className="text-sm text-[#A1A1AA]">
                  Deep learning predictions may take 1-2 minutes if the model needs to train on new data.
                  The LSTM model learns from the latest price data to provide more accurate predictions.
                  For best results, allow the model to complete training before making trading decisions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default DeepLearningAI;
