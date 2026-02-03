import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { createChart, CandlestickSeries, LineSeries, AreaSeries } from 'lightweight-charts';
import { motion } from 'framer-motion';
import { marketAPI, tradingAPI } from '../services/api';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, CandlestickChart, LineChart, BarChart3 } from 'lucide-react';
import { useTradingMode } from '../context/TradingModeContext';

const TradingView = () => {
  // Use global trading mode context for consistency across pages
  const { mode: tradingMode, setMode: setTradingMode } = useTradingMode();
  
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [chartType, setChartType] = useState('candlestick');
  const [timeframe, setTimeframe] = useState('7');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(null);
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    loadChartData();
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [selectedCoin, timeframe, chartType]);

  const loadChartData = async () => {
    try {
      let prices = [];
      
      try {
        const response = await marketAPI.getHistoricalData(selectedCoin, parseInt(timeframe));
        prices = response.data.prices || [];
        console.log(`Loaded ${prices.length} price points for ${selectedCoin}`);
      } catch (apiError) {
        console.error('API error fetching historical data:', apiError);
        // Don't use simulated data - show error state instead
        prices = [];
      }
      
      if (prices.length > 0) {
        setCurrentPrice(prices[prices.length - 1][1]);
        const firstPrice = prices[0][1];
        const lastPrice = prices[prices.length - 1][1];
        setPriceChange(((lastPrice - firstPrice) / firstPrice) * 100);
      }

      // Clear existing chart
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }

      if (!chartContainerRef.current) {
        console.log('Chart container not ready');
        return;
      }
      
      if (prices.length === 0) {
        console.log('No price data available');
        return;
      }

      // Create new chart
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: 'solid', color: '#0A0A0A' },
          textColor: '#A1A1AA',
        },
        grid: {
          vertLines: { color: '#1F1F1F' },
          horzLines: { color: '#1F1F1F' },
        },
        width: chartContainerRef.current.clientWidth,
        height: 400,
        crosshair: {
          mode: 1,
        },
        rightPriceScale: {
          borderColor: '#1F1F1F',
        },
        timeScale: {
          borderColor: '#1F1F1F',
          timeVisible: true,
        },
      });

      chartRef.current = chart;
      console.log('Chart created successfully');

      // Generate OHLC data from prices
      const ohlcData = generateOHLC(prices);
      console.log(`Generated ${ohlcData.length} OHLC candles`);

      if (chartType === 'candlestick') {
        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#00FF94',
          downColor: '#FF0055',
          borderDownColor: '#FF0055',
          borderUpColor: '#00FF94',
          wickDownColor: '#FF0055',
          wickUpColor: '#00FF94',
        });
        candleSeries.setData(ohlcData);
      } else if (chartType === 'line') {
        const lineSeries = chart.addSeries(LineSeries, {
          color: '#00FF94',
          lineWidth: 2,
        });
        lineSeries.setData(prices.map(([time, price]) => ({
          time: Math.floor(time / 1000),
          value: price,
        })));
      } else if (chartType === 'area') {
        const areaSeries = chart.addSeries(AreaSeries, {
          topColor: 'rgba(0, 255, 148, 0.4)',
          bottomColor: 'rgba(0, 255, 148, 0.0)',
          lineColor: '#00FF94',
          lineWidth: 2,
        });
        areaSeries.setData(prices.map(([time, price]) => ({
          time: Math.floor(time / 1000),
          value: price,
        })));
      }

      chart.timeScale().fitContent();

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({ 
            width: chartContainerRef.current.clientWidth 
          });
        }
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);

    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const generateOHLC = (prices) => {
    // Group prices into periods and generate OHLC
    const periodMs = parseInt(timeframe) > 30 ? 86400000 : 3600000; // Daily or hourly
    const ohlcMap = new Map();

    prices.forEach(([timestamp, price]) => {
      const periodStart = Math.floor(timestamp / periodMs) * periodMs;
      
      if (!ohlcMap.has(periodStart)) {
        ohlcMap.set(periodStart, {
          time: Math.floor(periodStart / 1000),
          open: price,
          high: price,
          low: price,
          close: price,
        });
      } else {
        const candle = ohlcMap.get(periodStart);
        candle.high = Math.max(candle.high, price);
        candle.low = Math.min(candle.low, price);
        candle.close = price;
      }
    });

    return Array.from(ohlcMap.values()).sort((a, b) => a.time - b.time);
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
                    <Badge className={`${priceChange >= 0 ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}`}>
                      {priceChange >= 0 ? <TrendingUp size={12} className="mr-1" /> : <TrendingDown size={12} className="mr-1" />}
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

              <div className="flex bg-[#121212] rounded-lg p-1">
                <Button
                  size="sm"
                  variant={chartType === 'candlestick' ? 'default' : 'ghost'}
                  onClick={() => setChartType('candlestick')}
                  className={chartType === 'candlestick' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="candlestick-btn"
                >
                  <CandlestickChart size={16} />
                </Button>
                <Button
                  size="sm"
                  variant={chartType === 'line' ? 'default' : 'ghost'}
                  onClick={() => setChartType('line')}
                  className={chartType === 'line' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="line-btn"
                >
                  <LineChart size={16} />
                </Button>
                <Button
                  size="sm"
                  variant={chartType === 'area' ? 'default' : 'ghost'}
                  onClick={() => setChartType('area')}
                  className={chartType === 'area' ? 'bg-[#00FF94] text-black' : ''}
                  data-testid="area-btn"
                >
                  <BarChart3 size={16} />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="chart-card">
            <CardContent className="p-0">
              <div 
                ref={chartContainerRef} 
                className="w-full h-[400px]" 
                data-testid="price-chart"
              />
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
                  <TabsTrigger value="paper" data-testid="paper-mode-tab">Paper</TabsTrigger>
                  <TabsTrigger value="real" data-testid="real-mode-tab">Real</TabsTrigger>
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

                {currentPrice && amount && (
                  <div className="p-3 bg-[#121212] rounded-lg">
                    <div className="text-xs text-[#A1A1AA]">You will receive approximately</div>
                    <div className="text-lg font-data font-bold text-[#00FF94]">
                      {(parseFloat(amount) / currentPrice).toFixed(8)} {coins.find(c => c.value === selectedCoin)?.symbol}
                    </div>
                  </div>
                )}

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
                    <TrendingDown size={16} className="mr-2" />
                    SELL
                  </Button>
                </div>

                {tradingMode === 'paper' && (
                  <div className="bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg p-4">
                    <p className="text-xs text-[#007AFF]">
                      📊 Paper Trading: Simulated trades, no real money.
                    </p>
                  </div>
                )}

                {tradingMode === 'real' && (
                  <div className="bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg p-4">
                    <p className="text-xs text-[#FF0055]">
                      ⚠️ Real Trading: Actual trades on Kraken exchange.
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
