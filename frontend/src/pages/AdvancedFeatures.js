import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FlaskConical, Play, TrendingUp, TrendingDown, BarChart3,
  RefreshCw, Trophy, Users, Copy, Heart, Share2, PieChart
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AdvancedFeatures = () => {
  // Backtesting state
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [strategy, setStrategy] = useState({
    name: 'Custom Strategy',
    min_score: 50,
    position_size_pct: 10,
    stop_loss_pct: 10,
    take_profit_pct: 30,
    max_positions: 3
  });
  const [presets, setPresets] = useState([]);

  // Rebalancing state
  const [rebalanceData, setRebalanceData] = useState(null);
  const [targetAllocation, setTargetAllocation] = useState({
    BTC: 40, ETH: 30, SOL: 15, USD: 15
  });

  // Social state
  const [leaderboard, setLeaderboard] = useState([]);
  const [strategies, setStrategies] = useState([]);

  const userId = localStorage.getItem('user_id') || 'demo_user';

  useEffect(() => {
    loadPresets();
    loadLeaderboard();
    loadStrategies();
    loadRebalanceData();
  }, []);

  const loadPresets = async () => {
    try {
      const res = await api.get('/backtest/presets');
      setPresets(res.data.presets || []);
    } catch (e) { console.error(e); }
  };

  const loadLeaderboard = async () => {
    try {
      const res = await api.get('/social/leaderboard?limit=10');
      setLeaderboard(res.data.traders || []);
    } catch (e) { console.error(e); }
  };

  const loadStrategies = async () => {
    try {
      const res = await api.get('/social/strategies?limit=10');
      setStrategies(res.data.strategies || []);
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
        strategy,
        coins: ['bitcoin', 'ethereum', 'solana'],
        days: 365,
        initial_capital: 10000
      });
      
      toast.dismiss();
      setBacktestResult(res.data);
      toast.success(`Backtest complete! ${res.data.total_return_pct >= 0 ? '+' : ''}${res.data.total_return_pct.toFixed(2)}% return`);
    } catch (e) {
      toast.dismiss();
      toast.error('Backtest failed');
    } finally {
      setBacktestLoading(false);
    }
  };

  const executeRebalance = async () => {
    try {
      toast.loading('Rebalancing portfolio...');
      await api.post(`/rebalance/execute/${userId}?mode=paper`);
      toast.dismiss();
      toast.success('Portfolio rebalanced!');
      loadRebalanceData();
    } catch (e) {
      toast.dismiss();
      toast.error('Rebalance failed');
    }
  };

  const saveTargetAllocation = async () => {
    try {
      await api.post(`/rebalance/target/${userId}`, { allocations: targetAllocation });
      toast.success('Target allocation saved!');
      loadRebalanceData();
    } catch (e) {
      toast.error('Failed to save allocation');
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
          <TabsTrigger value="social"><Users size={16} className="mr-2" />Social Trading</TabsTrigger>
        </TabsList>

        {/* BACKTESTING TAB */}
        <TabsContent value="backtest" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Strategy Config */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading">Strategy Configuration</CardTitle>
                <CardDescription>Configure your strategy parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Presets */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {presets.map((preset, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      size="sm"
                      onClick={() => setStrategy({...preset.strategy, name: preset.name})}
                      className="border-[#1F1F1F] hover:border-[#00FF94]"
                    >
                      {preset.name}
                    </Button>
                  ))}
                </div>

                <div>
                  <Label>Min Signal Score</Label>
                  <div className="flex items-center gap-4 mt-2">
                    <Slider
                      value={[strategy.min_score]}
                      onValueChange={([v]) => setStrategy(s => ({...s, min_score: v}))}
                      min={30} max={80} step={5}
                    />
                    <span className="font-data w-12">{strategy.min_score}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Position Size %</Label>
                    <Input
                      type="number"
                      value={strategy.position_size_pct}
                      onChange={(e) => setStrategy(s => ({...s, position_size_pct: +e.target.value}))}
                      className="bg-[#121212] border-[#1F1F1F] mt-1"
                    />
                  </div>
                  <div>
                    <Label>Max Positions</Label>
                    <Input
                      type="number"
                      value={strategy.max_positions}
                      onChange={(e) => setStrategy(s => ({...s, max_positions: +e.target.value}))}
                      className="bg-[#121212] border-[#1F1F1F] mt-1"
                    />
                  </div>
                  <div>
                    <Label>Stop Loss %</Label>
                    <Input
                      type="number"
                      value={strategy.stop_loss_pct}
                      onChange={(e) => setStrategy(s => ({...s, stop_loss_pct: +e.target.value}))}
                      className="bg-[#121212] border-[#1F1F1F] mt-1"
                    />
                  </div>
                  <div>
                    <Label>Take Profit %</Label>
                    <Input
                      type="number"
                      value={strategy.take_profit_pct}
                      onChange={(e) => setStrategy(s => ({...s, take_profit_pct: +e.target.value}))}
                      className="bg-[#121212] border-[#1F1F1F] mt-1"
                    />
                  </div>
                </div>

                <Button
                  onClick={runBacktest}
                  disabled={backtestLoading}
                  className="w-full bg-[#FFB800] hover:bg-[#E6A600] text-black font-bold rounded-full"
                >
                  <Play size={16} className="mr-2" />
                  {backtestLoading ? 'Running...' : 'Run Backtest (1 Year)'}
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading">Backtest Results</CardTitle>
              </CardHeader>
              <CardContent>
                {backtestResult ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Total Return</div>
                        <div className={`text-2xl font-data font-bold ${backtestResult.total_return_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {backtestResult.total_return_pct >= 0 ? '+' : ''}{backtestResult.total_return_pct?.toFixed(2)}%
                        </div>
                      </div>
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Win Rate</div>
                        <div className="text-2xl font-data font-bold text-white">
                          {backtestResult.win_rate?.toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Total Trades</div>
                        <div className="text-2xl font-data font-bold text-[#007AFF]">
                          {backtestResult.total_trades}
                        </div>
                      </div>
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Max Drawdown</div>
                        <div className="text-2xl font-data font-bold text-[#FF0055]">
                          -{backtestResult.max_drawdown_pct?.toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Sharpe Ratio</div>
                        <div className="text-2xl font-data font-bold text-white">
                          {backtestResult.sharpe_ratio?.toFixed(2)}
                        </div>
                      </div>
                      <div className="p-3 bg-[#121212] rounded-lg">
                        <div className="text-xs text-[#A1A1AA]">Final Value</div>
                        <div className="text-2xl font-data font-bold text-[#00FF94]">
                          ${backtestResult.final_value?.toLocaleString()}
                        </div>
                      </div>
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

        {/* REBALANCING TAB */}
        <TabsContent value="rebalance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading">Target Allocation</CardTitle>
                <CardDescription>Set your ideal portfolio distribution</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {['BTC', 'ETH', 'SOL', 'USD'].map(asset => (
                  <div key={asset}>
                    <Label className="flex justify-between">
                      <span>{asset}</span>
                      <span className="text-[#00FF94]">{targetAllocation[asset]}%</span>
                    </Label>
                    <Slider
                      value={[targetAllocation[asset]]}
                      onValueChange={([v]) => setTargetAllocation(a => ({...a, [asset]: v}))}
                      min={0} max={100} step={5}
                      className="mt-2"
                    />
                  </div>
                ))}
                <div className="flex justify-between pt-2 border-t border-[#1F1F1F]">
                  <span>Total</span>
                  <span className={Object.values(targetAllocation).reduce((a,b) => a+b, 0) === 100 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                    {Object.values(targetAllocation).reduce((a,b) => a+b, 0)}%
                  </span>
                </div>
                <Button onClick={saveTargetAllocation} className="w-full bg-[#007AFF] hover:bg-[#0066DD] text-white rounded-full">
                  Save Target Allocation
                </Button>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading">Rebalance Actions</CardTitle>
              </CardHeader>
              <CardContent>
                {rebalanceData?.trades_needed?.length > 0 ? (
                  <div className="space-y-3">
                    {rebalanceData.trades_needed.map((trade, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                        <div className="flex items-center gap-2">
                          {trade.action === 'BUY' ? (
                            <TrendingUp className="text-[#00FF94]" size={16} />
                          ) : (
                            <TrendingDown className="text-[#FF0055]" size={16} />
                          )}
                          <span className="font-bold">{trade.asset}</span>
                        </div>
                        <div className="text-right">
                          <Badge className={trade.action === 'BUY' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                            {trade.action} ${trade.value_usd?.toFixed(0)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                    <Button onClick={executeRebalance} className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full mt-4">
                      <RefreshCw size={16} className="mr-2" />
                      Execute Rebalance (Paper)
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
          </div>
        </TabsContent>

        {/* SOCIAL TRADING TAB */}
        <TabsContent value="social" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading flex items-center gap-2">
                  <Trophy className="text-[#FFB800]" />
                  Top Traders
                </CardTitle>
              </CardHeader>
              <CardContent>
                {leaderboard.length > 0 ? (
                  <div className="space-y-2">
                    {leaderboard.map((trader, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className={`font-bold ${i < 3 ? 'text-[#FFB800]' : 'text-[#A1A1AA]'}`}>
                            #{i + 1}
                          </span>
                          <span className="font-bold text-white">{trader.display_name || 'Trader'}</span>
                          {trader.badges?.slice(0, 2).map((b, j) => (
                            <span key={j}>{b.icon}</span>
                          ))}
                        </div>
                        <div className="text-right">
                          <div className={`font-data ${trader.total_profit_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                            {trader.total_profit_pct >= 0 ? '+' : ''}{trader.total_profit_pct?.toFixed(1)}%
                          </div>
                          <div className="text-xs text-[#A1A1AA]">{trader.win_rate?.toFixed(0)}% win</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Users size={48} className="mx-auto mb-4 text-[#FFB800] opacity-50" />
                    <p className="text-[#A1A1AA]">No traders yet. Be the first!</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading flex items-center gap-2">
                  <Share2 className="text-[#9D00FF]" />
                  Shared Strategies
                </CardTitle>
              </CardHeader>
              <CardContent>
                {strategies.length > 0 ? (
                  <div className="space-y-2">
                    {strategies.map((strat, i) => (
                      <div key={i} className="p-3 bg-[#121212] rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-white">{strat.name}</span>
                          <div className="flex items-center gap-2">
                            <Heart size={14} className="text-[#FF0055]" />
                            <span className="text-sm">{strat.likes || 0}</span>
                            <Copy size={14} className="text-[#007AFF]" />
                            <span className="text-sm">{strat.copies || 0}</span>
                          </div>
                        </div>
                        <p className="text-xs text-[#A1A1AA]">{strat.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Share2 size={48} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
                    <p className="text-[#A1A1AA]">No strategies shared yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedFeatures;
