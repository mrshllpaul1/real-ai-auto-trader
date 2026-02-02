import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { 
  Rocket, Target, TrendingUp, Sparkles, DollarSign, 
  Loader2, RefreshCw, Trophy, Flame, Shield, HelpCircle, Zap
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import AutopilotControl from '../components/AutopilotControl';
import UserTutorial from '../components/UserTutorial';
import { AIDecisionsPanel, generateAIReasoning } from '../components/AIDecisionVisualization';

const GrowthDashboard = () => {
  const [stats, setStats] = useState(null);
  const [positions, setPositions] = useState([]);
  const [budget, setBudget] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [paperMode, setPaperMode] = useState(true);
  const [showTutorial, setShowTutorial] = useState(false);
  const [budgetInput, setBudgetInput] = useState('');
  const [settingBudget, setSettingBudget] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);
  const [settingThreshold, setSettingThreshold] = useState(false);

  useEffect(() => {
    loadData();
    loadBudget();
    // Show tutorial on first visit
    const tutorialSeen = localStorage.getItem('tutorial_completed');
    if (!tutorialSeen) {
      setShowTutorial(true);
    }
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, posRes] = await Promise.all([
        api.get('/growth/stats'),
        api.get('/growth/positions?status=OPEN')
      ]);
      setStats(statsRes.data);
      setPositions(posRes.data.positions || []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const loadBudget = async () => {
    try {
      const response = await api.get('/budget/');
      setBudget(response.data);
      setConfidenceThreshold(response.data.ai_confidence_threshold || 70);
    } catch (error) {
      console.error('Budget error:', error);
    }
  };

  const handleSetConfidenceThreshold = async (newThreshold) => {
    setSettingThreshold(true);
    try {
      await api.post('/budget/confidence-threshold', { threshold: newThreshold });
      setConfidenceThreshold(newThreshold);
      toast.success(`AI confidence threshold set to ${newThreshold}%`);
    } catch (error) {
      toast.error('Failed to set confidence threshold');
    } finally {
      setSettingThreshold(false);
    }
  };

  const handleSetBudget = async () => {
    const amount = parseFloat(budgetInput);
    if (isNaN(amount) || amount < 0) {
      toast.error('Please enter a valid budget amount');
      return;
    }
    setSettingBudget(true);
    try {
      const response = await api.post('/budget/set', {
        amount: amount,
        enable_real_trading: true
      });
      setBudget(response.data);
      toast.success(`Budget set to $${amount}. Real trading enabled!`);
      setBudgetInput('');
    } catch (error) {
      toast.error('Failed to set budget');
    } finally {
      setSettingBudget(false);
    }
  };

  const completeTutorial = () => {
    localStorage.setItem('tutorial_completed', 'true');
    setShowTutorial(false);
  };

  const executeGrowth = async () => {
    setExecuting(true);
    try {
      const response = await api.post('/growth/execute', {
        capital: 500,
        paper_trade: paperMode
      });
      if (response.data.success) {
        toast.success(`Deployed $500! ${response.data.execution.total_trades} trades`);
        loadData();
      }
    } catch (error) {
      toast.error('Execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const monitorPositions = async () => {
    setLoading(true);
    try {
      const response = await api.post('/growth/monitor');
      const sl = response.data.stop_losses_hit?.length || 0;
      const tp = response.data.take_profits_hit?.length || 0;
      if (sl || tp) {
        toast.info(`SL: ${sl} | TP: ${tp}`);
      } else {
        toast.success('All positions healthy');
      }
      loadData();
    } catch (error) {
      toast.error('Monitor failed');
    } finally {
      setLoading(false);
    }
  };

  const portfolio = stats?.portfolio || {};
  const goalProgress = stats?.goal_progress || {};
  const statistics = stats?.statistics || {};
  
  // Generate AI decisions for positions
  const aiDecisions = positions.map(pos => generateAIReasoning(pos));

  return (
    <div className="min-h-screen bg-[#000000] text-white p-4 md:p-8">
      {/* Tutorial Modal */}
      {showTutorial && (
        <UserTutorial 
          onComplete={completeTutorial} 
          onSkip={completeTutorial}
        />
      )}
      
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold mb-2 flex items-center gap-3">
              <Rocket className="text-[#00FF94]" />
              $500 → $100,000
            </h1>
            <p className="text-[#A1A1AA]">Aggressive Growth Engine • Always hunting • Always compounding</p>
          </div>
          <Button
            variant="ghost"
            onClick={() => setShowTutorial(true)}
            className="text-[#A1A1AA] hover:text-white"
          >
            <HelpCircle className="mr-2" size={16} />
            Tutorial
          </Button>
        </div>
      </motion.div>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <Card className="bg-gradient-to-br from-[#00FF94]/20 via-[#007AFF]/10 to-[#9D00FF]/20 border-[#00FF94]/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-sm text-[#A1A1AA]">Current Value</div>
                <div className="text-4xl md:text-5xl font-bold text-[#00FF94]">
                  ${portfolio.total_value?.toLocaleString() || '0'}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-[#A1A1AA]">Goal</div>
                <div className="text-2xl font-bold text-white">$100,000</div>
              </div>
            </div>
            
            <Progress 
              value={goalProgress.progress_pct || 0} 
              className="h-4 mb-2 bg-[#1F1F1F]"
            />
            
            <div className="flex justify-between text-sm">
              <span className="text-[#A1A1AA]">{goalProgress.progress_pct?.toFixed(1) || 0}% complete</span>
              <span className="text-[#00FF94] font-bold">{portfolio.current_multiplier?.toFixed(1) || 0}x</span>
              <span className="text-[#A1A1AA]">${goalProgress.remaining?.toLocaleString() || '100,000'} to go</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Budget Control - Only shows when real trading is selected */}
      {!paperMode && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <Card className="bg-[#0A0A0A] border-[#FF9500]/30">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Shield className="text-[#FF9500]" />
                Budget Protection
                {budget?.real_trading_enabled && (
                  <Badge className="bg-[#00FF94]/20 text-[#00FF94] ml-2">ENABLED</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-[#A1A1AA] mb-4">
                Set your trading budget. The AI will ONLY use this amount - your other assets remain untouched.
              </p>
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1">
                  <Input
                    type="number"
                    placeholder="Enter budget amount ($)"
                    value={budgetInput}
                    onChange={(e) => setBudgetInput(e.target.value)}
                    className="bg-[#121212] border-[#1F1F1F]"
                  />
                </div>
                <Button
                  onClick={handleSetBudget}
                  disabled={settingBudget}
                  className="bg-[#FF9500] hover:bg-[#CC7700] text-black"
                >
                  {settingBudget ? <Loader2 className="animate-spin" /> : 'Set Budget'}
                </Button>
              </div>
              {budget && (
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-lg font-bold text-[#00FF94]">${budget.allocated_budget || 0}</div>
                    <div className="text-xs text-[#A1A1AA]">Allocated</div>
                  </div>
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-lg font-bold text-[#007AFF]">${budget.available_budget || 0}</div>
                    <div className="text-xs text-[#A1A1AA]">Available</div>
                  </div>
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-lg font-bold text-[#FF9500]">${budget.used_budget || 0}</div>
                    <div className="text-xs text-[#A1A1AA]">In Use</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-[#A1A1AA]">Paper Mode</span>
                <Switch checked={paperMode} onCheckedChange={setPaperMode} />
                <Badge className={paperMode ? "bg-[#FF9500]/20 text-[#FF9500]" : "bg-[#FF0055]/20 text-[#FF0055]"}>
                  {paperMode ? 'PAPER' : 'REAL'}
                </Badge>
              </div>
              
              <Button
                onClick={executeGrowth}
                disabled={executing}
                className="bg-[#00FF94] hover:bg-[#00CC77] text-black font-bold"
                data-testid="deploy-growth-btn"
              >
                {executing ? <Loader2 className="animate-spin mr-2" /> : <Rocket className="mr-2" />}
                Deploy $500
              </Button>
              
              <Button
                onClick={monitorPositions}
                disabled={loading}
                variant="outline"
                className="border-[#007AFF] text-[#007AFF]"
              >
                {loading ? <Loader2 className="animate-spin mr-2" /> : <RefreshCw className="mr-2" />}
                Check Positions
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                <Target size={16} />
                <span className="text-xs">Win Rate</span>
              </div>
              <div className={`text-2xl font-bold ${statistics.win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                {statistics.win_rate || 0}%
              </div>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25 }}>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                <TrendingUp size={16} />
                <span className="text-xs">Total P/L</span>
              </div>
              <div className={`text-2xl font-bold ${statistics.total_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                ${statistics.total_pnl?.toLocaleString() || 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                <Trophy size={16} />
                <span className="text-xs">Moonshots</span>
              </div>
              <div className="text-2xl font-bold text-[#FFD700]">
                {statistics.moonshots || 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
        
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.35 }}>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                <Flame size={16} />
                <span className="text-xs">Open Positions</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {statistics.open_trades || 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <AutopilotControl paperMode={paperMode} />

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="text-[#00FF94]" />
              Open Positions ({positions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <p className="text-[#A1A1AA] text-center py-8">No open positions. Deploy capital to start!</p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {positions.map((pos, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="font-bold">{pos.coin_id?.toUpperCase()}</span>
                      {pos.is_gem && (
                        <Badge className="bg-[#FFD700]/20 text-[#FFD700]">
                          <Sparkles size={10} className="mr-1" />GEM
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-[#A1A1AA]">${pos.amount_usd}</span>
                      <span>@ ${pos.entry_price?.toFixed(4)}</span>
                      <span className="text-[#FF0055]">SL: ${pos.stop_loss_price?.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default GrowthDashboard;
