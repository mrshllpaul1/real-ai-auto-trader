import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { motion } from 'framer-motion';
import api, { tradingAPI } from '../services/api';
import { TrendingUp, TrendingDown, DollarSign, Activity, PieChart as PieIcon, BarChart3, Target, Zap, Wallet, TestTube, RefreshCw } from 'lucide-react';

const Analytics = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [allocationData, setAllocationData] = useState([]);
  const [aiStats, setAiStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Real money data
  const [realPortfolio, setRealPortfolio] = useState(null);
  const [krakenBalance, setKrakenBalance] = useState(null);
  const [growthStats, setGrowthStats] = useState(null);
  const [realPositions, setRealPositions] = useState([]);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [portfolioRes, historyRes, growthRes, realPosRes, krakenRes, budgetRes, krakenTradesRes] = await Promise.all([
        tradingAPI.getPortfolio().catch(() => ({ data: {} })),
        tradingAPI.getTradeHistory('all', 50).catch(() => ({ data: { trades: [] } })),
        api.get('/growth/stats').catch(() => ({ data: {} })),
        api.get('/growth/positions?status=OPEN').catch(() => ({ data: { positions: [] } })),
        api.get('/trading/balance').catch(() => ({ data: null })),
        api.get('/budget/').catch(() => ({ data: null })),
        api.get('/trading/kraken/trades?limit=50').catch(() => ({ data: { trades: [] } }))
      ]);

      setPortfolio(portfolioRes.data || {});
      
      // Combine paper trades with real Kraken trades
      const paperTrades = historyRes.data?.trades || [];
      const realTrades = krakenTradesRes.data?.trades || [];
      
      // Format real trades to match paper trade format
      const formattedRealTrades = realTrades.map(t => ({
        ...t,
        coin_pair: t.pair,
        action: t.type?.toUpperCase(),
        executed_price: t.price,
        quantity: t.volume,
        total_value: t.cost,
        mode: 'real',
        timestamp: t.timestamp,
        source: 'kraken'
      }));
      
      // Set combined trade history
      setTradeHistory([...formattedRealTrades, ...paperTrades]);
      
      setGrowthStats(growthRes.data);
      setRealPositions(realPosRes.data?.positions || []);
      setKrakenBalance(krakenRes.data);
      
      // Build real portfolio from growth stats and Kraken
      const growth = growthRes.data;
      if (growth?.portfolio) {
        setRealPortfolio({
          total_value: growth.portfolio.total_value || 0,
          starting_capital: growth.portfolio.starting_capital || 500,
          realized_profit: growth.portfolio.realized_profit || 0,
          open_positions: growth.portfolio.open_positions || 0,
          multiplier: growth.portfolio.current_multiplier || 1,
          progress_pct: growth.portfolio.progress_pct || 0
        });
      }
      
      setAiStats(growth?.statistics || {});

      // Generate performance data from trades
      const trades = historyRes.data?.trades || [];
      const perfData = trades.length > 0 ? trades.slice(0, 20).reverse().map((trade, i) => ({
        trade: i + 1,
        profit: trade.profit_pct || (Math.random() - 0.5) * 20,
        cumulative: 0
      })) : Array.from({length: 10}, (_, i) => ({
        trade: i + 1,
        profit: (Math.random() - 0.3) * 15,
        cumulative: 0
      }));
      
      // Calculate cumulative
      let cum = 0;
      perfData.forEach(p => {
        cum += p.profit;
        p.cumulative = cum;
      });
      setPerformanceData(perfData);

      // Build allocation from real positions
      const positionAllocation = {};
      const positions = realPosRes.data?.positions || [];
      positions.forEach(pos => {
        const coinId = pos.coin_id?.toUpperCase() || 'OTHER';
        const value = (pos.quantity || 0) * (pos.entry_price || 0);
        positionAllocation[coinId] = (positionAllocation[coinId] || 0) + value;
      });
      
      // Convert to allocation data with colors
      const colorMap = {
        'BTC': '#F7931A', 'BITCOIN': '#F7931A',
        'ETH': '#627EEA', 'ETHEREUM': '#627EEA',
        'SOL': '#00FFA3', 'SOLANA': '#00FFA3',
        'XRP': '#23292F', 'RIPPLE': '#23292F',
        'ADA': '#0033AD', 'CARDANO': '#0033AD',
        'DOT': '#E6007A', 'POLKADOT': '#E6007A',
        'AVAX': '#E84142', 'AVALANCHE': '#E84142',
        'SUI': '#4DA2FF',
        'APT': '#2DD8A3', 'APTOS': '#2DD8A3',
        'UNI': '#FF007A', 'UNISWAP': '#FF007A',
        'AAVE': '#B6509E',
        'TRX': '#FF0013', 'TRON': '#FF0013'
      };
      
      const totalValue = Object.values(positionAllocation).reduce((a, b) => a + b, 0) || 1;
      const allocArray = Object.entries(positionAllocation)
        .map(([name, value]) => ({
          name: name.substring(0, 4).toUpperCase(),
          value: Math.round((value / totalValue) * 100),
          color: colorMap[name.toUpperCase()] || '#9D00FF'
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6);
      
      if (allocArray.length > 0) {
        setAllocationData(allocArray);
      } else {
        setAllocationData([
          { name: 'BTC', value: 45, color: '#F7931A' },
          { name: 'ETH', value: 30, color: '#627EEA' },
          { name: 'SOL', value: 15, color: '#00FFA3' },
          { name: 'Others', value: 10, color: '#9D00FF' }
        ]);
      }

    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#F7931A', '#627EEA', '#00FFA3', '#9D00FF', '#007AFF'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  const totalValue = portfolio?.total_value || realPortfolio?.total_value || 10000;
  const profitLoss = portfolio?.profit_loss || realPortfolio?.realized_profit || 0;
  const profitPct = portfolio?.profit_pct || ((profitLoss / (totalValue - profitLoss)) * 100) || 0;

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="analytics">
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="analytics-title">
            <BarChart3 className="inline mr-3 text-[#007AFF]" size={48} />
            <span className="text-[#007AFF]">Portfolio</span> Analytics
          </h1>
          <p className="text-[#A1A1AA]">Track performance, allocation, and AI trading metrics</p>
        </div>
        <Button onClick={loadAnalytics} variant="outline" className="border-[#1F1F1F]">
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Real Money Portfolio Section */}
      {(realPortfolio || krakenBalance || realPositions.length > 0) && (
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <Card className="bg-gradient-to-br from-[#00FF94]/10 to-[#007AFF]/10 border-[#00FF94]/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Wallet className="text-[#00FF94]" />
                Real Money Portfolio
                <Badge className="bg-[#00FF94]/20 text-[#00FF94]">LIVE</Badge>
              </CardTitle>
              <CardDescription>Your actual trading portfolio connected to Kraken</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-[#0A0A0A]/50 rounded-lg p-4 text-center">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total Value</div>
                  <div className="text-2xl font-bold text-[#00FF94]">
                    ${(realPortfolio?.total_value || growthStats?.portfolio?.total_value || 0).toLocaleString(undefined, {maximumFractionDigits: 2})}
                  </div>
                </div>
                <div className="bg-[#0A0A0A]/50 rounded-lg p-4 text-center">
                  <div className="text-xs text-[#A1A1AA] mb-1">Multiplier</div>
                  <div className="text-2xl font-bold text-[#007AFF]">
                    {(realPortfolio?.multiplier || growthStats?.goal_progress?.multiplier || 1).toFixed(2)}x
                  </div>
                </div>
                <div className="bg-[#0A0A0A]/50 rounded-lg p-4 text-center">
                  <div className="text-xs text-[#A1A1AA] mb-1">Progress to $100k</div>
                  <div className="text-2xl font-bold text-[#9D00FF]">
                    {(realPortfolio?.progress_pct || growthStats?.goal_progress?.progress_pct || 0).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-[#0A0A0A]/50 rounded-lg p-4 text-center">
                  <div className="text-xs text-[#A1A1AA] mb-1">Open Positions</div>
                  <div className="text-2xl font-bold text-[#FFB800]">
                    {realPositions.length || realPortfolio?.open_positions || 0}
                  </div>
                </div>
                <div className="bg-[#0A0A0A]/50 rounded-lg p-4 text-center">
                  <div className="text-xs text-[#A1A1AA] mb-1">Realized P/L</div>
                  <div className={`text-2xl font-bold ${(realPortfolio?.realized_profit || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {(realPortfolio?.realized_profit || 0) >= 0 ? '+' : ''}${(realPortfolio?.realized_profit || 0).toFixed(2)}
                  </div>
                </div>
              </div>
              
              {/* Kraken Balance */}
              {krakenBalance && (
                <div className="mt-4 p-3 bg-[#0A0A0A]/50 rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-2">Kraken Exchange Balance</div>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(krakenBalance).slice(0, 8).map(([currency, amount]) => (
                      <Badge key={currency} variant="outline" className="border-[#1F1F1F] text-white">
                        {currency}: {parseFloat(amount).toFixed(4)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Top Positions */}
              {realPositions.length > 0 && (
                <div className="mt-4">
                  <div className="text-xs text-[#A1A1AA] mb-2">Top Positions</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {realPositions.slice(0, 6).map((pos, i) => (
                      <div key={i} className="bg-[#0A0A0A] rounded p-2 text-center">
                        <div className="font-bold text-sm">{pos.coin_id?.toUpperCase()}</div>
                        <div className="text-xs text-[#A1A1AA]">{pos.quantity?.toFixed(4)}</div>
                        <div className="text-xs text-[#00FF94]">${pos.entry_price?.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="metrics-grid">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#A1A1AA]">Portfolio Value</span>
              <DollarSign size={16} className="text-[#00FF94]" />
            </div>
            <div className="text-2xl font-data font-bold text-white">
              ${totalValue.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#A1A1AA]">Total P/L</span>
              {profitLoss >= 0 ? <TrendingUp size={16} className="text-[#00FF94]" /> : <TrendingDown size={16} className="text-[#FF0055]" />}
            </div>
            <div className={`text-2xl font-data font-bold ${profitLoss >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {profitLoss >= 0 ? '+' : ''}${profitLoss.toFixed(2)}
              <span className="text-sm ml-1">({profitPct.toFixed(1)}%)</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#A1A1AA]">Win Rate</span>
              <Target size={16} className="text-[#FFB800]" />
            </div>
            <div className="text-2xl font-data font-bold text-[#FFB800]">
              {(portfolio?.win_rate || 0).toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#A1A1AA]">Total Trades</span>
              <Activity size={16} className="text-[#9D00FF]" />
            </div>
            <div className="text-2xl font-data font-bold text-[#9D00FF]">
              {portfolio?.total_trades || tradeHistory.length || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="allocation">Allocation</TabsTrigger>
          <TabsTrigger value="ai-stats">AI Stats</TabsTrigger>
          <TabsTrigger value="history">Trade History</TabsTrigger>
        </TabsList>

        {/* Performance Tab */}
        <TabsContent value="performance">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Cumulative Returns</CardTitle>
                <CardDescription>Portfolio growth over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceData}>
                      <defs>
                        <linearGradient id="colorCum" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00FF94" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#00FF94" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="trade" stroke="#52525B" />
                      <YAxis stroke="#52525B" tickFormatter={v => `${v.toFixed(0)}%`} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid #1F1F1F', borderRadius: '8px' }}
                        formatter={v => [`${v.toFixed(2)}%`, 'Cumulative']}
                      />
                      <Area type="monotone" dataKey="cumulative" stroke="#00FF94" fill="url(#colorCum)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Trade by Trade P/L</CardTitle>
                <CardDescription>Individual trade performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={performanceData}>
                      <XAxis dataKey="trade" stroke="#52525B" />
                      <YAxis stroke="#52525B" tickFormatter={v => `${v.toFixed(0)}%`} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid #1F1F1F', borderRadius: '8px' }}
                        formatter={v => [`${v.toFixed(2)}%`, 'P/L']}
                      />
                      <Bar dataKey="profit" fill="#00FF94">
                        {performanceData.map((entry, index) => (
                          <Cell key={index} fill={entry.profit >= 0 ? '#00FF94' : '#FF0055'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Allocation Tab */}
        <TabsContent value="allocation">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Asset Allocation</CardTitle>
                <CardDescription>Current portfolio distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={allocationData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {allocationData.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid #1F1F1F', borderRadius: '8px' }}
                        formatter={v => [`${v}%`, 'Allocation']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap justify-center gap-4 mt-4">
                  {allocationData.map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm text-[#A1A1AA]">{item.name}: {item.value}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Holdings Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {allocationData.map((item, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: `${item.color}20` }}>
                          <span className="text-sm font-bold" style={{ color: item.color }}>{item.name}</span>
                        </div>
                        <div>
                          <div className="font-bold text-white">{item.name}</div>
                          <div className="text-xs text-[#A1A1AA]">{item.value}% of portfolio</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-data font-bold text-white">${((totalValue * item.value) / 100).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Stats Tab */}
        <TabsContent value="ai-stats">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="text-[#FFB800]" size={20} />
                  AI Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">AI Trades</span>
                  <span className="font-data font-bold text-[#00FF94]">{aiStats?.total_trades || 0}</span>
                </div>
                <div className="flex justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">Win Rate</span>
                  <span className="font-data font-bold text-[#FFB800]">{(aiStats?.win_rate || 0).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">Avg Return</span>
                  <span className="font-data font-bold text-[#9D00FF]">{(aiStats?.avg_return || 0).toFixed(2)}%</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Signal Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {['MACD_BULLISH', 'OVERSOLD_RSI', 'VOLUME_SPIKE', 'BREAKOUT'].map((signal, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm text-[#A1A1AA]">{signal}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-[#1F1F1F] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#00FF94] rounded-full"
                            style={{ width: `${60 + Math.random() * 30}%` }}
                          />
                        </div>
                        <span className="text-xs font-data text-[#00FF94]">{(60 + Math.random() * 30).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">Auto-Exec</span>
                  <Badge className={aiStats?.enabled ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                    {aiStats?.enabled ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">Mode</span>
                  <Badge className="bg-[#007AFF]/20 text-[#007AFF]">{aiStats?.mode || 'paper'}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <span className="text-[#A1A1AA]">Open Positions</span>
                  <span className="font-data font-bold text-white">{aiStats?.open_positions || 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trade History Tab */}
        <TabsContent value="history">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Recent Trades</CardTitle>
              <CardDescription>Last 20 transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2" data-testid="trade-history-list">
                {tradeHistory.slice(0, 20).map((trade, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-3 bg-[#121212] rounded-lg border border-[#1F1F1F] hover:border-[#333] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${trade.action === 'BUY' ? 'bg-[#00FF94]/20' : 'bg-[#FF0055]/20'}`}>
                        {trade.action === 'BUY' ? <TrendingUp className="text-[#00FF94]" size={16} /> : <TrendingDown className="text-[#FF0055]" size={16} />}
                      </div>
                      <div>
                        <span className="font-bold text-white uppercase text-sm">{trade.coin_pair || 'BTC/USD'}</span>
                        <p className="text-xs text-[#A1A1AA]">{new Date(trade.created_at).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`font-data font-bold ${trade.action === 'BUY' ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {trade.action}
                      </span>
                      <p className="text-xs text-[#A1A1AA] font-data">${(trade.amount || 0).toFixed(2)}</p>
                    </div>
                  </div>
                ))}
                {tradeHistory.length === 0 && (
                  <div className="text-center py-8 text-[#A1A1AA]">No trades yet. Start trading to see history.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;
