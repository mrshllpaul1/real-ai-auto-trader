import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { 
  Shield, DollarSign, AlertTriangle, Wallet, TrendingUp, TrendingDown,
  Lock, Unlock, RefreshCw, Power, PowerOff, CheckCircle, XCircle,
  AlertOctagon, Play, Pause, Activity, PieChart
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const TradingBudget = () => {
  const [budgetStatus, setBudgetStatus] = useState(null);
  const [isolation, setIsolation] = useState(null);
  const [positions, setPositions] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [emergencyStatus, setEmergencyStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Budget form
  const [newBudget, setNewBudget] = useState('');
  const [enableRealTrading, setEnableRealTrading] = useState(false);
  
  // Emergency stop modal state
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [emergencyStep, setEmergencyStep] = useState(0);
  const [liquidatePositions, setLiquidatePositions] = useState(false);
  const [emergencyLoading, setEmergencyLoading] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, isolationRes, positionsRes, transactionsRes, emergencyRes] = await Promise.all([
        api.get('/isolated-portfolio/status').catch(() => ({ data: null })),
        api.get('/isolated-portfolio/verify-isolation').catch(() => ({ data: null })),
        api.get('/isolated-portfolio/positions').catch(() => ({ data: { positions: [] } })),
        api.get('/isolated-portfolio/transactions?limit=20').catch(() => ({ data: { transactions: [] } })),
        api.get('/isolated-portfolio/emergency-status').catch(() => ({ data: null }))
      ]);
      
      setBudgetStatus(statusRes.data);
      setIsolation(isolationRes.data);
      setPositions(positionsRes.data?.positions || []);
      setTransactions(transactionsRes.data?.transactions || []);
      setEmergencyStatus(emergencyRes.data);
    } catch (error) {
      console.error('Error loading budget data:', error);
      toast.error('Failed to load budget data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleSetBudget = async () => {
    const amount = parseFloat(newBudget);
    if (isNaN(amount) || amount < 0) {
      toast.error('Please enter a valid budget amount');
      return;
    }
    
    try {
      const response = await api.post('/isolated-portfolio/set-budget', {
        amount_usd: amount,
        enable_real_trading: enableRealTrading
      });
      
      if (response.data.success) {
        toast.success(`Budget set to $${amount.toFixed(2)}`);
        setNewBudget('');
        loadData();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to set budget');
    }
  };

  const handleEmergencyStop = async () => {
    setEmergencyLoading(true);
    
    try {
      if (emergencyStep === 0) {
        // First confirmation
        const response = await api.post('/isolated-portfolio/emergency-stop', {
          liquidate_positions: liquidatePositions,
          confirmation_code: 'CONFIRM_STEP_1'
        });
        
        if (response.data.step === 1) {
          setEmergencyStep(1);
          toast.warning('First confirmation received. Confirm again to proceed.');
        }
      } else if (emergencyStep === 1) {
        // Final confirmation
        const response = await api.post('/isolated-portfolio/emergency-stop', {
          liquidate_positions: liquidatePositions,
          confirmation_code: 'EMERGENCY_STOP_CONFIRMED'
        });
        
        if (response.data.success) {
          toast.success('🚨 Emergency stop activated!');
          setShowEmergencyModal(false);
          setEmergencyStep(0);
          loadData();
        } else {
          toast.error(response.data.error || 'Emergency stop failed');
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Emergency stop failed');
    } finally {
      setEmergencyLoading(false);
    }
  };

  const handleResume = async () => {
    try {
      const response = await api.post('/isolated-portfolio/resume-trading', {
        confirmation_code: 'RESUME_TRADING_CONFIRMED'
      });
      
      if (response.data.success) {
        toast.success('Trading resumed!');
        loadData();
      } else {
        toast.error(response.data.error || 'Failed to resume');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to resume trading');
    }
  };

  const closeEmergencyModal = () => {
    setShowEmergencyModal(false);
    setEmergencyStep(0);
    setLiquidatePositions(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Budget Manager...</p>
        </div>
      </div>
    );
  }

  const isEmergencyStopped = emergencyStatus?.emergency_stopped;
  const isTradingEnabled = budgetStatus?.real_trading_enabled && !isEmergencyStopped;
  const pnlPercent = budgetStatus?.pnl_pct || 0;

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="trading-budget-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Shield size={40} className="text-[#00FF94]" />
            <span className="text-white">AI Trading</span>
            <span className="text-[#00FF94]">Budget</span>
          </h1>
          <p className="text-[#A1A1AA]">
            Isolated budget management - Your main assets are always protected
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={loadData}
            variant="outline"
            className="border-[#1F1F1F]"
            data-testid="refresh-btn"
          >
            <RefreshCw size={16} />
          </Button>
          
          {/* Emergency Stop / Resume Button */}
          {isEmergencyStopped ? (
            <Button
              onClick={handleResume}
              className="bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
              data-testid="resume-btn"
            >
              <Play size={16} className="mr-2" />
              Resume Trading
            </Button>
          ) : (
            <Button
              onClick={() => setShowEmergencyModal(true)}
              className="bg-[#FF0055] hover:bg-[#FF0055]/80"
              data-testid="emergency-stop-btn"
            >
              <PowerOff size={16} className="mr-2" />
              Emergency Stop
            </Button>
          )}
        </div>
      </motion.div>

      {/* Emergency Stopped Banner */}
      <AnimatePresence>
        {isEmergencyStopped && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <Card className="bg-[#FF0055]/20 border-[#FF0055]">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <AlertOctagon size={24} className="text-[#FF0055]" />
                  <div>
                    <h3 className="font-bold text-[#FF0055]">🚨 EMERGENCY STOP ACTIVE</h3>
                    <p className="text-sm text-[#A1A1AA]">
                      All AI trading has been halted. Click "Resume Trading" to re-enable.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Isolation Verification Banner */}
      {isolation?.isolated && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-[#00FF94]/10 border-[#00FF94]/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Lock size={20} className="text-[#00FF94]" />
                <div>
                  <span className="text-[#00FF94] font-bold">Budget Isolation Active</span>
                  <span className="text-[#A1A1AA] ml-2">- {isolation.message}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Main Stats Grid */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Initial Budget */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="initial-budget-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Wallet size={20} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Initial Budget</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              ${(budgetStatus?.initial_budget || 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>

        {/* Current Value */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="current-value-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign size={20} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Current Value</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              ${(budgetStatus?.current_value || 0).toLocaleString()}
            </div>
            {pnlPercent !== 0 && (
              <div className={`text-sm flex items-center gap-1 mt-1 ${pnlPercent >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                {pnlPercent >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cash Available */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="cash-available-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Activity size={20} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Cash Available</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FFB800]">
              ${(budgetStatus?.cash_available || 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>

        {/* Trading Status */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="trading-status-card">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Power size={20} className={isTradingEnabled ? 'text-[#00FF94]' : 'text-[#FF0055]'} />
              <span className="text-sm text-[#A1A1AA]">Trading Status</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={isTradingEnabled ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                {isTradingEnabled ? 'ENABLED' : isEmergencyStopped ? 'STOPPED' : 'DISABLED'}
              </Badge>
            </div>
            <div className="text-xs text-[#A1A1AA] mt-2">
              {budgetStatus?.trades_executed || 0} trades executed
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Set Budget Section */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <DollarSign className="text-[#9D00FF]" />
              Set Trading Budget
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-[#A1A1AA] mb-2 block">Budget Amount (USD)</label>
                <Input
                  type="number"
                  placeholder="500"
                  value={newBudget}
                  onChange={(e) => setNewBudget(e.target.value)}
                  className="bg-[#121212] border-[#1F1F1F]"
                  data-testid="budget-input"
                />
              </div>
              <div>
                <label className="text-sm text-[#A1A1AA] mb-2 block">Enable Real Trading</label>
                <div className="flex items-center gap-3 h-10">
                  <Switch
                    checked={enableRealTrading}
                    onCheckedChange={setEnableRealTrading}
                    data-testid="real-trading-toggle"
                  />
                  <span className={enableRealTrading ? 'text-[#00FF94]' : 'text-[#A1A1AA]'}>
                    {enableRealTrading ? 'Real Trades' : 'Paper Only'}
                  </span>
                </div>
              </div>
              <div className="flex items-end">
                <Button
                  onClick={handleSetBudget}
                  className="w-full bg-[#9D00FF] hover:bg-[#9D00FF]/80"
                  data-testid="set-budget-btn"
                >
                  <Wallet size={16} className="mr-2" />
                  Set Budget
                </Button>
              </div>
            </div>
            
            <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
              <div className="flex items-start gap-3">
                <Shield className="text-[#00FF94] flex-shrink-0 mt-0.5" size={18} />
                <div className="text-sm text-[#A1A1AA]">
                  <strong className="text-white">Budget Isolation Guarantee:</strong> The AI will ONLY trade with the budget you allocate here. 
                  Your existing Kraken holdings are completely protected and will never be touched.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Positions Section */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <PieChart className="text-[#FFB800]" />
              AI-Managed Positions ({positions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <div className="text-center py-8 text-[#A1A1AA]">
                <Activity size={48} className="mx-auto mb-4 opacity-50" />
                <p>No open positions</p>
                <p className="text-sm">Positions opened by AI will appear here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {positions.map((pos, idx) => (
                  <div key={pos.position_id || idx} className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white">{pos.coin_id?.toUpperCase()}</span>
                          <Badge className={pos.pnl_pct >= 0 ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                            {pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct?.toFixed(2)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-[#A1A1AA]">
                          {pos.quantity?.toFixed(6)} @ ${pos.entry_price?.toFixed(4)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-data text-white">${pos.current_value?.toFixed(2)}</p>
                        <p className={`text-sm ${pos.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {pos.pnl_usd >= 0 ? '+' : ''}${pos.pnl_usd?.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Transactions */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="text-[#007AFF]" />
              Recent Transactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-[#A1A1AA]">
                <p>No transactions yet</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {transactions.map((tx, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${tx.type === 'buy' ? 'bg-[#00FF94]/20' : tx.type === 'sell' ? 'bg-[#FF0055]/20' : 'bg-[#FFB800]/20'}`}>
                        {tx.type === 'buy' ? <TrendingUp size={16} className="text-[#00FF94]" /> : 
                         tx.type === 'sell' ? <TrendingDown size={16} className="text-[#FF0055]" /> :
                         <AlertTriangle size={16} className="text-[#FFB800]" />}
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">{tx.type?.toUpperCase()} {tx.coin_id?.toUpperCase()}</p>
                        <p className="text-xs text-[#A1A1AA]">{new Date(tx.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-data">${tx.amount_usd?.toFixed(2)}</p>
                      {tx.pnl_usd !== undefined && (
                        <p className={`text-xs ${tx.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          P&L: {tx.pnl_usd >= 0 ? '+' : ''}${tx.pnl_usd?.toFixed(2)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Emergency Stop Modal - Double Confirmation */}
      <AnimatePresence>
        {showEmergencyModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={closeEmergencyModal}>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#0A0A0A] border-2 border-[#FF0055] rounded-2xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              data-testid="emergency-modal"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-[#FF0055]/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertOctagon size={32} className="text-[#FF0055]" />
                </div>
                <h2 className="text-2xl font-bold text-[#FF0055]">
                  {emergencyStep === 0 ? '🚨 Emergency Stop' : '⚠️ Final Confirmation'}
                </h2>
              </div>

              {emergencyStep === 0 ? (
                <>
                  <p className="text-[#A1A1AA] text-center mb-6">
                    This will <strong className="text-white">immediately halt all AI trading</strong>. 
                    Your budget will remain intact unless you choose to liquidate.
                  </p>
                  
                  <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F] mb-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">Liquidate All Positions</p>
                        <p className="text-xs text-[#A1A1AA]">Close all open positions at market price</p>
                      </div>
                      <Switch
                        checked={liquidatePositions}
                        onCheckedChange={setLiquidatePositions}
                        data-testid="liquidate-toggle"
                      />
                    </div>
                  </div>
                  
                  <Button
                    onClick={handleEmergencyStop}
                    disabled={emergencyLoading}
                    className="w-full bg-[#FF0055] hover:bg-[#FF0055]/80 mb-3"
                    data-testid="confirm-step-1-btn"
                  >
                    {emergencyLoading ? 'Processing...' : 'First Confirmation - Are You Sure?'}
                  </Button>
                </>
              ) : (
                <>
                  <div className="p-4 bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg mb-6">
                    <p className="text-[#FF0055] font-bold mb-2">⚠️ THIS IS YOUR FINAL WARNING</p>
                    <p className="text-sm text-[#A1A1AA]">
                      Clicking the button below will:
                    </p>
                    <ul className="text-sm text-white mt-2 space-y-1">
                      <li>• <strong>Disable</strong> all AI trading immediately</li>
                      {liquidatePositions && (
                        <li>• <strong>Liquidate</strong> all {positions.length} open positions</li>
                      )}
                    </ul>
                  </div>
                  
                  <Button
                    onClick={handleEmergencyStop}
                    disabled={emergencyLoading}
                    className="w-full bg-[#FF0055] hover:bg-[#FF0055]/80 mb-3"
                    data-testid="confirm-step-2-btn"
                  >
                    {emergencyLoading ? 'STOPPING...' : '🚨 CONFIRM EMERGENCY STOP'}
                  </Button>
                </>
              )}
              
              <Button
                variant="outline"
                className="w-full border-[#1F1F1F]"
                onClick={closeEmergencyModal}
              >
                Cancel
              </Button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TradingBudget;
