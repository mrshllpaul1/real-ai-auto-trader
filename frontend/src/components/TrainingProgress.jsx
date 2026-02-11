import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from './ui/card';
import { Progress } from './ui/progress';
import { 
  Brain, CheckCircle, XCircle, Clock, Loader2,
  ChevronDown, ChevronUp
} from 'lucide-react';
import api from '../services/api';

/**
 * Training Progress Monitor Component
 * 
 * Shows real-time progress of long-running training tasks.
 * Can be used as a floating notification or embedded component.
 */
const TrainingProgress = ({ 
  taskId = null, 
  embedded = false,
  onComplete = null,
  pollInterval = 2000 
}) => {
  const [task, setTask] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [expanded, setExpanded] = useState(true);
  const [error, setError] = useState(null);

  // Fetch specific task status
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

  // Fetch all active tasks
  const fetchActiveTasks = useCallback(async () => {
    try {
      const response = await api.get('/training-progress/active');
      setActiveTasks(response.data.tasks || []);
    } catch (err) {
      // Silently fail for active tasks fetch
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    if (taskId) {
      fetchTaskStatus();
    } else {
      fetchActiveTasks();
    }

    // Poll for updates
    const interval = setInterval(() => {
      if (taskId) {
        fetchTaskStatus();
      } else {
        fetchActiveTasks();
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
        <span className="text-xs text-gray-400">
          {formatDuration(t.duration_seconds)}
        </span>
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
              </div>
              {expanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              )}
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
