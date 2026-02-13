import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Brain, Target, TrendingUp, TrendingDown, Loader2, BarChart3, Calendar, Play, GraduationCap, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AICoinSelectionSection = () => {
  const [selectedCoins, setSelectedCoins] = useState([]);
  const [simulationResults, setSimulationResults] = useState(null);
  const [dataStatus, setDataStatus] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [marketCondition, setMarketCondition] = useState('neutral');

  useEffect(() => {
    loadDataStatus();
    loadLatestSimulation();
    loadTrainingStatus();
  }, []);

  const loadDataStatus = async () => {
    try {
      const response = await api.get('/ai-selection/historical-data-status');
      setDataStatus(response.data);
    } catch (error) {
      console.error('Error loading data status:', error);
    }
  };

  const loadLatestSimulation = async () => {
    try {
      const response = await api.get('/ai-selection/simulation-results?limit=1');
      if (response.data.results?.length > 0) {
        setSimulationResults(response.data.results[0]);
      }
    } catch (error) {
      console.error('Error loading simulation results:', error);
    }
  };

  const loadTrainingStatus = async () => {
    try {
      const response = await api.get('/ai-selection/training-status');
      setTrainingStatus(response.data);
    } catch (error) {
      console.error('Error loading training status:', error);
    }
  };

  const selectCoinsForWeek = async () => {
    setLoading(true);
    try {
      const response = await api.post('/ai-selection/select-coins', {
        market_condition: marketCondition,
        max_coins: 10
      });
      setSelectedCoins(response.data.selected_coins || []);
      toast.success(`Selected ${response.data.total_selected} coins for trading!`);
    } catch (error) {
      toast.error('Failed to select coins');
    } finally {
      setLoading(false);
    }
  };

  const seedHistoricalData = async () => {
    setLoading(true);
    try {
      await api.post('/ai-selection/seed-historical-data');
      toast.success('Historical data seeding started! This may take a few minutes.');
      setTimeout(loadDataStatus, 30000);
    } catch (error) {
      toast.error('Failed to start data seeding');
    } finally {
      setLoading(false);
    }
  };

  const startTraining = async () => {
    setTraining(true);
    try {
      await api.post('/ai-selection/train-ai');
      toast.success('AI training started! Training 2009-2026 data in background.');
      setTimeout(loadTrainingStatus, 60000);
    } catch (error) {
      toast.error('Failed to start training');
    } finally {
      setTraining(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-[#00FF94]';
    if (score >= 50) return 'text-[#007AFF]';
    return 'text-[#A1A1AA]';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <Card className="bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/10 border-[#9D00FF]/30">
          <CardHeader>
            <CardTitle className="text-2xl font-heading flex items-center gap-3">
              <Brain className="text-[#9D00FF]" size={28} />
              Adaptive AI Coin Selection Engine
              <Badge className="bg-[#00FF94]/20 text-[#00FF94]">10 + 1 GEM</Badge>
            </CardTitle>
            <CardDescription className="text-[#A1A1AA]">
              AI selects 10 main coins + 1 hidden gem each week. Learns from 100+ coins, adapts to market conditions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[150px] p-4 bg-[#0A0A0A] rounded-lg">
                <div className="text-xs text-[#A1A1AA] mb-1">Historical Data</div>
                <div className="text-lg font-bold">
                  {dataStatus?.total_records?.toLocaleString() || 0} records
                </div>
                <div className="text-xs text-[#A1A1AA]">
                  {dataStatus?.coin_count || 0} coins tracked
                </div>
              </div>
              <div className="flex-1 min-w-[150px] p-4 bg-[#0A0A0A] rounded-lg">
                <div className="text-xs text-[#A1A1AA] mb-1">AI Status</div>
                <Badge 
                  className={trainingStatus?.trained 
                    ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                    : 'bg-[#FF9500]/20 text-[#FF9500]'
                  }
                >
                  {trainingStatus?.trained ? 'TRAINED' : 'NOT TRAINED'}
                </Badge>
                {trainingStatus?.weights && (
                  <div className="text-xs text-[#A1A1AA] mt-1">
                    {trainingStatus.weights.total_weeks_trained} weeks learned
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-[150px] p-4 bg-[#0A0A0A] rounded-lg">
                <div className="text-xs text-[#A1A1AA] mb-1">Win Rate</div>
                <div className={`text-lg font-bold ${trainingStatus?.weights?.win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                  {trainingStatus?.weights?.win_rate?.toFixed(1) || 0}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Training Status & Controls */}
      {trainingStatus?.trained && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.05 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-2">
                <GraduationCap className="text-[#9D00FF]" size={24} />
                AI Learned Preferences
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Top Coins */}
                <div>
                  <h4 className="text-sm font-bold text-[#A1A1AA] mb-2">Top Performing Coins</h4>
                  <div className="space-y-1">
                    {trainingStatus.weights?.weights?.coin_scores && 
                      Object.entries(trainingStatus.weights.weights.coin_scores)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 5)
                        .map(([coin, score]) => (
                          <div key={coin} className="flex justify-between text-sm p-1 bg-[#121212] rounded">
                            <span className="capitalize">{coin}</span>
                            <span className={getScoreColor(score)}>{score.toFixed(1)}</span>
                          </div>
                        ))
                    }
                  </div>
                </div>
                {/* Category Preferences */}
                <div>
                  <h4 className="text-sm font-bold text-[#A1A1AA] mb-2">Category Performance</h4>
                  <div className="space-y-1">
                    {trainingStatus.weights?.weights?.category_scores && 
                      Object.entries(trainingStatus.weights.weights.category_scores)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 5)
                        .map(([cat, score]) => (
                          <div key={cat} className="flex justify-between text-sm p-1 bg-[#121212] rounded">
                            <span className="capitalize">{cat}</span>
                            <span className={getScoreColor(score)}>{score.toFixed(1)}</span>
                          </div>
                        ))
                    }
                  </div>
                </div>
              </div>
              
              <div className="mt-4 flex gap-2">
                <Button
                  onClick={startTraining}
                  disabled={training}
                  variant="outline"
                  className="border-[#9D00FF] text-[#9D00FF] hover:bg-[#9D00FF]/10"
                  data-testid="retrain-btn"
                >
                  {training ? <Loader2 className="animate-spin mr-2" size={16} /> : <GraduationCap className="mr-2" size={16} />}
                  Retrain AI
                </Button>
                <Button
                  onClick={seedHistoricalData}
                  disabled={loading}
                  variant="outline"
                  className="border-[#333] text-[#A1A1AA]"
                  data-testid="seed-more-btn"
                >
                  {loading ? <Loader2 className="animate-spin mr-2" size={16} /> : <BarChart3 className="mr-2" size={16} />}
                  Seed More Data
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* AI Coin Selection */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-xl font-heading flex items-center gap-2">
              <Target className="text-[#00FF94]" size={24} />
              Select Best Coins This Week
            </CardTitle>
            <CardDescription>
              AI picks 10 main coins + 1 gem based on learned preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Market Condition Selector */}
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-[#A1A1AA] self-center mr-2">Market Condition:</span>
              {['bullish', 'neutral', 'bearish'].map((condition) => (
                <Button
                  key={condition}
                  variant={marketCondition === condition ? 'default' : 'outline'}
                  className={`rounded-full capitalize ${
                    marketCondition === condition 
                      ? condition === 'bullish' ? 'bg-[#00FF94] text-black' 
                        : condition === 'bearish' ? 'bg-[#FF0055] text-white'
                        : 'bg-[#007AFF] text-white'
                      : 'border-[#333] text-[#A1A1AA]'
                  }`}
                  onClick={() => setMarketCondition(condition)}
                  data-testid={`market-${condition}-btn`}
                >
                  {condition === 'bullish' && <TrendingUp size={14} className="mr-1" />}
                  {condition === 'bearish' && <TrendingDown size={14} className="mr-1" />}
                  {condition}
                </Button>
              ))}
            </div>

            <Button
              onClick={selectCoinsForWeek}
              disabled={loading || !dataStatus?.ready_for_simulation}
              className="w-full bg-[#9D00FF] hover:bg-[#7A00CC] text-white font-bold py-3 rounded-lg"
              data-testid="select-coins-btn"
            >
              {loading ? (
                <Loader2 className="animate-spin mr-2" size={20} />
              ) : (
                <Brain className="mr-2" size={20} />
              )}
              Select 10 Coins + 1 Gem
            </Button>

            {/* Selected Coins Display */}
            {selectedCoins.length > 0 && (
              <div className="space-y-3 mt-4">
                <h4 className="text-sm font-bold text-[#A1A1AA]">AI Selected Portfolio:</h4>
                {selectedCoins.map((coin, index) => (
                  <motion.div
                    key={coin.coin_id}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={index === 0 ? "bg-[#FFD700]/20 text-[#FFD700] border-[#FFD700]/30" : "bg-[#9D00FF]/20 text-[#9D00FF] border-[#9D00FF]/30"}>
                          #{index + 1}
                        </Badge>
                        <span className="font-bold text-white">{coin.symbol}</span>
                        {coin.category === 'meme' || coin.category === 'ai' || coin.category === 'new' ? (
                          <Badge className="bg-[#FF9500]/20 text-[#FF9500] text-xs">
                            <Sparkles size={10} className="mr-1" />GEM
                          </Badge>
                        ) : null}
                      </div>
                      <div className={`text-xl font-bold ${getScoreColor(coin.total_score)}`}>
                        {coin.total_score}
                      </div>
                    </div>
                    <p className="text-sm text-[#A1A1AA] mb-2">{coin.reasoning}</p>
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-xs">
                      {Object.entries(coin.scores || {}).map(([key, value]) => (
                        <div key={key} className="text-center p-1 bg-[#0A0A0A] rounded">
                          <div className="text-[#A1A1AA] capitalize">{key}</div>
                          <div className={getScoreColor(value)}>{value}</div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Simulation Results */}
      {simulationResults && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-2">
                <BarChart3 className="text-[#007AFF]" size={24} />
                Latest Simulation Results
              </CardTitle>
              <CardDescription>
                Weekly paper trading simulation with fixed $10,000 capital per week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total Weeks</div>
                  <div className="text-2xl font-bold text-white">
                    {simulationResults.total_weeks}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Win Rate</div>
                  <div className={`text-2xl font-bold ${simulationResults.win_rate_pct >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {simulationResults.win_rate_pct}%
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total P/L</div>
                  <div className={`text-2xl font-bold ${simulationResults.total_profit_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    ${simulationResults.total_profit_usd?.toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Avg Weekly</div>
                  <div className={`text-2xl font-bold ${simulationResults.avg_weekly_return_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {simulationResults.avg_weekly_return_pct?.toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* Best/Worst Week */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {simulationResults.best_week && (
                  <div className="p-3 bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg">
                    <div className="text-xs text-[#00FF94] mb-1 flex items-center gap-1">
                      <TrendingUp size={12} />
                      Best Week
                    </div>
                    <div className="text-lg font-bold text-[#00FF94]">
                      +{simulationResults.best_week.return_pct?.toFixed(2)}%
                    </div>
                    <div className="text-xs text-[#A1A1AA]">
                      {simulationResults.best_week.date?.slice(0, 10)}
                    </div>
                  </div>
                )}
                {simulationResults.worst_week && (
                  <div className="p-3 bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg">
                    <div className="text-xs text-[#FF0055] mb-1 flex items-center gap-1">
                      <TrendingDown size={12} />
                      Worst Week
                    </div>
                    <div className="text-lg font-bold text-[#FF0055]">
                      {simulationResults.worst_week.return_pct?.toFixed(2)}%
                    </div>
                    <div className="text-xs text-[#A1A1AA]">
                      {simulationResults.worst_week.date?.slice(0, 10)}
                    </div>
                  </div>
                )}
              </div>

              {/* Annual Breakdown */}
              {simulationResults.annual_breakdown && Object.keys(simulationResults.annual_breakdown).length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-bold text-[#A1A1AA] mb-2 flex items-center gap-1">
                    <Calendar size={14} />
                    Annual Breakdown
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(simulationResults.annual_breakdown).map(([year, data]) => (
                      <div key={year} className="flex items-center justify-between p-2 bg-[#121212] rounded">
                        <span className="font-bold">{year}</span>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-[#A1A1AA]">{data.weeks} weeks</span>
                          <span className={data.total_profit >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                            ${data.total_profit?.toLocaleString()}
                          </span>
                          <span className="text-[#A1A1AA]">{data.win_rate}% win</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default AICoinSelectionSection;
