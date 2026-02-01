import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FlaskConical, Play, TrendingUp, TrendingDown, BarChart3, RefreshCw, Trophy, Users, PieChart } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AdvancedFeatures = () => {
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [minScore, setMinScore] = useState(50);
  const [positionSize, setPositionSize] = useState(10);
  const [stopLoss, setStopLoss] = useState(10);
  const [takeProfit, setTakeProfit] = useState(30);
  const [rebalanceData, setRebalanceData] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  const userId = localStorage.getItem('user_id') || 'demo_user';

  useEffect(() => {
    loadLeaderboard();
    loadRebalanceData();
  }, []);

  const loadLeaderboard = async () => {
    try {
      const res = await api.get('/social/leaderboard?limit=10');
      setLeaderboard(res.data.traders || []);
    } catch (e) { console.error(e); }
  };

  const loadRebalanceData = async () => {
    try {
      const res = await api.get(`/rebalance/calculate/${userId}`);
      setRebalanceData(res.data);
    } catch (e) { console.error(e); }
  };

  const runBacktest = async () => {
    try {
      setBacktestLoading(true);
      toast.loading('Running backtest...');
      
      const res = await api.post('/backtest/run', {
        strategy: { min_score: minScore, position_size_pct: positionSize, stop_loss_pct: stopLoss, take_profit_pct: takeProfit, max_positions: 3 },
        coins: ['bitcoin', 'ethereum', 'solana'],
        days: 365,
        initial_capital: 10000
      });
      
      toast.dismiss();
      setBacktestResult(res.data);
      toast.success('Backtest complete!');
    } catch (e) {
      toast.dismiss();
      toast.error('Backtest failed');
    } finally {
      setBacktestLoading(false);
    }
  };

  const executeRebalance = async () => {
    try {
      toast.loading('Rebalancing...');
      await api.post(`/rebalance/execute/${userId}?mode=paper`);
      toast.dismiss();
      toast.success('Portfolio rebalanced!');
      loadRebalanceData();
    } catch (e) {
      toast.dismiss();
      toast.error('Rebalance failed');
    }
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="advanced-features">
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2">
          <FlaskConical className="inline mr-3 text-[#FFB800]" size={48} />
          <span className="text-[#FFB800]">Advanced</span> Features
        </h1>
        <p className="text-[#A1A1AA]">Backtesting, Portfolio Rebalancing & Social Trading</p>
      </motion.div>

      <Tabs defaultValue="backtest" className="space-y-6">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="backtest"><FlaskConical size={16} className="mr-2" />Backtesting</TabsTrigger>
          <TabsTrigger value="rebalance"><PieChart size={16} className="mr-2" />Rebalancing</TabsTrigger>
          <TabsTrigger value="social"><Users size={16} className="mr-2" />Social</TabsTrigger>
        </TabsList>

        <TabsContent value="backtest" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl">Strategy Config</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Min Score</Label>
                    <Input type="number" value={minScore} onChange={(e) => setMinScore(+e.target.value)} className="bg-[#121212] border-[#1F1F1F] mt-1" />
                  </div>
                  <div>
                    <Label>Position %</Label>
                    <Input type="number" value={positionSize} onChange={(e) => setPositionSize(+e.target.value)} className="bg-[#121212] border-[#1F1F1F] mt-1" />
                  </div>
                  <div>
                    <Label>Stop Loss %</Label>
                    <Input type="number" value={stopLoss} onChange={(e) => setStopLoss(+e.target.value)} className="bg-[#121212] border-[#1F1F1F] mt-1" />
                  </div>
                  <div>
                    <Label>Take Profit %</Label>
                    <Input type="number" value={takeProfit} onChange={(e) => setTakeProfit(+e.target.value)} className="bg-[#121212] border-[#1F1F1F] mt-1" />
                  </div>
                </div>
                <Button onClick={runBacktest} disabled={backtestLoading} className="w-full bg-[#FFB800] hover:bg-[#E6A600] text-black font-bold rounded-full">
                  <Play size={16} className="mr-2" />{backtestLoading ? 'Running...' : 'Run Backtest'}
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl">Results</CardTitle>
              </CardHeader>
              <CardContent>
                {backtestResult ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA]">Return</div>
                      <div className={`text-2xl font-data font-bold ${backtestResult.total_return_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {backtestResult.total_return_pct >= 0 ? '+' : ''}{backtestResult.total_return_pct?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-3 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA]">Win Rate</div>
                      <div className="text-2xl font-data font-bold text-white">{backtestResult.win_rate?.toFixed(1)}%</div>
                    </div>
                    <div className="p-3 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA]">Trades</div>
                      <div className="text-2xl font-data font-bold text-[#007AFF]">{backtestResult.total_trades}</div>
                    </div>
                    <div className="p-3 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA]">Final Value</div>
                      <div className="text-2xl font-data font-bold text-[#00FF94]">${backtestResult.final_value?.toLocaleString()}</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <BarChart3 size={48} className="mx-auto mb-4 text-[#FFB800] opacity-50" />
                    <p className="text-[#A1A1AA]">Run a backtest to see results</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rebalance" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl">Portfolio Rebalancing</CardTitle>
              <CardDescription>Trades needed to reach target allocation</CardDescription>
            </CardHeader>
            <CardContent>
              {rebalanceData?.trades_needed?.length > 0 ? (
                <div className="space-y-3">
                  <div className="text-lg font-bold mb-4">Total Value: ${rebalanceData.total_value?.toLocaleString()}</div>
                  {rebalanceData.trades_needed.map((trade, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center gap-2">
                        {trade.action === 'BUY' ? <TrendingUp className="text-[#00FF94]" size={16} /> : <TrendingDown className="text-[#FF0055]" size={16} />}
                        <span className="font-bold">{trade.asset}</span>
                      </div>
                      <Badge className={trade.action === 'BUY' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                        {trade.action} ${trade.value_usd?.toFixed(0)}
                      </Badge>
                    </div>
                  ))}
                  <Button onClick={executeRebalance} className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full mt-4">
                    <RefreshCw size={16} className="mr-2" />Execute Rebalance
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <PieChart size={48} className="mx-auto mb-4 text-[#00FF94] opacity-50" />
                  <p className="text-[#A1A1AA]">Portfolio is balanced!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="social" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Trophy className="text-[#FFB800]" />Top Traders Leaderboard
              </CardTitle>
            </CardHeader>
            <CardContent>
              {leaderboard.length > 0 ? (
                <div className="space-y-2">
                  {leaderboard.map((trader, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className={`font-bold ${i < 3 ? 'text-[#FFB800]' : 'text-[#A1A1AA]'}`}>#{i + 1}</span>
                        <span className="font-bold text-white">{trader.display_name || 'Trader'}</span>
                      </div>
                      <div className="text-right">
                        <div className={`font-data ${(trader.total_profit_pct || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {(trader.total_profit_pct || 0) >= 0 ? '+' : ''}{(trader.total_profit_pct || 0).toFixed(1)}%
                        </div>
                        <div className="text-xs text-[#A1A1AA]">{(trader.win_rate || 0).toFixed(0)}% win</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users size={48} className="mx-auto mb-4 text-[#FFB800] opacity-50" />
                  <p className="text-[#A1A1AA]">No traders yet. Start trading to appear!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedFeatures;
