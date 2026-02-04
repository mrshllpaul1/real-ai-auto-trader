import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Target, Zap, TrendingUp, TrendingDown, RefreshCw, Activity,
  Award, AlertTriangle, BarChart3, Clock, CheckCircle, XCircle,
  Users, Shield, Building, Newspaper, Globe
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const categoryIcons = {
  celebrity: Users,
  regulatory: Shield,
  whale: TrendingUp,
  institutional: Building,
  security: AlertTriangle,
  partnership: Zap,
  macro: Globe,
  market_event: BarChart3,
  other: Target
};

const categoryColors = {
  celebrity: '#FFB800',
  regulatory: '#FF0055',
  whale: '#00FF94',
  institutional: '#9D00FF',
  security: '#FF6B35',
  partnership: '#00D4FF',
  macro: '#7B68EE',
  market_event: '#FF1493',
  other: '#A1A1AA'
};

const TriggerPerformance = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/triggers/performance/dashboard');
      setData(response.data);
    } catch (error) {
      console.error('Error loading trigger performance:', error);
      toast.error('Failed to load trigger performance data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Trigger Performance...</p>
        </div>
      </div>
    );
  }

  const { summary, by_category, trigger_metrics, top_performers, recent_executions } = data;

  const filteredTriggers = selectedCategory 
    ? trigger_metrics.filter(t => t.category === selectedCategory)
    : trigger_metrics;

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="trigger-performance-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Target size={40} className="text-[#FFB800]" />
            <span className="text-white">Trigger</span>
            <span className="text-[#FFB800]">Performance</span>
          </h1>
          <p className="text-[#A1A1AA]">
            Analytics and metrics for all {summary.total_triggers} event triggers
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

      {/* Summary Stats */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-5 gap-4"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target size={18} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Total Triggers</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">{summary.total_triggers}</div>
            <p className="text-xs text-[#A1A1AA]">{summary.enabled_triggers} enabled</p>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Total Fires</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FFB800]">{summary.total_executions}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Success Rate</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#00FF94]">{summary.overall_success_rate}%</div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              {summary.total_pnl_usd >= 0 ? (
                <TrendingUp size={18} className="text-[#00FF94]" />
              ) : (
                <TrendingDown size={18} className="text-[#FF0055]" />
              )}
              <span className="text-sm text-[#A1A1AA]">Total P&L</span>
            </div>
            <div className={`text-3xl font-data font-bold ${summary.total_pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              ${summary.total_pnl_usd.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={18} className="text-[#007AFF]" />
              <span className="text-sm text-[#A1A1AA]">Categories</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">{Object.keys(by_category).length}</div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Category Breakdown */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="text-[#9D00FF]" />
              Performance by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(by_category).map(([category, stats]) => {
                const Icon = categoryIcons[category] || Target;
                const color = categoryColors[category] || '#A1A1AA';
                const isSelected = selectedCategory === category;
                
                return (
                  <motion.div
                    key={category}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedCategory(isSelected ? null : category)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      isSelected 
                        ? 'bg-[#1F1F1F] border-2' 
                        : 'bg-[#121212] border border-[#1F1F1F] hover:border-[#333]'
                    }`}
                    style={{ borderColor: isSelected ? color : undefined }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Icon size={18} style={{ color }} />
                      <span className="text-white font-medium capitalize">{category.replace('_', ' ')}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-[#A1A1AA]">Triggers:</span>
                        <span className="text-white">{stats.total_triggers}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-[#A1A1AA]">Fires:</span>
                        <span style={{ color }}>{stats.total_fires}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-[#A1A1AA]">P&L:</span>
                        <span className={stats.total_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                          ${stats.total_pnl.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Performers */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Top by Fires */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Award className="text-[#FFB800]" />
              Top by Fire Count
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {top_performers.by_fires.map((trigger, idx) => (
              <div key={trigger.trigger_id} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    idx === 0 ? 'bg-[#FFB800]/20' : idx === 1 ? 'bg-[#C0C0C0]/20' : 'bg-[#CD7F32]/20'
                  }`}>
                    <span className={`font-bold ${
                      idx === 0 ? 'text-[#FFB800]' : idx === 1 ? 'text-[#C0C0C0]' : 'text-[#CD7F32]'
                    }`}>{idx + 1}</span>
                  </div>
                  <div>
                    <p className="text-white font-medium">{trigger.name}</p>
                    <p className="text-xs text-[#A1A1AA] capitalize">{trigger.category.replace('_', ' ')}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-[#FFB800] font-data font-bold">{trigger.total_fires}</p>
                  <p className="text-xs text-[#A1A1AA]">{trigger.success_rate}% success</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Top by P&L */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="text-[#00FF94]" />
              Top by P&L
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {top_performers.by_pnl.map((trigger, idx) => (
              <div key={trigger.trigger_id} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    idx === 0 ? 'bg-[#00FF94]/20' : idx === 1 ? 'bg-[#00FF94]/10' : 'bg-[#1F1F1F]'
                  }`}>
                    <span className={`font-bold ${
                      idx === 0 ? 'text-[#00FF94]' : 'text-[#A1A1AA]'
                    }`}>{idx + 1}</span>
                  </div>
                  <div>
                    <p className="text-white font-medium">{trigger.name}</p>
                    <p className="text-xs text-[#A1A1AA]">{trigger.total_fires} fires</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-data font-bold ${trigger.total_pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    ${trigger.total_pnl_usd.toFixed(2)}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </motion.div>

      {/* All Triggers Table */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Target className="text-[#9D00FF]" />
              All Triggers {selectedCategory && `(${selectedCategory.replace('_', ' ')})`}
              {selectedCategory && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedCategory(null)}
                  className="ml-2 text-[#A1A1AA]"
                >
                  Clear filter
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1F1F1F]">
                    <th className="text-left p-3 text-[#A1A1AA] font-medium">Trigger</th>
                    <th className="text-left p-3 text-[#A1A1AA] font-medium">Category</th>
                    <th className="text-center p-3 text-[#A1A1AA] font-medium">Fires</th>
                    <th className="text-center p-3 text-[#A1A1AA] font-medium">Success</th>
                    <th className="text-right p-3 text-[#A1A1AA] font-medium">P&L</th>
                    <th className="text-center p-3 text-[#A1A1AA] font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTriggers.map((trigger) => {
                    const Icon = categoryIcons[trigger.category] || Target;
                    const color = categoryColors[trigger.category] || '#A1A1AA';
                    
                    return (
                      <tr key={trigger.trigger_id} className="border-b border-[#1F1F1F]/50 hover:bg-[#121212]">
                        <td className="p-3">
                          <div>
                            <p className="text-white font-medium">{trigger.name}</p>
                            <p className="text-xs text-[#A1A1AA]">{trigger.keywords.slice(0, 3).join(', ')}...</p>
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <Icon size={14} style={{ color }} />
                            <span className="text-sm capitalize" style={{ color }}>{trigger.category.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <span className="font-data text-[#FFB800]">{trigger.total_fires}</span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <Progress 
                              value={trigger.success_rate} 
                              className="w-16 h-2"
                            />
                            <span className="text-sm text-[#A1A1AA]">{trigger.success_rate}%</span>
                          </div>
                        </td>
                        <td className="p-3 text-right">
                          <span className={`font-data ${trigger.total_pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                            ${trigger.total_pnl_usd.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Badge className={trigger.enabled ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                            {trigger.enabled ? 'Active' : 'Disabled'}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Executions */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="text-[#007AFF]" />
              Recent Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {recent_executions.map((exec, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div className="flex items-center gap-3">
                    {exec.success ? (
                      <CheckCircle size={18} className="text-[#00FF94]" />
                    ) : (
                      <XCircle size={18} className="text-[#FF0055]" />
                    )}
                    <div>
                      <p className="text-white text-sm">{exec.trigger_id}</p>
                      <p className="text-xs text-[#A1A1AA]">{exec.matched_headline?.slice(0, 50)}...</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-[#A1A1AA]">
                      {new Date(exec.timestamp).toLocaleString()}
                    </p>
                    {exec.pnl_usd !== undefined && (
                      <p className={`text-sm ${exec.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        ${exec.pnl_usd?.toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default TriggerPerformance;
