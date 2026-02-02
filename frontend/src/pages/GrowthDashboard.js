import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Rocket, Target, TrendingUp, Sparkles, DollarSign, 
  Loader2, RefreshCw, Trophy, Flame, Shield, HelpCircle, Zap,
  Wallet, TestTube, AlertTriangle, CheckCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import AutopilotControl from '../components/AutopilotControl';
import UserTutorial from '../components/UserTutorial';
import CoinUniverseManager from '../components/CoinUniverseManager';
import AIDiscoveryPanel from '../components/AIDiscoveryPanel';
import MarketSentimentPanel from '../components/MarketSentimentPanel';
import CryptoNewsFeed from '../components/CryptoNewsFeed';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const GrowthDashboard = () => {
  // Trading mode state - persist to localStorage
  const [tradingMode, setTradingMode] = useState(() => {
    return localStorage.getItem('growth_trading_mode') || 'paper';
  });
  
  // Paper trading state
  const [paperStats, setPaperStats] = useState(null);
  const [paperPositions, setPaperPositions] = useState([]);
  
  // Real trading state
  const [realStats, setRealStats] = useState(null);
  const [realPositions, setRealPositions] = useState([]);
  const [budget, setBudget] = useState(null);
  const [krakenBalance, setKrakenBalance] = useState(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [budgetInput, setBudgetInput] = useState('');
  const [settingBudget, setSettingBudget] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);
  const [settingThreshold, setSettingThreshold] = useState(false);

  // Load data based on mode
  const loadPaperData = useCallback(async () => {
    try {
      const [statsRes, posRes] = await Promise.all([
        api.get('/growth/stats?mode=paper'),
        api.get('/growth/positions?status=OPEN&mode=paper')
      ]);
      setPaperStats(statsRes.data);
      setPaperPositions(posRes.data.positions || []);
    } catch (error) {
      console.error('Paper data error:', error);
    }
  }, []);

  const loadRealData = useCallback(async () => {
    try {
      const [statsRes, posRes, budgetRes] = await Promise.all([
        api.get('/growth/stats?mode=real'),
        api.get('/growth/positions?status=OPEN&mode=real'),
        api.get('/budget/')
      ]);
      setRealStats(statsRes.data);
      setRealPositions(posRes.data.positions || []);
      setBudget(budgetRes.data);
      setConfidenceThreshold(budgetRes.data.ai_confidence_threshold || 70);
      
      // Try to get Kraken balance
      try {
        const krakenRes = await api.get('/trading/balance');
        setKrakenBalance(krakenRes.data);
      } catch (e) {
        console.log('Kraken balance not available');
      }
    } catch (error) {
      console.error('Real data error:', error);
    }
  }, []);

  // Save trading mode to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('growth_trading_mode', tradingMode);
  }, [tradingMode]);

  useEffect(() => {
    loadPaperData();
    loadRealData();
    
    const tutorialSeen = localStorage.getItem('tutorial_completed');
    if (!tutorialSeen) {
      setShowTutorial(true);
    }
    
    const interval = setInterval(() => {
      if (tradingMode === 'paper') loadPaperData();
      else loadRealData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [loadPaperData, loadRealData, tradingMode]);

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

  const completeTutorial = () => {
    localStorage.setItem('tutorial_completed', 'true');
    setShowTutorial(false);
  };

  const executeStrategy = async () => {
    setExecuting(true);
    const isPaper = tradingMode === 'paper';
    
    try {
      const response = await api.post('/growth/execute', {
        capital: isPaper ? 500 : (budget?.available_budget || 500),
        paper_trade: isPaper
      });
      
      if (response.data.success) {
        const exec = response.data.execution;
        toast.success(
          `${isPaper ? '📝 Paper' : '💰 Real'} Trade Executed! ${exec.total_trades} trades deployed`
        );
        
        if (isPaper) loadPaperData();
        else loadRealData();
      }
    } catch (error) {
      toast.error('Execution failed: ' + (error.response?.data?.detail || error.message));
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
        toast.info(`Stop Losses: ${sl} | Take Profits: ${tp}`);
      } else {
        toast.success('All positions healthy');
      }
      if (tradingMode === 'paper') loadPaperData();
      else loadRealData();
    } catch (error) {
      toast.error('Monitor failed');
    } finally {
      setLoading(false);
    }
  };

  // Get current stats based on mode
  const currentStats = tradingMode === 'paper' ? paperStats : realStats;
  const currentPositions = tradingMode === 'paper' ? paperPositions : realPositions;
  const portfolio = currentStats?.portfolio || {};
  const goalProgress = currentStats?.goal_progress || {};

  return (
    <div className="min-h-screen bg-[#000000] text-white p-4 md:p-8">
      {/* Tutorial Modal */}
      {showTutorial && (
        <UserTutorial 
          onComplete={completeTutorial} 
          onSkip={completeTutorial}
        />
      )}
      
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
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
            <HelpCircle className="mr-2" size={18} />
            Tutorial
          </Button>
        </div>
      </motion.div>

      {/* Trading Mode Tabs - Single Selection */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <Tabs value={tradingMode} onValueChange={setTradingMode} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-[#0A0A0A] p-1 h-auto">
            <TabsTrigger 
              value="paper" 
              className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black py-4 text-lg font-bold"
              data-testid="paper-trading-tab"
            >
              <TestTube className="mr-2" size={20} />
              Paper Trading
              <Badge className="ml-2 bg-[#FF9500]/20 text-[#FF9500] data-[state=active]:bg-black/20 data-[state=active]:text-black">
                Practice
              </Badge>
            </TabsTrigger>
            <TabsTrigger 
              value="real" 
              className="data-[state=active]:bg-[#00FF94] data-[state=active]:text-black py-4 text-lg font-bold"
              data-testid="real-trading-tab"
            >
              <Wallet className="mr-2" size={20} />
              Real Trading
              <Badge className="ml-2 bg-[#00FF94]/20 text-[#00FF94] data-[state=active]:bg-black/20 data-[state=active]:text-black">
                Live
              </Badge>
            </TabsTrigger>
          </TabsList>

          {/* Paper Trading Content */}
          <TabsContent value="paper" className="mt-6">
            <AnimatePresence mode="wait">
              <motion.div
                key="paper"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {/* Paper Trading Info Banner */}
                <Card className="bg-[#FF9500]/10 border-[#FF9500]/30 mb-6">
                  <CardContent className="p-4 flex items-center gap-3">
                    <TestTube className="text-[#FF9500]" size={24} />
                    <div>
                      <p className="font-medium text-[#FF9500]">Paper Trading Mode</p>
                      <p className="text-sm text-[#A1A1AA]">
                        Practice with simulated trades. No real money at risk. Perfect for testing strategies.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Paper Portfolio Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <DollarSign className="mx-auto mb-2 text-[#FF9500]" size={24} />
                      <div className="text-2xl font-bold">${portfolio.total_value?.toFixed(2) || '500.00'}</div>
                      <div className="text-xs text-[#A1A1AA]">Paper Portfolio</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <TrendingUp className="mx-auto mb-2 text-[#00FF94]" size={24} />
                      <div className="text-2xl font-bold">{goalProgress.multiplier?.toFixed(2) || '1.00'}x</div>
                      <div className="text-xs text-[#A1A1AA]">Multiplier</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <Sparkles className="mx-auto mb-2 text-[#9D00FF]" size={24} />
                      <div className="text-2xl font-bold">{paperPositions.length}</div>
                      <div className="text-xs text-[#A1A1AA]">Open Positions</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <Target className="mx-auto mb-2 text-[#007AFF]" size={24} />
                      <div className="text-2xl font-bold">{goalProgress.progress_pct?.toFixed(1) || '0.0'}%</div>
                      <div className="text-xs text-[#A1A1AA]">To $100k</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Paper Trading Execute Button */}
                <Card className="bg-[#0A0A0A] border-[#1F1F1F] mb-6">
                  <CardContent className="p-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <h3 className="font-bold text-lg mb-1">Execute Paper Strategy</h3>
                        <p className="text-sm text-[#A1A1AA]">Deploy $500 in simulated trades to test the AI</p>
                      </div>
                      <div className="flex gap-3">
                        <Button
                          onClick={executeStrategy}
                          disabled={executing}
                          className="bg-[#FF9500] hover:bg-[#CC7700] text-black font-bold px-8"
                          data-testid="execute-paper-btn"
                        >
                          {executing ? <Loader2 className="animate-spin mr-2" /> : <TestTube className="mr-2" />}
                          Paper Trade $500
                        </Button>
                        <Button
                          onClick={monitorPositions}
                          disabled={loading}
                          variant="outline"
                          className="border-[#FF9500] text-[#FF9500]"
                        >
                          {loading ? <Loader2 className="animate-spin mr-2" /> : <RefreshCw className="mr-2" />}
                          Monitor
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Paper Autopilot */}
                <AutopilotControl mode="paper" />
              </motion.div>
            </AnimatePresence>
          </TabsContent>

          {/* Real Trading Content */}
          <TabsContent value="real" className="mt-6">
            <AnimatePresence mode="wait">
              <motion.div
                key="real"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {/* Real Trading Warning Banner */}
                <Card className="bg-[#FF0055]/10 border-[#FF0055]/30 mb-6">
                  <CardContent className="p-4 flex items-center gap-3">
                    <AlertTriangle className="text-[#FF0055]" size={24} />
                    <div>
                      <p className="font-medium text-[#FF0055]">Real Trading Mode - Live Money</p>
                      <p className="text-sm text-[#A1A1AA]">
                        Trades will execute with real funds on Kraken. Only your allocated budget will be used.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Budget & Kraken Connection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  {/* Budget Control */}
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="text-[#00FF94]" />
                        Budget Protection
                        {budget?.real_trading_enabled && (
                          <Badge className="bg-[#00FF94]/20 text-[#00FF94]">ACTIVE</Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-[#A1A1AA] mb-4">
                        Set your trading budget. The AI will ONLY use this amount.
                      </p>
                      <div className="flex items-center gap-3 mb-4">
                        <Input
                          type="number"
                          placeholder="Budget ($)"
                          value={budgetInput}
                          onChange={(e) => setBudgetInput(e.target.value)}
                          className="bg-[#121212] border-[#1F1F1F] flex-1"
                        />
                        <Button
                          onClick={handleSetBudget}
                          disabled={settingBudget}
                          className="bg-[#00FF94] hover:bg-[#00CC77] text-black"
                        >
                          {settingBudget ? <Loader2 className="animate-spin" size={16} /> : 'Set'}
                        </Button>
                      </div>
                      {budget && (
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="p-2 bg-[#121212] rounded">
                            <div className="font-bold text-[#00FF94]">${budget.allocated_budget || 0}</div>
                            <div className="text-xs text-[#A1A1AA]">Allocated</div>
                          </div>
                          <div className="p-2 bg-[#121212] rounded">
                            <div className="font-bold text-[#007AFF]">${budget.available_budget || 0}</div>
                            <div className="text-xs text-[#A1A1AA]">Available</div>
                          </div>
                          <div className="p-2 bg-[#121212] rounded">
                            <div className="font-bold text-[#FF9500]">${budget.used_budget || 0}</div>
                            <div className="text-xs text-[#A1A1AA]">In Use</div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* AI Confidence Threshold */}
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="text-[#9D00FF]" />
                        AI Confidence Threshold
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-[#A1A1AA] mb-4">
                        Only execute trades when AI confidence exceeds this level.
                      </p>
                      <div className="flex items-center gap-4 mb-2">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={confidenceThreshold}
                          onChange={(e) => setConfidenceThreshold(parseInt(e.target.value))}
                          className="flex-1 h-2 bg-[#1F1F1F] rounded-lg appearance-none cursor-pointer accent-[#9D00FF]"
                        />
                        <span className={`text-xl font-bold min-w-[50px] text-center ${
                          confidenceThreshold >= 80 ? 'text-[#00FF94]' : 
                          confidenceThreshold >= 60 ? 'text-[#FF9500]' : 'text-[#FF0055]'
                        }`}>
                          {confidenceThreshold}%
                        </span>
                        <Button
                          size="sm"
                          onClick={() => handleSetConfidenceThreshold(confidenceThreshold)}
                          disabled={settingThreshold}
                          className="bg-[#9D00FF] hover:bg-[#7A00CC]"
                        >
                          {settingThreshold ? <Loader2 size={14} className="animate-spin" /> : 'Save'}
                        </Button>
                      </div>
                      <div className="flex justify-between text-xs text-[#71717A]">
                        <span>Aggressive</span>
                        <span>Conservative</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Real Portfolio Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <Card className="bg-[#0A0A0A] border-[#00FF94]/30">
                    <CardContent className="p-4 text-center">
                      <Wallet className="mx-auto mb-2 text-[#00FF94]" size={24} />
                      <div className="text-2xl font-bold text-[#00FF94]">
                        ${portfolio.total_value?.toFixed(2) || budget?.available_budget || '0.00'}
                      </div>
                      <div className="text-xs text-[#A1A1AA]">Real Portfolio</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <TrendingUp className="mx-auto mb-2 text-[#00FF94]" size={24} />
                      <div className="text-2xl font-bold">{goalProgress.multiplier?.toFixed(2) || '1.00'}x</div>
                      <div className="text-xs text-[#A1A1AA]">Multiplier</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <Sparkles className="mx-auto mb-2 text-[#9D00FF]" size={24} />
                      <div className="text-2xl font-bold">{realPositions.length}</div>
                      <div className="text-xs text-[#A1A1AA]">Real Positions</div>
                    </CardContent>
                  </Card>
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4 text-center">
                      <Target className="mx-auto mb-2 text-[#007AFF]" size={24} />
                      <div className="text-2xl font-bold">{goalProgress.progress_pct?.toFixed(1) || '0.0'}%</div>
                      <div className="text-xs text-[#A1A1AA]">To $100k</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Real Trading Execute Button */}
                <Card className="bg-gradient-to-r from-[#00FF94]/10 to-[#0A0A0A] border-[#00FF94]/30 mb-6">
                  <CardContent className="p-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <h3 className="font-bold text-lg mb-1 flex items-center gap-2">
                          <CheckCircle className="text-[#00FF94]" size={20} />
                          Execute Real Strategy
                        </h3>
                        <p className="text-sm text-[#A1A1AA]">
                          Deploy ${budget?.available_budget || 500} with {confidenceThreshold}% confidence threshold
                        </p>
                      </div>
                      <div className="flex gap-3">
                        <Button
                          onClick={executeStrategy}
                          disabled={executing || !budget?.real_trading_enabled}
                          className="bg-[#00FF94] hover:bg-[#00CC77] text-black font-bold px-8"
                          data-testid="execute-real-btn"
                        >
                          {executing ? <Loader2 className="animate-spin mr-2" /> : <Wallet className="mr-2" />}
                          Trade Real ${budget?.available_budget || 500}
                        </Button>
                        <Button
                          onClick={monitorPositions}
                          disabled={loading}
                          variant="outline"
                          className="border-[#00FF94] text-[#00FF94]"
                        >
                          {loading ? <Loader2 className="animate-spin mr-2" /> : <RefreshCw className="mr-2" />}
                          Monitor
                        </Button>
                      </div>
                    </div>
                    {!budget?.real_trading_enabled && (
                      <p className="text-sm text-[#FF9500] mt-3">
                        ⚠️ Set a budget above to enable real trading
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Real Autopilot */}
                <AutopilotControl mode="real" />
              </motion.div>
            </AnimatePresence>
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Progress to $100k Goal */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="text-[#FFD700]" />
              Progress to $100,000
              <Badge className={tradingMode === 'paper' ? 'bg-[#FF9500]/20 text-[#FF9500]' : 'bg-[#00FF94]/20 text-[#00FF94]'}>
                {tradingMode === 'paper' ? 'Paper' : 'Real'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm text-[#A1A1AA]">$500</span>
                <span className="text-sm font-bold">${portfolio.total_value?.toFixed(2) || '500'}</span>
                <span className="text-sm text-[#A1A1AA]">$100,000</span>
              </div>
              <Progress 
                value={goalProgress.progress_pct || 0} 
                className="h-3 bg-[#1F1F1F]"
              />
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-[#00FF94]">{goalProgress.multiplier?.toFixed(1) || '1.0'}x</div>
                <div className="text-xs text-[#A1A1AA]">Current</div>
              </div>
              <div>
                <div className="text-xl font-bold text-[#FFD700]">200x</div>
                <div className="text-xs text-[#A1A1AA]">Target</div>
              </div>
              <div>
                <div className="text-xl font-bold text-[#007AFF]">${goalProgress.remaining?.toLocaleString() || '99,500'}</div>
                <div className="text-xs text-[#A1A1AA]">Remaining</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* AI Sentiment Panel */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.22 }}
        className="mb-8"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MarketSentimentPanel />
          <CryptoNewsFeed />
        </div>
      </motion.div>

      {/* Coin Universe Manager */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.25 }}
        className="mb-8"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CoinUniverseManager />
          <AIDiscoveryPanel />
        </div>
      </motion.div>

      {/* Open Positions */}
      {currentPositions.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Flame className="text-[#FF9500]" />
                  Open Positions ({currentPositions.length})
                </span>
                <Badge className={tradingMode === 'paper' ? 'bg-[#FF9500]/20 text-[#FF9500]' : 'bg-[#00FF94]/20 text-[#00FF94]'}>
                  {tradingMode === 'paper' ? 'Paper' : 'Real'}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[400px] overflow-y-auto">
                {currentPositions.slice(0, 12).map((pos, i) => (
                  <div key={i} className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold">{pos.coin_id?.toUpperCase()}</span>
                      {pos.is_gem && <Badge className="bg-[#FFD700]/20 text-[#FFD700]">GEM</Badge>}
                    </div>
                    <div className="text-sm text-[#A1A1AA]">
                      <div>Entry: ${pos.entry_price?.toFixed(4)}</div>
                      <div>Amount: {pos.amount?.toFixed(6)}</div>
                      <div className={pos.pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                        P/L: {pos.pnl >= 0 ? '+' : ''}{pos.pnl?.toFixed(2) || '0.00'}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {currentPositions.length > 12 && (
                <p className="text-center text-sm text-[#A1A1AA] mt-4">
                  +{currentPositions.length - 12} more positions
                </p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default GrowthDashboard;
