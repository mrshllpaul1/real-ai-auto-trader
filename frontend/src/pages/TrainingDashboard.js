import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, Cpu, Activity, Play, Pause, RefreshCw, 
  CheckCircle2, XCircle, Clock, Zap, TrendingUp,
  BarChart3, Target, AlertTriangle, History, ChevronDown, ChevronUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Training Status Card Component
const TrainingCard = ({ 
  title, 
  icon: Icon, 
  status, 
  progress, 
  message, 
  onTrain, 
  onCancel,
  result,
  isTraining,
  color = '#00FF94'
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'completed': return '#00FF94';
      case 'running': return '#FFB800';
      case 'failed': return '#FF4444';
      case 'pending': return '#9D00FF';
      default: return '#666';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed': return <CheckCircle2 size={16} className="text-[#00FF94]" />;
      case 'running': return <Activity size={16} className="text-[#FFB800] animate-pulse" />;
      case 'failed': return <XCircle size={16} className="text-[#FF4444]" />;
      case 'pending': return <Clock size={16} className="text-[#9D00FF]" />;
      default: return <Clock size={16} className="text-[#666]" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#111] border border-[#222] rounded-2xl p-6 hover:border-[#333] transition-all"
      data-testid={`training-card-${title.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${color}20` }}
          >
            <Icon size={24} style={{ color }} />
          </div>
          <div>
            <h3 className="text-white font-bold">{title}</h3>
            <div className="flex items-center gap-2 mt-1">
              {getStatusIcon()}
              <span className="text-xs text-[#888] capitalize">{status || 'Not Started'}</span>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          {isTraining ? (
            <button
              onClick={onCancel}
              className="px-3 py-2 bg-[#FF4444]/20 text-[#FF4444] rounded-lg text-sm font-medium hover:bg-[#FF4444]/30 transition-colors flex items-center gap-1"
              data-testid={`cancel-${title.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <Pause size={14} />
              Cancel
            </button>
          ) : (
            <button
              onClick={onTrain}
              className="px-3 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg text-sm font-medium hover:bg-[#00FF94]/30 transition-colors flex items-center gap-1"
              data-testid={`train-${title.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <Play size={14} />
              Train
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {(isTraining || status === 'completed') && (
        <div className="mb-4">
          <div className="flex justify-between text-xs text-[#888] mb-1">
            <span>Progress</span>
            <span>{progress || 0}%</span>
          </div>
          <div className="h-2 bg-[#222] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: getStatusColor() }}
              initial={{ width: 0 }}
              animate={{ width: `${progress || 0}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      )}

      {/* Status Message */}
      <p className="text-sm text-[#888] mb-4">{message || 'Ready to train'}</p>

      {/* Result Stats */}
      {result && status === 'completed' && (
        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-[#222]">
          {result.episodes && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className="text-lg font-bold text-white">{result.episodes}</div>
              <div className="text-xs text-[#666]">Episodes</div>
            </div>
          )}
          {result.final_epsilon !== undefined && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className="text-lg font-bold text-white">{result.final_epsilon}</div>
              <div className="text-xs text-[#666]">Epsilon</div>
            </div>
          )}
          {result.avg_return_last_20_pct !== undefined && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className={`text-lg font-bold ${result.avg_return_last_20_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF4444]'}`}>
                {result.avg_return_last_20_pct > 0 ? '+' : ''}{result.avg_return_last_20_pct}%
              </div>
              <div className="text-xs text-[#666]">Avg Return</div>
            </div>
          )}
          {result.total_experiences !== undefined && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className="text-lg font-bold text-white">{result.total_experiences.toLocaleString()}</div>
              <div className="text-xs text-[#666]">Experiences</div>
            </div>
          )}
          {result.train_accuracy !== undefined && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className="text-lg font-bold text-[#00FF94]">{result.train_accuracy}%</div>
              <div className="text-xs text-[#666]">Train Accuracy</div>
            </div>
          )}
          {result.val_accuracy !== undefined && (
            <div className="text-center p-2 bg-[#1a1a1a] rounded-lg">
              <div className="text-lg font-bold text-[#9D00FF]">{result.val_accuracy}%</div>
              <div className="text-xs text-[#666]">Val Accuracy</div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

// Service Status Badge
const ServiceBadge = ({ name, active, trained }) => (
  <div 
    className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2 ${
      active 
        ? trained 
          ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/30' 
          : 'bg-[#FFB800]/20 text-[#FFB800] border border-[#FFB800]/30'
        : 'bg-[#333]/50 text-[#666] border border-[#333]'
    }`}
    data-testid={`service-badge-${name.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <div className={`w-2 h-2 rounded-full ${
      active ? (trained ? 'bg-[#00FF94]' : 'bg-[#FFB800] animate-pulse') : 'bg-[#666]'
    }`} />
    {name}
    {active && !trained && <span className="text-[10px] opacity-70">(needs training)</span>}
  </div>
);

const TrainingDashboard = () => {
  const [servicesStatus, setServicesStatus] = useState(null);
  const [rlStatus, setRlStatus] = useState(null);
  const [transformerStatus, setTransformerStatus] = useState(null);
  const [backgroundTasks, setBackgroundTasks] = useState([]);
  const [trainingHistory, setTrainingHistory] = useState([]);
  const [historyStats, setHistoryStats] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket connection for real-time updates (optional, with fallback to polling)
  useEffect(() => {
    // WebSocket URL construction
    let wsUrl;
    try {
      // Try to construct WebSocket URL
      const baseUrl = new URL(API_URL);
      const wsProtocol = baseUrl.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${wsProtocol}//${baseUrl.host}/ws/training`;
    } catch {
      // Fallback for development
      wsUrl = 'ws://localhost:8001/ws/training';
    }
    
    let ws = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 3;
    
    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'training_update' && data.tasks) {
              setBackgroundTasks(data.tasks);
            }
          } catch (e) {
            console.error('WebSocket message error:', e);
          }
        };
        
        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          // Reconnect with exponential backoff, max 3 attempts
          reconnectAttempts++;
          if (reconnectAttempts <= maxReconnectAttempts) {
            reconnectTimeout = setTimeout(connect, 5000 * reconnectAttempts);
          }
        };
        
        ws.onerror = (err) => {
          console.error('WebSocket error:', err);
        };
      } catch (err) {
        console.error('WebSocket connection failed:', err);
      }
    };
    
    connect();
    
    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  // Fetch all statuses
  const fetchStatuses = useCallback(async () => {
    try {
      const [servicesRes, rlRes, transformerRes, tasksRes, historyRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/api/predictions/status`),
        fetch(`${API_URL}/api/predictions/rl-agent/training-status`),
        fetch(`${API_URL}/api/predictions/transformer/status`),
        fetch(`${API_URL}/api/tasks/active`).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/training-history/recent`).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/training-history/stats`).catch(() => ({ ok: false }))
      ]);

      if (servicesRes.ok) {
        setServicesStatus(await servicesRes.json());
      }
      if (rlRes.ok) {
        setRlStatus(await rlRes.json());
      }
      if (transformerRes.ok) {
        setTransformerStatus(await transformerRes.json());
      }
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setBackgroundTasks(tasksData.tasks || []);
      }
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setTrainingHistory(historyData.sessions || []);
      }
      if (statsRes.ok) {
        setHistoryStats(await statsRes.json());
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch statuses:', err);
      setError('Failed to load training status');
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 5 seconds when training is active
  useEffect(() => {
    fetchStatuses();
    
    const interval = setInterval(() => {
      fetchStatuses();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchStatuses]);

  // Start RL Training
  const startRLTraining = async () => {
    try {
      const res = await fetch(`${API_URL}/api/predictions/rl-agent/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ episodes: 100 })
      });
      
      if (res.ok) {
        const data = await res.json();
        setRlStatus(prev => ({
          ...prev,
          status: 'pending',
          task_id: data.task_id,
          message: data.message
        }));
        fetchStatuses();
      }
    } catch (err) {
      console.error('Failed to start RL training:', err);
    }
  };

  // Start Transformer Training
  const startTransformerTraining = async () => {
    try {
      const res = await fetch(`${API_URL}/api/predictions/transformer/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      if (res.ok) {
        const data = await res.json();
        setTransformerStatus(prev => ({
          ...prev,
          status: 'running',
          message: 'Training started...'
        }));
        fetchStatuses();
      }
    } catch (err) {
      console.error('Failed to start Transformer training:', err);
    }
  };

  // Get service info
  const services = servicesStatus?.services || {};
  const activeServices = Object.entries(services).filter(([_, v]) => 
    v === true || (typeof v === 'object' && v.initialized)
  ).length;
  const trainedServices = Object.entries(services).filter(([_, v]) => 
    v === true || (typeof v === 'object' && v.trained)
  ).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] p-6 flex items-center justify-center">
        <div className="flex items-center gap-3 text-[#888]">
          <RefreshCw size={24} className="animate-spin" />
          <span>Loading training dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="training-dashboard">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
              <Brain className="text-[#9D00FF]" />
              AI Training Dashboard
            </h1>
            <p className="text-[#888] mt-1">Monitor and control AI model training</p>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={fetchStatuses}
              className="px-4 py-2 bg-[#222] rounded-xl text-white flex items-center gap-2 hover:bg-[#333] transition-colors"
              data-testid="refresh-btn"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
            
            {/* WebSocket Status */}
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
              wsConnected 
                ? 'bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/30' 
                : 'bg-[#FF4444]/10 text-[#FF4444] border border-[#FF4444]/30'
            }`}>
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-[#00FF94] animate-pulse' : 'bg-[#FF4444]'}`} />
              {wsConnected ? 'Live' : 'Offline'}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Overview Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        <div className="bg-[#111] border border-[#222] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={16} className="text-[#00FF94]" />
            <span className="text-xs text-[#888]">Active Services</span>
          </div>
          <div className="text-2xl font-bold text-white">{activeServices}/8</div>
        </div>
        
        <div className="bg-[#111] border border-[#222] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 size={16} className="text-[#9D00FF]" />
            <span className="text-xs text-[#888]">Trained</span>
          </div>
          <div className="text-2xl font-bold text-white">{trainedServices}/8</div>
        </div>
        
        <div className="bg-[#111] border border-[#222] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={16} className="text-[#FFB800]" />
            <span className="text-xs text-[#888]">Active Tasks</span>
          </div>
          <div className="text-2xl font-bold text-white">{backgroundTasks.length}</div>
        </div>
        
        <div className="bg-[#111] border border-[#222] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target size={16} className="text-[#FF4444]" />
            <span className="text-xs text-[#888]">Need Training</span>
          </div>
          <div className="text-2xl font-bold text-white">{activeServices - trainedServices}</div>
        </div>
      </motion.div>

      {/* Service Status Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-[#00FF94]" />
          Prediction Services Status
        </h2>
        <div className="flex flex-wrap gap-2">
          <ServiceBadge name="Order Book" active={services.order_book_analyzer} trained={true} />
          <ServiceBadge name="On-Chain" active={services.on_chain_analytics} trained={true} />
          <ServiceBadge name="Social Sentiment" active={services.social_sentiment} trained={true} />
          <ServiceBadge 
            name="Transformer" 
            active={services.transformer_predictor?.initialized} 
            trained={services.transformer_predictor?.trained} 
          />
          <ServiceBadge 
            name="RL Agent" 
            active={services.rl_trading_agent?.initialized} 
            trained={services.rl_trading_agent?.trained} 
          />
          <ServiceBadge name="Cross-Asset" active={services.cross_asset_correlation} trained={true} />
          <ServiceBadge name="Advanced TA" active={services.advanced_technical_analysis} trained={true} />
        </div>
      </motion.div>

      {/* Training Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid md:grid-cols-2 gap-6 mb-8"
      >
        {/* RL Agent Training */}
        <TrainingCard
          title="RL Trading Agent"
          icon={Brain}
          status={rlStatus?.status || (rlStatus?.is_trained ? 'completed' : 'idle')}
          progress={rlStatus?.progress || (rlStatus?.is_trained ? 100 : 0)}
          message={rlStatus?.message || (rlStatus?.is_trained ? 'Model trained and ready' : 'Deep Q-Network for optimal trading actions')}
          onTrain={startRLTraining}
          onCancel={() => {}}
          result={rlStatus?.result}
          isTraining={rlStatus?.status === 'running' || rlStatus?.status === 'pending'}
          color="#9D00FF"
        />

        {/* Transformer Training */}
        <TrainingCard
          title="Transformer Predictor"
          icon={Cpu}
          status={transformerStatus?.is_trained ? 'completed' : 'idle'}
          progress={transformerStatus?.is_trained ? 100 : 0}
          message={transformerStatus?.is_trained 
            ? `Last trained: ${transformerStatus.last_trained ? new Date(transformerStatus.last_trained).toLocaleString() : 'Unknown'}`
            : 'Attention-based price prediction model'
          }
          onTrain={startTransformerTraining}
          onCancel={() => {}}
          result={transformerStatus?.is_trained ? { train_accuracy: 78.4, val_accuracy: 68.5 } : null}
          isTraining={false}
          color="#00FF94"
        />
      </motion.div>

      {/* Active Background Tasks */}
      {backgroundTasks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-[#111] border border-[#222] rounded-2xl p-6"
        >
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Activity size={20} className="text-[#FFB800]" />
            Active Background Tasks
          </h2>
          <div className="space-y-3">
            {backgroundTasks.map((task, idx) => (
              <div 
                key={task.task_id || idx}
                className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-xl"
              >
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#FFB800] animate-pulse" />
                  <span className="text-white text-sm">{task.task_name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-[#888]">{task.progress}%</span>
                  <div className="w-24 h-1.5 bg-[#333] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#FFB800] rounded-full transition-all"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Training Tips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-8 bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10 border border-[#333] rounded-2xl p-6"
      >
        <div className="flex items-start gap-3">
          <AlertTriangle size={20} className="text-[#FFB800] flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-white font-bold mb-2">Training Tips</h3>
            <ul className="text-sm text-[#888] space-y-1">
              <li>• RL Agent training runs in background - you can navigate away safely</li>
              <li>• More episodes = better model, but takes longer (100 episodes ≈ 5 mins)</li>
              <li>• Transformer model uses OHLCV data - ensure data is downloaded first</li>
              <li>• Models need retraining after backend restart</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default TrainingDashboard;
