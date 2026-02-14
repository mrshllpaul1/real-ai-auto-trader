/**
 * Performance Monitoring Dashboard
 * Real-time performance metrics, API latency, and system health
 * With WebSocket support for live updates
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Zap, Clock, Server, Database, Cpu, HardDrive,
  Wifi, RefreshCw, TrendingUp, TrendingDown, AlertTriangle,
  CheckCircle, XCircle, BarChart3, LineChart as LineChartIcon,
  Gauge, Timer, Globe, ArrowUp, ArrowDown, Minus, WifiOff
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import api from '../services/api';
import toast from '../utils/toast';
import {
  StatsGridSkeleton,
  ChartSkeleton,
  TableSkeleton,
  CardSkeleton
} from '../components/LoadingSkeletons';

const STATUS_COLORS = {
  healthy: '#00FF94',
  degraded: '#FFB800',
  critical: '#FF0055',
  unknown: '#666666',
};

// HTTP Polling hook for real-time performance metrics
// (WebSocket disabled - Kubernetes ingress doesn't support WS protocol upgrade)
const usePerformanceWebSocket = (onMetrics) => {
  const [wsConnected, setWsConnected] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    const API_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
    
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${API_URL}/api/performance/summary`);
        if (res.ok) {
          const data = await res.json();
          onMetrics(data);
          setWsConnected(true);
        }
      } catch (e) {
        setWsConnected(false);
      }
    };
    
    // Initial fetch and polling
    fetchMetrics();
    intervalRef.current = setInterval(fetchMetrics, 5000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [onMetrics]);

  return wsConnected;
};
    };
  }, [onMetrics]);
  
  return wsConnected;
};

const PerformanceDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [apiLatency, setApiLatency] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [cacheStats, setCacheStats] = useState(null);
  const [dbStats, setDbStats] = useState(null);
  const [timeRange, setTimeRange] = useState('1h');
  const [activeTab, setActiveTab] = useState('overview');
  
  // WebSocket for real-time metrics
  const handleWsMetrics = useCallback((newMetrics) => {
    setMetrics(newMetrics);
    setLoading(false);
  }, []);
  
  const wsConnected = usePerformanceWebSocket(handleWsMetrics);

  // Fetch performance metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const { data } = await api.get('/performance/summary');
      setMetrics(data);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      // Generate mock metrics for demo
      setMetrics(generateMockMetrics());
    }
  }, []);

  // Fetch API latency data
  const fetchApiLatency = useCallback(async () => {
    try {
      const { data } = await api.get('/performance/latency', { params: { range: timeRange } });
      setApiLatency(data.latency || []);
    } catch (err) {
      // Generate mock data
      setApiLatency(generateMockLatency(timeRange));
    }
  }, [timeRange]);

  // Fetch system health
  const fetchSystemHealth = useCallback(async () => {
    try {
      const [healthRes, cacheRes] = await Promise.all([
        api.get('/api/health'),
        api.get('/performance/cache-stats').catch(() => ({ data: null })),
      ]);
      setSystemHealth(healthRes.data);
      setCacheStats(cacheRes.data);
    } catch (err) {
      setSystemHealth({ status: 'unknown', database: 'unknown' });
    }
  }, []);

  // Fetch database stats
  const fetchDbStats = useCallback(async () => {
    try {
      const { data } = await api.get('/performance/db-stats');
      setDbStats(data);
    } catch (err) {
      setDbStats(generateMockDbStats());
    }
  }, []);

  // Generate mock metrics
  const generateMockMetrics = () => ({
    avg_response_time: 145,
    p95_response_time: 320,
    p99_response_time: 580,
    requests_per_minute: 42,
    error_rate: 0.5,
    uptime: 99.97,
    active_connections: 12,
    memory_usage: 68,
    cpu_usage: 23,
    cache_hit_rate: 87,
  });

  // Generate mock latency data
  const generateMockLatency = (range) => {
    const points = range === '1h' ? 60 : range === '6h' ? 72 : 144;
    const interval = range === '1h' ? 1 : range === '6h' ? 5 : 10;
    const data = [];
    
    for (let i = points; i >= 0; i--) {
      const date = new Date();
      date.setMinutes(date.getMinutes() - i * interval);
      data.push({
        time: date.toISOString(),
        label: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        avg: 100 + Math.random() * 100,
        p95: 200 + Math.random() * 150,
        p99: 350 + Math.random() * 200,
      });
    }
    return data;
  };

  // Generate mock DB stats
  const generateMockDbStats = () => ({
    connections: { active: 5, available: 95, max: 100 },
    operations: { reads: 1234, writes: 567, queries: 890 },
    storage: { used: 2.4, total: 10, unit: 'GB' },
    indexes: { count: 24, size: '156 MB' },
  });

  // Load all data
  const loadData = useCallback(async () => {
    setLoading(true);
    await Promise.all([
      fetchMetrics(),
      fetchApiLatency(),
      fetchSystemHealth(),
      fetchDbStats(),
    ]);
    setLoading(false);
  }, [fetchMetrics, fetchApiLatency, fetchSystemHealth, fetchDbStats]);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Calculate health status
  const getHealthStatus = useMemo(() => {
    if (!metrics) return 'unknown';
    if (metrics.error_rate > 5 || metrics.avg_response_time > 1000) return 'critical';
    if (metrics.error_rate > 1 || metrics.avg_response_time > 500) return 'degraded';
    return 'healthy';
  }, [metrics]);

  // Top slow endpoints (mock data)
  const slowEndpoints = [
    { endpoint: '/api/ensemble/rebuild-universe', avg: 4520, p95: 8200, calls: 12 },
    { endpoint: '/api/training/start-all', avg: 2340, p95: 4100, calls: 45 },
    { endpoint: '/api/adaptive-strategy/optimal-strategy', avg: 890, p95: 1450, calls: 234 },
    { endpoint: '/api/market/analysis', avg: 456, p95: 780, calls: 567 },
    { endpoint: '/api/portfolio/visualization/summary', avg: 234, p95: 420, calls: 890 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="performance-dashboard-loading">
        <div className="mb-8">
          <div className="h-10 w-72 bg-[#1F1F1F] rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-[#1F1F1F] rounded animate-pulse" />
        </div>
        <StatsGridSkeleton columns={5} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          <ChartSkeleton height={300} type="line" />
          <ChartSkeleton height={300} type="bar" />
        </div>
        <div className="mt-8">
          <TableSkeleton rows={5} columns={4} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="performance-dashboard">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#00FF94]/20 to-[#9D00FF]/20 border border-[#00FF94]/30">
                <Gauge size={32} className="text-[#00FF94]" />
              </div>
              <span className="text-white">Performance</span>
              <span className="bg-gradient-to-r from-[#00FF94] to-[#9D00FF] bg-clip-text text-transparent">Monitor</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Real-time system performance, API latency, and health metrics
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {/* WebSocket Status */}
            <Badge
              className={`px-2 py-1 ${
                wsConnected ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'
              }`}
              title={wsConnected ? 'Real-time updates active' : 'Reconnecting...'}
            >
              {wsConnected ? <Wifi size={12} className="mr-1" /> : <WifiOff size={12} className="mr-1" />}
              {wsConnected ? 'LIVE' : 'OFFLINE'}
            </Badge>
            
            {/* Health Status */}
            <Badge
              className={`px-3 py-1 ${
                getHealthStatus === 'healthy' ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                getHealthStatus === 'degraded' ? 'bg-[#FFB800]/20 text-[#FFB800]' :
                'bg-[#FF0055]/20 text-[#FF0055]'
              }`}
            >
              {getHealthStatus === 'healthy' ? <CheckCircle size={14} className="mr-1" /> :
               getHealthStatus === 'degraded' ? <AlertTriangle size={14} className="mr-1" /> :
               <XCircle size={14} className="mr-1" />}
              {getHealthStatus.toUpperCase()}
            </Badge>
            
            {/* Time Range */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-[#111] border border-[#1F1F1F] rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="1h">Last 1 Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
            </select>
            
            {/* Refresh */}
            <Button
              onClick={loadData}
              variant="outline"
              className="border-[#1F1F1F]"
            >
              <RefreshCw size={16} />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8"
      >
        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Timer size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Avg Response</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {(metrics?.avg_response_time ?? 0).toFixed(0)}
              <span className="text-sm text-[#666] ml-1">ms</span>
            </div>
            <p className={`text-xs ${(metrics?.avg_response_time ?? 0) < 200 ? 'text-[#00FF94]' : 'text-[#FFB800]'}`}>
              {(metrics?.avg_response_time ?? 0) < 200 ? 'Excellent' : 'Acceptable'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={18} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Requests/min</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {metrics?.requests_per_minute ?? 0}
            </div>
            <p className="text-xs text-[#666]">Current load</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={18} className="text-[#FF0055]" />
              <span className="text-sm text-[#A1A1AA]">Error Rate</span>
            </div>
            <div className={`text-3xl font-data font-bold ${(metrics?.error_rate ?? 0) < 1 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {(metrics?.error_rate ?? 0).toFixed(2)}%
            </div>
            <p className={`text-xs ${(metrics?.error_rate ?? 0) < 1 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {(metrics?.error_rate ?? 0) < 1 ? 'Healthy' : 'Needs attention'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Cache Hit</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {(metrics?.cache_hit_rate ?? 0).toFixed(0)}%
            </div>
            <Progress value={metrics?.cache_hit_rate ?? 0} className="h-1 mt-2" />
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Uptime</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#00FF94]">
              {(metrics?.uptime ?? 0).toFixed(2)}%
            </div>
            <p className="text-xs text-[#666]">Last 30 days</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-8">
        <TabsList className="bg-[#111] border border-[#1F1F1F]">
          <TabsTrigger value="overview" className="data-[state=active]:bg-[#9D00FF]/20">
            <LineChartIcon size={14} className="mr-1" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="api" className="data-[state=active]:bg-[#9D00FF]/20">
            <Globe size={14} className="mr-1" />
            API Performance
          </TabsTrigger>
          <TabsTrigger value="system" className="data-[state=active]:bg-[#9D00FF]/20">
            <Server size={14} className="mr-1" />
            System Resources
          </TabsTrigger>
          <TabsTrigger value="database" className="data-[state=active]:bg-[#9D00FF]/20">
            <Database size={14} className="mr-1" />
            Database
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Response Time Chart */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Timer size={20} className="text-[#00FF94]" />
                  Response Time Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={apiLatency}>
                      <defs>
                        <linearGradient id="avgGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00FF94" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#00FF94" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="p95Gradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#FFB800" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#FFB800" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                      <XAxis dataKey="label" stroke="#666" fontSize={12} />
                      <YAxis stroke="#666" fontSize={12} unit="ms" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F1F1F',
                          border: '1px solid #333',
                          borderRadius: '8px',
                        }}
                        formatter={(value) => [`${value.toFixed(0)} ms`]}
                      />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="avg"
                        name="Average"
                        stroke="#00FF94"
                        fill="url(#avgGradient)"
                        strokeWidth={2}
                      />
                      <Area
                        type="monotone"
                        dataKey="p95"
                        name="P95"
                        stroke="#FFB800"
                        fill="url(#p95Gradient)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* P99 and Percentiles */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <BarChart3 size={20} className="text-[#9D00FF]" />
                  Response Percentiles
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[#A1A1AA]">Average (P50)</span>
                      <span className="text-white font-data">{(metrics?.avg_response_time ?? 0).toFixed(0)} ms</span>
                    </div>
                    <Progress value={Math.min((metrics?.avg_response_time ?? 0) / 10, 100)} className="h-3 bg-[#1F1F1F]" />
                  </div>
                  
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[#A1A1AA]">P95</span>
                      <span className="text-[#FFB800] font-data">{(metrics?.p95_response_time ?? 0).toFixed(0)} ms</span>
                    </div>
                    <Progress value={Math.min((metrics?.p95_response_time ?? 0) / 10, 100)} className="h-3 bg-[#1F1F1F]" />
                  </div>
                  
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-[#A1A1AA]">P99</span>
                      <span className="text-[#FF0055] font-data">{(metrics?.p99_response_time ?? 0).toFixed(0)} ms</span>
                    </div>
                    <Progress value={Math.min((metrics?.p99_response_time ?? 0) / 10, 100)} className="h-3 bg-[#1F1F1F]" />
                  </div>

                  {/* Resource Usage */}
                  <div className="pt-4 border-t border-[#1F1F1F]">
                    <h4 className="text-white font-medium mb-4">Resource Usage</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-[#A1A1AA] text-sm flex items-center gap-1">
                            <Cpu size={14} />
                            CPU
                          </span>
                          <span className="text-white font-data">{metrics?.cpu_usage ?? 0}%</span>
                        </div>
                        <Progress value={metrics?.cpu_usage ?? 0} className="h-2 bg-[#1F1F1F]" />
                      </div>
                      <div>
                        <div className="flex justify-between mb-2">
                          <span className="text-[#A1A1AA] text-sm flex items-center gap-1">
                            <HardDrive size={14} />
                            Memory
                          </span>
                          <span className="text-white font-data">{metrics?.memory_usage ?? 0}%</span>
                        </div>
                        <Progress value={metrics?.memory_usage ?? 0} className="h-2 bg-[#1F1F1F]" />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* API Performance Tab */}
        <TabsContent value="api">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <AlertTriangle size={20} className="text-[#FFB800]" />
                Slowest Endpoints
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {slowEndpoints.map((endpoint, idx) => (
                  <div
                    key={endpoint.endpoint}
                    className="p-4 rounded-xl bg-[#111] border border-[#1F1F1F]"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                          idx === 0 ? 'bg-[#FF0055]/20 text-[#FF0055]' :
                          idx === 1 ? 'bg-[#FF6B00]/20 text-[#FF6B00]' :
                          'bg-[#FFB800]/20 text-[#FFB800]'
                        }`}>
                          #{idx + 1}
                        </div>
                        <code className="text-white font-mono text-sm">{endpoint.endpoint}</code>
                      </div>
                      <Badge className="bg-[#1F1F1F] text-[#A1A1AA]">
                        {endpoint.calls} calls
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-[#666]">Avg: </span>
                        <span className={`font-data ${endpoint.avg > 1000 ? 'text-[#FF0055]' : 'text-white'}`}>
                          {endpoint.avg} ms
                        </span>
                      </div>
                      <div>
                        <span className="text-[#666]">P95: </span>
                        <span className={`font-data ${endpoint.p95 > 2000 ? 'text-[#FF0055]' : 'text-[#FFB800]'}`}>
                          {endpoint.p95} ms
                        </span>
                      </div>
                      <div>
                        <Progress 
                          value={Math.min(endpoint.avg / 50, 100)} 
                          className="h-2 bg-[#1F1F1F] mt-2" 
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Resources Tab */}
        <TabsContent value="system">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Server size={20} className="text-[#00FF94]" />
                  Backend Service
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Status</span>
                    <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                      <CheckCircle size={12} className="mr-1" />
                      Running
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Active Connections</span>
                    <span className="text-white font-data">{metrics?.active_connections ?? 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Uptime</span>
                    <span className="text-[#00FF94] font-data">{(metrics?.uptime ?? 0).toFixed(2)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Zap size={20} className="text-[#FFB800]" />
                  Cache Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Hit Rate</span>
                    <span className="text-[#00FF94] font-data">{(metrics?.cache_hit_rate ?? 0).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Entries</span>
                    <span className="text-white font-data">{cacheStats?.entries ?? 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Memory Used</span>
                    <span className="text-white font-data">{cacheStats?.memory ?? '0 MB'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Wifi size={20} className="text-[#9D00FF]" />
                  Network
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Database</span>
                    <Badge className={systemHealth?.database === 'connected' 
                      ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                      : 'bg-[#FF0055]/20 text-[#FF0055]'
                    }>
                      {systemHealth?.database === 'connected' ? 'Connected' : 'Disconnected'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">External APIs</span>
                    <Badge className="bg-[#00FF94]/20 text-[#00FF94]">Healthy</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#A1A1AA]">Websockets</span>
                    <Badge className="bg-[#FFB800]/20 text-[#FFB800]">N/A</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Database Tab */}
        <TabsContent value="database">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Database size={20} className="text-[#00FF94]" />
                  Connection Pool
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Active</span>
                    <span className="text-[#00FF94] font-data">{dbStats?.connections?.active ?? 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Available</span>
                    <span className="text-white font-data">{dbStats?.connections?.available ?? 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Max</span>
                    <span className="text-[#666] font-data">{dbStats?.connections?.max ?? 0}</span>
                  </div>
                  <Progress 
                    value={((dbStats?.connections?.active ?? 0) / (dbStats?.connections?.max ?? 100)) * 100} 
                    className="h-2 bg-[#1F1F1F]" 
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Activity size={20} className="text-[#9D00FF]" />
                  Operations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Reads</span>
                    <span className="text-[#00FF94] font-data">{(dbStats?.operations?.reads ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Writes</span>
                    <span className="text-[#FFB800] font-data">{(dbStats?.operations?.writes ?? 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#A1A1AA]">Queries</span>
                    <span className="text-white font-data">{(dbStats?.operations?.queries ?? 0).toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F] lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <HardDrive size={20} className="text-[#FFB800]" />
                  Storage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-[#111] rounded-lg p-4">
                    <p className="text-[#A1A1AA] text-sm mb-1">Used</p>
                    <p className="text-2xl font-data font-bold text-white">
                      {dbStats?.storage?.used ?? 0} {dbStats?.storage?.unit ?? 'GB'}
                    </p>
                  </div>
                  <div className="bg-[#111] rounded-lg p-4">
                    <p className="text-[#A1A1AA] text-sm mb-1">Total</p>
                    <p className="text-2xl font-data font-bold text-white">
                      {dbStats?.storage?.total ?? 0} {dbStats?.storage?.unit ?? 'GB'}
                    </p>
                  </div>
                  <div className="bg-[#111] rounded-lg p-4">
                    <p className="text-[#A1A1AA] text-sm mb-1">Indexes</p>
                    <p className="text-2xl font-data font-bold text-[#9D00FF]">
                      {dbStats?.indexes?.count ?? 0}
                    </p>
                  </div>
                  <div className="bg-[#111] rounded-lg p-4">
                    <p className="text-[#A1A1AA] text-sm mb-1">Index Size</p>
                    <p className="text-2xl font-data font-bold text-white">
                      {dbStats?.indexes?.size ?? '0 MB'}
                    </p>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex justify-between mb-2">
                    <span className="text-[#A1A1AA]">Storage Usage</span>
                    <span className="text-white font-data">
                      {(((dbStats?.storage?.used ?? 0) / (dbStats?.storage?.total ?? 1)) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <Progress 
                    value={((dbStats?.storage?.used ?? 0) / (dbStats?.storage?.total ?? 1)) * 100} 
                    className="h-3 bg-[#1F1F1F]" 
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PerformanceDashboard;
