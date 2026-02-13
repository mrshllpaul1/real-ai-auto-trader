import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Brain, CheckCircle, XCircle, Clock, Loader2, Play, Pause,
  ChevronDown, ChevronUp, Square, StopCircle, Zap, TrendingUp,
  Activity, Cpu, BarChart3, Layers, RefreshCw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

/**
 * Visual Training Progress Meter
 * 
 * Beautiful animated progress meter for training visualization.
 * Shows real-time progress with detailed stats.
 */
const VisualTrainingProgress = ({ 
  embedded = false,
  pollInterval = 3000,
  onComplete = null,
  showControls = true,
}) => {
  const [activeTasks, setActiveTasks] = useState([]);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [expanded, setExpanded] = useState(true);
  const [loading, setLoading] = useState(true);
  const animationRef = useRef(null);

  // Fetch active training tasks
  const fetchData = useCallback(async () => {
    try {
      const [tasksRes, statusRes] = await Promise.allSettled([
        api.get('/training-progress/active'),
        api.get('/tethys-train/status')
      ]);

      if (tasksRes.status === 'fulfilled') {
        setActiveTasks(tasksRes.value.data.tasks || []);
      }
      
      if (statusRes.status === 'fulfilled') {
        setTrainingStatus(statusRes.value.data);
      }
    } catch (err) {
      console.error('Error fetching training data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, pollInterval);
    return () => clearInterval(interval);
  }, [fetchData, pollInterval]);

  // Check if any training is happening
  const isTraining = activeTasks.length > 0 || trainingStatus?.is_training;
  const overallProgress = activeTasks.length > 0 
    ? Math.round(activeTasks.reduce((sum, t) => sum + (t.progress || 0), 0) / activeTasks.length)
    : trainingStatus?.progress_pct || 0;

  const handleStopAll = async () => {
    try {
      await api.post('/training-progress/stop-all');
      toast.success('All training stopped');
      fetchData();
    } catch (error) {
      toast.error('Failed to stop training');
    }
  };

  const handleStopTask = async (taskId) => {
    try {
      await api.post(`/training-progress/stop/${taskId}`);
      toast.success('Training stopped');
      fetchData();
    } catch (error) {
      toast.error('Failed to stop training');
    }
  };

  const getProgressColor = (progress) => {
    if (progress < 30) return 'from-red-500 to-orange-500';
    if (progress < 60) return 'from-orange-500 to-yellow-500';
    if (progress < 90) return 'from-yellow-500 to-green-500';
    return 'from-green-500 to-cyan-500';
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-blue-500/20 text-blue-400 animate-pulse">Training</Badge>;
      case 'completed':
        return <Badge className="bg-green-500/20 text-green-400">Complete</Badge>;
      case 'failed':
        return <Badge className="bg-red-500/20 text-red-400">Failed</Badge>;
      case 'stopped':
        return <Badge className="bg-orange-500/20 text-orange-400">Stopped</Badge>;
      default:
        return <Badge className="bg-gray-500/20 text-gray-400">Pending</Badge>;
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    if (mins < 60) return `${mins}m ${secs}s`;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}m`;
  };

  // Circular progress ring component
  const CircularProgress = ({ progress, size = 120, strokeWidth = 8 }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (progress / 100) * circumference;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="none"
            className="text-gray-700"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="url(#progressGradient)"
            strokeWidth={strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-500 ease-out"
          />
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#ec4899" />
            </linearGradient>
          </defs>
        </svg>
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{progress}%</span>
          <span className="text-xs text-gray-400">Complete</span>
        </div>
      </div>
    );
  };

  // If not training and not loading, show idle state
  if (!loading && !isTraining) {
    if (embedded) return null;
    
    return (
      <Card className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-4 text-gray-400">
            <Brain className="w-8 h-8" />
            <div>
              <p className="text-white font-medium">No Active Training</p>
              <p className="text-sm">Click "Train Now" to start training models</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={embedded ? '' : 'w-full'}
    >
      <Card className="bg-gradient-to-br from-purple-900/20 via-gray-900/50 to-cyan-900/20 border-purple-500/30 overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <CardHeader className="relative pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
              Training Progress
              {isTraining && (
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <Zap className="w-4 h-4 text-yellow-400" />
                </motion.div>
              )}
            </CardTitle>
            
            <div className="flex items-center gap-2">
              {isTraining && showControls && (
                <Button 
                  size="sm" 
                  variant="destructive" 
                  onClick={handleStopAll}
                  className="bg-red-500/20 hover:bg-red-500/30 text-red-400"
                >
                  <StopCircle className="w-4 h-4 mr-1" />
                  Stop All
                </Button>
              )}
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={() => setExpanded(!expanded)}
                className="text-gray-400"
              >
                {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="relative">
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="space-y-4"
              >
                {/* Main Progress Display */}
                <div className="flex items-center justify-center gap-8 py-4">
                  <CircularProgress progress={overallProgress} size={140} strokeWidth={10} />
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-cyan-400" />
                      <span className="text-gray-400">Status:</span>
                      {isTraining ? (
                        <Badge className="bg-green-500/20 text-green-400 animate-pulse">
                          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                          Active
                        </Badge>
                      ) : (
                        <Badge className="bg-gray-500/20 text-gray-400">Idle</Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-purple-400" />
                      <span className="text-gray-400">Tasks:</span>
                      <span className="text-white font-medium">{activeTasks.length}</span>
                    </div>
                    
                    {trainingStatus?.current_epoch && (
                      <div className="flex items-center gap-2">
                        <RefreshCw className="w-4 h-4 text-orange-400" />
                        <span className="text-gray-400">Epoch:</span>
                        <span className="text-white font-medium">
                          {trainingStatus.current_epoch}/{trainingStatus.total_epochs || '?'}
                        </span>
                      </div>
                    )}
                    
                    {trainingStatus?.elapsed_time && (
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-400" />
                        <span className="text-gray-400">Elapsed:</span>
                        <span className="text-white font-medium">
                          {formatTime(trainingStatus.elapsed_time)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Overall Progress</span>
                    <span className="text-white font-medium">{overallProgress}%</span>
                  </div>
                  <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full bg-gradient-to-r ${getProgressColor(overallProgress)} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${overallProgress}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </div>

                {/* Individual Tasks */}
                {activeTasks.length > 0 && (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    <div className="text-sm text-gray-400 mb-2">Active Tasks</div>
                    {activeTasks.map((task) => (
                      <motion.div
                        key={task.task_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="p-3 bg-gray-800/50 rounded-lg border border-gray-700"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Cpu className="w-4 h-4 text-cyan-400" />
                            <span className="text-white text-sm font-medium">
                              {task.task_type?.replace(/-/g, ' ') || 'Training Task'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusBadge(task.status)}
                            {task.status === 'running' && showControls && (
                              <button
                                onClick={() => handleStopTask(task.task_id)}
                                className="p-1 rounded hover:bg-red-500/20 text-red-400"
                              >
                                <Square className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                        
                        {task.status === 'running' && (
                          <>
                            <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-1">
                              <motion.div
                                className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${task.progress || 0}%` }}
                              />
                            </div>
                            <div className="flex justify-between text-xs text-gray-400">
                              <span>{task.message || 'Processing...'}</span>
                              <span>{task.progress || 0}%</span>
                            </div>
                            {task.current_item && (
                              <div className="text-xs text-gray-500 mt-1">
                                Current: {task.current_item}
                              </div>
                            )}
                          </>
                        )}
                        
                        {task.status === 'completed' && (
                          <div className="flex items-center gap-1 text-xs text-green-400">
                            <CheckCircle className="w-3 h-3" />
                            {task.message || 'Completed successfully'}
                          </div>
                        )}
                        
                        {task.status === 'failed' && (
                          <div className="flex items-center gap-1 text-xs text-red-400">
                            <XCircle className="w-3 h-3" />
                            {task.error || 'Task failed'}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                )}

                {/* Training Stats */}
                {trainingStatus && (
                  <div className="grid grid-cols-3 gap-3 pt-2 border-t border-gray-700">
                    <div className="text-center">
                      <div className="text-xl font-bold text-cyan-400">
                        {trainingStatus.episodes_completed || 0}
                      </div>
                      <div className="text-xs text-gray-400">Episodes</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-purple-400">
                        {trainingStatus.loss?.toFixed(4) || '0.0000'}
                      </div>
                      <div className="text-xs text-gray-400">Loss</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-green-400">
                        {trainingStatus.reward?.toFixed(2) || '0.00'}
                      </div>
                      <div className="text-xs text-gray-400">Reward</div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default VisualTrainingProgress;
