import React, { useState, useEffect } from 'react';
import { 
  Brain, Activity, AlertTriangle, RefreshCw, TrendingUp, TrendingDown,
  Zap, Target, BarChart3, PieChart, Clock, Check, X, ChevronRight,
  Play, Pause, Settings, Eye, AlertCircle, Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, 
  AreaChart, Area, BarChart, Bar, ScatterChart, Scatter, CartesianGrid, Legend
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const MLDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelDetails, setModelDetails] = useState(null);
  const [driftStatus, setDriftStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedModel) {
      fetchModelDetails(selectedModel);
    }
  }, [selectedModel]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, driftRes, alertsRes] = await Promise.all([
        fetch(`${API_URL}/api/ml-monitoring/dashboard/overview`),
        fetch(`${API_URL}/api/ml-monitoring/drift/status`),
        fetch(`${API_URL}/api/ml-monitoring/alerts/active`)
      ]);

      if (dashRes.ok) setDashboard(await dashRes.json());
      if (driftRes.ok) setDriftStatus(await driftRes.json());
      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchModelDetails = async (modelId) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-monitoring/dashboard/model/${modelId}`);
      if (res.ok) {
        setModelDetails(await res.json());
      }
    } catch (err) {
      console.error('Error fetching model details:', err);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await fetch(`${API_URL}/api/ml-monitoring/alerts/${alertId}/acknowledge`, { method: 'POST' });
      toast.success('Alert acknowledged');
      fetchData();
    } catch (err) {
      toast.error('Failed to acknowledge alert');
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'text-[#00FF94] bg-[#00FF94]/20';
      case 'degraded': return 'text-yellow-400 bg-yellow-500/20';
      case 'critical': return 'text-red-400 bg-red-500/20';
      default: return 'text-[#A1A1AA] bg-[#333]';
    }
  };

  const getDriftColor = (status) => {
    switch (status) {
      case 'stable': return 'text-[#00FF94]';
      case 'warning': return 'text-yellow-400';
      case 'drift_detected': return 'text-red-400';
      default: return 'text-[#A1A1AA]';
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'models', label: 'Models', icon: Brain },
    { id: 'drift', label: 'Drift Detection', icon: AlertTriangle },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle, count: alerts.filter(a => !a.acknowledged).length }
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="ml-dashboard-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Brain className="text-[#9D00FF]" />
            ML Performance Dashboard
          </h1>
          <p className="text-[#A1A1AA] mt-1">Model monitoring, drift detection & analytics</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a]"
        >
          <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          <span className="text-[#A1A1AA]">Refresh</span>
        </button>
      </div>

      {/* Summary Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Active Models</p>
            <p className="text-2xl font-bold text-[#00FF94]">{dashboard.summary?.active_models}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Degraded</p>
            <p className="text-2xl font-bold text-yellow-400">{dashboard.summary?.degraded_models}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Predictions Today</p>
            <p className="text-2xl font-bold text-white">{dashboard.summary?.(total_predictions_today ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Avg Accuracy</p>
            <p className="text-2xl font-bold text-white">{(dashboard.summary?.avg_accuracy_24h * 100)?.toFixed(1)}%</p>
          </div>
          <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
            <p className="text-sm text-[#A1A1AA]">Avg Sharpe</p>
            <p className="text-2xl font-bold text-[#9D00FF]">{dashboard.summary?.(avg_sharpe_24h ?? 0).toFixed(2)}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
              activeTab === tab.id
                ? 'bg-[#9D00FF]/20 text-[#9D00FF] border border-[#9D00FF]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
            {tab.count > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && dashboard && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Models Grid */}
            <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Active Models</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboard.models?.map((model) => (
                  <div
                    key={model.model_id}
                    onClick={() => {
                      setSelectedModel(model.model_id);
                      setActiveTab('models');
                    }}
                    className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg cursor-pointer hover:border-[#9D00FF]/50 transition"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">{model.name}</span>
                      <span className={`px-2 py-0.5 text-xs rounded ${getHealthColor(model.health)}`}>
                        {model.health}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <p className="text-[#A1A1AA]">Accuracy</p>
                        <p className="text-white">{(model.accuracy_24h * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-[#A1A1AA]">Sharpe</p>
                        <p className="text-[#00FF94]">{(model?.sharpe_24h ?? 0).toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-[#A1A1AA]">Predictions</p>
                        <p className="text-white">{model.predictions_today.toLocaleString()}</p>
                      </div>
                    </div>
                    {model.alert && (
                      <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs text-yellow-400">
                        {model.alert}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Drift Overview */}
            {driftStatus && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <h2 className="text-lg font-semibold text-white mb-4">Drift Status</h2>
                <div className="space-y-3">
                  {driftStatus.drift_reports?.map((report) => (
                    <div key={report.model_id} className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <div>
                        <p className="text-white text-sm">{report.model_name}</p>
                        <p className="text-xs text-[#A1A1AA]">Score: {(report?.overall_drift_score ?? 0).toFixed(3)}</p>
                      </div>
                      <span className={`font-medium ${getDriftColor(report.drift_status)}`}>
                        {report.drift_status.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Alerts */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Recent Alerts</h2>
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-[#A1A1AA]">
                  <Check size={32} className="mx-auto text-[#00FF94] mb-2" />
                  No active alerts
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.slice(0, 5).map((alert) => (
                    <div
                      key={alert.alert_id}
                      className={`p-3 rounded-lg border ${
                        alert.severity === 'high' ? 'bg-red-500/10 border-red-500/30' :
                        alert.severity === 'medium' ? 'bg-yellow-500/10 border-yellow-500/30' :
                        'bg-[#0A0A0A] border-[#333]'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-white text-sm">{alert.message}</p>
                          <p className="text-xs text-[#A1A1AA] mt-1">{alert.model_id}</p>
                        </div>
                        {!alert.acknowledged && (
                          <button
                            onClick={() => acknowledgeAlert(alert.alert_id)}
                            className="p-1 hover:bg-white/10 rounded"
                          >
                            <Check size={14} className="text-[#A1A1AA]" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === 'models' && (
          <motion.div
            key="models"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Model Selector */}
            <div className="flex gap-2 flex-wrap">
              {dashboard?.models?.map((model) => (
                <button
                  key={model.model_id}
                  onClick={() => setSelectedModel(model.model_id)}
                  className={`px-4 py-2 rounded-lg transition ${
                    selectedModel === model.model_id
                      ? 'bg-[#9D00FF] text-white'
                      : 'bg-[#1F1F1F] text-[#A1A1AA] hover:bg-[#2a2a2a]'
                  }`}
                >
                  {model.name.split(' ').slice(0, 2).join(' ')}
                </button>
              ))}
            </div>

            {modelDetails && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Metrics Chart */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-4">Performance History (24h)</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={modelDetails.metrics_history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="timestamp" tickFormatter={(v) => new Date(v).getHours() + ':00'} stroke="#A1A1AA" />
                        <YAxis stroke="#A1A1AA" />
                        <Tooltip contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }} />
                        <Line type="monotone" dataKey="accuracy" stroke="#00FF94" name="Accuracy" dot={false} />
                        <Line type="monotone" dataKey="sharpe_ratio" stroke="#9D00FF" name="Sharpe" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Current Metrics */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-4">Current Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {modelDetails.current_metrics && Object.entries(modelDetails.current_metrics)
                      .filter(([key]) => !['timestamp'].includes(key))
                      .slice(0, 8)
                      .map(([key, value]) => (
                        <div key={key} className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                          <p className="text-sm text-[#A1A1AA] capitalize">{key.replace('_', ' ')}</p>
                          <p className="text-lg font-bold text-white">
                            {typeof value === 'number' ? value.toFixed(3) : value}
                          </p>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Feature Drift */}
                <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-4">Feature Drift Analysis</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {modelDetails.feature_drift?.map((feature) => (
                      <div
                        key={feature.feature}
                        className={`p-3 rounded-lg border ${
                          feature.status === 'drift_detected' ? 'bg-red-500/10 border-red-500/30' :
                          feature.status === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                          'bg-[#0A0A0A] border-[#333]'
                        }`}
                      >
                        <p className="text-white text-sm truncate">{feature.feature}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-[#A1A1AA]">Score: {(feature?.drift_score ?? 0).toFixed(3)}</span>
                          <span className={`text-xs ${getDriftColor(feature.status)}`}>
                            {feature.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Resource Usage */}
                <div className="lg:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-4">Resource Usage</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <p className="text-sm text-[#A1A1AA]">Avg Latency</p>
                      <p className="text-xl font-bold text-white">{modelDetails.resource_usage?.avg_latency_ms}ms</p>
                    </div>
                    <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <p className="text-sm text-[#A1A1AA]">P99 Latency</p>
                      <p className="text-xl font-bold text-white">{modelDetails.resource_usage?.p99_latency_ms}ms</p>
                    </div>
                    <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <p className="text-sm text-[#A1A1AA]">Memory</p>
                      <p className="text-xl font-bold text-white">{modelDetails.resource_usage?.memory_mb}MB</p>
                    </div>
                    <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <p className="text-sm text-[#A1A1AA]">CPU</p>
                      <p className="text-xl font-bold text-white">{modelDetails.resource_usage?.cpu_percent}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'drift' && driftStatus && (
          <motion.div
            key="drift"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[#00FF94]/10 border border-[#00FF94]/50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-[#00FF94]">{driftStatus.summary?.stable}</p>
                <p className="text-sm text-[#A1A1AA]">Stable</p>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-yellow-400">{driftStatus.summary?.warning}</p>
                <p className="text-sm text-[#A1A1AA]">Warning</p>
              </div>
              <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-red-400">{driftStatus.summary?.drifted}</p>
                <p className="text-sm text-[#A1A1AA]">Drifted</p>
              </div>
            </div>

            {/* Drift Reports */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h3 className="text-white font-semibold mb-4">Drift Reports</h3>
              <div className="space-y-4">
                {driftStatus.drift_reports?.map((report) => (
                  <div key={report.model_id} className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-white font-medium">{report.model_name}</p>
                        <p className="text-sm text-[#A1A1AA]">Last check: {new Date(report.last_check).toLocaleTimeString()}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        report.drift_status === 'stable' ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                        report.drift_status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {report.drift_status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-[#A1A1AA]">Drift Score</p>
                        <p className="text-white font-medium">{(report?.overall_drift_score ?? 0).toFixed(3)}</p>
                      </div>
                      <div>
                        <p className="text-[#A1A1AA]">Features Drifted</p>
                        <p className="text-white font-medium">{report.features_drifted}</p>
                      </div>
                      <div>
                        <p className="text-[#A1A1AA]">Concept Drift</p>
                        <p className={report.concept_drift ? 'text-red-400' : 'text-[#00FF94]'}>
                          {report.concept_drift ? 'Yes' : 'No'}
                        </p>
                      </div>
                      <div>
                        <p className="text-[#A1A1AA]">Data Drift</p>
                        <p className={report.data_drift ? 'text-yellow-400' : 'text-[#00FF94]'}>
                          {report.data_drift ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                    {report.recommended_action && (
                      <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
                        <strong>Recommended:</strong> {report.recommended_action}
                      </div>
                    )}
                    {report.drifted_features && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {report.drifted_features.map((f) => (
                          <span key={f} className="px-2 py-1 bg-[#333] text-[#A1A1AA] text-xs rounded">
                            {f}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'alerts' && (
          <motion.div
            key="alerts"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <h3 className="text-white font-semibold mb-4">Active Alerts</h3>
            {alerts.length === 0 ? (
              <div className="text-center py-12">
                <Check size={48} className="mx-auto text-[#00FF94] mb-4" />
                <p className="text-white font-medium">All Clear!</p>
                <p className="text-[#A1A1AA]">No active alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`p-4 rounded-lg border ${
                      alert.severity === 'high' ? 'bg-red-500/10 border-red-500/30' :
                      alert.severity === 'medium' ? 'bg-yellow-500/10 border-yellow-500/30' :
                      'bg-[#0A0A0A] border-[#333]'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 text-xs rounded ${
                            alert.severity === 'high' ? 'bg-red-500/30 text-red-400' :
                            alert.severity === 'medium' ? 'bg-yellow-500/30 text-yellow-400' :
                            'bg-blue-500/30 text-blue-400'
                          }`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <span className="text-xs text-[#A1A1AA]">{alert.type}</span>
                        </div>
                        <p className="text-white">{alert.message}</p>
                        <p className="text-sm text-[#A1A1AA] mt-1">Model: {alert.model_id}</p>
                        {alert.recommended_action && (
                          <p className="text-sm text-[#9D00FF] mt-2">→ {alert.recommended_action}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {alert.acknowledged ? (
                          <span className="text-xs text-[#00FF94]">Acknowledged</span>
                        ) : (
                          <button
                            onClick={() => acknowledgeAlert(alert.alert_id)}
                            className="px-3 py-1 bg-[#333] text-white text-sm rounded hover:bg-[#444]"
                          >
                            Acknowledge
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MLDashboard;
