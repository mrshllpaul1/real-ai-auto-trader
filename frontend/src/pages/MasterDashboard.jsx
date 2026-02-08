import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
  Brain, Play, Pause, Settings, TrendingUp, TrendingDown, AlertTriangle,
  Check, X, DollarSign, Activity, Shield, Zap, BarChart3, Clock,
  ChevronRight, RefreshCw, Target, Gauge, Bell, ArrowUp, ArrowDown
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import api from '../services/api';

const MasterDashboard = () => {
  const [status, setStatus] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pendingSignals, setPendingSignals] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [statusRes, dashboardRes, pendingRes] = await Promise.all([
        api.get('/master/status'),
        api.get('/master/dashboard'),
        api.get('/master/pending')
      ]);
      
      setStatus(statusRes.data);
      setDashboardData(dashboardRes.data);
      setPendingSignals(pendingRes.data.pending || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [loadData]);

  const startOrchestrator = async () => {
    try {
      await api.post('/master/start');
      toast.success('Master Orchestrator started');
      loadData();
    } catch (error) {
      toast.error('Failed to start orchestrator');
    }
  };

  const stopOrchestrator = async () => {
    try {
      await api.post('/master/stop');
      toast.success('Master Orchestrator stopped');
      loadData();
    } catch (error) {
      toast.error('Failed to stop orchestrator');
    }
  };

  const setMode = async (mode) => {
    try {
      await api.post('/master/set-mode', { mode });
      toast.success(`Mode set to: ${mode}`);
      loadData();
    } catch (error) {
      toast.error('Failed to set mode');
    }
  };

  const confirmSignal = async (signalId) => {
    try {
      await api.post(`/master/confirm/${signalId}`);
      toast.success('Trade executed');
      loadData();
    } catch (error) {
      toast.error('Failed to confirm trade');
    }
  };

  const rejectSignal = async (signalId) => {
    try {
      await api.post(`/master/reject/${signalId}`);
      toast.info('Signal rejected');
      loadData();
    } catch (error) {
      toast.error('Failed to reject signal');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="animate-spin text-[#00FF94]" size={48} />
      </div>
    );
  }

  const isActive = status?.is_active;
  const mode = status?.mode || 'manual';
  const stats = status?.stats || {};
  const riskStatus = status?.risk_status || {};

  return (
    <div className="p-3 lg:p-6 space-y-4" data-testid="master-dashboard">
      {/* Header - Compact for Chromebook */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-3"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl ${isActive ? 'bg-green-500/20' : 'bg-gray-600/20'}`}>
            <Brain size={28} className={isActive ? 'text-green-400' : 'text-gray-400'} />
          </div>
          <div>
            <h1 className="text-xl lg:text-2xl font-bold flex items-center gap-2">
              Master Trader
              <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}`}>
                {isActive ? 'LIVE' : 'STOPPED'}
              </span>
            </h1>
            <p className="text-xs text-[#A1A1AA]">
              Hybrid Auto-Trading • {mode === 'auto_small' ? 'Small trades auto-execute' : mode}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={mode} onValueChange={setMode}>
            <SelectTrigger className="w-32 h-8 text-xs bg-[#121212] border-[#1F1F1F]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#121212] border-[#1F1F1F]">
              <SelectItem value="manual">Manual</SelectItem>
              <SelectItem value="auto_small">Hybrid</SelectItem>
              <SelectItem value="full_auto">Full Auto</SelectItem>
            </SelectContent>
          </Select>
          
          {isActive ? (
            <Button onClick={stopOrchestrator} variant="destructive" size="sm" className="h-8">
              <Pause size={14} className="mr-1" /> Stop
            </Button>
          ) : (
            <Button onClick={startOrchestrator} className="bg-green-500 hover:bg-green-600 h-8" size="sm">
              <Play size={14} className="mr-1" /> Start
            </Button>
          )}
        </div>
      </motion.div>

      {/* Quick Stats Row - Optimized for smaller screen */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-2">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#A1A1AA]">Portfolio</p>
                <p className="text-lg font-bold text-white">${(status?.portfolio_value || 0).toLocaleString()}</p>
              </div>
              <DollarSign className="text-green-400" size={20} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#A1A1AA]">Daily P&L</p>
                <p className={`text-lg font-bold ${riskStatus.daily_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {riskStatus.daily_pnl_pct >= 0 ? '+' : ''}{(riskStatus.daily_pnl_pct || 0).toFixed(2)}%
                </p>
              </div>
              {riskStatus.daily_pnl_pct >= 0 ? <ArrowUp className="text-green-400" size={20} /> : <ArrowDown className="text-red-400" size={20} />}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#A1A1AA]">Trades</p>
                <p className="text-lg font-bold text-white">{stats.executed_trades || 0}</p>
              </div>
              <BarChart3 className="text-[#9D00FF]" size={20} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#A1A1AA]">Win Rate</p>
                <p className="text-lg font-bold text-[#FFB800]">{((stats.win_rate || 0) * 100).toFixed(0)}%</p>
              </div>
              <Target className="text-[#FFB800]" size={20} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F] col-span-2 lg:col-span-1">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-[#A1A1AA]">Drawdown</p>
                <p className={`text-lg font-bold ${(riskStatus.current_drawdown_pct || 0) > 10 ? 'text-red-400' : 'text-green-400'}`}>
                  {(riskStatus.current_drawdown_pct || 0).toFixed(1)}%
                </p>
              </div>
              <Shield className={`${(riskStatus.current_drawdown_pct || 0) > 10 ? 'text-red-400' : 'text-green-400'}`} size={20} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Pending Confirmations - Most Important */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F] lg:col-span-2">
          <CardHeader className="py-3 px-4">
            <CardTitle className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Bell className="text-[#FFB800]" size={16} />
                Pending Confirmations
              </div>
              {pendingSignals.length > 0 && (
                <span className="px-2 py-0.5 bg-[#FFB800]/20 text-[#FFB800] rounded-full text-xs">
                  {pendingSignals.length} pending
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-2 max-h-64 overflow-y-auto">
            <AnimatePresence>
              {pendingSignals.length === 0 ? (
                <div className="text-center py-8 text-[#A1A1AA] text-sm">
                  <Check className="mx-auto mb-2" size={24} />
                  No pending confirmations
                </div>
              ) : (
                <div className="space-y-2">
                  {pendingSignals.map((signal) => (
                    <motion.div
                      key={signal.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            signal.action === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {signal.action}
                          </span>
                          <span className="font-medium text-sm">{signal.symbol}</span>
                        </div>
                        <span className="text-xs text-[#A1A1AA]">{signal.size_pct?.toFixed(1)}% size</span>
                      </div>
                      
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Gauge size={12} className="text-[#A1A1AA]" />
                          <span className="text-xs text-[#A1A1AA]">Confidence: {signal.confidence?.toFixed(0)}%</span>
                        </div>
                        <span className="text-xs text-[#A1A1AA]">{signal.source}</span>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button
                          onClick={() => confirmSignal(signal.id)}
                          size="sm"
                          className="flex-1 h-7 bg-green-500 hover:bg-green-600 text-xs"
                        >
                          <Check size={12} className="mr-1" /> Confirm
                        </Button>
                        <Button
                          onClick={() => rejectSignal(signal.id)}
                          size="sm"
                          variant="destructive"
                          className="flex-1 h-7 text-xs"
                        >
                          <X size={12} className="mr-1" /> Reject
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>

        {/* AI Systems Status */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader className="py-3 px-4">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="text-[#9D00FF]" size={16} />
              AI Systems
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-3">
            {/* News Monitor */}
            <div className="p-2 bg-[#121212] rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium">News Monitor</span>
                <span className={`w-2 h-2 rounded-full ${dashboardData?.news?.is_running ? 'bg-green-400' : 'bg-gray-500'}`}></span>
              </div>
              <p className="text-[10px] text-[#A1A1AA]">
                {dashboardData?.news?.stats?.news_processed || 0} articles • {dashboardData?.news?.stats?.alerts_triggered || 0} alerts
              </p>
            </div>

            {/* Market Regime */}
            <div className="p-2 bg-[#121212] rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium">Market Regime</span>
                <span className={`text-xs font-bold capitalize ${
                  dashboardData?.specialists?.regime?.current_regime?.includes('bull') ? 'text-green-400' :
                  dashboardData?.specialists?.regime?.current_regime?.includes('bear') ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {dashboardData?.specialists?.regime?.current_regime?.replace('_', ' ') || 'Unknown'}
                </span>
              </div>
              <Progress value={dashboardData?.specialists?.regime?.confidence || 0} className="h-1" />
            </div>

            {/* Orchestrator Stats */}
            <div className="p-2 bg-[#121212] rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium">Signals</span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-center">
                <div>
                  <p className="text-sm font-bold text-white">{stats.total_signals || 0}</p>
                  <p className="text-[9px] text-[#A1A1AA]">Total</p>
                </div>
                <div>
                  <p className="text-sm font-bold text-green-400">{stats.auto_executed || 0}</p>
                  <p className="text-[9px] text-[#A1A1AA]">Auto</p>
                </div>
                <div>
                  <p className="text-sm font-bold text-red-400">{stats.rejected || 0}</p>
                  <p className="text-[9px] text-[#A1A1AA]">Rejected</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Trades */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader className="py-3 px-4">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Clock className="text-[#00FF94]" size={16} />
            Recent Trades
          </CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          <div className="max-h-40 overflow-y-auto">
            {status?.recent_trades?.length > 0 ? (
              <div className="space-y-1">
                {status.recent_trades.slice(-5).reverse().map((trade, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-[#121212] rounded text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        trade.status === 'executed' ? 'bg-green-400' : 'bg-red-400'
                      }`}></span>
                      <span className={`font-medium ${trade.action === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.action}
                      </span>
                      <span className="text-white">{trade.symbol}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[#A1A1AA]">
                      <span>{trade.size_pct?.toFixed(1)}%</span>
                      <span>{trade.confidence?.toFixed(0)}% conf</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-[#A1A1AA] text-sm">
                No trades yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Risk Limits */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
        <div className="p-2 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg">
          <p className="text-[#A1A1AA]">Max Position</p>
          <p className="font-bold text-white">{riskStatus.limits?.max_position_pct || 10}%</p>
        </div>
        <div className="p-2 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg">
          <p className="text-[#A1A1AA]">Max Daily Loss</p>
          <p className="font-bold text-white">{riskStatus.limits?.max_daily_loss_pct || 5}%</p>
        </div>
        <div className="p-2 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg">
          <p className="text-[#A1A1AA]">Max Drawdown</p>
          <p className="font-bold text-white">{riskStatus.limits?.max_drawdown_pct || 15}%</p>
        </div>
        <div className="p-2 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg">
          <p className="text-[#A1A1AA]">Min Confidence</p>
          <p className="font-bold text-white">{riskStatus.limits?.min_confidence || 60}%</p>
        </div>
      </div>
    </div>
  );
};

export default MasterDashboard;
