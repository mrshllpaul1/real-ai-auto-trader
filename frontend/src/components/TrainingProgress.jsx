import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent } from './ui/card';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { 
  Brain, CheckCircle, XCircle, Clock, Loader2,
  ChevronDown, ChevronUp, Wifi, WifiOff, Square, StopCircle
} from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

/**
 * Training Progress Monitor Component
 * 
 * Shows real-time progress of long-running training tasks.
 * Uses WebSocket for real-time updates with polling fallback.
 * Can be used as a floating notification or embedded component.
 */
const TrainingProgress = ({ 
  taskId = null, 
  embedded = false,
  onComplete = null,
  pollInterval = 5000  // Increased since WebSocket handles real-time
}) => {
  const [task, setTask] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [expanded, setExpanded] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      // Get WebSocket URL from current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/training-progress/ws`;
      
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        
        ws.onopen = () => {
          console.log('[TrainingProgress] WebSocket connected');
          setWsConnected(true);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'progress_update' || data.type === 'initial_state') {
              // Update specific task if we're tracking one
              if (taskId && data.task_id === taskId) {
                setTask(data);
                if (data.status === 'completed' && onComplete) {
                  onComplete(data);
                }
              }
              
              // Update active tasks list
              setActiveTasks(prev => {
                const updated = prev.filter(t => t.task_id !== data.task_id);
                if (data.status === 'running') {
                  updated.push(data);
                }
                return updated;
              });
            }
          } catch (e) {
            console.error('[TrainingProgress] Error parsing WebSocket message:', e);
          }
        };
        
        ws.onclose = () => {
          console.log('[TrainingProgress] WebSocket disconnected');
          setWsConnected(false);
          // Reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };
        
        ws.onerror = (error) => {
          console.error('[TrainingProgress] WebSocket error:', error);
          setWsConnected(false);
        };
        
      } catch (e) {
        console.error('[TrainingProgress] Failed to create WebSocket:', e);
        setWsConnected(false);
      }
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [taskId, onComplete]);

  // Fallback polling (less frequent since WebSocket handles most updates)
  const fetchActiveTasks = useCallback(async () => {
    try {
      const response = await api.get('/training-progress/active');
      setActiveTasks(response.data.tasks || []);
    } catch (err) {
      // Silently fail for active tasks fetch
    }
  }, []);

  // Fetch specific task status (fallback)
  const fetchTaskStatus = useCallback(async () => {
    if (!taskId) return;
    try {
      const response = await api.get(`/training-progress/task/${taskId}`);
      setTask(response.data);
      
      if (response.data.status === 'completed' && onComplete) {
        onComplete(response.data);
      }
    } catch (err) {
      if (err.response?.status !== 404) {
        console.error('Error fetching task:', err);
      }
    }
  }, [taskId, onComplete]);

  useEffect(() => {
    // Initial fetch
    if (taskId) {
      fetchTaskStatus();
    } else {
      fetchActiveTasks();
    }

    // Fallback polling (only if WebSocket isn't connected)
    const interval = setInterval(() => {
      if (!wsConnected) {
        if (taskId) {
          fetchTaskStatus();
        } else {
          fetchActiveTasks();
        }
      }
    }, pollInterval);

    return () => clearInterval(interval);
  }, [taskId, fetchTaskStatus, fetchActiveTasks, pollInterval]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-400" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'border-blue-500/30 bg-blue-500/5';
      case 'completed':
        return 'border-green-500/30 bg-green-500/5';
      case 'failed':
        return 'border-red-500/30 bg-red-500/5';
      default:
        return 'border-gray-500/30 bg-gray-500/5';
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const handleStopTask = async (taskId) => {
    try {
      await api.post(`/training-progress/stop/${taskId}`);
      toast.success('Training stopped', {
        description: 'The training task has been stopped gracefully'
      });
      // Remove task from activeTasks
      setActiveTasks(prev => prev.filter(t => t.task_id !== taskId));
    } catch (error) {
      toast.error('Failed to stop training', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  const handleStopAllTasks = async () => {
    try {
      await api.post('/training-progress/stop-all');
      toast.success('All training stopped', {
        description: 'All training tasks have been stopped'
      });
      setActiveTasks([]);
    } catch (error) {
      toast.error('Failed to stop training', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  const renderTask = (t) => (
    <div 
      key={t.task_id}
      className={`p-3 rounded-lg border ${getStatusColor(t.status)} transition-all`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon(t.status)}
          <span className="text-sm font-medium text-white capitalize">
            {t.task_type?.replace(/-/g, ' ') || 'Training'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {formatDuration(t.duration_seconds)}
          </span>
          {t.status === 'running' && (
            <button
              onClick={(e) => { e.stopPropagation(); handleStopTask(t.task_id); }}
              className="p-1 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
              title="Stop this training"
            >
              <Square className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
      
      {t.status === 'running' && (
        <>
          <Progress 
            value={t.progress} 
            className="h-2 mb-2 bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>{t.message || 'Processing...'}</span>
            <span>{t.progress}%</span>
          </div>
          {t.current_item && (
            <div className="text-xs text-gray-500 mt-1">
              Current: {t.current_item}
            </div>
          )}
          {t.items_processed > 0 && t.total_items > 0 && (
            <div className="text-xs text-gray-500 mt-1">
              {t.items_processed} / {t.total_items} items
            </div>
          )}
        </>
      )}
      
      {t.status === 'completed' && (
        <div className="text-xs text-green-400">
          ✓ {t.message || 'Completed successfully'}
        </div>
      )}
      
      {t.status === 'failed' && (
        <div className="text-xs text-red-400">
          ✗ {t.error || 'Task failed'}
        </div>
      )}
      
      {t.status === 'stopped' && (
        <div className="text-xs text-orange-400">
          ⏹ {t.message || 'Training stopped'}
        </div>
      )}
    </div>
  );

  // Single task mode
  if (taskId && task) {
    if (embedded) {
      return renderTask(task);
    }
    return (
      <Card className="bg-[#0a0a0a] border-gray-800">
        <CardContent className="p-4">
          {renderTask(task)}
        </CardContent>
      </Card>
    );
  }

  // Active tasks mode - floating notification style
  if (!taskId && activeTasks.length > 0) {
    return (
      <div className="fixed bottom-4 right-4 z-50 w-80">
        <Card className="bg-[#0a0a0a]/95 border-gray-700 backdrop-blur-sm shadow-xl">
          <CardContent className="p-3">
            <div 
              className="flex items-center justify-between cursor-pointer mb-2"
              onClick={() => setExpanded(!expanded)}
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-white">
                  Training Progress ({activeTasks.length})
                </span>
                {wsConnected ? (
                  <Wifi className="w-3 h-3 text-green-400" title="WebSocket connected" />
                ) : (
                  <WifiOff className="w-3 h-3 text-orange-400" title="Using polling" />
                )}
              </div>
              <div className="flex items-center gap-1">
                {activeTasks.length > 0 && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleStopAllTasks(); }}
                    className="px-2 py-1 rounded text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 hover:text-red-300 transition-colors flex items-center gap-1"
                    title="Stop all training"
                  >
                    <StopCircle className="w-3 h-3" />
                    Stop All
                  </button>
                )}
                {expanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                )}
              </div>
            </div>
            
            {expanded && (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {activeTasks.map(renderTask)}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

export default TrainingProgress;
