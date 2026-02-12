/**
 * System State Management Hook
 * ============================
 * Manages persistent running states across the app.
 * States survive page navigation and browser refresh.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

/**
 * Component types that can be tracked
 */
export const ComponentType = {
  AUTO_TRADING: 'auto_trading',
  ADAPTIVE_MONITORING: 'adaptive_monitoring',
  MASTER_ORCHESTRATOR: 'master_orchestrator',
  TETHYS_TRADING: 'tethys_trading',
  TETHYS_AUTOPILOT: 'tethys_autopilot',
  UNIVERSE_REBUILD: 'universe_rebuild',
  MODEL_TRAINING: 'model_training',
  REAL_TRADING: 'real_trading',
};

/**
 * Get all system states
 */
export const fetchAllSystemStates = async (userId = 'default') => {
  try {
    const response = await api.get(`/system-state/all?user_id=${userId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch system states:', error);
    return { running_components: [], states: {} };
  }
};

/**
 * Get state of a specific component
 */
export const fetchComponentState = async (component, userId = 'default') => {
  try {
    const response = await api.get(`/system-state/${component}?user_id=${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch ${component} state:`, error);
    return { is_running: false };
  }
};

/**
 * Set state of a component
 */
export const setComponentState = async (component, isRunning, metadata = {}, userId = 'default') => {
  try {
    const response = await api.post('/system-state/set', {
      component,
      is_running: isRunning,
      user_id: userId,
      metadata,
    });
    return response.data;
  } catch (error) {
    console.error(`Failed to set ${component} state:`, error);
    return { success: false };
  }
};

/**
 * Hook to manage a single component's running state
 * @param {string} component - Component type from ComponentType
 * @param {object} options - Options
 */
export const useComponentState = (component, options = {}) => {
  const {
    userId = 'default',
    pollInterval = null, // Set to milliseconds to enable polling
    onStateChange = null,
  } = options;

  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [metadata, setMetadata] = useState({});
  const mountedRef = useRef(true);

  // Fetch initial state
  const fetchState = useCallback(async () => {
    const state = await fetchComponentState(component, userId);
    if (mountedRef.current) {
      const newIsRunning = state.is_running || false;
      if (newIsRunning !== isRunning && onStateChange) {
        onStateChange(newIsRunning);
      }
      setIsRunning(newIsRunning);
      setMetadata(state.metadata || {});
      setLoading(false);
    }
    return state;
  }, [component, userId, isRunning, onStateChange]);

  // Update state
  const updateState = useCallback(async (newIsRunning, newMetadata = {}) => {
    const result = await setComponentState(component, newIsRunning, newMetadata, userId);
    if (result.success && mountedRef.current) {
      setIsRunning(newIsRunning);
      setMetadata(prev => ({ ...prev, ...newMetadata }));
      if (onStateChange) {
        onStateChange(newIsRunning);
      }
    }
    return result;
  }, [component, userId, onStateChange]);

  // Initial fetch
  useEffect(() => {
    mountedRef.current = true;
    fetchState();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Polling
  useEffect(() => {
    if (!pollInterval) return;

    const interval = setInterval(fetchState, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, fetchState]);

  return {
    isRunning,
    loading,
    metadata,
    setRunning: updateState,
    refresh: fetchState,
  };
};

/**
 * Hook to manage all system states at once
 */
export const useAllSystemStates = (options = {}) => {
  const {
    userId = 'default',
    pollInterval = 30000, // 30 seconds default
  } = options;

  const [states, setStates] = useState({});
  const [runningComponents, setRunningComponents] = useState([]);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  const fetchStates = useCallback(async () => {
    const data = await fetchAllSystemStates(userId);
    if (mountedRef.current) {
      setStates(data.states || {});
      setRunningComponents(data.running_components || []);
      setLoading(false);
    }
    return data;
  }, [userId]);

  useEffect(() => {
    mountedRef.current = true;
    fetchStates();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!pollInterval) return;
    const interval = setInterval(fetchStates, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, fetchStates]);

  const isComponentRunning = useCallback((component) => {
    return states[component]?.is_running || false;
  }, [states]);

  return {
    states,
    runningComponents,
    loading,
    isComponentRunning,
    refresh: fetchStates,
  };
};

/**
 * Helper hook for common toggle patterns
 */
export const useToggleComponent = (component, startApi, stopApi, options = {}) => {
  const { isRunning, loading, setRunning, refresh } = useComponentState(component, options);
  const [toggling, setToggling] = useState(false);

  const toggle = useCallback(async () => {
    setToggling(true);
    try {
      if (isRunning) {
        await stopApi();
        await setRunning(false);
      } else {
        await startApi();
        await setRunning(true);
      }
      await refresh();
    } catch (error) {
      console.error(`Failed to toggle ${component}:`, error);
    } finally {
      setToggling(false);
    }
  }, [isRunning, startApi, stopApi, setRunning, refresh, component]);

  return {
    isRunning,
    loading,
    toggling,
    toggle,
    refresh,
  };
};

export default useComponentState;
