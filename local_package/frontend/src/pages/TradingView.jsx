import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, 
  ResponsiveContainer, CartesianGrid, ComposedChart, Bar
} from 'recharts';
import { motion } from 'framer-motion';
import { marketAPI, tradingAPI } from '../services/api';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, CandlestickChart, LineChart as LineChartIcon, BarChart3, RefreshCw } from 'lucide-react';
import { useTradingMode } from '../context/TradingModeContext';

const TradingView = () => {
  const { mode: tradingMode, setMode: setTradingMode } = useTradingMode();
  
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [chartType, setChartType] = useState('area');
  const [timeframe, setTimeframe] = useState('7');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(null);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    loadChartData();
  }, [selectedCoin, timeframe]);

  const loadChartData = async () => {
    setChartLoading(true);
    try {
      const response = await marketAPI.getHistoricalData(selectedCoin, parseInt(timeframe));
      const prices = response.data.prices || [];
      
      if (prices.length > 0) {
        // Transform data for Recharts
        const data = prices.map(([timestamp, price]) => ({
          time: new Date(timestamp).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            hour: timeframe <= 1 ? 'numeric' : undefined
          }),
          price: price,
          timestamp: timestamp
        }));
        
        setChartData(data);
        setCurrentPrice(prices[prices.length - 1][1]);
        const firstPrice = prices[0][1];
        const lastPrice = prices[prices.length - 1][1];
        setPriceChange(((lastPrice - firstPrice) / firstPrice) * 100);
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
      toast.error('Failed to load price data');
    } finally {
      setChartLoading(false);
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

  const coins = [
    { value: 'bitcoin', label: 'Bitcoin (BTC)', symbol: 'BTC' },
    { value: 'ethereum', label: 'Ethereum (ETH)', symbol: 'ETH' },
    { value: 'solana', label: 'Solana (SOL)', symbol: 'SOL' },
    { value: 'cardano', label: 'Cardano (ADA)', symbol: 'ADA' },
    { value: 'polkadot', label: 'Polkadot (DOT)', symbol: 'DOT' },
    { value: 'avalanche-2', label: 'Avalanche (AVAX)', symbol: 'AVAX' },
  ];

  const formatYAxis = (value) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1F1F1F] border border-[#333] rounded-lg p-3 shadow-lg">
          <p className="text-[#A1A1AA] text-sm">{label}</p>
          <p className="text-[#00FF94] font-bold text-lg">
            ${payload[0].value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </p>
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    if (chartLoading) {
      return (
        <div className="h-[400px] flex items-center justify-center">
          <RefreshCw className="animate-spin text-[#00FF94]" size={32} />
        </div>
      );
    }

    if (chartData.length === 0) {
      return (
        <div className="h-[400px] flex items-center justify-center text-[#A1A1AA]">
          No price data available
        </div>
      );
    }

    const commonProps = {
      data: chartData,
      margin: { top: 20, right: 30, left: 20, bottom: 20 }
    };

    if (chartType === 'line') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
            <XAxis 
              dataKey="time" 
              stroke="#A1A1AA" 
              tick={{ fill: '#A1A1AA', fontSize: 12 }}
              axisLine={{ stroke: '#1F1F1F' }}
            />
            <YAxis 
              stroke="#A1A1AA" 
              tick={{ fill: '#A1A1AA', fontSize: 12 }}
              tickFormatter={formatYAxis}
              axisLine={{ stroke: '#1F1F1F' }}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#00FF94" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: '#00FF94' }}
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }

    if (chartType === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
            <XAxis 
              dataKey="time" 
              stroke="#A1A1AA" 
              tick={{ fill: '#A1A1AA', fontSize: 12 }}
              axisLine={{ stroke: '#1F1F1F' }}
            />
            <YAxis 
              stroke="#A1A1AA" 
              tick={{ fill: '#A1A1AA', fontSize: 12 }}
              tickFormatter={formatYAxis}
              axisLine={{ stroke: '#1F1F1F' }}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="price" fill="#00FF94" opacity={0.8} />
          </ComposedChart>
        </ResponsiveContainer>
      );
    }

    // Default: Area chart
    return (
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart {...commonProps}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00FF94" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#00FF94" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
          <XAxis 
            dataKey="time" 
            stroke="#A1A1AA" 
            tick={{ fill: '#A1A1AA', fontSize: 12 }}
            axisLine={{ stroke: '#1F1F1F' }}
          />
          <YAxis 
            stroke="#A1A1AA" 
            tick={{ fill: '#A1A1AA', fontSize: 12 }}
            tickFormatter={formatYAxis}
            axisLine={{ stroke: '#1F1F1F' }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke="#00FF94" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorPrice)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="trading-view">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="trading-title">
          <CandlestickChart className="inline mr-3 text-[#00FF94]" size={48} />
          <span className="text-[#00FF94]">Live</span> Trading
        </h1>
        <p className="text-[#A1A1AA]">Professional charts and real-time trading</p>
      </motion.div>

      {/* Price Header */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                <SelectTrigger className="w-48 bg-[#121212] border-[#1F1F1F]" data-testid="coin-selector">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0A0A0A] border-[#1F1F1F]">
                  {coins.map(coin => (
                    <SelectItem key={coin.value} value={coin.value}>{coin.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {currentPrice && (
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-data font-bold text-white">
                    ${currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </span>
                  {priceChange !== null && (
                    <Badge className={priceChange >= 0 ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                      {priceChange >= 0 ? <TrendingUp size={14} className="mr-1" /> : <TrendingDown size={14} className="mr-1" />}
                      {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                    </Badge>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger className="w-24 bg-[#121212] border-[#1F1F1F]" data-testid="timeframe-selector">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <SelectItem value="1">1D</SelectItem>
                  <SelectItem value="7">7D</SelectItem>
                  <SelectItem value="30">30D</SelectItem>
                  <SelectItem value="90">90D</SelectItem>
                  <SelectItem value="365">1Y</SelectItem>
                </SelectContent>
              </Select>
              
              <div className="flex gap-1 bg-[#121212] rounded-lg p-1">
                <Button
                  size="sm"
                  variant={chartType === 'area' ? 'default' : 'ghost'}
                  onClick={() => setChartType('area')}
                  className={chartType === 'area' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="area-btn"
                >
                  <BarChart3 size={16} />
                </Button>
                <Button
                  size="sm"
                  variant={chartType === 'line' ? 'default' : 'ghost'}
                  onClick={() => setChartType('line')}
                  className={chartType === 'line' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="line-btn"
                >
                  <LineChartIcon size={16} />
                </Button>
                <Button
                  size="sm"
                  variant={chartType === 'bar' ? 'default' : 'ghost'}
                  onClick={() => setChartType('bar')}
                  className={chartType === 'bar' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="bar-btn"
                >
                  <CandlestickChart size={16} />
                </Button>
              </div>
              
              <Button
                size="sm"
                variant="ghost"
                onClick={loadChartData}
                disabled={chartLoading}
                data-testid="refresh-btn"
              >
                <RefreshCw size={16} className={chartLoading ? 'animate-spin' : ''} />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="chart-card">
            <CardContent className="p-4">
              {renderChart()}
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
                  <TabsTrigger 
                    value="paper" 
                    className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black"
                    data-testid="paper-mode-tab"
                  >
                    Paper
                  </TabsTrigger>
                  <TabsTrigger 
                    value="real"
                    className="data-[state=active]:bg-[#00FF94] data-[state=active]:text-black"
                    data-testid="real-mode-tab"
                  >
                    Real
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              {tradingMode === 'real' && (
                <div className="mb-4 p-3 bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg">
                  <p className="text-sm text-[#FF0055]">⚠️ Real money trading enabled</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <Label className="text-[#A1A1AA]">Amount (USD)</Label>
                  <Input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Enter amount"
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                    data-testid="amount-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Button
                    onClick={() => executeTrade('BUY')}
                    disabled={loading}
                    className="bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold"
                    data-testid="buy-btn"
                  >
                    {loading ? 'Processing...' : 'BUY'}
                  </Button>
                  <Button
                    onClick={() => executeTrade('SELL')}
                    disabled={loading}
                    className="bg-[#FF0055] hover:bg-[#CC0044] text-white font-bold"
                    data-testid="sell-btn"
                  >
                    {loading ? 'Processing...' : 'SELL'}
                  </Button>
                </div>
              </div>

              {/* Quick amounts */}
              <div className="mt-6">
                <Label className="text-[#A1A1AA] text-sm">Quick amounts</Label>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  {['25', '50', '100', '500'].map(val => (
                    <Button
                      key={val}
                      size="sm"
                      variant="outline"
                      onClick={() => setAmount(val)}
                      className="border-[#1F1F1F] hover:bg-[#1F1F1F]"
                    >
                      ${val}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Market Info */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] mt-6">
            <CardHeader>
              <CardTitle className="text-lg font-heading">Market Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-[#A1A1AA]">24h Change</span>
                <span className={priceChange >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                  {(priceChange ?? 0).toFixed(2) || '0.00'}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#A1A1AA]">Timeframe</span>
                <span className="text-white">{timeframe} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#A1A1AA]">Data Points</span>
                <span className="text-white">{chartData.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#A1A1AA]">Mode</span>
                <Badge className={tradingMode === 'real' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF9500]/20 text-[#FF9500]'}>
                  {tradingMode.toUpperCase()}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TradingView;
