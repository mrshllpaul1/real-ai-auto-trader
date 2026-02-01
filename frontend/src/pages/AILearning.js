import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Brain, TrendingUp, Zap, BarChart3, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AILearning = () => {
  const [learningReport, setLearningReport] = useState(null);
  const [indicators, setIndicators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    loadLearningData();
  }, []);

  const loadLearningData = async () => {
    try {
      setLoading(true);
      const [reportRes, indicatorsRes] = await Promise.all([
        api.get('/learning/report').catch(() => ({ data: null })),
        api.get('/learning/indicators/performance').catch(() => ({ data: { indicators: [] } }))
      ]);

      setLearningReport(reportRes.data);
      setIndicators(indicatorsRes.data.indicators || []);
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#00FF94';
      case 'initializing': return '#007AFF';
      default: return '#9D00FF';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="ai-learning">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2 flex items-center gap-4" data-testid="learning-title">
            <Brain size={48} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">AI</span> Learning System
          </h1>
          <p className="text-[#A1A1AA]">
            The AI continuously learns from every trade to improve future predictions
          </p>
        </div>
        <Button
          onClick={triggerTraining}
          className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
          disabled={training}
          data-testid="train-ai-btn"
        >
          <Zap size={16} className="mr-2" />
          {training ? 'Training...' : 'Train AI Now'}
        </Button>
      </motion.div>

      {/* Learning Status */}
      {learningReport && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="learning-status-card">
            <CardHeader>
              <CardTitle className="text-2xl font-heading flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full animate-pulse"
                  style={{ backgroundColor: getStatusColor(learningReport.learning_system_status) }}
                />
                Learning System Status: {learningReport.learning_system_status}
              </CardTitle>
              <CardDescription>Real-time AI learning metrics and performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/20">
                  <div className="text-sm text-[#A1A1AA] mb-1">Strategies Evaluated</div>
                  <div className="text-3xl font-data font-bold text-[#9D00FF]">
                    {learningReport.total_strategies_evaluated}
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#00FF94]/20">
                  <div className="text-sm text-[#A1A1AA] mb-1">Learning Samples</div>
                  <div className="text-3xl font-data font-bold text-[#00FF94]">
                    {learningReport.total_learning_samples}
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#007AFF]/20">
                  <div className="text-sm text-[#A1A1AA] mb-1">Overall Accuracy</div>
                  <div className="text-3xl font-data font-bold text-[#007AFF]">
                    {learningReport.overall_accuracy.toFixed(1)}%
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg border border-[#00FF94]/20">
                  <div className="text-sm text-[#A1A1AA] mb-1">Learned P/L</div>
                  <div className={`text-3xl font-data font-bold ${
                    learningReport.total_learned_profit_loss >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                  }`}>
                    ${learningReport.total_learned_profit_loss.toFixed(2)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Best Performing Indicators */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="indicators-card">
          <CardHeader>
            <CardTitle className="text-2xl font-heading flex items-center gap-3">
              <BarChart3 className="text-[#00FF94]" />
              Best Performing Indicators
            </CardTitle>
            <CardDescription>
              AI has analyzed which technical indicators perform best
            </CardDescription>
          </CardHeader>
          <CardContent>
            {indicators.length === 0 ? (
              <div className="text-center py-12">
                <Brain size={48} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
                <p className="text-[#A1A1AA]">
                  AI is gathering data. Execute trades to start learning.
                </p>
              </div>
            ) : (
              <div className="space-y-3" data-testid="indicators-list">
                {indicators.map((indicator, index) => (
                  <div
                    key={indicator.indicator}
                    className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-all"
                    data-testid={`indicator-item-${index}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-[#9D00FF]/20">
                        <span className="font-bold text-[#9D00FF]">#{index + 1}</span>
                      </div>
                      <div>
                        <h3 className="font-bold text-white uppercase">
                          {indicator.indicator}
                        </h3>
                        <p className="text-sm text-[#A1A1AA]">
                          Used {indicator.total_uses} times
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-sm text-[#A1A1AA]">Accuracy</div>
                        <div className="text-xl font-data font-bold text-[#00FF94]">
                          {indicator.accuracy.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-[#A1A1AA]">Avg P/L</div>
                        <div className={`text-xl font-data font-bold ${
                          indicator.avg_profit_per_use >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                        }`}>
                          ${indicator.avg_profit_per_use.toFixed(2)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-[#A1A1AA]">Score</div>
                        <div className="text-xl font-data font-bold text-[#9D00FF]">
                          {indicator.effectiveness_score.toFixed(0)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* How Learning Works */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="how-it-works-card">
          <CardHeader>
            <CardTitle className="text-2xl font-heading">How AI Learning Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 bg-[#121212] rounded-lg border border-[#9D00FF]/20">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[#9D00FF]/20 flex items-center justify-center">
                    <Brain size={20} className="text-[#9D00FF]" />
                  </div>
                  <h3 className="font-bold text-white">1. Track Performance</h3>
                </div>
                <p className="text-sm text-[#A1A1AA]">
                  Every trade is recorded with predicted vs actual outcomes, profit/loss, and confidence scores.
                </p>
              </div>

              <div className="p-6 bg-[#121212] rounded-lg border border-[#00FF94]/20">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[#00FF94]/20 flex items-center justify-center">
                    <TrendingUp size={20} className="text-[#00FF94]" />
                  </div>
                  <h3 className="font-bold text-white">2. Analyze Patterns</h3>
                </div>
                <p className="text-sm text-[#A1A1AA]">
                  AI identifies which indicators and strategies perform best for each cryptocurrency.
                </p>
              </div>

              <div className="p-6 bg-[#121212] rounded-lg border border-[#007AFF]/20">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-[#007AFF]/20 flex items-center justify-center">
                    <CheckCircle size={20} className="text-[#007AFF]" />
                  </div>
                  <h3 className="font-bold text-white">3. Improve Predictions</h3>
                </div>
                <p className="text-sm text-[#A1A1AA]">
                  Future strategies are adjusted based on historical accuracy, weighting successful patterns higher.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default AILearning;
