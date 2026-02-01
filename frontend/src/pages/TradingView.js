import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { marketAPI, tradingAPI } from '../services/api';
import { toast } from 'sonner';
import { TrendingUp, DollarSign } from 'lucide-react';

const TradingView = () => {
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [chartData, setChartData] = useState([]);
  const [tradingMode, setTradingMode] = useState('paper');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadChartData();
  }, [selectedCoin]);

  const loadChartData = async () => {
    try {
      const response = await marketAPI.getHistoricalData(selectedCoin, 7);
      const formatted = response.data.prices.map(([timestamp, price]) => ({
        time: new Date(timestamp).toLocaleDateString(),
        price: price
      }));
      setChartData(formatted);
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const executeTrade = async (action) => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      setLoading(true);
      await tradingAPI.executeTrade({
        user_id: localStorage.getItem('user_id') || 'demo_user',
        strategy_id: 'manual_trade',
        coin_pair: `${selectedCoin.toUpperCase()}/USD`,
        action: action,
        amount: parseFloat(amount),
        mode: tradingMode
      });
      
      toast.success(`${action} order executed successfully in ${tradingMode} mode!`);
      setAmount('');
    } catch (error) {
      toast.error('Failed to execute trade');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="trading-view">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="trading-title">
          <span className="text-[#00FF94]">Live</span> Trading
        </h1>
        <p className="text-[#A1A1AA]">Execute trades and view real-time market charts</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full" data-testid="chart-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl font-heading">Price Chart</CardTitle>
                <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                  <SelectTrigger className="w-40 bg-[#121212] border-[#1F1F1F]" data-testid="coin-selector">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <SelectItem value="bitcoin">Bitcoin</SelectItem>
                    <SelectItem value="ethereum">Ethereum</SelectItem>
                    <SelectItem value="solana">Solana</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-96" data-testid="price-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00FF94" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00FF94" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="time" 
                      stroke="#52525B"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      stroke="#52525B"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `$${value.toFixed(0)}`}
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: '#0A0A0A',
                        border: '1px solid #1F1F1F',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#00FF94" 
                      strokeWidth={2}
                      fill="url(#colorPrice)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trading Panel */}
        <div>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="trading-panel">
            <CardHeader>
              <CardTitle className="text-xl font-heading">Execute Trade</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs value={tradingMode} onValueChange={setTradingMode} className="mb-6" data-testid="trading-mode-tabs">
                <TabsList className="grid w-full grid-cols-2 bg-[#121212]">
                  <TabsTrigger value="paper" data-testid="paper-mode-tab">Paper Trading</TabsTrigger>
                  <TabsTrigger value="real" data-testid="real-mode-tab">Real Trading</TabsTrigger>
                </TabsList>
              </Tabs>

              <div className="space-y-4">
                <div>
                  <Label className="text-[#A1A1AA]">Amount (USD)</Label>
                  <Input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0.00"
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="amount-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Button
                    onClick={() => executeTrade('BUY')}
                    className="bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                    disabled={loading}
                    data-testid="buy-button"
                  >
                    <TrendingUp size={16} className="mr-2" />
                    BUY
                  </Button>
                  <Button
                    onClick={() => executeTrade('SELL')}
                    className="bg-[#FF0055] hover:bg-[#CC0044] text-white font-bold rounded-full"
                    disabled={loading}
                    data-testid="sell-button"
                  >
                    <TrendingUp size={16} className="mr-2 rotate-180" />
                    SELL
                  </Button>
                </div>

                {tradingMode === 'paper' && (
                  <div className="bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg p-4 mt-4">
                    <p className="text-xs text-[#007AFF]">
                      📊 Paper Trading Mode: Trades are simulated and don't use real money.
                    </p>
                  </div>
                )}

                {tradingMode === 'real' && (
                  <div className="bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg p-4 mt-4">
                    <p className="text-xs text-[#FF0055]">
                      ⚠️ Real Trading Mode: Trades will be executed with real money on Kraken.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TradingView;