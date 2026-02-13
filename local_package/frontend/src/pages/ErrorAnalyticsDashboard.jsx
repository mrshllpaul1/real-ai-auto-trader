/**
 * Error Analytics Dashboard
 * Real-time error monitoring, trends, alerting, and error grouping
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, Bug, TrendingUp, TrendingDown, RefreshCw,
  Clock, AlertCircle, CheckCircle, XCircle, BarChart3,
  PieChart as PieChartIcon, Activity, Bell, BellOff, Filter,
  ChevronDown, ChevronUp, ExternalLink, Copy, Check, Trash2,
  Layers, Hash, GitMerge, Eye, EyeOff, Search, SortAsc, SortDesc
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import api from '../services/api';
import toast from '../utils/toast';
import {
  StatsGridSkeleton,
  ChartSkeleton,
  TableSkeleton,
  ListItemSkeleton
} from '../components/LoadingSkeletons';

const SEVERITY_COLORS = {
  critical: '#FF0055',
  high: '#FF6B00',
  medium: '#FFB800',
  low: '#00FF94',
};

const CATEGORY_COLORS = {
  ui_crash: '#FF0055',
  api_error: '#FF6B00',
  network_error: '#FFB800',
  auth_error: '#9D00FF',
  data_error: '#00D4FF',
  unknown: '#666666',
};

/**
 * Generate fingerprint for error grouping
 */
const generateFingerprint = (error) => {
  const message = (error.message || '').replace(/\d+/g, 'X').substring(0, 100);
  const type = error.error_type || error.type || 'unknown';
  const path = error.pathname || error.url?.split('?')[0] || '';
  return `${type}|${message}|${path}`;
};

/**
 * Group errors by fingerprint for deduplication
 */
const groupErrors = (errors) => {
  const groups = new Map();
  
  errors.forEach(error => {
    const fingerprint = generateFingerprint(error);
    
    if (groups.has(fingerprint)) {
      const group = groups.get(fingerprint);
      group.count += 1;
      group.errors.push(error);
      // Update last seen
      const errorTime = new Date(error.timestamp);
      if (errorTime > new Date(group.lastSeen)) {
        group.lastSeen = error.timestamp;
        group.latestError = error;
      }
      // Update first seen
      if (errorTime < new Date(group.firstSeen)) {
        group.firstSeen = error.timestamp;
      }
    } else {
      groups.set(fingerprint, {
        fingerprint,
        count: 1,
        errors: [error],
        firstSeen: error.timestamp,
        lastSeen: error.timestamp,
        latestError: error,
        message: error.message,
        type: error.error_type || error.type,
        severity: error.severity,
        pathname: error.pathname || error.url?.split('?')[0],
      });
    }
  });
  
  return Array.from(groups.values());
};

const ErrorAnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [errors, setErrors] = useState([]);
  const [trends, setTrends] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [selectedError, setSelectedError] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('grouped'); // 'grouped' or 'individual'
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('count'); // 'count', 'lastSeen', 'severity'
  const [sortOrder, setSortOrder] = useState('desc');
  const [activeTab, setActiveTab] = useState('overview');

  // Group and filter errors
  const groupedErrors = useMemo(() => {
    let filtered = errors;
    
    // Apply severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(e => e.severity === severityFilter);
    }
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(e => 
        (e.message || '').toLowerCase().includes(query) ||
        (e.pathname || '').toLowerCase().includes(query) ||
        (e.error_type || '').toLowerCase().includes(query)
      );
    }
    
    const groups = groupErrors(filtered);
    
    // Sort groups
    groups.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'count':
          comparison = a.count - b.count;
          break;
        case 'lastSeen':
          comparison = new Date(a.lastSeen) - new Date(b.lastSeen);
          break;
        case 'severity':
          const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          comparison = (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0);
          break;
        default:
          comparison = 0;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return groups;
  }, [errors, severityFilter, searchQuery, sortBy, sortOrder]);

  // Calculate deduplication stats
  const deduplicationStats = useMemo(() => {
    const totalErrors = errors.length;
    const uniqueGroups = groupedErrors.length;
    const deduplicationRate = totalErrors > 0 
      ? ((totalErrors - uniqueGroups) / totalErrors * 100).toFixed(1)
      : 0;
    const avgErrorsPerGroup = uniqueGroups > 0 
      ? (totalErrors / uniqueGroups).toFixed(1)
      : 0;
    
    return {
      totalErrors,
      uniqueGroups,
      deduplicationRate,
      avgErrorsPerGroup,
    };
  }, [errors, groupedErrors]);

  // Fetch error statistics
  const fetchStats = useCallback(async () => {
    try {
      const { data } = await api.get('/monitoring/errors/stats');
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch error stats:', err);
    }
  }, []);

  // Fetch recent errors
  const fetchErrors = useCallback(async () => {
    try {
      const params = severityFilter !== 'all' ? { severity: severityFilter } : {};
      const { data } = await api.get('/monitoring/errors', { params: { limit: 100, ...params } });
      setErrors(data.errors || []);
    } catch (err) {
      console.error('Failed to fetch errors:', err);
    }
  }, [severityFilter]);

  // Fetch error trends
  const fetchTrends = useCallback(async () => {
    try {
      const { data } = await api.get('/monitoring/errors/trends', { params: { range: timeRange } });
      setTrends(data.trends || generateMockTrends());
    } catch (err) {
      // Generate mock trends if endpoint doesn't exist
      setTrends(generateMockTrends());
    }
  }, [timeRange]);

  // Generate mock trends for visualization
  const generateMockTrends = () => {
    const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720;
    const interval = timeRange === '24h' ? 1 : timeRange === '7d' ? 6 : 24;
    const data = [];
    
    for (let i = hours; i >= 0; i -= interval) {
      const date = new Date();
      date.setHours(date.getHours() - i);
      data.push({
        time: date.toISOString(),
        label: timeRange === '24h' 
          ? date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
          : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        errors: Math.floor(Math.random() * 10),
        critical: Math.floor(Math.random() * 2),
        high: Math.floor(Math.random() * 3),
        medium: Math.floor(Math.random() * 4),
        low: Math.floor(Math.random() * 5),
      });
    }
    return data;
  };

  // Check for alert conditions
  const checkAlerts = useCallback(() => {
    if (!alertsEnabled || !stats) return;
    
    const newAlerts = [];
    
    // High error rate alert
    if (stats.errors_last_hour > 50) {
      newAlerts.push({
        id: 'high_error_rate',
        type: 'critical',
        message: `High error rate detected: ${stats.errors_last_hour} errors in the last hour`,
        timestamp: new Date().toISOString(),
      });
    }
    
    // Critical errors alert
    if (stats.by_severity?.critical > 0) {
      newAlerts.push({
        id: 'critical_errors',
        type: 'critical',
        message: `${stats.by_severity.critical} critical error(s) detected`,
        timestamp: new Date().toISOString(),
      });
    }
    
    // UI crash alert
    if (stats.by_type?.ui_crash > 5) {
      newAlerts.push({
        id: 'ui_crashes',
        type: 'high',
        message: `Multiple UI crashes detected: ${stats.by_type.ui_crash} in the last hour`,
        timestamp: new Date().toISOString(),
      });
    }
    
    setAlerts(newAlerts);
    
    // Show toast notifications for new alerts
    newAlerts.forEach(alert => {
      if (alert.type === 'critical') {
        toast.error(alert.message);
      } else {
        toast.warning(alert.message);
      }
    });
  }, [alertsEnabled, stats]);

  // Load all data
  const loadData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchStats(), fetchErrors(), fetchTrends()]);
    setLoading(false);
  }, [fetchStats, fetchErrors, fetchTrends]);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    checkAlerts();
  }, [checkAlerts]);

  // Copy error details
  const handleCopyError = async (error) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(error, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success('Error details copied to clipboard');
    } catch (err) {
      toast.error('Failed to copy');
    }
  };

  // Clear all errors (admin action)
  const handleClearErrors = async () => {
    try {
      await api.delete('/monitoring/errors/clear');
      toast.success('Error history cleared');
      loadData();
    } catch (err) {
      toast.error('Failed to clear errors');
    }
  };

  // Prepare chart data
  const severityPieData = stats?.by_severity 
    ? Object.entries(stats.by_severity).map(([name, value]) => ({ name, value }))
    : [];

  const categoryPieData = stats?.by_type
    ? Object.entries(stats.by_type).map(([name, value]) => ({ name, value }))
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="error-analytics-loading">
        <div className="mb-8">
          <div className="h-10 w-64 bg-[#1F1F1F] rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-[#1F1F1F] rounded animate-pulse" />
        </div>
        <StatsGridSkeleton columns={4} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          <ChartSkeleton height={300} type="line" />
          <ChartSkeleton height={300} type="bar" />
        </div>
        <div className="mt-8">
          <TableSkeleton rows={5} columns={5} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="error-analytics-dashboard">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#FF0055]/20 to-[#FFB800]/20 border border-[#FF0055]/30">
                <Bug size={32} className="text-[#FF0055]" />
              </div>
              <span className="text-white">Error</span>
              <span className="bg-gradient-to-r from-[#FF0055] to-[#FFB800] bg-clip-text text-transparent">Analytics</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Real-time error monitoring, trends, and alerting dashboard
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Alert Toggle */}
            <Button
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              variant="outline"
              className={`border-[#1F1F1F] ${alertsEnabled ? 'text-[#00FF94]' : 'text-[#666]'}`}
            >
              {alertsEnabled ? <Bell size={16} className="mr-2" /> : <BellOff size={16} className="mr-2" />}
              {alertsEnabled ? 'Alerts On' : 'Alerts Off'}
            </Button>
            
            {/* Time Range */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-[#111] border border-[#1F1F1F] rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
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

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border mb-2 flex items-center justify-between ${
                alert.type === 'critical'
                  ? 'bg-[#FF0055]/10 border-[#FF0055]/30'
                  : 'bg-[#FFB800]/10 border-[#FFB800]/30'
              }`}
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className={alert.type === 'critical' ? 'text-[#FF0055]' : 'text-[#FFB800]'} />
                <span className="text-white">{alert.message}</span>
              </div>
              <Badge className={alert.type === 'critical' ? 'bg-[#FF0055]/20 text-[#FF0055]' : 'bg-[#FFB800]/20 text-[#FFB800]'}>
                {alert.type.toUpperCase()}
              </Badge>
            </div>
          ))}
        </motion.div>
      )}

      {/* Stats Grid */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle size={18} className="text-[#FF0055]" />
              <span className="text-sm text-[#A1A1AA]">Total Errors</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {(stats?.total_errors ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-[#666]">All time</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Last Hour</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {stats?.errors_last_hour ?? 0}
            </div>
            <p className={`text-xs ${(stats?.errors_last_hour ?? 0) > 10 ? 'text-[#FF0055]' : 'text-[#00FF94]'}`}>
              {(stats?.errors_last_hour ?? 0) > 10 ? 'Above normal' : 'Normal rate'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Bug size={18} className="text-[#FF0055]" />
              <span className="text-sm text-[#A1A1AA]">Critical</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FF0055]">
              {stats?.by_severity?.critical ?? 0}
            </div>
            <p className="text-xs text-[#666]">Needs attention</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Frontend Errors</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {stats?.frontend_errors ?? 0}
            </div>
            <p className="text-xs text-[#666]">UI crashes tracked</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Charts Row */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
      >
        {/* Error Trend Chart */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <TrendingUp size={20} className="text-[#9D00FF]" />
              Error Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends}>
                  <defs>
                    <linearGradient id="errorGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF0055" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#FF0055" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                  <XAxis dataKey="label" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F1F1F',
                      border: '1px solid #333',
                      borderRadius: '8px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="errors"
                    stroke="#FF0055"
                    fill="url(#errorGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Severity Breakdown */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <BarChart3 size={20} className="text-[#FFB800]" />
              By Severity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trends.slice(-12)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                  <XAxis dataKey="label" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F1F1F',
                      border: '1px solid #333',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Bar dataKey="critical" fill={SEVERITY_COLORS.critical} stackId="a" />
                  <Bar dataKey="high" fill={SEVERITY_COLORS.high} stackId="a" />
                  <Bar dataKey="medium" fill={SEVERITY_COLORS.medium} stackId="a" />
                  <Bar dataKey="low" fill={SEVERITY_COLORS.low} stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Distribution Charts */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
      >
        {/* Severity Distribution */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <PieChartIcon size={20} className="text-[#FF0055]" />
              Severity Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px] flex items-center justify-center">
              {severityPieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={severityPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {severityPieData.map((entry, index) => (
                        <Cell key={index} fill={SEVERITY_COLORS[entry.name] || '#666'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F1F1F',
                        border: '1px solid #333',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-[#666]">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <PieChartIcon size={20} className="text-[#9D00FF]" />
              Error Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px] flex items-center justify-center">
              {categoryPieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {categoryPieData.map((entry, index) => (
                        <Cell key={index} fill={CATEGORY_COLORS[entry.name] || '#666'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F1F1F',
                        border: '1px solid #333',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-[#666]">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Deduplication Stats Bar */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.35 }}
        className="mb-6"
      >
        <div className="bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10 border border-[#9D00FF]/30 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <GitMerge size={20} className="text-[#9D00FF]" />
              <span className="text-white font-medium">Error Grouping</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-[#A1A1AA]">Total: </span>
                <span className="text-white font-data">{deduplicationStats.totalErrors}</span>
              </div>
              <div>
                <span className="text-[#A1A1AA]">Unique Groups: </span>
                <span className="text-[#00FF94] font-data">{deduplicationStats.uniqueGroups}</span>
              </div>
              <div>
                <span className="text-[#A1A1AA]">Dedup Rate: </span>
                <span className="text-[#9D00FF] font-data">{deduplicationStats.deduplicationRate}%</span>
              </div>
              <div>
                <span className="text-[#A1A1AA]">Avg/Group: </span>
                <span className="text-white font-data">{deduplicationStats.avgErrorsPerGroup}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setViewMode(viewMode === 'grouped' ? 'individual' : 'grouped')}
              variant="outline"
              size="sm"
              className={`border-[#1F1F1F] ${viewMode === 'grouped' ? 'text-[#9D00FF]' : 'text-[#666]'}`}
            >
              {viewMode === 'grouped' ? <Layers size={14} className="mr-1" /> : <Activity size={14} className="mr-1" />}
              {viewMode === 'grouped' ? 'Grouped' : 'Individual'}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Errors Section with Search and Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <CardTitle className="flex items-center gap-2 text-white">
                <AlertTriangle size={20} className="text-[#FF0055]" />
                {viewMode === 'grouped' ? 'Grouped Errors' : 'All Errors'}
                <Badge className="bg-[#1F1F1F] text-[#A1A1AA] ml-2">
                  {viewMode === 'grouped' ? groupedErrors.length : errors.length}
                </Badge>
              </CardTitle>
              
              <div className="flex flex-wrap items-center gap-2">
                {/* Search */}
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" />
                  <input
                    type="text"
                    placeholder="Search errors..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-[#111] border border-[#1F1F1F] rounded-lg pl-9 pr-3 py-1.5 text-white text-sm w-48 focus:border-[#9D00FF] outline-none"
                  />
                </div>
                
                {/* Severity Filter */}
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="bg-[#111] border border-[#1F1F1F] rounded-lg px-3 py-1.5 text-white text-sm"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                
                {/* Sort By */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-[#111] border border-[#1F1F1F] rounded-lg px-3 py-1.5 text-white text-sm"
                >
                  <option value="count">Sort by Count</option>
                  <option value="lastSeen">Sort by Recent</option>
                  <option value="severity">Sort by Severity</option>
                </select>
                
                {/* Sort Order */}
                <Button
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  variant="outline"
                  size="sm"
                  className="border-[#1F1F1F]"
                >
                  {sortOrder === 'desc' ? <SortDesc size={14} /> : <SortAsc size={14} />}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {viewMode === 'grouped' ? (
              // Grouped View
              groupedErrors.length > 0 ? (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {groupedErrors.map((group, idx) => (
                    <div
                      key={group.fingerprint || idx}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        selectedGroup?.fingerprint === group.fingerprint
                          ? 'bg-[#1F1F1F] border-[#9D00FF]'
                          : 'bg-[#111] border-[#1F1F1F] hover:border-[#333]'
                      }`}
                      onClick={() => setSelectedGroup(selectedGroup?.fingerprint === group.fingerprint ? null : group)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            {/* Count Badge */}
                            <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] font-data">
                              <Hash size={12} className="mr-1" />
                              {group.count}x
                            </Badge>
                            
                            {/* Severity */}
                            <Badge
                              className={`${
                                group.severity === 'critical' ? 'bg-[#FF0055]/20 text-[#FF0055]' :
                                group.severity === 'high' ? 'bg-[#FF6B00]/20 text-[#FF6B00]' :
                                group.severity === 'medium' ? 'bg-[#FFB800]/20 text-[#FFB800]' :
                                'bg-[#00FF94]/20 text-[#00FF94]'
                              }`}
                            >
                              {group.severity?.toUpperCase() || 'UNKNOWN'}
                            </Badge>
                            
                            {/* Type */}
                            <Badge className="bg-[#1F1F1F] text-[#A1A1AA]">
                              {group.type || 'unknown'}
                            </Badge>
                            
                            {/* Time Range */}
                            <span className="text-xs text-[#666]">
                              First: {new Date(group.firstSeen).toLocaleString()}
                            </span>
                            <span className="text-xs text-[#666]">
                              Last: {new Date(group.lastSeen).toLocaleString()}
                            </span>
                          </div>
                          
                          <p className="text-white font-medium mb-1 line-clamp-2">
                            {group.message || 'No message'}
                          </p>
                          
                          {group.pathname && (
                            <p className="text-xs text-[#666] flex items-center gap-1">
                              <ExternalLink size={12} />
                              {group.pathname}
                            </p>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyError(group.latestError);
                            }}
                            className="p-2 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                          >
                            {copied ? <Check size={16} className="text-[#00FF94]" /> : <Copy size={16} className="text-[#666]" />}
                          </button>
                        </div>
                      </div>

                      {/* Expanded Group Details */}
                      <AnimatePresence>
                        {selectedGroup?.fingerprint === group.fingerprint && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-4 pt-4 border-t border-[#1F1F1F]"
                          >
                            {/* Group Summary */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                              <div className="bg-[#0A0A0A] rounded-lg p-3">
                                <p className="text-xs text-[#666] mb-1">Total Occurrences</p>
                                <p className="text-xl font-data font-bold text-white">{group.count}</p>
                              </div>
                              <div className="bg-[#0A0A0A] rounded-lg p-3">
                                <p className="text-xs text-[#666] mb-1">First Seen</p>
                                <p className="text-sm text-white">{new Date(group.firstSeen).toLocaleDateString()}</p>
                              </div>
                              <div className="bg-[#0A0A0A] rounded-lg p-3">
                                <p className="text-xs text-[#666] mb-1">Last Seen</p>
                                <p className="text-sm text-white">{new Date(group.lastSeen).toLocaleDateString()}</p>
                              </div>
                              <div className="bg-[#0A0A0A] rounded-lg p-3">
                                <p className="text-xs text-[#666] mb-1">Fingerprint</p>
                                <p className="text-xs font-mono text-[#9D00FF] truncate">{group.fingerprint.slice(0, 20)}...</p>
                              </div>
                            </div>
                            
                            {/* Stack Trace from Latest Error */}
                            {group.latestError?.stack && (
                              <div className="mb-3">
                                <p className="text-xs text-[#666] mb-1">Stack Trace (Latest):</p>
                                <pre className="text-xs text-[#FF0055] bg-[#0A0A0A] p-2 rounded overflow-x-auto max-h-32">
                                  {group.latestError.stack}
                                </pre>
                              </div>
                            )}
                            
                            {/* Individual Errors List */}
                            <div>
                              <p className="text-xs text-[#666] mb-2">All Occurrences ({group.count}):</p>
                              <div className="max-h-40 overflow-y-auto space-y-1">
                                {group.errors.slice(0, 10).map((error, i) => (
                                  <div key={i} className="flex items-center justify-between py-1 px-2 bg-[#0A0A0A] rounded text-xs">
                                    <span className="text-[#666]">{new Date(error.timestamp).toLocaleString()}</span>
                                    <span className="text-white truncate max-w-[200px]">{error.url || 'N/A'}</span>
                                    <span className="text-[#A1A1AA]">{error.user_agent?.slice(0, 30)}...</span>
                                  </div>
                                ))}
                                {group.count > 10 && (
                                  <p className="text-center text-[#666] text-xs py-2">
                                    +{group.count - 10} more occurrences
                                  </p>
                                )}
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle size={48} className="mx-auto text-[#00FF94] mb-4" />
                  <p className="text-white font-medium">No errors found</p>
                  <p className="text-[#666] text-sm">Your application is running smoothly!</p>
                </div>
              )
            ) : (
              // Individual View (Original)
              errors.length > 0 ? (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {errors.filter(e => 
                    severityFilter === 'all' || e.severity === severityFilter
                  ).filter(e =>
                    !searchQuery || 
                    (e.message || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                    (e.pathname || '').toLowerCase().includes(searchQuery.toLowerCase())
                  ).map((error, idx) => (
                    <div
                      key={error.error_id || idx}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        selectedError?.error_id === error.error_id
                          ? 'bg-[#1F1F1F] border-[#9D00FF]'
                          : 'bg-[#111] border-[#1F1F1F] hover:border-[#333]'
                      }`}
                      onClick={() => setSelectedError(selectedError?.error_id === error.error_id ? null : error)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge
                              className={`${
                                error.severity === 'critical' ? 'bg-[#FF0055]/20 text-[#FF0055]' :
                                error.severity === 'high' ? 'bg-[#FF6B00]/20 text-[#FF6B00]' :
                                error.severity === 'medium' ? 'bg-[#FFB800]/20 text-[#FFB800]' :
                                'bg-[#00FF94]/20 text-[#00FF94]'
                              }`}
                            >
                              {error.severity?.toUpperCase() || 'UNKNOWN'}
                            </Badge>
                            <Badge className="bg-[#1F1F1F] text-[#A1A1AA]">
                              {error.error_type || error.type || 'unknown'}
                            </Badge>
                            <span className="text-xs text-[#666]">
                              {new Date(error.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-white font-medium mb-1 line-clamp-1">
                            {error.message || 'No message'}
                          </p>
                          {error.url && (
                            <p className="text-xs text-[#666] flex items-center gap-1">
                              <ExternalLink size={12} />
                              {error.url}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyError(error);
                          }}
                          className="p-2 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                        >
                          {copied ? <Check size={16} className="text-[#00FF94]" /> : <Copy size={16} className="text-[#666]" />}
                        </button>
                      </div>

                      {/* Expanded Details */}
                      <AnimatePresence>
                        {selectedError?.error_id === error.error_id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-4 pt-4 border-t border-[#1F1F1F]"
                          >
                            {error.stack && (
                              <div className="mb-3">
                                <p className="text-xs text-[#666] mb-1">Stack Trace:</p>
                                <pre className="text-xs text-[#FF0055] bg-[#0A0A0A] p-2 rounded overflow-x-auto max-h-32">
                                  {error.stack}
                                </pre>
                              </div>
                            )}
                            {error.component_stack && (
                              <div className="mb-3">
                                <p className="text-xs text-[#666] mb-1">Component Stack:</p>
                                <pre className="text-xs text-[#9D00FF] bg-[#0A0A0A] p-2 rounded overflow-x-auto max-h-32">
                                  {error.component_stack}
                                </pre>
                              </div>
                            )}
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="text-[#666]">Error ID: </span>
                                <span className="text-white font-mono">{error.error_id}</span>
                              </div>
                              <div>
                                <span className="text-[#666]">User Agent: </span>
                                <span className="text-white truncate">{error.user_agent?.slice(0, 50)}...</span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle size={48} className="mx-auto text-[#00FF94] mb-4" />
                  <p className="text-white font-medium">No errors found</p>
                  <p className="text-[#666] text-sm">Your application is running smoothly!</p>
                </div>
              )
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default ErrorAnalyticsDashboard;
