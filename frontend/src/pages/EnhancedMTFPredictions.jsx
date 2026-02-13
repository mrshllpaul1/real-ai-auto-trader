import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, Zap, Target, Activity, Play, RefreshCw, TrendingUp, TrendingDown,
  BarChart3, Layers, Sparkles, AlertTriangle, CheckCircle, Clock,
  Gauge, Heart, Frown, Smile, Meh, Twitter, MessageCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import toast from '../utils/toast';
import TrainingProgress from '../components/TrainingProgress';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

// Fear & Greed Gauge Component
const FearGreedGauge = ({ value, classification }) => {
  const getColor = (val) => {
    if (val <= 25) return 'text-red-500';
    if (val <= 45) return 'text-orange-500';
    if (val <= 55) return 'text-yellow-500';
    if (val <= 75) return 'text-lime-500';
    return 'text-green-500';
  };

  const getIcon = (val) => {
    if (val <= 25) return <Frown className="w-6 h-6" />;
    if (val <= 45) return <Meh className="w-6 h-6" />;
    if (val <= 75) return <Smile className="w-6 h-6" />;
    return <Heart className="w-6 h-6" />;
  };

  return (
    <div className="text-center">
      <div className={`text-4xl font-bold ${getColor(value)}`}>
        {value}
      </div>
      <div className="flex items-center justify-center gap-2 mt-2">
        <span className={getColor(value)}>{getIcon(value)}</span>
        <span className="text-gray-400">{classification}</span>
      </div>
      <Progress value={value} className="mt-3 h-2" />
    </div>
  );
};

// Signal Badge Component
const SignalBadge = ({ signal, confidence }) => {
  const config = {
    BUY: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
    SELL: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
    HOLD: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' }
  };
  const style = config[signal] || config.HOLD;

  return (
    <Badge className={`${style.bg} ${style.text} ${style.border} border px-3 py-1`}>
      {signal === 'BUY' && <TrendingUp className="w-3 h-3 mr-1" />}
      {signal === 'SELL' && <TrendingDown className="w-3 h-3 mr-1" />}
      {signal === 'HOLD' && <Activity className="w-3 h-3 mr-1" />}
      {signal} ({confidence})
    </Badge>
  );
};

// Prediction Card Component
const PredictionCard = ({ prediction }) => {
  const sentiment = prediction.analysis?.sentiment || {};
  const fearGreed = prediction.analysis?.fear_greed || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 hover:border-purple-500/50 transition-all"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500/20 to-cyan-500/20 rounded-full flex items-center justify-center">
            <span className="font-bold text-white">{prediction.symbol?.slice(0, 2)}</span>
          </div>
          <div>
            <div className="font-semibold text-white">{prediction.symbol}</div>
            <div className="text-xs text-gray-400">Model Accuracy: {((prediction?.model_accuracy ?? 0) * 100).toFixed(0)}%</div>
          </div>
        </div>
        <SignalBadge signal={prediction.signal} confidence={prediction.confidence_pct} />
      </div>

      {/* Sentiment Breakdown */}
      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="bg-gray-900/50 rounded p-2">
          <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
            <Twitter className="w-3 h-3" /> Twitter
          </div>
          <Progress value={sentiment.twitter * 100 || 50} className="h-1.5" />
          <div className="text-xs text-gray-500 mt-1">{((sentiment.twitter || 0.5) * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-gray-900/50 rounded p-2">
          <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
            <MessageCircle className="w-3 h-3" /> Reddit
          </div>
          <Progress value={sentiment.reddit * 100 || 50} className="h-1.5" />
          <div className="text-xs text-gray-500 mt-1">{((sentiment.reddit || 0.5) * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* FOMO/Fear Indicators */}
      <div className="flex gap-2 mt-3">
        {sentiment.fomo_score > 0.5 && (
          <Badge className="bg-orange-500/20 text-orange-400 text-xs">
            FOMO: {((sentiment?.fomo_score ?? 0) * 100).toFixed(0)}%
          </Badge>
        )}
        {sentiment.fear_score > 0.5 && (
          <Badge className="bg-red-500/20 text-red-400 text-xs">
            Fear: {((sentiment?.fear_score ?? 0) * 100).toFixed(0)}%
          </Badge>
        )}
      </div>
    </motion.div>
  );
};

// Main Component
const EnhancedMTFPredictions = ({ embedded = false }) => {
  const [trainingStatus, setTrainingStatus] = useState({ status: 'idle' });
  const [predictions, setPredictions] = useState(null);
  const [fearGreed, setFearGreed] = useState({ value: 50, classification: 'Neutral' });
  const [modelInfo, setModelInfo] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingTaskId, setTrainingTaskId] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch all data in parallel
  const fetchData = useCallback(async () => {
    try {
      const [statusRes, modelRes, fgRes] = await Promise.allSettled([
        api.get('/enhanced-mtf-training/status'),
        api.get('/enhanced-mtf-training/model-info'),
        api.get('/enhanced-mtf-training/fear-greed')
      ]);

      if (statusRes.status === 'fulfilled') setTrainingStatus(statusRes.value.data);
      if (modelRes.status === 'fulfilled') setModelInfo(modelRes.value.data);
      if (fgRes.status === 'fulfilled') setFearGreed(fgRes.value.data);

    } catch (err) {
      console.error('Failed to fetch data:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Train model on all Kraken coins (fast mode)
  const handleTrain = async () => {
    setIsTraining(true);
    setTrainingTaskId(null);
    toast.loading('Training on ALL 634 Kraken coins...', { id: 'train' });
    
    try {
      const response = await api.post('/enhanced-mtf-training/train-fast', null, {
        params: { epochs: 100, batch_size: 100 }
      });
      
      // Check if we got a task_id for background tracking
      if (response.data.task_id) {
        setTrainingTaskId(response.data.task_id);
        toast.success('Training started in background...', { id: 'train' });
      } else if (response.data.status === 'completed') {
        toast.success(`Training completed! ${response.data.symbols_trained} coins, Accuracy: ${response.data.accuracy_pct}`, { id: 'train' });
        setIsTraining(false);
        fetchData();
      } else {
        toast.error(`Training failed: ${response.data.error}`, { id: 'train' });
        setIsTraining(false);
      }
    } catch (err) {
      toast.error('Training failed: ' + (err.response?.data?.detail || err.message), { id: 'train' });
      setIsTraining(false);
    }
  };

  const handleTrainingComplete = useCallback((result) => {
    setIsTraining(false);
    setTrainingTaskId(null);
    toast.success(`Training completed! Accuracy: ${result?.result?.accuracy || 'N/A'}`, { id: 'train-complete' });
    fetchData();
  }, [fetchData]);

  // Get predictions for ALL Kraken coins
  const handlePredict = async () => {
    setIsPredicting(true);
    toast.loading('Running predictions on ALL 634 Kraken coins...', { id: 'predict' });
    
    try {
      const response = await api.post('/enhanced-mtf-training/predict-all', {
        symbols: ["all"]
      });
      setPredictions(response.data);
      toast.success(`Predictions complete! ${response.data.total_predictions} coins analyzed`, { id: 'predict' });
    } catch (err) {
      toast.error('Prediction failed: ' + (err.response?.data?.detail || err.message), { id: 'predict' });
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Brain className="w-8 h-8 text-purple-500" />
              Enhanced MTF AI Predictions
            </h1>
            <p className="text-gray-400 mt-1">
              Multi-Timeframe + Sentiment Analysis Model
            </p>
          </div>
          <div className="flex gap-3">
            <Button 
              onClick={handleTrain} 
              disabled={isTraining}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isTraining ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Training 634 coins...</>
              ) : (
                <><Play className="w-4 h-4 mr-2" /> Train All Kraken (634)</>
              )}
            </Button>
            <Button 
              onClick={handlePredict} 
              disabled={isPredicting || modelInfo?.status !== 'ready'}
              variant="outline"
              className="border-cyan-500 text-cyan-400 hover:bg-cyan-500/10"
            >
              {isPredicting ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Predicting...</>
              ) : (
                <><Sparkles className="w-4 h-4 mr-2" /> Predict All (634)</>
              )}
            </Button>
          </div>
        </div>

        {/* Training Progress Indicator */}
        {trainingTaskId && (
          <div className="mb-6">
            <TrainingProgress 
              taskId={trainingTaskId} 
              embedded={true}
              onComplete={handleTrainingComplete}
            />
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
            <CardContent className="pt-4 text-center">
              <Brain className="w-6 h-6 mx-auto mb-2 text-purple-400" />
              <div className="text-2xl font-bold text-white">
                {((modelInfo?.model?.training_info?.accuracy || 0) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-400">Model Accuracy</div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-4 text-center">
              <Layers className="w-6 h-6 mx-auto mb-2 text-cyan-400" />
              <div className="text-2xl font-bold text-white">
                {modelInfo?.model?.feature_info?.total_features || 45}
              </div>
              <div className="text-xs text-gray-400">Total Features</div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-4 text-center">
              <BarChart3 className="w-6 h-6 mx-auto mb-2 text-green-400" />
              <div className="text-2xl font-bold text-white">
                {predictions?.total_predictions || 0}
              </div>
              <div className="text-xs text-gray-400">Predictions</div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-4 text-center">
              <TrendingUp className="w-6 h-6 mx-auto mb-2 text-green-400" />
              <div className="text-2xl font-bold text-green-400">
                {predictions?.buy_signals || 0}
              </div>
              <div className="text-xs text-gray-400">Buy Signals</div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="pt-4 text-center">
              <TrendingDown className="w-6 h-6 mx-auto mb-2 text-red-400" />
              <div className="text-2xl font-bold text-red-400">
                {predictions?.sell_signals || 0}
              </div>
              <div className="text-xs text-gray-400">Sell Signals</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Fear & Greed + Model Info */}
          <div className="space-y-6">
            {/* Fear & Greed Index */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-orange-400" />
                  Fear & Greed Index
                </CardTitle>
              </CardHeader>
              <CardContent>
                <FearGreedGauge 
                  value={fearGreed.value || 50} 
                  classification={fearGreed.classification || 'Neutral'} 
                />
                {fearGreed.trend_7d && (
                  <div className="mt-4 text-center text-sm text-gray-400">
                    7-day trend: {fearGreed.trend_7d > 0 ? '+' : ''}{fearGreed.trend_7d}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Model Info */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Layers className="w-5 h-5 text-purple-400" />
                  Model Features
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center p-2 bg-gray-800/50 rounded">
                  <span className="text-gray-400">Technical Features</span>
                  <Badge className="bg-cyan-500/20 text-cyan-400">
                    {modelInfo?.model?.feature_info?.n_technical || 33}
                  </Badge>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-800/50 rounded">
                  <span className="text-gray-400">Sentiment Features</span>
                  <Badge className="bg-purple-500/20 text-purple-400">
                    {modelInfo?.model?.feature_info?.n_sentiment || 12}
                  </Badge>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-800/50 rounded">
                  <span className="text-gray-400">Timeframes</span>
                  <span className="text-white">1h, 4h, 1D</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-gray-800/50 rounded">
                  <span className="text-gray-400">Status</span>
                  <Badge className={modelInfo?.status === 'ready' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}>
                    {modelInfo?.status === 'ready' ? 'Ready' : 'Not Trained'}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Training Status */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-green-400" />
                  Training Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status</span>
                    <Badge className={
                      trainingStatus.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      trainingStatus.status === 'training' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }>
                      {trainingStatus.status}
                    </Badge>
                  </div>
                  {trainingStatus.last_trained && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Last Trained</span>
                      <span className="text-white text-sm">
                        {new Date(trainingStatus.last_trained).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {trainingStatus.coins_trained > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Coins Trained</span>
                      <span className="text-white">{trainingStatus.coins_trained}</span>
                    </div>
                  )}
                  {trainingStatus.accuracy > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Accuracy</span>
                      <span className="text-green-400">{((trainingStatus?.accuracy ?? 0) * 100).toFixed(1)}%</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Predictions */}
          <div className="lg:col-span-2">
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-cyan-400" />
                    AI Predictions
                  </div>
                  {predictions && (
                    <div className="flex gap-2">
                      <Badge className="bg-green-500/20 text-green-400">
                        {predictions.buy_signals} BUY
                      </Badge>
                      <Badge className="bg-yellow-500/20 text-yellow-400">
                        {predictions.hold_signals} HOLD
                      </Badge>
                      <Badge className="bg-red-500/20 text-red-400">
                        {predictions.sell_signals} SELL
                      </Badge>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!predictions ? (
                  <div className="text-center py-12">
                    <Brain className="w-12 h-12 mx-auto text-gray-600 mb-4" />
                    <p className="text-gray-400">
                      {modelInfo?.status === 'ready' 
                        ? 'Click "Run Predictions" to analyze all coins'
                        : 'Train the model first, then run predictions'}
                    </p>
                  </div>
                ) : (
                  <Tabs defaultValue="all" className="w-full">
                    <TabsList className="mb-4">
                      <TabsTrigger value="all">All ({predictions.total_predictions})</TabsTrigger>
                      <TabsTrigger value="buy">Buy ({predictions.buy_signals})</TabsTrigger>
                      <TabsTrigger value="sell">Sell ({predictions.sell_signals})</TabsTrigger>
                      <TabsTrigger value="hold">Hold ({predictions.hold_signals})</TabsTrigger>
                    </TabsList>

                    <TabsContent value="all" className="space-y-3 max-h-[600px] overflow-y-auto">
                      {predictions.all_predictions?.map((pred, idx) => (
                        <PredictionCard key={idx} prediction={pred} />
                      ))}
                    </TabsContent>

                    <TabsContent value="buy" className="space-y-3 max-h-[600px] overflow-y-auto">
                      {predictions.all_predictions?.filter(p => p.signal === 'BUY').map((pred, idx) => (
                        <PredictionCard key={idx} prediction={pred} />
                      ))}
                      {predictions.buy_signals === 0 && (
                        <div className="text-center py-8 text-gray-400">No buy signals at this time</div>
                      )}
                    </TabsContent>

                    <TabsContent value="sell" className="space-y-3 max-h-[600px] overflow-y-auto">
                      {predictions.all_predictions?.filter(p => p.signal === 'SELL').map((pred, idx) => (
                        <PredictionCard key={idx} prediction={pred} />
                      ))}
                    </TabsContent>

                    <TabsContent value="hold" className="space-y-3 max-h-[600px] overflow-y-auto">
                      {predictions.all_predictions?.filter(p => p.signal === 'HOLD').map((pred, idx) => (
                        <PredictionCard key={idx} prediction={pred} />
                      ))}
                    </TabsContent>
                  </Tabs>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedMTFPredictions;
