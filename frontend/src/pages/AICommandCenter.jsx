import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, Zap, Target, Activity, Play, Square, RefreshCw,
  TrendingUp, BarChart3, Cpu, Layers, Network, Sparkles,
  LineChart, PieChart, AlertTriangle, CheckCircle, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import api, { clearAllCacheAndRefresh } from '../services/api';
import toast from '../utils/toast';
import VisualTrainingProgress from '../components/VisualTrainingProgress';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

// AI Brain Tab - Enhanced AI Dashboard
const AIBrainTab = ({ enhancedStatus, onTrainModel, isTraining }) => (
  <div className="space-y-6">
    {/* Visual Training Progress - Shows when training is active */}
    <VisualTrainingProgress embedded={false} pollInterval={3000} showControls={true} />
    
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
        <CardContent className="pt-4 text-center">
          <Brain className="w-8 h-8 mx-auto mb-2 text-purple-400" />
          <div className="text-2xl font-bold text-white">
            {(enhancedStatus?.accuracy ?? 0).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">AI Accuracy</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <Sparkles className="w-8 h-8 mx-auto mb-2 text-cyan-400" />
          <div className="text-2xl font-bold text-white">
            {enhancedStatus?.predictions_today || 0}
          </div>
          <div className="text-sm text-gray-400">Predictions Today</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <TrendingUp className="w-8 h-8 mx-auto mb-2 text-green-400" />
          <div className="text-2xl font-bold text-white">
            {(enhancedStatus?.win_rate ?? 0).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">Win Rate</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <Layers className="w-8 h-8 mx-auto mb-2 text-orange-400" />
          <div className="text-2xl font-bold text-white">
            {enhancedStatus?.models_active || 0}
          </div>
          <div className="text-sm text-gray-400">Active Models</div>
        </CardContent>
      </Card>
    </div>

    {/* Model Status */}
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Network className="w-5 h-5 text-purple-400" />
          AI Models
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { name: 'Ensemble', status: enhancedStatus?.ensemble_active, accuracy: 78 },
            { name: 'Transformer', status: enhancedStatus?.transformer_active, accuracy: 74 },
            { name: 'RL Agent', status: enhancedStatus?.rl_active, accuracy: 72 },
            { name: 'Regime Predictor', status: enhancedStatus?.regime_active, accuracy: 76 },
            { name: 'Sentiment', status: enhancedStatus?.sentiment_active, accuracy: 68 },
            { name: 'Technical', status: enhancedStatus?.technical_active, accuracy: 70 },
          ].map((model, idx) => (
            <div key={idx} className="p-3 bg-gray-800/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-medium">{model.name}</span>
                <Badge className={model.status ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}>
                  {model.status ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full"
                  style={{ width: `${model.accuracy}%` }}
                />
              </div>
              <div className="text-xs text-gray-400 mt-1">{model.accuracy}% accuracy</div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex gap-3 flex-wrap">
          <Button onClick={() => onTrainModel('all')} className="bg-purple-600 hover:bg-purple-700">
            <Play className="w-4 h-4 mr-2" /> Train All Models
          </Button>
          <Button onClick={() => onTrainModel('fast')} className="bg-cyan-600 hover:bg-cyan-700">
            <Zap className="w-4 h-4 mr-2" /> Fast Train (3-5x)
          </Button>
          <Button onClick={() => window.location.href = '/model-performance'} variant="outline" className="border-gray-600">
            <BarChart3 className="w-4 h-4 mr-2" /> View Performance
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
);

// Tethys AI Tab
const TethysTab = ({ tethysStatus, onToggleTethys }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
        <CardContent className="pt-4 text-center">
          <Cpu className="w-8 h-8 mx-auto mb-2 text-cyan-400" />
          <Badge className={tethysStatus?.is_active ? 'bg-green-500' : 'bg-gray-600'}>
            {tethysStatus?.is_active ? 'ACTIVE' : 'STANDBY'}
          </Badge>
          <div className="text-sm text-gray-400 mt-2">Tethys Status</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <Target className="w-8 h-8 mx-auto mb-2 text-green-400" />
          <div className="text-2xl font-bold text-white">
            {tethysStatus?.signals_generated || 0}
          </div>
          <div className="text-sm text-gray-400">Signals Generated</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <Activity className="w-8 h-8 mx-auto mb-2 text-orange-400" />
          <div className="text-2xl font-bold text-white">
            {(tethysStatus?.confidence ?? 0).toFixed(0)}%
          </div>
          <div className="text-sm text-gray-400">Confidence</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <LineChart className="w-8 h-8 mx-auto mb-2 text-purple-400" />
          <div className="text-2xl font-bold text-white">
            {tethysStatus?.market_regime || 'Unknown'}
          </div>
          <div className="text-sm text-gray-400">Market Regime</div>
        </CardContent>
      </Card>
    </div>

    {/* Tethys Control */}
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-cyan-400" />
          Tethys Trading Engine
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-gray-300">
          Tethys is an advanced AI trading system that combines Rainbow DQN, Transformer encoders, 
          and ensemble models to generate high-confidence trading signals.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Rainbow DQN', value: tethysStatus?.rainbow_dqn_status || 'Ready' },
            { label: 'Transformer', value: tethysStatus?.transformer_status || 'Ready' },
            { label: 'Ensemble', value: tethysStatus?.ensemble_status || 'Ready' },
            { label: 'Risk Manager', value: tethysStatus?.risk_manager || 'Active' },
          ].map((item, idx) => (
            <div key={idx} className="p-2 bg-gray-800/50 rounded text-center">
              <div className="text-xs text-gray-400">{item.label}</div>
              <div className="text-sm text-cyan-400">{item.value}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <Button 
            onClick={onToggleTethys}
            className={tethysStatus?.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-cyan-600 hover:bg-cyan-700'}
          >
            {tethysStatus?.is_active ? <Square className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            {tethysStatus?.is_active ? 'Stop Tethys' : 'Start Tethys'}
          </Button>
          <Button onClick={() => window.location.href = '/ai-learning'} variant="outline" className="border-gray-600">
            <Brain className="w-4 h-4 mr-2" /> AI Learning
          </Button>
        </div>
      </CardContent>
    </Card>

    {/* Recent Signals */}
    {tethysStatus?.recent_signals?.length > 0 && (
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Recent Signals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {tethysStatus.recent_signals.slice(0, 5).map((signal, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/30 rounded">
                <div className="flex items-center gap-2">
                  <Badge className={signal.action === 'BUY' ? 'bg-green-500' : signal.action === 'SELL' ? 'bg-red-500' : 'bg-gray-500'}>
                    {signal.action}
                  </Badge>
                  <span className="text-white">{signal.symbol}</span>
                </div>
                <div className="text-gray-400 text-sm">
                  {(signal?.confidence ?? 0).toFixed(0)}% confidence
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )}
  </div>
);

// Learning Tab
const LearningTab = ({ learningStatus, onTrain }) => (
  <div className="space-y-6">
    {/* Visual Training Progress for Learning Tab */}
    <VisualTrainingProgress embedded={false} pollInterval={3000} showControls={true} />
    
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-orange-500/10 to-yellow-500/10 border-orange-500/20">
        <CardContent className="pt-4 text-center">
          <Brain className="w-8 h-8 mx-auto mb-2 text-orange-400" />
          <div className="text-2xl font-bold text-white">
            {learningStatus?.total_samples || 0}
          </div>
          <div className="text-sm text-gray-400">Learning Samples</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <TrendingUp className="w-8 h-8 mx-auto mb-2 text-green-400" />
          <div className="text-2xl font-bold text-white">
            {(learningStatus?.improvement ?? 0).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">Improvement</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4 text-center">
          <Activity className="w-8 h-8 mx-auto mb-2 text-cyan-400" />
          <div className="text-2xl font-bold text-white">
            {learningStatus?.training_cycles || 0}
          </div>
          <div className="text-sm text-gray-400">Training Cycles</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardContent className="pt-4">
          <Button onClick={onTrain} className="w-full bg-orange-600 hover:bg-orange-700">
            <Play className="w-4 h-4 mr-2" /> Train Now
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
);

const AICommandCenter = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('brain');
  const [loading, setLoading] = useState(true);
  const [enhancedStatus, setEnhancedStatus] = useState(null);
  const [tethysStatus, setTethysStatus] = useState(null);
  const [learningStatus, setLearningStatus] = useState(null);

  const fetchData = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        clearAllCacheAndRefresh();
      }
      const [enhancedRes, tethysRes, learningRes] = await Promise.allSettled([
        api.get('/enhanced-ai/status'),
        api.get('/tethys-train/status'),
        api.get('/learning/status')
      ]);

      if (enhancedRes.status === 'fulfilled') setEnhancedStatus(enhancedRes.value.data);
      if (tethysRes.status === 'fulfilled') setTethysStatus(tethysRes.value.data);
      if (learningRes.status === 'fulfilled') setLearningStatus(learningRes.value.data);
      
      if (forceRefresh) {
        toast.success('Data refreshed');
      }
    } catch (error) {
      console.error('Error loading AI data:', error);
      if (forceRefresh) toast.error('Refresh failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTrainModel = async (mode) => {
    try {
      let response;
      
      if (mode === 'fast') {
        // Fast parallel training with batch processing
        response = await api.post('/training/train-fast', {
          batch_size: 10,
          phases: ["historical", "technical", "gems"]
        });
        
        toast.success('Fast Training Started', {
          description: `Training ${response.data.coin_count || 77} coins in parallel batches. 3-5x faster!`,
          duration: 5000,
        });
      } else {
        // Standard sequential training
        response = await api.post('/training/train-all');
        
        if (response.data.status === 'lightweight_mode') {
          toast.info('Lightweight Mode Active', {
            description: 'Training disabled for deployment efficiency. Models using pre-computed patterns.',
            duration: 6000,
          });
        } else if (response.data.task_id) {
          toast.success('Training Started', {
            description: `Training ${response.data.coin_count || 77} coins. Check Training Progress panel for real-time updates.`,
            duration: 5000,
          });
        } else {
          toast.success('Training Started', {
            description: 'AI models training in background.',
          });
        }
      }
      
      fetchData();
    } catch (error) {
      toast.error('Failed to start training', {
        description: error.response?.data?.detail || 'Please try again later',
      });
    }
  };

  const handleToggleTethys = async () => {
    const isActive = tethysStatus?.is_active;
    const loadingToast = toast.loading(isActive ? 'Stopping Tethys AI...' : 'Starting Tethys AI...');
    
    try {
      if (isActive) {
        await api.post('/tethys-train/stop');
        toast.dismiss(loadingToast);
        toast.ai.stopped('Tethys AI');
      } else {
        await api.post('/tethys-train/start');
        toast.dismiss(loadingToast);
        toast.ai.started('Tethys AI');
      }
      
      // Refresh status after 2 seconds to allow backend to update
      setTimeout(fetchData, 2000);
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to toggle Tethys', {
        description: error.response?.data?.detail || 'Please check system status',
      });
    }
  };

  const handleTrain = async () => {
    const loadingToast = toast.ai.training('Learning Engine');
    try {
      const response = await api.post('/learning/train');
      toast.dismiss(loadingToast);
      toast.success('Learning engine training started', {
        description: 'Check back in a few minutes for results',
        duration: 5000,
      });
      fetchData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to start training', {
        description: error.response?.data?.detail || 'Please try again',
      });
    }
  };

  const tabs = [
    { id: 'brain', label: 'AI Brain', icon: Brain },
    { id: 'tethys', label: 'Tethys AI', icon: Cpu },
    { id: 'learning', label: 'Learning', icon: Sparkles },
  ];

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="p-6 space-y-6" data-testid="ai-command-center">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-8 h-8 text-purple-400" />
            AI Command Center
          </h1>
          <p className="text-gray-400">Unified AI and machine learning control</p>
        </div>
        <Button onClick={() => fetchData(true)} variant="outline" className="border-gray-700">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-800 pb-2 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-purple-500/20 text-purple-400 border-b-2 border-purple-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'brain' && (
          <AIBrainTab enhancedStatus={enhancedStatus} onTrainModel={handleTrainModel} />
        )}
        {activeTab === 'tethys' && (
          <TethysTab tethysStatus={tethysStatus} onToggleTethys={handleToggleTethys} />
        )}
        {activeTab === 'learning' && (
          <LearningTab learningStatus={learningStatus} onTrain={handleTrain} />
        )}
      </motion.div>
    </div>
  );
};

export default AICommandCenter;
