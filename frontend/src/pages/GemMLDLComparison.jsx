import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, Cpu, Sparkles, TrendingUp, Trophy, RefreshCw, 
  Zap, Target, BarChart3, Layers, Activity, Award,
  ChevronRight, Play, Loader2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import TrainingProgress from '../components/TrainingProgress';

const GemMLDLComparison = ({ embedded = false }) => {
  const [comparison, setComparison] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [scanResults, setScanResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [trainingTaskId, setTrainingTaskId] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [compRes, infoRes, statusRes] = await Promise.all([
        api.get('/gems/ml-dl/compare').catch(() => ({ data: null })),
        api.get('/gems/ml-dl/model-info').catch(() => ({ data: null })),
        api.get('/gems/ml-dl/status').catch(() => ({ data: null }))
      ]);
      
      setComparison(compRes.data);
      setModelInfo(infoRes.data);
      setTrainingStatus(statusRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleTrainingComplete = useCallback((result) => {
    setTraining(false);
    setTrainingTaskId(null);
    loadData();
    toast.success('ML/DL training complete!');
  }, [loadData]);

  const handleTrain = async () => {
    try {
      setTraining(true);
      setTrainingTaskId(null);
      const response = await api.post('/gems/ml-dl/train', {});
      
      // Set task ID for progress tracking
      if (response.data.task_id) {
        setTrainingTaskId(response.data.task_id);
        toast.success('Training started! Check progress in the Training Progress panel.');
      } else {
        toast.success('Training started! This may take a few minutes.');
        // Fallback polling for old API
        const pollInterval = setInterval(async () => {
          try {
            const res = await api.get('/gems/ml-dl/status');
            setTrainingStatus(res.data);
            
            if (!res.data.running) {
              clearInterval(pollInterval);
              setTraining(false);
              loadData();
              toast.success('Training complete!');
            }
          } catch (e) {
            clearInterval(pollInterval);
            setTraining(false);
          }
        }, 5000);
      }
    } catch (error) {
      toast.error('Failed to start training');
      setTraining(false);
    }
  };

  const handleScan = async () => {
    try {
      setScanning(true);
      const res = await api.post('/gems/ml-dl/scan', {});
      setScanResults(res.data);
      toast.success(`Scanned ${res.data.count} coins`);
    } catch (error) {
      toast.error('Scan failed - models may not be trained');
    } finally {
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#050505]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading ML/DL Comparison...</p>
        </div>
      </div>
    );
  }

  const isTrained = trainingStatus?.is_trained;
  const mlModels = comparison?.ml_ranking || [];
  const dlModels = comparison?.dl_ranking || [];
  const overallRanking = comparison?.overall_ranking || [];

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="gem-ml-dl-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/20 border border-[#9D00FF]/30">
                <Brain size={32} className="text-[#9D00FF]" />
              </div>
              <span className="text-white">ML vs DL</span>
              <span className="bg-gradient-to-r from-[#FFB800] to-[#FF6B00] bg-clip-text text-transparent">Gem Prediction</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Compare Machine Learning and Deep Learning models for hidden gem detection
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleTrain}
              disabled={training}
              className="bg-[#9D00FF] hover:bg-[#9D00FF]/80"
              data-testid="train-btn"
            >
              {training ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <Play size={16} className="mr-2" />
              )}
              {training ? 'Training...' : 'Train Models'}
            </Button>
            <Button
              onClick={handleScan}
              disabled={scanning || !isTrained}
              variant="outline"
              className="border-[#1F1F1F]"
              data-testid="scan-btn"
            >
              {scanning ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <Target size={16} className="mr-2" />
              )}
              Scan Gems
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
        </div>
      </motion.div>

      {/* Training Status Banner */}
      {trainingStatus?.running && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-6"
        >
          <Card className="bg-[#9D00FF]/10 border-[#9D00FF]/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Loader2 className="animate-spin text-[#9D00FF]" />
                <div className="flex-1">
                  <p className="text-[#9D00FF] font-medium">{trainingStatus.message}</p>
                  <p className="text-xs text-[#A1A1AA]">Started: {trainingStatus.started_at}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Not Trained Warning */}
      {!isTrained && !trainingStatus?.running && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6"
        >
          <Card className="bg-[#FFB800]/10 border-[#FFB800]/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Zap className="text-[#FFB800]" />
                <div>
                  <p className="text-[#FFB800] font-medium">Models not trained</p>
                  <p className="text-xs text-[#A1A1AA]">Click &quot;Train Models&quot; to start training all ML and DL models</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Winner Card */}
      {comparison?.ml_vs_dl && isTrained && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <Card className={`border-2 ${comparison.ml_vs_dl.winner === 'ML' ? 'border-[#00FF94] bg-[#00FF94]/5' : 'border-[#9D00FF] bg-[#9D00FF]/5'}`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${comparison.ml_vs_dl.winner === 'ML' ? 'bg-[#00FF94]/20' : 'bg-[#9D00FF]/20'}`}>
                    <Trophy size={32} className={comparison.ml_vs_dl.winner === 'ML' ? 'text-[#00FF94]' : 'text-[#9D00FF]'} />
                  </div>
                  <div>
                    <p className="text-[#A1A1AA] text-sm">Best Approach for Gem Detection</p>
                    <h2 className={`text-3xl font-bold ${comparison.ml_vs_dl.winner === 'ML' ? 'text-[#00FF94]' : 'text-[#9D00FF]'}`}>
                      {comparison.ml_vs_dl.winner === 'ML' ? 'Machine Learning' : 'Deep Learning'} Wins!
                    </h2>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex gap-8">
                    <div>
                      <p className="text-xs text-[#A1A1AA]">ML Average</p>
                      <p className="text-2xl font-data font-bold text-[#00FF94]">{comparison.ml_vs_dl.ml_avg_accuracy}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-[#A1A1AA]">DL Average</p>
                      <p className="text-2xl font-data font-bold text-[#9D00FF]">{comparison.ml_vs_dl.dl_avg_accuracy}%</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Model Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* ML Models */}
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-[#00FF94]">
                <BarChart3 className="text-[#00FF94]" />
                Machine Learning Models
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {mlModels.length === 0 ? (
                <p className="text-[#A1A1AA] text-center py-8">Train models to see comparison</p>
              ) : (
                mlModels.map((model, idx) => (
                  <div key={model.model} className="p-4 rounded-lg bg-[#111] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={idx === 0 ? 'bg-[#FFB800]/20 text-[#FFB800]' : 'bg-[#1F1F1F] text-[#A1A1AA]'}>
                          #{model.rank}
                        </Badge>
                        <span className="text-white font-medium capitalize">
                          {model.model.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="text-[#00FF94] font-data font-bold">{model.accuracy}%</span>
                    </div>
                    <Progress value={model.accuracy} className="h-2 bg-[#1F1F1F]" />
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* DL Models */}
        <motion.div
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-[#9D00FF]">
                <Cpu className="text-[#9D00FF]" />
                Deep Learning Models
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {dlModels.length === 0 ? (
                <p className="text-[#A1A1AA] text-center py-8">Train models to see comparison</p>
              ) : (
                dlModels.map((model, idx) => (
                  <div key={model.model} className="p-4 rounded-lg bg-[#111] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={idx === 0 ? 'bg-[#FFB800]/20 text-[#FFB800]' : 'bg-[#1F1F1F] text-[#A1A1AA]'}>
                          #{model.rank}
                        </Badge>
                        <span className="text-white font-medium uppercase">
                          {model.model.replace('_', '-')}
                        </span>
                      </div>
                      <span className="text-[#9D00FF] font-data font-bold">{model.accuracy}%</span>
                    </div>
                    <Progress value={model.accuracy} className="h-2 bg-[#1F1F1F]" />
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Overall Ranking */}
      {overallRanking.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Award className="text-[#FFB800]" />
                Overall Model Ranking
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {overallRanking.slice(0, 8).map((model, idx) => (
                  <div 
                    key={model.model} 
                    className={`p-4 rounded-lg border ${
                      idx === 0 
                        ? 'bg-gradient-to-br from-[#FFB800]/10 to-transparent border-[#FFB800]/30' 
                        : 'bg-[#111] border-[#1F1F1F]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {idx === 0 && <Trophy size={16} className="text-[#FFB800]" />}
                        <span className={`text-sm font-bold ${idx === 0 ? 'text-[#FFB800]' : 'text-[#A1A1AA]'}`}>
                          #{model.rank}
                        </span>
                      </div>
                      <Badge className={model.type === 'ML' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#9D00FF]/20 text-[#9D00FF]'}>
                        {model.type}
                      </Badge>
                    </div>
                    <p className="text-white font-medium capitalize mb-1">
                      {model.model.replace('_', ' ')}
                    </p>
                    <p className="text-2xl font-data font-bold text-white">{model.accuracy}%</p>
                    <p className="text-xs text-[#A1A1AA] mt-1">{model.category}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Scan Results */}
      <AnimatePresence>
        {scanResults && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
          >
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Sparkles className="text-[#FFB800]" />
                  Gem Scan Results
                  <Badge className="ml-2 bg-[#9D00FF]/20 text-[#9D00FF]">
                    Model: {scanResults.best_model}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {scanResults.gems?.slice(0, 9).map((gem, idx) => {
                    const gemColors = {
                      'moonshot': { bg: 'bg-[#FF6B00]/20', text: 'text-[#FF6B00]', border: 'border-[#FF6B00]/30' },
                      'high_potential': { bg: 'bg-[#FFB800]/20', text: 'text-[#FFB800]', border: 'border-[#FFB800]/30' },
                      'likely_gem': { bg: 'bg-[#00FF94]/20', text: 'text-[#00FF94]', border: 'border-[#00FF94]/30' },
                      'potential': { bg: 'bg-[#9D00FF]/20', text: 'text-[#9D00FF]', border: 'border-[#9D00FF]/30' },
                      'no_gem': { bg: 'bg-[#1F1F1F]', text: 'text-[#A1A1AA]', border: 'border-[#1F1F1F]' }
                    };
                    const colors = gemColors[gem.prediction] || gemColors['no_gem'];
                    
                    return (
                      <div 
                        key={gem.coin_id} 
                        className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-white font-bold text-lg">{gem.symbol}</span>
                          <Badge className={`${colors.bg} ${colors.text}`}>
                            {gem.prediction.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-[#A1A1AA]">Gem Score</span>
                            <span className="text-white font-data">{gem.gem_score}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-[#A1A1AA]">Confidence</span>
                            <span className="text-white font-data">{gem.confidence}%</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-[#A1A1AA]">Consensus</span>
                            <span className="text-white font-data">{gem.consensus?.agreement}%</span>
                          </div>
                          <div className="flex gap-2 mt-2">
                            {gem.ml_vote && (
                              <Badge className="bg-[#00FF94]/10 text-[#00FF94] text-xs">
                                ML: {gem.ml_vote}
                              </Badge>
                            )}
                            {gem.dl_vote && (
                              <Badge className="bg-[#9D00FF]/10 text-[#9D00FF] text-xs">
                                DL: {gem.dl_vote}
                              </Badge>
                            )}
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
      </AnimatePresence>

      {/* Model Details */}
      {modelInfo?.models && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Layers className="text-[#007AFF]" />
                Model Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#1F1F1F]">
                      <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium">Model</th>
                      <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium">Type</th>
                      <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium">Category</th>
                      <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium">Accuracy</th>
                      <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modelInfo.models.map((model) => (
                      <tr key={model.name} className="border-b border-[#1F1F1F]/50 hover:bg-[#111]">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {model.is_best && <Trophy size={14} className="text-[#FFB800]" />}
                            <span className="text-white font-medium capitalize">{model.name.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={model.type === 'ML' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#9D00FF]/20 text-[#9D00FF]'}>
                            {model.type}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-[#A1A1AA] capitalize">{model.category}</td>
                        <td className="py-3 px-4">
                          <span className="text-white font-data">{model.accuracy}%</span>
                        </td>
                        <td className="py-3 px-4 text-[#A1A1AA] text-sm max-w-xs truncate">{model.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default GemMLDLComparison;
