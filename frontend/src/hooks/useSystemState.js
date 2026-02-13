/**
 * System State Management Hook
 * ============================
 * Manages persistent running states across the app.
 * States survive page navigation and browser refresh.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
    return response.data || {};
  } catch (error) {
    console.error('Failed to fetch system states:', error);
    return {};
  }
};

/**
 * Fetch a single component's state
 */
export const fetchComponentState = async (component, userId = 'default') => {
  try {
    const response = await api.get(`/system-state/${component}?user_id=${userId}`);
    return response.data || { is_running: false, metadata: {} };
  } catch (error) {
    console.error(`Failed to fetch state for ${component}:`, error);
    return { is_running: false, metadata: {} };
  }
};

/**
 * Update a component's state
 */
export const setComponentState = async (component, isRunning, metadata = {}, userId = 'default') => {
  try {
    const response = await api.post('/system-state/update', {
      component,
      user_id: userId,
      is_running: isRunning,
      metadata,
    });
    return response.data || { success: false };
  } catch (error) {
    console.error(`Failed to update state for ${component}:`, error);
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
    pollInterval = null,
    onStateChange = null,
  } = options;

  // Ensure we're using React hooks properly
  const [isRunning, setIsRunning] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [metadata, setMetadata] = React.useState({});
  const mountedRef = React.useRef(true);

  // Fetch initial state
  const fetchState = React.useCallback(async () => {
    try {
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
    } catch (error) {
      console.error('Error fetching state:', error);
      if (mountedRef.current) {
        setLoading(false);
      }
      return { is_running: false, metadata: {} };
    }
  }, [component, userId, isRunning, onStateChange]);

  // Update state
  const updateState = React.useCallback(async (newIsRunning, newMetadata = {}) => {
    try {
      const result = await setComponentState(component, newIsRunning, newMetadata, userId);
      if (result.success && mountedRef.current) {
        setIsRunning(newIsRunning);
        setMetadata(prev => ({ ...prev, ...newMetadata }));
        if (onStateChange) {
          onStateChange(newIsRunning);
        }
      }
      return result;
    } catch (error) {
      console.error('Error updating state:', error);
      return { success: false };
    }
  }, [component, userId, onStateChange]);

  // Initial fetch
  React.useEffect(() => {
    mountedRef.current = true;
    fetchState();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Polling
  React.useEffect(() => {
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
    pollInterval = null,
  } = options;

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
      console.error('Error fetching all states:', error);
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [userId]);

  React.useEffect(() => {
    mountedRef.current = true;
    fetchStates();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  React.useEffect(() => {
    if (!pollInterval) return;

    const interval = setInterval(fetchStates, pollInterval);
    return () => clearInterval(interval);
  }, [pollInterval, fetchStates]);

  const isComponentRunning = React.useCallback((component) => {
    return states[component]?.is_running || false;
  }, [states]);

  const updateComponentState = React.useCallback(async (component, isRunning, metadata = {}) => {
    const result = await setComponentState(component, isRunning, metadata, userId);
    if (result.success) {
      await fetchStates();
    }
    return result;
  }, [userId, fetchStates]);

  return {
    states,
    loading,
    isComponentRunning,
    updateComponentState,
    refresh: fetchStates,
  };
};

export default {
  ComponentType,
  useComponentState,
  useAllSystemStates,
  fetchAllSystemStates,
  fetchComponentState,
  setComponentState,
};
