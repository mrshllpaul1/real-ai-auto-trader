import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { 
  Bot, Play, Pause, TrendingUp, TrendingDown, Bell, 
  Loader2, AlertCircle, CheckCircle, Sparkles, Target
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import { useTradingMode } from '../context/TradingModeContext';

const AutomatedTradingSection = () => {
  const [positions, setPositions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  
  // Use global trading mode context
  const { isPaperMode, setMode } = useTradingMode();

  // Handle paper mode toggle
  const handlePaperModeChange = (isPaper) => {
    setMode(isPaper ? 'paper' : 'real');
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [posRes, alertRes, perfRes] = await Promise.all([
        api.get('/auto-trade/active-positions'),
        api.get('/auto-trade/alerts?limit=5'),
        api.get('/auto-trade/performance')
      ]);
      
      setPositions(posRes.data.positions || []);
      setAlerts(alertRes.data.alerts || []);
      setPerformance(perfRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const executeWeekly = async () => {
    setExecuting(true);
    try {
      const response = await api.post('/auto-trade/execute-weekly', {
        paper_trade: isPaperMode
      });
      
      if (response.data.success) {
        const exec = response.data.execution;
        toast.success(`Executed ${exec.total_trades} trades! Total: $${exec.total_invested.toLocaleString()}`);
        loadData();
      } else {
        toast.error(response.data.error || 'Execution failed');
      }
    } catch (error) {
      toast.error('Failed to execute trades');
    } finally {
      setExecuting(false);
    }
  };

  const checkPositions = async () => {
    setLoading(true);
    try {
      const response = await api.post('/auto-trade/check-positions');
      if (response.data.triggered?.length > 0) {
        toast.info(`${response.data.triggered.length} positions closed`);
      } else {
        toast.success('All positions healthy');
      }
      loadData();
    } catch (error) {
      toast.error('Failed to check positions');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <Card className="bg-gradient-to-br from-[#00FF94]/20 to-[#007AFF]/10 border-[#00FF94]/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-heading flex items-center gap-3">
                  <Bot className="text-[#00FF94]" size={28} />
                  Automated Weekly Trading
                  <Badge className={paperMode ? "bg-[#FF9500]/20 text-[#FF9500]" : "bg-[#FF0055]/20 text-[#FF0055]"}>
                    {paperMode ? 'PAPER' : 'REAL'}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  AI executes 10 coins + 1 gem weekly with stop-loss & take-profit
                </CardDescription>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-[#A1A1AA]">Paper Mode</span>
                  <Switch
                    checked={paperMode}
                    onCheckedChange={handlePaperModeChange}
                    data-testid="paper-mode-switch"
                  />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button
                onClick={executeWeekly}
                disabled={executing}
                className="bg-[#00FF94] hover:bg-[#00CC77] text-black font-bold"
                data-testid="execute-weekly-btn"
              >
                {executing ? (
                  <Loader2 className="animate-spin mr-2" size={20} />
                ) : (
                  <Play className="mr-2" size={20} />
                )}
                Execute Weekly Rebalance
              </Button>
              <Button
                onClick={checkPositions}
                disabled={loading}
                variant="outline"
                className="border-[#007AFF] text-[#007AFF]"
                data-testid="check-positions-btn"
              >
                {loading ? (
                  <Loader2 className="animate-spin mr-2" size={16} />
                ) : (
                  <Target className="mr-2" size={16} />
                )}
                Check Stop/Take Profit
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Performance Summary */}
      {performance && performance.total_trades > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-2">
                <TrendingUp className="text-[#00FF94]" size={24} />
                Performance Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total Trades</div>
                  <div className="text-2xl font-bold text-white">{performance.total_trades}</div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Win Rate</div>
                  <div className={`text-2xl font-bold ${performance.win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {performance.win_rate}%
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total P/L</div>
                  <div className={`text-2xl font-bold ${performance.total_pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    ${performance.total_pnl_usd?.toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Gem Win Rate</div>
                  <div className={`text-2xl font-bold ${performance.gem_win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#A1A1AA]'}`}>
                    {performance.gem_win_rate || 0}%
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Active Positions */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-xl font-heading flex items-center gap-2">
              <Target className="text-[#007AFF]" size={24} />
              Active Positions ({positions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <p className="text-[#A1A1AA] text-center py-4">No active positions</p>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {positions.map((pos, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-[#121212] rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-white">{pos.coin_id?.toUpperCase()}</span>
                      {pos.is_gem && (
                        <Badge className="bg-[#FFD700]/20 text-[#FFD700]">
                          <Sparkles size={10} className="mr-1" />GEM
                        </Badge>
                      )}
                      <Badge className={pos.paper_trade ? "bg-[#FF9500]/20 text-[#FF9500]" : "bg-[#00FF94]/20 text-[#00FF94]"}>
                        {pos.paper_trade ? 'PAPER' : 'REAL'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-[#A1A1AA]">${pos.amount_usd?.toLocaleString()}</span>
                      <span className="text-white">@ ${pos.entry_price?.toFixed(4)}</span>
                      <span className="text-[#FF0055]">SL: ${pos.stop_loss_price?.toFixed(4)}</span>
                      <span className="text-[#00FF94]">TP: ${pos.take_profit_price?.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-2">
                <Bell className="text-[#FF9500]" size={24} />
                Recent Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      alert.priority === 'high' ? 'bg-[#FF0055]/10 border-[#FF0055]/30' :
                      alert.priority === 'critical' ? 'bg-[#FF9500]/10 border-[#FF9500]/30' :
                      'bg-[#121212] border-[#1F1F1F]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-white">{alert.title}</span>
                      <span className="text-xs text-[#A1A1AA]">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-[#A1A1AA] whitespace-pre-line">{alert.message}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default AutomatedTradingSection;
