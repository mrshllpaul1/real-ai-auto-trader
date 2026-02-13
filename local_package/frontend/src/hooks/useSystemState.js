/**
 * System State Management Hook v3
 * ===============================
 * Completely self-contained with inline API calls
 * No external dependencies that could cause circular imports
 */

import React from 'react';

// Component types
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

// Inline API helper to avoid circular dependency
const apiCall = async (method, endpoint, data = null) => {
  const baseUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
  const url = `${baseUrl}/api${endpoint}`;
  
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (data) options.body = JSON.stringify(data);
    
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    return null;
  }
};

// Fetch functions
export const fetchAllSystemStates = async (userId = 'default') => {
  const data = await apiCall('GET', `/system-state/all?user_id=${userId}`);
  return data || {};
};

export const fetchComponentState = async (component, userId = 'default') => {
  const data = await apiCall('GET', `/system-state/${component}?user_id=${userId}`);
  return data || { is_running: false, metadata: {} };
};

export const setComponentState = async (component, isRunning, metadata = {}, userId = 'default') => {
  const data = await apiCall('POST', '/system-state/update', {
    component,
    user_id: userId,
    is_running: isRunning,
    metadata,
  });
  return data || { success: false };
};

// Main hook
export function useComponentState(component, options = {}) {
  const { userId = 'default', pollInterval = null, onStateChange = null } = options;

  const [isRunning, setIsRunning] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [metadata, setMetadata] = React.useState({});
  const mountedRef = React.useRef(true);
  const isRunningRef = React.useRef(isRunning);

  React.useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

  const fetchState = React.useCallback(async () => {
    try {
      const state = await fetchComponentState(component, userId);
      if (mountedRef.current) {
        const newIsRunning = state?.is_running || false;
        if (newIsRunning !== isRunningRef.current && onStateChange) {
          onStateChange(newIsRunning);
        }
        setIsRunning(newIsRunning);
        setMetadata(state?.metadata || {});
        setLoading(false);
      }
    } catch (error) {
      if (mountedRef.current) setLoading(false);
    }
  }, [component, userId, onStateChange]);

  const updateState = React.useCallback(async (newIsRunning, newMetadata = {}) => {
    try {
      const result = await setComponentState(component, newIsRunning, newMetadata, userId);
      if (result?.success && mountedRef.current) {
        setIsRunning(newIsRunning);
        setMetadata(prev => ({ ...prev, ...newMetadata }));
        if (onStateChange) onStateChange(newIsRunning);
      }
      return result || { success: false };
    } catch (error) {
      return { success: false };
    }
  }, [component, userId, onStateChange]);

  React.useEffect(() => {
    mountedRef.current = true;
    fetchState();
    return () => { mountedRef.current = false; };
  }, [fetchState]);

  React.useEffect(() => {
    if (!pollInterval) return;
    const interval = setInterval(fetchState, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, fetchState]);

  return { isRunning, loading, metadata, setRunning: updateState, refresh: fetchState };
}

// All states hook
export function useAllSystemStates(options = {}) {
  const { userId = 'default', pollInterval = null } = options;

  const [states, setStates] = React.useState({});
  const [loading, setLoading] = React.useState(true);
  const mountedRef = React.useRef(true);

  const fetchStates = React.useCallback(async () => {
    try {
      const allStates = await fetchAllSystemStates(userId);
      if (mountedRef.current) {
        setStates(allStates);
        setLoading(false);
      }
    } catch (error) {
      if (mountedRef.current) setLoading(false);
    }
  }, [userId]);

  React.useEffect(() => {
    mountedRef.current = true;
    fetchStates();
    return () => { mountedRef.current = false; };
  }, [fetchStates]);

  React.useEffect(() => {
    if (!pollInterval) return;
    const interval = setInterval(fetchStates, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, fetchStates]);

  const isComponentRunning = React.useCallback((comp) => states[comp]?.is_running || false, [states]);

  const updateComponentState = React.useCallback(async (comp, running, meta = {}) => {
    const result = await setComponentState(comp, running, meta, userId);
    if (result?.success) await fetchStates();
    return result || { success: false };
  }, [userId, fetchStates]);

  return { states, loading, isComponentRunning, updateComponentState, refresh: fetchStates };
}

export default { ComponentType, useComponentState, useAllSystemStates, fetchAllSystemStates, fetchComponentState, setComponentState };
