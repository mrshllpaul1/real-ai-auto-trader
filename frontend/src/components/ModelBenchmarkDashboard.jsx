import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, LineChart, Line
} from 'recharts';
import { 
  Trophy, TrendingUp, TrendingDown, Activity, RefreshCw, 
  Play, Award, AlertTriangle, Zap, Target, BarChart3,
  Brain, Cpu, Layers, Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import api from '../services/api';

const MODEL_COLORS = {
  ensemble: '#10B981',      // Green
  time_series: '#6366F1',   // Indigo
  finrl: '#F59E0B',         // Amber
  combined: '#EC4899'       // Pink
};

const MODEL_ICONS = {
  ensemble: <Layers className="w-4 h-4" />,
  time_series: <Activity className="w-4 h-4" />,
  finrl: <Brain className="w-4 h-4" />,
  combined: <Sparkles className="w-4 h-4" />
};

const ModelBenchmarkDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [chartData, setChartData] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedView, setSelectedView] = useState('performance');

  const loadBenchmarkData = useCallback(async () => {
    try {
      setLoading(true);
      const [chartRes, rankRes] = await Promise.all([
        api.get('/model-benchmark/chart-data'),
        api.get('/model-benchmark/rankings')
      ]);
      
      setChartData(chartRes.data);
      setRankings(rankRes.data.rankings);
      setRecommendations(rankRes.data.recommendations || []);
    } catch (error) {
      console.error('Failed to load benchmark data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const runBenchmark = async () => {
    try {
      setRunning(true);
      toast.info('Running model benchmark... This may take a moment.');
      
      const res = await api.post('/model-benchmark/run', { days: 365 });
      
      toast.success(`Benchmark complete! Top model: ${res.data.top_model}`);
      await loadBenchmarkData();
    } catch (error) {
      console.error('Benchmark failed:', error);
      toast.error('Benchmark failed');
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadBenchmarkData();
  }, [loadBenchmarkData]);

  const renderPerformanceChart = () => {
    if (!chartData?.performance_comparison?.length) {
      return (
        <div className="h-64 flex flex-col items-center justify-center text-slate-500">
          <BarChart3 className="w-12 h-12 mb-3 opacity-50" />
          <p>No benchmark data available</p>
          <p className="text-sm">Click "Run Benchmark" to compare models</p>
        </div>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData.performance_comparison} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="model" 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickFormatter={(value) => value.split(' ')[0]}
          />
          <YAxis 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickFormatter={(value) => `${value.toFixed(1)}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F9FAFB'
            }}
            formatter={(value, name) => [
              `${value.toFixed(2)}%`,
              name === 'avg_return' ? 'Avg Return' : name === 'avg_win_rate' ? 'Win Rate' : name
            ]}
          />
          <Legend />
          <Bar dataKey="avg_return" name="Avg Return %" fill="#10B981" radius={[4, 4, 0, 0]} />
          <Bar dataKey="avg_win_rate" name="Win Rate %" fill="#6366F1" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderScenarioChart = () => {
    if (!chartData?.scenario_breakdown?.length) return null;

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData.scenario_breakdown} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="scenario" 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
          />
          <YAxis 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickFormatter={(value) => `${value.toFixed(0)}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F9FAFB'
            }}
            formatter={(value) => [`${value?.toFixed(2) || 0}%`, 'Return']}
          />
          <Legend />
          <Bar dataKey="ensemble" name="Ensemble" fill={MODEL_COLORS.ensemble} radius={[2, 2, 0, 0]} />
          <Bar dataKey="time_series" name="Time Series" fill={MODEL_COLORS.time_series} radius={[2, 2, 0, 0]} />
          <Bar dataKey="finrl" name="FinRL" fill={MODEL_COLORS.finrl} radius={[2, 2, 0, 0]} />
          <Bar dataKey="combined" name="Combined" fill={MODEL_COLORS.combined} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderRiskRadar = () => {
    if (!chartData?.risk_metrics?.length) return null;

    return (
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={chartData.risk_metrics}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis 
            dataKey="model" 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickFormatter={(value) => value.split(' ')[0]}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={{ fill: '#6B7280', fontSize: 8 }}
          />
          <Radar
            name="Sharpe Score"
            dataKey="sharpe"
            stroke="#10B981"
            fill="#10B981"
            fillOpacity={0.3}
          />
          <Radar
            name="Win Rate"
            dataKey="win_rate"
            stroke="#6366F1"
            fill="#6366F1"
            fillOpacity={0.3}
          />
          <Radar
            name="Consistency"
            dataKey="consistency"
            stroke="#F59E0B"
            fill="#F59E0B"
            fillOpacity={0.3}
          />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    );
  };

  const renderRankings = () => {
    if (!rankings?.overall?.length) {
      return (
        <div className="text-center text-slate-500 py-8">
          <Trophy className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Run benchmark to see rankings</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {rankings.overall.map((model, index) => (
          <motion.div
            key={model.model}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`p-4 rounded-lg border ${
              index === 0 
                ? 'bg-gradient-to-r from-amber-500/20 to-yellow-500/10 border-amber-500/30' 
                : 'bg-slate-800/50 border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  index === 0 ? 'bg-amber-500 text-black' :
                  index === 1 ? 'bg-slate-400 text-black' :
                  index === 2 ? 'bg-amber-700 text-white' :
                  'bg-slate-700 text-slate-300'
                }`}>
                  {index === 0 ? <Trophy className="w-4 h-4" /> : index + 1}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span style={{ color: MODEL_COLORS[model.model] }}>
                      {MODEL_ICONS[model.model]}
                    </span>
                    <span className="font-medium text-white">{model.name}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Score: {model.overall_score?.toFixed(2)}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2">
                  <Badge className={model.avg_return >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
                    {model.avg_return >= 0 ? '+' : ''}{(model.avg_return * 100).toFixed(1)}%
                  </Badge>
                  <Badge className="bg-blue-500/20 text-blue-400">
                    Sharpe: {model.avg_sharpe?.toFixed(2)}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Win Rate: {(model.avg_win_rate * 100).toFixed(0)}% | DD: {(model.avg_drawdown * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderRecommendations = () => {
    if (!recommendations.length) return null;

    return (
      <div className="space-y-3">
        {recommendations.slice(0, 4).map((rec, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`p-3 rounded-lg border ${
              rec.type === 'primary' ? 'bg-green-500/10 border-green-500/30' :
              rec.type === 'warning' ? 'bg-amber-500/10 border-amber-500/30' :
              'bg-slate-800/50 border-slate-700'
            }`}
          >
            <div className="flex items-start gap-3">
              {rec.type === 'primary' ? (
                <Award className="w-5 h-5 text-green-400 mt-0.5" />
              ) : rec.type === 'warning' ? (
                <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
              ) : (
                <Target className="w-5 h-5 text-cyan-400 mt-0.5" />
              )}
              <div>
                <h4 className="font-medium text-white text-sm">{rec.title}</h4>
                <p className="text-xs text-slate-400 mt-1">{rec.message}</p>
                {rec.metrics && (
                  <div className="flex gap-2 mt-2">
                    <Badge className="bg-slate-700 text-slate-300 text-xs">
                      Sharpe: {rec.metrics.sharpe?.toFixed(2)}
                    </Badge>
                    <Badge className="bg-slate-700 text-slate-300 text-xs">
                      Return: {(rec.metrics.return * 100).toFixed(1)}%
                    </Badge>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="model-benchmark-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-6 h-6 text-cyan-400" />
            Model Performance Benchmark
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Compare FinRL vs Ensemble vs Time-Series across market conditions
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadBenchmarkData}
            disabled={loading}
            className="border-slate-700 hover:bg-slate-800"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={runBenchmark}
            disabled={running}
            className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
          >
            {running ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Benchmark
              </>
            )}
          </Button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 border-b border-slate-700 pb-2">
        {[
          { id: 'performance', label: 'Performance', icon: <BarChart3 className="w-4 h-4" /> },
          { id: 'scenarios', label: 'Scenarios', icon: <Layers className="w-4 h-4" /> },
          { id: 'risk', label: 'Risk Analysis', icon: <Activity className="w-4 h-4" /> },
        ].map((tab) => (
          <Button
            key={tab.id}
            variant={selectedView === tab.id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setSelectedView(tab.id)}
            className={selectedView === tab.id ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400'}
          >
            {tab.icon}
            <span className="ml-2">{tab.label}</span>
          </Button>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Charts Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Performance Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
          >
            <h3 className="font-medium text-white mb-4 flex items-center gap-2">
              {selectedView === 'performance' && <TrendingUp className="w-4 h-4 text-green-400" />}
              {selectedView === 'scenarios' && <Layers className="w-4 h-4 text-indigo-400" />}
              {selectedView === 'risk' && <Activity className="w-4 h-4 text-amber-400" />}
              {selectedView === 'performance' && 'Model Performance Comparison'}
              {selectedView === 'scenarios' && 'Performance by Market Scenario'}
              {selectedView === 'risk' && 'Risk-Adjusted Metrics'}
            </h3>
            
            {selectedView === 'performance' && renderPerformanceChart()}
            {selectedView === 'scenarios' && renderScenarioChart()}
            {selectedView === 'risk' && renderRiskRadar()}
          </motion.div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
            >
              <h3 className="font-medium text-white mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                AI Recommendations
              </h3>
              {renderRecommendations()}
            </motion.div>
          )}
        </div>

        {/* Rankings Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl"
        >
          <h3 className="font-medium text-white mb-4 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-amber-400" />
            Model Rankings
          </h3>
          {renderRankings()}
        </motion.div>
      </div>
    </div>
  );
};

export default ModelBenchmarkDashboard;
