import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Brain, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Activity, BarChart2, RefreshCw, Settings, Bell, BellOff,
  Target, Zap, Database, Clock, AlertCircle, Info
} from 'lucide-react';
import api from '../services/api';
import { useToast } from '../hooks/use-toast';

const MLAnalytics = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [calibrationData, setCalibrationData] = useState(null);
  const [driftAlerts, setDriftAlerts] = useState([]);
  const [abTests, setAbTests] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, calibrationRes, alertsRes, testsRes] = await Promise.all([
        api.get('/ml-analytics/dashboard'),
        api.get('/ml-analytics/calibration/accuracy-by-level'),
        api.get('/ml-analytics/drift/alerts'),
        api.get('/ml-analytics/ab-test/list')
      ]);

      setDashboard(dashboardRes.data);
      setCalibrationData(calibrationRes.data);
      setDriftAlerts(alertsRes.data.alerts || []);
      setAbTests(testsRes.data.tests || []);
    } catch (err) {
      console.error('Failed to fetch ML analytics:', err);
      toast({
        title: 'Error',
        description: 'Failed to load ML analytics',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await api.post(`/ml-analytics/drift/alerts/${alertId}/acknowledge`);
      fetchAllData();
      toast({ title: 'Alert acknowledged' });
    } catch (err) {
      toast({ title: 'Failed to acknowledge alert', variant: 'destructive' });
    }
  };

  const getConfidenceLevelColor = (level) => {
    switch (level) {
      case 'HIGH': return 'text-green-400 bg-green-500/20';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-500/20';
      case 'LOW': return 'text-orange-400 bg-orange-500/20';
      case 'VERY_LOW': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'calibration', label: 'Confidence Calibration', icon: Target },
    { id: 'drift', label: 'Model Drift', icon: AlertTriangle },
    { id: 'ab-testing', label: 'A/B Testing', icon: BarChart2 },
    { id: 'cache', label: 'Cache & Performance', icon: Database }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">ML Analytics Dashboard</h1>
              <p className="text-gray-400">Monitor model performance, drift, and experiments</p>
            </div>
          </div>
          <button
            onClick={fetchAllData}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && dashboard && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid md:grid-cols-4 gap-4"
          >
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-2">
                <Target className="w-5 h-5" />
                <span>Overall Accuracy</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {calibrationData?.overall_accuracy ?? 'N/A'}%
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {calibrationData?.total_predictions ?? 0} predictions
              </div>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-2">
                <AlertTriangle className="w-5 h-5" />
                <span>Drift Alerts</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {dashboard?.drift?.active_alerts ?? 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                Active alerts requiring attention
              </div>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-2">
                <BarChart2 className="w-5 h-5" />
                <span>Active A/B Tests</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {dashboard?.ab_testing?.active_tests ?? 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                of {dashboard?.ab_testing?.total_tests ?? 0} total tests
              </div>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 mb-2">
                <Zap className="w-5 h-5" />
                <span>Cache Hit Rate</span>
              </div>
              <div className="text-3xl font-bold text-white">
                {dashboard?.infrastructure?.cache?.memory_stats?.hit_rate?.toFixed(1) ?? 0}%
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {dashboard?.infrastructure?.cache?.backend ?? 'memory'} backend
              </div>
            </div>
          </motion.div>
        )}

        {/* Calibration Tab */}
        {activeTab === 'calibration' && calibrationData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Accuracy by Confidence Level</h3>
              <p className="text-gray-400 mb-6">Shows how accurate predictions are at each confidence level</p>
              
              <div className="grid md:grid-cols-4 gap-4">
                {Object.entries(calibrationData.levels || {}).map(([level, data]) => (
                  <div
                    key={level}
                    className={`p-4 rounded-xl border ${getConfidenceLevelColor(level)} border-current/30`}
                  >
                    <div className="text-lg font-bold mb-1">{level}</div>
                    <div className="text-sm opacity-80 mb-3">{data.range}</div>
                    <div className="text-3xl font-bold">
                      {data.accuracy !== null ? `${data.accuracy}%` : 'N/A'}
                    </div>
                    <div className="text-sm opacity-70 mt-1">
                      {data.count} predictions
                    </div>
                    {data.count > 0 && (
                      <div className="mt-2 text-xs">
                        {data.correct} correct / {data.incorrect} incorrect
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {calibrationData.total_predictions === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Info className="w-8 h-8 mx-auto mb-2" />
                  <p>No prediction data yet. Predictions will appear here as the system makes trades.</p>
                </div>
              )}
            </div>

            <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 border border-purple-500/20">
              <h4 className="font-semibold text-white mb-2">What is Confidence Calibration?</h4>
              <p className="text-gray-300 text-sm">
                A well-calibrated model should have predictions with 80% confidence be correct 80% of the time.
                If HIGH confidence predictions are only 60% accurate, the model is overconfident and needs adjustment.
              </p>
            </div>
          </motion.div>
        )}

        {/* Drift Tab */}
        {activeTab === 'drift' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Drift Status */}
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Model Drift Status</h3>
              
              {Object.keys(dashboard?.drift?.status?.models || {}).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(dashboard.drift.status.models).map(([model, data]) => (
                    <div
                      key={model}
                      className={`p-4 rounded-lg border ${
                        data.status === 'critical' ? 'bg-red-500/10 border-red-500/30' :
                        data.status === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                        'bg-green-500/10 border-green-500/30'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium text-white">{model}</span>
                          <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                            data.status === 'critical' ? 'bg-red-500/20 text-red-400' :
                            data.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-green-500/20 text-green-400'
                          }`}>
                            {data.status}
                          </span>
                        </div>
                        <div className="text-right text-sm">
                          <div className="text-gray-400">Baseline: {data.baseline_accuracy}%</div>
                          <div className="text-white">Current: {data.current_accuracy}%</div>
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-500">
                        Drift: {data.drift_percentage > 0 ? '+' : ''}{data.drift_percentage}% | {data.sample_count} samples
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                  <p>No model drift detected. All models performing within baseline.</p>
                </div>
              )}
            </div>

            {/* Drift Alerts */}
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Drift Alerts</h3>
              
              {driftAlerts.length > 0 ? (
                <div className="space-y-3">
                  {driftAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-4 rounded-lg border ${
                        alert.severity === 'high' ? 'bg-red-500/10 border-red-500/30' :
                        'bg-yellow-500/10 border-yellow-500/30'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <AlertCircle className={`w-5 h-5 ${
                            alert.severity === 'high' ? 'text-red-400' : 'text-yellow-400'
                          }`} />
                          <span className="font-medium text-white">{alert.model_name}</span>
                        </div>
                        {!alert.acknowledged && (
                          <button
                            onClick={() => acknowledgeAlert(alert.id)}
                            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-sm text-gray-300 rounded-lg transition-colors"
                          >
                            Acknowledge
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-gray-300 mt-2">{alert.recommendation}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Direction: {alert.direction}</span>
                        <span>Drift: {alert.drift_percentage}%</span>
                        <span>{new Date(alert.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <BellOff className="w-8 h-8 mx-auto mb-2" />
                  <p>No active drift alerts</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* A/B Testing Tab */}
        {activeTab === 'ab-testing' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Strategy A/B Tests</h3>
              
              {abTests.length > 0 ? (
                <div className="space-y-4">
                  {abTests.map((test) => (
                    <div
                      key={test.id}
                      className="p-4 bg-gray-900/50 rounded-lg border border-gray-700"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <span className="font-medium text-white">{test.name}</span>
                          <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                            test.status === 'running' ? 'bg-green-500/20 text-green-400' :
                            'bg-gray-600/20 text-gray-400'
                          }`}>
                            {test.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {test.total_samples} samples
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {test.variants?.map((variant) => (
                          <div
                            key={variant.id}
                            className="p-3 bg-gray-800 rounded-lg"
                          >
                            <div className="text-sm text-gray-400">{variant.name}</div>
                            <div className="text-lg font-bold text-white">
                              {(variant.traffic_share * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-gray-500">traffic</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <BarChart2 className="w-8 h-8 mx-auto mb-2" />
                  <p>No A/B tests configured. Create tests to compare strategy variants.</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Cache Tab */}
        {activeTab === 'cache' && dashboard && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid md:grid-cols-2 gap-6"
          >
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Cache Statistics</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Backend</span>
                  <span className="text-white font-medium capitalize">
                    {dashboard.infrastructure?.cache?.backend || 'memory'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Hit Rate</span>
                  <span className="text-green-400 font-medium">
                    {dashboard.infrastructure?.cache?.memory_stats?.hit_rate?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Hits / Misses</span>
                  <span className="text-white">
                    {dashboard.infrastructure?.cache?.memory_stats?.hits || 0} / {dashboard.infrastructure?.cache?.memory_stats?.misses || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Cache Size</span>
                  <span className="text-white">
                    {dashboard.infrastructure?.cache?.memory_stats?.size || 0} / {dashboard.infrastructure?.cache?.memory_stats?.max_size || 10000}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Redis Connected</span>
                  <span className={dashboard.infrastructure?.cache?.redis_connected ? 'text-green-400' : 'text-gray-500'}>
                    {dashboard.infrastructure?.cache?.redis_connected ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Request Deduplication</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Unique Requests</span>
                  <span className="text-white font-medium">
                    {dashboard.infrastructure?.deduplication?.unique || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Deduplicated</span>
                  <span className="text-green-400 font-medium">
                    {dashboard.infrastructure?.deduplication?.deduplicated || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Dedup Rate</span>
                  <span className="text-white">
                    {dashboard.infrastructure?.deduplication?.dedup_rate?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Pending Requests</span>
                  <span className="text-yellow-400">
                    {dashboard.infrastructure?.deduplication?.pending || 0}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default MLAnalytics;
