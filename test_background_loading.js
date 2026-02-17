/**
 * Background Loading Tests
 * ========================
 * Tests for BackgroundLoader, WebSocketManager, and enhanced hooks.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { getBackgroundLoader, Priority } from '../frontend/src/services/backgroundLoader';
import { getWebSocketManager } from '../frontend/src/services/websocketManager';

describe('BackgroundLoader', () => {
  let backgroundLoader;
  
  beforeEach(() => {
    backgroundLoader = getBackgroundLoader();
  });
  
  afterEach(() => {
    backgroundLoader.destroy();
  });
  
  it('should initialize with correct default values', () => {
    expect(backgroundLoader.queue).toBeDefined();
    expect(backgroundLoader.stats.totalRequests).toBe(0);
    expect(backgroundLoader.isOnline).toBe(true);
  });
  
  it('should add requests to queue', async () => {
    const mockFn = vi.fn().mockResolvedValue('test data');
    
    const promise = backgroundLoader.addRequest(mockFn, {
      priority: Priority.MEDIUM,
      id: 'test-request',
    });
    
    expect(backgroundLoader.queue[Priority.MEDIUM].length).toBeGreaterThan(0);
    
    const result = await promise;
    expect(result).toBe('test data');
    expect(backgroundLoader.stats.totalRequests).toBe(1);
  });
  
  it('should respect priority ordering', async () => {
    const executionOrder = [];
    
    const lowPriorityFn = vi.fn().mockImplementation(async () => {
      executionOrder.push('LOW');
      return 'low';
    });
    
    const highPriorityFn = vi.fn().mockImplementation(async () => {
      executionOrder.push('HIGH');
      return 'high';
    });
    
    // Add low priority first
    backgroundLoader.addRequest(lowPriorityFn, {
      priority: Priority.LOW,
    });
    
    // Add high priority after
    backgroundLoader.addRequest(highPriorityFn, {
      priority: Priority.HIGH,
    });
    
    // Wait for processing
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // High priority should execute first
    expect(executionOrder[0]).toBe('HIGH');
  });
  
  it('should cancel requests', async () => {
    const mockFn = vi.fn().mockImplementation(async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      return 'data';
    });
    
    const requestId = 'cancelable-request';
    
    const promise = backgroundLoader.addRequest(mockFn, {
      priority: Priority.LOW,
      id: requestId,
      cancelable: true,
    });
    
    // Cancel immediately
    backgroundLoader.cancelRequest(requestId);
    
    // Should reject
    await expect(promise).rejects.toThrow('Request canceled');
    expect(backgroundLoader.stats.canceledRequests).toBe(1);
  });
  
  it('should retry failed requests', async () => {
    let attempts = 0;
    
    const flakeyFn = vi.fn().mockImplementation(async () => {
      attempts++;
      if (attempts < 3) {
        throw new Error('Temporary failure');
      }
      return 'success';
    });
    
    const result = await backgroundLoader.addRequest(flakeyFn, {
      priority: Priority.MEDIUM,
      retries: 3,
    });
    
    expect(result).toBe('success');
    expect(attempts).toBe(3);
  });
  
  it('should track statistics', async () => {
    const mockFn = vi.fn().mockResolvedValue('data');
    
    await backgroundLoader.addRequest(mockFn, { priority: Priority.HIGH });
    await backgroundLoader.addRequest(mockFn, { priority: Priority.LOW });
    
    const stats = backgroundLoader.getStats();
    
    expect(stats.totalRequests).toBe(2);
    expect(stats.completedRequests).toBeGreaterThan(0);
    expect(stats).toHaveProperty('queueSizes');
    expect(stats).toHaveProperty('activeRequests');
  });
  
  it('should preload critical data', async () => {
    // Mock axios
    const mockGet = vi.fn().mockResolvedValue({ data: 'mocked' });
    global.axios = { get: mockGet };
    
    await backgroundLoader.preloadCriticalData();
    
    // Should have made requests to critical endpoints
    expect(mockGet).toHaveBeenCalled();
  });
  
  it('should manage background sync', () => {
    const mockFn = vi.fn().mockResolvedValue('sync data');
    
    backgroundLoader.startBackgroundSync('test-sync', mockFn, {
      interval: 1000,
      priority: Priority.LOW,
    });
    
    expect(backgroundLoader.syncIntervals.has('test-sync')).toBe(true);
    
    backgroundLoader.stopBackgroundSync('test-sync');
    
    expect(backgroundLoader.syncIntervals.has('test-sync')).toBe(false);
  });
});

describe('WebSocketManager', () => {
  let wsManager;
  let mockWebSocket;
  
  beforeEach(() => {
    // Mock WebSocket
    mockWebSocket = {
      readyState: WebSocket.CONNECTING,
      send: vi.fn(),
      close: vi.fn(),
    };
    
    global.WebSocket = vi.fn().mockImplementation(() => mockWebSocket);
    global.WebSocket.CONNECTING = 0;
    global.WebSocket.OPEN = 1;
    global.WebSocket.CLOSING = 2;
    global.WebSocket.CLOSED = 3;
    
    wsManager = getWebSocketManager();
  });
  
  afterEach(() => {
    wsManager.disconnect();
  });
  
  it('should initialize correctly', () => {
    expect(wsManager.connectionState).toBe('DISCONNECTED');
    expect(wsManager.subscriptions.size).toBe(0);
    expect(wsManager.stats.messagesReceived).toBe(0);
  });
  
  it('should connect to WebSocket server', () => {
    wsManager.connect('ws://localhost:8000/ws');
    
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws', []);
    expect(wsManager.connectionState).toBe('CONNECTING');
  });
  
  it('should handle connection open', () => {
    wsManager.connect('ws://localhost:8000/ws');
    
    // Simulate connection open
    mockWebSocket.readyState = WebSocket.OPEN;
    wsManager._handleOpen({});
    
    expect(wsManager.connectionState).toBe('CONNECTED');
    expect(wsManager.lastConnectedAt).toBeTruthy();
  });
  
  it('should subscribe to channels', () => {
    const callback = vi.fn();
    
    const unsubscribe = wsManager.subscribe('test-channel', callback);
    
    expect(wsManager.subscriptions.has('test-channel')).toBe(true);
    expect(wsManager.subscriptions.get('test-channel').has(callback)).toBe(true);
    
    unsubscribe();
    
    expect(wsManager.subscriptions.has('test-channel')).toBe(false);
  });
  
  it('should send messages', () => {
    mockWebSocket.readyState = WebSocket.OPEN;
    wsManager.ws = mockWebSocket;
    wsManager.connectionState = 'CONNECTED';
    
    const result = wsManager.send({ type: 'test', data: 'hello' });
    
    expect(result).toBe(true);
    expect(mockWebSocket.send).toHaveBeenCalledWith('{"type":"test","data":"hello"}');
    expect(wsManager.stats.messagesSent).toBe(1);
  });
  
  it('should queue messages when offline', () => {
    mockWebSocket.readyState = WebSocket.CLOSED;
    wsManager.ws = mockWebSocket;
    
    const result = wsManager.send({ type: 'test' });
    
    expect(result).toBe(false);
    expect(wsManager.messageQueue.length).toBe(1);
  });
  
  it('should handle incoming messages', () => {
    const callback = vi.fn();
    wsManager.subscribe('test-channel', callback);
    
    const messageEvent = {
      data: JSON.stringify({
        channel: 'test-channel',
        type: 'update',
        payload: { value: 123 }
      })
    };
    
    wsManager._handleMessage(messageEvent);
    
    expect(callback).toHaveBeenCalledWith({
      channel: 'test-channel',
      type: 'update',
      payload: { value: 123 }
    });
    expect(wsManager.stats.messagesReceived).toBe(1);
  });
  
  it('should track statistics', () => {
    const stats = wsManager.getStats();
    
    expect(stats).toHaveProperty('messagesReceived');
    expect(stats).toHaveProperty('messagesSent');
    expect(stats).toHaveProperty('connectionState');
    expect(stats).toHaveProperty('subscriptions');
  });
  
  it('should handle reconnection', () => {
    wsManager.reconnectAttempts = 2;
    wsManager.url = 'ws://localhost:8000/ws';
    
    wsManager._scheduleReconnect();
    
    expect(wsManager.reconnectAttempts).toBe(3);
    expect(wsManager.reconnectTimer).toBeTruthy();
  });
});

describe('Integration Tests', () => {
  it('should handle priority queue with background sync', async () => {
    const backgroundLoader = getBackgroundLoader();
    const mockFn = vi.fn().mockResolvedValue('data');
    
    // Start background sync
    backgroundLoader.startBackgroundSync('test', mockFn, {
      interval: 500,
      priority: Priority.LOW,
    });
    
    // Add high priority request
    const highPriorityData = await backgroundLoader.addRequest(
      () => Promise.resolve('high priority'),
      { priority: Priority.HIGH }
    );
    
    expect(highPriorityData).toBe('high priority');
    
    // Cleanup
    backgroundLoader.stopBackgroundSync('test');
    backgroundLoader.destroy();
  });
  
  it('should handle offline/online transitions', async () => {
    const backgroundLoader = getBackgroundLoader();
    const mockFn = vi.fn().mockResolvedValue('data');
    
    // Simulate offline
    backgroundLoader.isOnline = false;
    
    // Add request while offline
    backgroundLoader.addRequest(mockFn, { priority: Priority.MEDIUM });
    
    // Simulate online
    backgroundLoader.isOnline = true;
    backgroundLoader._processQueue();
    
    // Wait for processing
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(mockFn).toHaveBeenCalled();
    
    backgroundLoader.destroy();
  });
});

// Run tests
if (import.meta.vitest) {
  // Tests will run automatically with vitest
}

export default {
  describe,
  it,
  expect,
};
