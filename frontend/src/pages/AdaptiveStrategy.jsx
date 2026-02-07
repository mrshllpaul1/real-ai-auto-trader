import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, TrendingUp, TrendingDown, RefreshCw, Activity, Minus,
  Gauge, Target, Shield, Percent, BarChart3, Zap, Clock, Award,
  Cpu, GitBranch, Trophy
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const regimeColors = {
  bull: '#00FF94',
  bear: '#FF0055',
  sideways: '#FFB800',
  unknown: '#A1A1AA'
};

const regimeIcons = {
  bull: TrendingUp,
  bear: TrendingDown,
  sideways: Minus,
  unknown: Activity
};

const AdaptiveStrategy = () => {
  const [strategyStatus, setStrategyStatus] = useState(null);
  const [regimePrediction, setRegimePrediction] = useState(null);
  const [modelComparison, setModelComparison] = useState(null);
  const [mlVsDl, setMlVsDl] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, regimeRes, modelsRes, mlDlRes] = await Promise.all([
        api.get('/strategy/status').catch(() => ({ data: null })),
        api.post('/performance/regime/predict', { symbol: 'BTC' }).catch(() => ({ data: null })),
        api.get('/performance/regime/compare').catch(() => ({ data: null })),
        api.get('/performance/regime/ml-vs-dl').catch(() => ({ data: null }))
      ]);
      
      setStrategyStatus(statusRes.data);
      setRegimePrediction(regimeRes.data);
      setModelComparison(modelsRes.data);
      setMlVsDl(mlDlRes.data);
    } catch (error) {
      console.error('Error loading adaptive strategy:', error);
      toast.error('Failed to load adaptive strategy data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
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

  const currentRegime = regimePrediction?.predicted_regime || strategyStatus?.current_regime || 'unknown';
  const RegimeIcon = regimeIcons[currentRegime] || Activity;
  const regimeColor = regimeColors[currentRegime] || '#A1A1AA';
  const params = strategyStatus?.adapted_params || strategyStatus?.current_params || {};
  const baseParams = strategyStatus?.base_params || {};

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
            ML-powered market regime detection and dynamic parameter adjustment
          </p>
        </div>
        <Button
          onClick={loadData}
          variant="outline"
          className="border-[#1F1F1F]"
          data-testid="refresh-btn"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
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
            <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div 
                  className="w-16 h-16 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: `${regimeColor}20` }}
                >
                  <RegimeIcon size={32} style={{ color: regimeColor }} />
                </div>
                <div>
                  <p className="text-[#A1A1AA] text-sm">Current Market Regime</p>
                  <h2 className="text-4xl font-bold capitalize" style={{ color: regimeColor }}>
                    {currentRegime}
                  </h2>
                  {regimePrediction?.confidence && (
                    <p className="text-sm text-[#A1A1AA]">
                      Confidence: {regimePrediction.confidence.toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-6">
                {regimePrediction?.model_used && (
                  <div className="text-center">
                    <p className="text-xs text-[#A1A1AA]">Active Model</p>
                    <Badge className="bg-[#9D00FF]/20 text-[#9D00FF]">
                      {regimePrediction.model_used}
                    </Badge>
                  </div>
                )}
                {regimePrediction?.model_accuracy && (
                  <div className="text-center">
                    <p className="text-xs text-[#A1A1AA]">Model Accuracy</p>
                    <p className="text-2xl font-data font-bold text-[#00FF94]">
                      {regimePrediction.model_accuracy.toFixed(0)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Adaptive Parameters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Position Size */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Target size={18} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Position Size</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {params.max_position_pct || baseParams.max_position_pct || 10}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-[#A1A1AA]">Base:</span>
              <span className="text-xs text-[#666]">{baseParams.max_position_pct || 10}%</span>
              {params.max_position_pct !== baseParams.max_position_pct && (
                <Badge className="text-xs bg-[#FFB800]/20 text-[#FFB800]">Adapted</Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Stop Loss */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield size={18} className="text-[#FF0055]" />
              <span className="text-sm text-[#A1A1AA]">Stop Loss</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FF0055]">
              {params.stop_loss_pct || baseParams.stop_loss_pct || 15}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-[#A1A1AA]">Base:</span>
              <span className="text-xs text-[#666]">{baseParams.stop_loss_pct || 15}%</span>
            </div>
          </CardContent>
        </Card>

        {/* Take Profit */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Take Profit</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#00FF94]">
              {params.take_profit_pct || baseParams.take_profit_pct || 30}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-[#A1A1AA]">Base:</span>
              <span className="text-xs text-[#666]">{baseParams.take_profit_pct || 30}%</span>
            </div>
          </CardContent>
        </Card>

        {/* Max Exposure */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Gauge size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Max Exposure</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FFB800]">
              {params.max_total_exposure || baseParams.max_total_exposure || 80}%
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-[#A1A1AA]">Base:</span>
              <span className="text-xs text-[#666]">{baseParams.max_total_exposure || 80}%</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ML vs DL Comparison */}
      {mlVsDl && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Trophy className="text-[#FFB800]" />
                ML vs Deep Learning Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <div className="flex items-center gap-2 mb-2">
                    <GitBranch size={16} className="text-[#007AFF]" />
                    <span className="text-sm text-[#A1A1AA]">ML Models</span>
                  </div>
                  <p className="text-2xl font-data font-bold text-white">{mlVsDl.summary?.total_ml_models || 0}</p>
                  <p className="text-xs text-[#A1A1AA]">Avg: {mlVsDl.summary?.ml_avg_accuracy || 0}%</p>
                </div>
                
                <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <div className="flex items-center gap-2 mb-2">
                    <Cpu size={16} className="text-[#9D00FF]" />
                    <span className="text-sm text-[#A1A1AA]">DL Models</span>
                  </div>
                  <p className="text-2xl font-data font-bold text-white">{mlVsDl.summary?.total_dl_models || 0}</p>
                  <p className="text-xs text-[#A1A1AA]">Avg: {mlVsDl.summary?.dl_avg_accuracy || 0}%</p>
                </div>
                
                <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <div className="flex items-center gap-2 mb-2">
                    <Award size={16} className="text-[#FFB800]" />
                    <span className="text-sm text-[#A1A1AA]">Winner</span>
                  </div>
                  <p className={`text-2xl font-bold ${mlVsDl.summary?.winner === 'ML' ? 'text-[#007AFF]' : 'text-[#9D00FF]'}`}>
                    {mlVsDl.summary?.winner || 'N/A'}
                  </p>
                </div>
                
                <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <div className="flex items-center gap-2 mb-2">
                    <Trophy size={16} className="text-[#00FF94]" />
                    <span className="text-sm text-[#A1A1AA]">Best Model</span>
                  </div>
                  <p className="text-lg font-bold text-[#00FF94] truncate">{mlVsDl.summary?.overall_best || 'None'}</p>
                </div>
              </div>
              
              {/* Side by Side Comparison */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* ML Models */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-[#007AFF] flex items-center gap-2">
                    <GitBranch size={16} />
                    Machine Learning
                  </h4>
                  {mlVsDl.ml_models?.map((model) => (
                    <div 
                      key={model.name}
                      className={`p-3 rounded-lg border ${model.is_best ? 'bg-[#007AFF]/10 border-[#007AFF]/50' : 'bg-[#121212] border-[#1F1F1F]'}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{model.name}</span>
                          {model.is_best && <Badge className="text-xs bg-[#00FF94]/20 text-[#00FF94]">Best</Badge>}
                        </div>
                        <span className={`font-data font-bold ${model.accuracy >= 70 ? 'text-[#00FF94]' : 'text-[#FFB800]'}`}>
                          {model.accuracy}%
                        </span>
                      </div>
                      <Progress value={model.accuracy} className="h-1.5" />
                      <p className="text-xs text-[#A1A1AA] mt-1">{model.category}</p>
                    </div>
                  ))}
                </div>
                
                {/* DL Models */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-[#9D00FF] flex items-center gap-2">
                    <Cpu size={16} />
                    Deep Learning
                  </h4>
                  {mlVsDl.dl_models?.map((model) => (
                    <div 
                      key={model.name}
                      className={`p-3 rounded-lg border ${model.is_best ? 'bg-[#9D00FF]/10 border-[#9D00FF]/50' : 'bg-[#121212] border-[#1F1F1F]'}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{model.name}</span>
                          {model.is_best && <Badge className="text-xs bg-[#00FF94]/20 text-[#00FF94]">Best</Badge>}
                        </div>
                        <span className={`font-data font-bold ${model.accuracy >= 70 ? 'text-[#00FF94]' : model.accuracy >= 50 ? 'text-[#FFB800]' : 'text-[#A1A1AA]'}`}>
                          {model.accuracy ? `${model.accuracy}%` : 'N/A'}
                        </span>
                      </div>
                      {model.accuracy && <Progress value={model.accuracy} className="h-1.5" />}
                      <p className="text-xs text-[#A1A1AA] mt-1">{model.category}: {model.description?.slice(0, 50)}...</p>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Recommendation */}
              {mlVsDl.recommendation && (
                <div className="mt-4 p-4 bg-[#00FF94]/10 rounded-lg border border-[#00FF94]/30">
                  <p className="text-sm text-[#00FF94]">
                    <strong>Recommendation:</strong> {mlVsDl.recommendation}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ML Model Comparison */}
      {modelComparison && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="text-[#007AFF]" />
                ML Model Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {modelComparison.models?.map((model, idx) => {
                  const isActive = model.name === modelComparison.best_model;
                  const accuracy = (model.accuracy * 100);
                  
                  return (
                    <div 
                      key={model.name}
                      className={`p-4 rounded-lg border ${
                        isActive 
                          ? 'bg-[#9D00FF]/10 border-[#9D00FF]/50' 
                          : 'bg-[#121212] border-[#1F1F1F]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          {isActive && <Award size={18} className="text-[#FFB800]" />}
                          <span className="text-white font-medium">{model.name}</span>
                          {isActive && (
                            <Badge className="bg-[#00FF94]/20 text-[#00FF94]">Active</Badge>
                          )}
                        </div>
                        <span className={`font-data font-bold ${accuracy >= 70 ? 'text-[#00FF94]' : accuracy >= 50 ? 'text-[#FFB800]' : 'text-[#FF0055]'}`}>
                          {accuracy.toFixed(1)}%
                        </span>
                      </div>
                      <Progress 
                        value={accuracy} 
                        className="h-2"
                      />
                      <div className="flex justify-between mt-2 text-xs text-[#A1A1AA]">
                        <span>Type: {model.type}</span>
                        {model.last_trained && (
                          <span>Trained: {new Date(model.last_trained).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {modelComparison.next_retraining && (
                <div className="mt-4 p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock size={14} className="text-[#A1A1AA]" />
                    <span className="text-[#A1A1AA]">Next scheduled retraining:</span>
                    <span className="text-white">{new Date(modelComparison.next_retraining).toLocaleString()}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Regime Adaptation Rules */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="text-[#FFB800]" />
              Regime Adaptation Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Bull Market */}
              <div className={`p-4 rounded-lg border ${currentRegime === 'bull' ? 'bg-[#00FF94]/10 border-[#00FF94]/50' : 'bg-[#121212] border-[#1F1F1F]'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={20} className="text-[#00FF94]" />
                  <span className="text-[#00FF94] font-bold">Bull Market</span>
                  {currentRegime === 'bull' && <Badge className="bg-[#00FF94]/20 text-[#00FF94]">Active</Badge>}
                </div>
                <ul className="text-sm text-[#A1A1AA] space-y-2">
                  <li>• Position Size: <span className="text-white">+20%</span></li>
                  <li>• Stop Loss: <span className="text-white">Wider (-5%)</span></li>
                  <li>• Take Profit: <span className="text-white">Higher (+50%)</span></li>
                  <li>• Max Exposure: <span className="text-white">90%</span></li>
                  <li>• Min Confidence: <span className="text-white">60%</span></li>
                </ul>
              </div>

              {/* Bear Market */}
              <div className={`p-4 rounded-lg border ${currentRegime === 'bear' ? 'bg-[#FF0055]/10 border-[#FF0055]/50' : 'bg-[#121212] border-[#1F1F1F]'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <TrendingDown size={20} className="text-[#FF0055]" />
                  <span className="text-[#FF0055] font-bold">Bear Market</span>
                  {currentRegime === 'bear' && <Badge className="bg-[#FF0055]/20 text-[#FF0055]">Active</Badge>}
                </div>
                <ul className="text-sm text-[#A1A1AA] space-y-2">
                  <li>• Position Size: <span className="text-white">-40%</span></li>
                  <li>• Stop Loss: <span className="text-white">Tighter (+5%)</span></li>
                  <li>• Take Profit: <span className="text-white">Lower (-30%)</span></li>
                  <li>• Max Exposure: <span className="text-white">50%</span></li>
                  <li>• Min Confidence: <span className="text-white">80%</span></li>
                </ul>
              </div>

              {/* Sideways Market */}
              <div className={`p-4 rounded-lg border ${currentRegime === 'sideways' ? 'bg-[#FFB800]/10 border-[#FFB800]/50' : 'bg-[#121212] border-[#1F1F1F]'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <Minus size={20} className="text-[#FFB800]" />
                  <span className="text-[#FFB800] font-bold">Sideways Market</span>
                  {currentRegime === 'sideways' && <Badge className="bg-[#FFB800]/20 text-[#FFB800]">Active</Badge>}
                </div>
                <ul className="text-sm text-[#A1A1AA] space-y-2">
                  <li>• Position Size: <span className="text-white">-20%</span></li>
                  <li>• Stop Loss: <span className="text-white">Tighter (+3%)</span></li>
                  <li>• Take Profit: <span className="text-white">Lower (-20%)</span></li>
                  <li>• Max Exposure: <span className="text-white">70%</span></li>
                  <li>• Min Confidence: <span className="text-white">70%</span></li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default AdaptiveStrategy;
