/**
 * WebSocket Hook - Real-time data connection
 * Handles connection, reconnection, and message handling
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/connect`;

export const useWebSocket = (channels = ['all'], options = {}) => {
  const {
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionState, setConnectionState] = useState('disconnected');
  
  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState('connecting');
    
    const channelParam = channels.join(',');
    const ws = new WebSocket(`${WS_URL}?channels=${channelParam}`);
    
    ws.onopen = () => {
      console.log('[WebSocket] Connected');
      setIsConnected(true);
      setConnectionState('connected');
      reconnectCountRef.current = 0;
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle ping/pong
        if (data.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
          return;
        }
        
        setLastMessage(data);
        onMessage?.(data);
      } catch (e) {
        console.error('[WebSocket] Parse error:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
      onError?.(error);
    };

    ws.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code);
      setIsConnected(false);
      setConnectionState('disconnected');
      onDisconnect?.(event);
      
      // Attempt reconnection
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1;
        setConnectionState('reconnecting');
        console.log(`[WebSocket] Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };

    wsRef.current = ws;
  }, [channels, reconnectAttempts, reconnectInterval, onMessage, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  const subscribe = useCallback((newChannels) => {
    send({ type: 'subscribe', channels: newChannels });
  }, [send]);

  const unsubscribe = useCallback((removeChannels) => {
    send({ type: 'unsubscribe', channels: removeChannels });
  }, [send]);

  // Connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    connectionState,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
};

// Specialized hooks for specific data types
export const usePriceUpdates = (onPriceUpdate) => {
  return useWebSocket(['prices'], {
    onMessage: (data) => {
      if (data.channel === 'prices' && data.data?.type === 'price_update') {
        onPriceUpdate?.(data.data.prices);
      }
    },
  });
};

export const useSignalUpdates = (onSignal) => {
  return useWebSocket(['signals'], {
    onMessage: (data) => {
      if (data.channel === 'signals' && data.data?.type === 'ai_signal') {
        onSignal?.(data.data.signal);
      }
    },
  });
};

export const useTrainingUpdates = (onProgress) => {
  return useWebSocket(['training'], {
    onMessage: (data) => {
      if (data.channel === 'training' && data.data?.type === 'training_progress') {
        onProgress?.(data.data.progress);
      }
    },
  });
};

export const usePortfolioUpdates = (onUpdate) => {
  return useWebSocket(['portfolio'], {
    onMessage: (data) => {
      if (data.channel === 'portfolio' && data.data?.type === 'portfolio_update') {
        onUpdate?.(data.data.portfolio);
      }
    },
  });
};

export default useWebSocket;
