import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { motion } from 'framer-motion';
import {
  TrendingUp, TrendingDown, DollarSign, Clock, Target, Percent,
  BookOpen, RefreshCw, ChevronUp, ChevronDown, Zap, AlertTriangle
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';

const OptionsTrading = () => {
  const [chain, setChain] = useState(null);
  const [positions, setPositions] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('chain');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [selectedExpiry, setSelectedExpiry] = useState('');
  const [orderForm, setOrderForm] = useState({
    symbol: 'BTC',
    option_type: 'call',
    strike_price: 45000,
    expiry_date: '',
    quantity: 1,
    action: 'buy'  // 'buy' or 'sell'
  });
  const [filterMinDelta, setFilterMinDelta] = useState(null);
  const [filterMaxDelta, setFilterMaxDelta] = useState(null);
  const [sortBy, setSortBy] = useState('strike'); // 'strike', 'volume', 'delta'
  const [showFilters, setShowFilters] = useState(false);
  const [estimatedGreeks, setEstimatedGreeks] = useState(null);
  const [strategyLegs, setStrategyLegs] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [expandedPosition, setExpandedPosition] = useState(null);
  const [positionAnalytics, setPositionAnalytics] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [chainRes, positionsRes, strategiesRes] = await Promise.all([
        api.get(`/options/chain/${selectedSymbol}`).catch(() => ({ data: null })),
        api.get('/options/positions').catch(() => ({ data: { positions: [], summary: {} } })),
        api.get('/options/strategies').catch(() => ({ data: { strategies: [] } }))
      ]);

      setChain(chainRes.data);
      setPositions(positionsRes.data.positions || []);
      setStrategies(strategiesRes.data.strategies || []);
      
      if (chainRes.data?.expiries?.length > 0 && !selectedExpiry) {
        setSelectedExpiry(chainRes.data.expiries[0].date);
        setOrderForm(prev => ({ ...prev, expiry_date: chainRes.data.expiries[0].date }));
      }
    } catch (error) {
      console.error('Error loading options data:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, selectedExpiry]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handlePlaceOrder = async () => {
    if (!orderForm.expiry_date) {
      toast.error('Please select an expiry date');
      return;
    }

    const loadingToast = toast.loading('Placing order...');
    try {
      await api.post('/options/order', orderForm);
      toast.dismiss(loadingToast);
      const actionText = orderForm.action === 'buy' ? 'Bought' : 'Sold';
      toast.success(`Option ${actionText}!`, {
        description: `${actionText} ${orderForm.quantity} ${orderForm.option_type.toUpperCase()} ${orderForm.symbol} @ $${orderForm.strike_price}`
      });
      loadData();
      setOrderForm(prev => ({ ...prev, strike_price: 45000, expiry_date: '', quantity: 1 }));
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to place order', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  // Calculate estimated Greeks for order form
  useEffect(() => {
    if (orderForm.expiry_date && chain?.current_price) {
      const expiry = new Date(orderForm.expiry_date);
      const now = new Date();
      const daysToExpiry = Math.max((expiry - now) / (1000 * 60 * 60 * 24), 0);
      const T = daysToExpiry / 365;
      
      // Find matching option in chain or estimate
      const matchingOption = chain.options?.find(opt => 
        opt.strike === orderForm.strike_price && opt.expiry === orderForm.expiry_date
      );
      
      if (matchingOption) {
        const greeks = orderForm.option_type === 'call' 
          ? matchingOption.call.greeks 
          : matchingOption.put.greeks;
        setEstimatedGreeks({
          ...greeks,
          cost: (orderForm.option_type === 'call' ? matchingOption.call.ask : matchingOption.put.ask) * orderForm.quantity,
          breakeven: orderForm.option_type === 'call' 
            ? orderForm.strike_price + matchingOption.call.ask
            : orderForm.strike_price - matchingOption.put.ask
        });
      }
    }
  }, [orderForm.strike_price, orderForm.expiry_date, orderForm.option_type, orderForm.quantity, chain]);

  // Strategy builder functions
  const addLegToStrategy = () => {
    setStrategyLegs([...strategyLegs, {
      id: Date.now(),
      action: 'buy',
      option_type: 'call',
      strike_price: chain?.current_price || 45000,
      expiry_date: selectedExpiry,
      quantity: 1
    }]);
  };

  const removeLegFromStrategy = (legId) => {
    setStrategyLegs(strategyLegs.filter(leg => leg.id !== legId));
  };

  const updateStrategyLeg = (legId, field, value) => {
    setStrategyLegs(strategyLegs.map(leg => 
      leg.id === legId ? { ...leg, [field]: value } : leg
    ));
  };

  const calculateStrategyPayoff = () => {
    if (strategyLegs.length === 0 || !chain) return null;
    
    let totalCost = 0;
    let netGreeks = { delta: 0, gamma: 0, theta: 0, vega: 0 };
    
    strategyLegs.forEach(leg => {
      const option = chain.options?.find(opt => 
        opt.strike === leg.strike_price && opt.expiry === leg.expiry_date
      );
      
      if (option) {
        const optionData = leg.option_type === 'call' ? option.call : option.put;
        const price = leg.action === 'buy' ? optionData.ask : optionData.bid;
        const multiplier = leg.action === 'buy' ? 1 : -1;
        
        totalCost += price * leg.quantity * multiplier;
        netGreeks.delta += optionData.greeks.delta * leg.quantity * multiplier;
        netGreeks.gamma += optionData.greeks.gamma * leg.quantity * multiplier;
        netGreeks.theta += optionData.greeks.theta * leg.quantity * multiplier;
        netGreeks.vega += optionData.greeks.vega * leg.quantity * multiplier;
      }
    });
    
    return { totalCost: totalCost.toFixed(2), netGreeks };
  };

  const executeStrategy = async () => {
    if (strategyLegs.length === 0) {
      toast.error('No legs in strategy');
      return;
    }

    const loadingToast = toast.loading('Executing multi-leg strategy...');
    try {
      // Execute each leg
      for (const leg of strategyLegs) {
        await api.post('/options/order', {
          symbol: selectedSymbol,
          ...leg
        });
      }
      
      toast.dismiss(loadingToast);
      toast.success('Multi-leg strategy executed!', {
        description: `${strategyLegs.length} legs opened successfully`
      });
      
      setStrategyLegs([]);
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to execute strategy', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  const loadPredefinedStrategy = (strategyName) => {
    if (!chain || !selectedExpiry) {
      toast.error('Please select a symbol and expiry first');
      return;
    }

    const currentPrice = chain.current_price;
    const atm = Math.round(currentPrice / 1000) * 1000;
    
    let legs = [];
    
    switch(strategyName) {
      case 'Bull Call Spread':
        legs = [
          { id: Date.now(), action: 'buy', option_type: 'call', strike_price: atm, expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 1, action: 'sell', option_type: 'call', strike_price: atm + (currentPrice * 0.1), expiry_date: selectedExpiry, quantity: 1 }
        ];
        break;
      case 'Bear Put Spread':
        legs = [
          { id: Date.now(), action: 'buy', option_type: 'put', strike_price: atm, expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 1, action: 'sell', option_type: 'put', strike_price: atm - (currentPrice * 0.1), expiry_date: selectedExpiry, quantity: 1 }
        ];
        break;
      case 'Straddle':
        legs = [
          { id: Date.now(), action: 'buy', option_type: 'call', strike_price: atm, expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 1, action: 'buy', option_type: 'put', strike_price: atm, expiry_date: selectedExpiry, quantity: 1 }
        ];
        break;
      case 'Iron Condor':
        legs = [
          { id: Date.now(), action: 'sell', option_type: 'put', strike_price: atm - (currentPrice * 0.05), expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 1, action: 'buy', option_type: 'put', strike_price: atm - (currentPrice * 0.1), expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 2, action: 'sell', option_type: 'call', strike_price: atm + (currentPrice * 0.05), expiry_date: selectedExpiry, quantity: 1 },
          { id: Date.now() + 3, action: 'buy', option_type: 'call', strike_price: atm + (currentPrice * 0.1), expiry_date: selectedExpiry, quantity: 1 }
        ];
        break;
      default:
        return;
    }
    
    setStrategyLegs(legs);
    setSelectedStrategy(strategyName);
    toast.success(`Loaded ${strategyName} strategy`);
  };

  const togglePositionDetails = async (positionId) => {
    if (expandedPosition === positionId) {
      setExpandedPosition(null);
      setPositionAnalytics(null);
    } else {
      setExpandedPosition(positionId);
      // Fetch analytics
      try {
        const res = await api.get(`/options/position-analytics/${positionId}`);
        setPositionAnalytics(res.data);
      } catch (error) {
        console.error('Failed to fetch position analytics:', error);
        toast.error('Failed to load position details');
      }
    }
  };

  const handleClosePosition = async (positionId) => {
    const loadingToast = toast.loading('Closing position...');
    try {
      const res = await api.post(`/options/close/${positionId}`);
      toast.dismiss(loadingToast);
      toast.success('Position closed!', {
        description: `P&L: $${res.data.final_pnl}`
      });
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to close position');
    }
  };

  const filteredOptions = chain?.options?.filter(opt => {
    if (opt.expiry !== selectedExpiry) return false;
    
    // Apply delta filters
    if (filterMinDelta !== null || filterMaxDelta !== null) {
      const callDelta = Math.abs(opt.call.greeks.delta);
      const putDelta = Math.abs(opt.put.greeks.delta);
      
      if (filterMinDelta !== null && callDelta < filterMinDelta && putDelta < filterMinDelta) return false;
      if (filterMaxDelta !== null && callDelta > filterMaxDelta && putDelta > filterMaxDelta) return false;
    }
    
    return true;
  }).sort((a, b) => {
    switch(sortBy) {
      case 'volume':
        return (b.call.volume + b.put.volume) - (a.call.volume + a.put.volume);
      case 'delta':
        return Math.abs(b.call.greeks.delta) - Math.abs(a.call.greeks.delta);
      case 'strike':
      default:
        return a.strike - b.strike;
    }
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#FF9500] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Options...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="options-trading-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Target size={40} className="text-[#FF9500]" />
            <span className="text-[#FF9500]">Options</span> Trading
          </h1>
          <p className="text-[#A1A1AA]">
            Trade crypto options with AI-powered Greeks calculation
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger className="w-32 bg-[#121212] border-[#1F1F1F]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#121212] border-[#1F1F1F]">
              <SelectItem value="BTC">BTC</SelectItem>
              <SelectItem value="ETH">ETH</SelectItem>
              <SelectItem value="SOL">SOL</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
            <RefreshCw size={16} />
          </Button>
        </div>
      </motion.div>

      {/* Current Price Banner */}
      {chain && (
        <Card className="bg-gradient-to-r from-[#FF9500]/20 to-[#FF9500]/5 border-[#FF9500]/30">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span className="text-[#A1A1AA]">{selectedSymbol} Current Price</span>
                <div className="text-3xl font-data font-bold text-white">
                  ${chain.current_price?.toLocaleString()}
                </div>
              </div>
              <div>
                <span className="text-[#A1A1AA]">Implied Volatility</span>
                <div className="text-2xl font-data text-[#FF9500]">
                  {(chain.volatility * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-[#A1A1AA]">IV Rank</span>
                <div className="flex items-center gap-2">
                  <div className="text-2xl font-data text-[#00FF94]">
                    {((chain.volatility * 100 / 100) * 100).toFixed(0)}%
                  </div>
                  <Badge className={
                    chain.volatility > 0.8 ? 'bg-[#FF0055]' : 
                    chain.volatility > 0.5 ? 'bg-[#FFB800]' : 
                    'bg-[#00FF94] text-black'
                  }>
                    {chain.volatility > 0.8 ? 'HIGH' : chain.volatility > 0.5 ? 'MEDIUM' : 'LOW'}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="chain" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Option Chain
          </TabsTrigger>
          <TabsTrigger value="trade" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Place Order
          </TabsTrigger>
          <TabsTrigger value="builder" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            <Zap size={16} className="mr-1" />
            Strategy Builder
          </TabsTrigger>
          <TabsTrigger value="positions" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Positions ({positions.length})
          </TabsTrigger>
          <TabsTrigger value="strategies" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Strategies
          </TabsTrigger>
        </TabsList>

        {/* Option Chain Tab */}
        <TabsContent value="chain" className="space-y-4">
          {/* Expiry Selector and Filters */}
          <div className="space-y-4">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {chain?.expiries?.map((exp) => (
                <Button
                  key={exp.date}
                  variant={selectedExpiry === exp.date ? "default" : "outline"}
                  onClick={() => setSelectedExpiry(exp.date)}
                  className={selectedExpiry === exp.date ? "bg-[#FF9500] text-black" : "border-[#1F1F1F]"}
                  size="sm"
                >
                  {exp.date} ({exp.days_to_expiry}d)
                </Button>
              ))}
            </div>

            {/* Filter and Sort Controls */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFilters(!showFilters)}
                    className="border-[#1F1F1F]"
                  >
                    <Target size={16} className="mr-2" />
                    {showFilters ? 'Hide Filters' : 'Show Filters'}
                  </Button>

                  <div className="flex items-center gap-2">
                    <Label className="text-[#A1A1AA] text-sm">Sort by:</Label>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="w-32 h-8 bg-[#121212] border-[#1F1F1F] text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="strike">Strike</SelectItem>
                        <SelectItem value="volume">Volume</SelectItem>
                        <SelectItem value="delta">Delta</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {(filterMinDelta !== null || filterMaxDelta !== null) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setFilterMinDelta(null);
                        setFilterMaxDelta(null);
                      }}
                      className="text-[#FF9500]"
                    >
                      Clear Filters
                    </Button>
                  )}
                </div>

                {showFilters && (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[#1F1F1F]">
                    <div>
                      <Label className="text-[#A1A1AA] text-sm mb-2 block">Min Delta</Label>
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="e.g., 0.3"
                        value={filterMinDelta || ''}
                        onChange={(e) => setFilterMinDelta(e.target.value ? parseFloat(e.target.value) : null)}
                        className="bg-[#121212] border-[#1F1F1F] h-8"
                      />
                    </div>
                    <div>
                      <Label className="text-[#A1A1AA] text-sm mb-2 block">Max Delta</Label>
                      <Input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        placeholder="e.g., 0.7"
                        value={filterMaxDelta || ''}
                        onChange={(e) => setFilterMaxDelta(e.target.value ? parseFloat(e.target.value) : null)}
                        className="bg-[#121212] border-[#1F1F1F] h-8"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Options Table */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1F1F1F] text-[#A1A1AA]">
                    <th colSpan="4" className="p-3 text-center bg-[#00FF94]/10 text-[#00FF94]">CALLS</th>
                    <th className="p-3 bg-[#1F1F1F]">Strike</th>
                    <th colSpan="4" className="p-3 text-center bg-[#FF0055]/10 text-[#FF0055]">PUTS</th>
                  </tr>
                  <tr className="border-b border-[#1F1F1F] text-xs text-[#666]">
                    <th className="p-2">Bid</th>
                    <th className="p-2">Ask</th>
                    <th className="p-2">Delta</th>
                    <th className="p-2">OI</th>
                    <th className="p-2 bg-[#1F1F1F]"></th>
                    <th className="p-2">Bid</th>
                    <th className="p-2">Ask</th>
                    <th className="p-2">Delta</th>
                    <th className="p-2">OI</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOptions.slice(0, 10).map((opt, i) => {
                    const isATM = Math.abs(opt.strike - chain.current_price) < chain.current_price * 0.02;
                    return (
                      <tr key={i} className={`border-b border-[#1F1F1F] hover:bg-[#1F1F1F]/50 ${isATM ? 'bg-[#FF9500]/10' : ''}`}>
                        <td className="p-2 text-[#00FF94] font-data">${opt.call.bid}</td>
                        <td className="p-2 text-[#00FF94] font-data">${opt.call.ask}</td>
                        <td className="p-2 font-data">{opt.call.greeks.delta}</td>
                        <td className="p-2 text-[#666] font-data">{opt.call.open_interest}</td>
                        <td className="p-2 font-bold text-white bg-[#1F1F1F] text-center">
                          ${opt.strike.toLocaleString()}
                          {isATM && <Badge className="ml-1 bg-[#FF9500] text-black text-xs">ATM</Badge>}
                        </td>
                        <td className="p-2 text-[#FF0055] font-data">${opt.put.bid}</td>
                        <td className="p-2 text-[#FF0055] font-data">${opt.put.ask}</td>
                        <td className="p-2 font-data">{opt.put.greeks.delta}</td>
                        <td className="p-2 text-[#666] font-data">{opt.put.open_interest}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>

        {/* Place Order Tab */}
        <TabsContent value="trade" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Place Option Order</CardTitle>
              <CardDescription>Buy or sell options with AI-powered Greeks calculation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <Label className="text-[#A1A1AA]">Action</Label>
                  <Select 
                    value={orderForm.action} 
                    onValueChange={(v) => setOrderForm({ ...orderForm, action: v })}
                  >
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                      <SelectItem value="buy">
                        <span className="flex items-center gap-2">
                          <TrendingUp className="text-[#00FF94]" size={16} /> Buy to Open
                        </span>
                      </SelectItem>
                      <SelectItem value="sell">
                        <span className="flex items-center gap-2">
                          <TrendingDown className="text-[#FF9500]" size={16} /> Sell to Open
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Option Type</Label>
                  <Select 
                    value={orderForm.option_type} 
                    onValueChange={(v) => setOrderForm({ ...orderForm, option_type: v })}
                  >
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                      <SelectItem value="call">
                        <span className="flex items-center gap-2">
                          <ChevronUp className="text-[#00FF94]" size={16} /> Call (Bullish)
                        </span>
                      </SelectItem>
                      <SelectItem value="put">
                        <span className="flex items-center gap-2">
                          <ChevronDown className="text-[#FF0055]" size={16} /> Put (Bearish)
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Strike Price</Label>
                  <Input
                    type="number"
                    value={orderForm.strike_price}
                    onChange={(e) => setOrderForm({ ...orderForm, strike_price: parseFloat(e.target.value) })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Expiry Date</Label>
                  <Select 
                    value={orderForm.expiry_date} 
                    onValueChange={(v) => setOrderForm({ ...orderForm, expiry_date: v })}
                  >
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                      <SelectValue placeholder="Select expiry" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                      {chain?.expiries?.map((exp) => (
                        <SelectItem key={exp.date} value={exp.date}>
                          {exp.date} ({exp.days_to_expiry} days)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Quantity</Label>
                  <Input
                    type="number"
                    value={orderForm.quantity}
                    onChange={(e) => setOrderForm({ ...orderForm, quantity: parseFloat(e.target.value) })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                    min={0.1}
                    step={0.1}
                  />
                </div>
              </div>

              {/* Estimated Greeks and Cost */}
              {estimatedGreeks && (
                <Card className="bg-[#121212] border-[#FF9500]/30">
                  <CardContent className="p-4">
                    <h4 className="text-sm font-bold text-[#FF9500] mb-3">Order Estimate</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-sm">
                      <div>
                        <p className="text-[#666]">Total Cost</p>
                        <p className="font-data font-bold text-white">${estimatedGreeks.cost?.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-[#666]">Breakeven</p>
                        <p className="font-data font-bold text-[#FF9500]">${estimatedGreeks.breakeven?.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-[#666]">Delta</p>
                        <p className="font-data text-white">{estimatedGreeks.delta}</p>
                      </div>
                      <div>
                        <p className="text-[#666]">Theta</p>
                        <p className="font-data text-[#FF0055]">{estimatedGreeks.theta}</p>
                      </div>
                      <div>
                        <p className="text-[#666]">Vega</p>
                        <p className="font-data text-white">{estimatedGreeks.vega}</p>
                      </div>
                      <div>
                        <p className="text-[#666]">Gamma</p>
                        <p className="font-data text-white">{estimatedGreeks.gamma}</p>
                      </div>
                    </div>
                    {orderForm.action === 'sell' && (
                      <div className="mt-3 pt-3 border-t border-[#1F1F1F]">
                        <div className="flex items-start gap-2">
                          <AlertTriangle size={16} className="text-[#FFB800] mt-0.5" />
                          <p className="text-xs text-[#FFB800]">
                            Selling options has unlimited risk. Ensure you understand the obligations.
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              <Button 
                onClick={handlePlaceOrder} 
                className={`w-full font-bold ${
                  orderForm.action === 'buy' 
                    ? (orderForm.option_type === 'call' ? 'bg-[#00FF94] text-black' : 'bg-[#FF0055] text-white')
                    : 'bg-[#FF9500] text-black'
                }`}
              >
                {orderForm.action === 'buy' ? 'Buy' : 'Sell'} {orderForm.option_type.toUpperCase()} Option
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Strategy Builder Tab */}
        <TabsContent value="builder" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="text-[#FF9500]" />
                Multi-Leg Strategy Builder
              </CardTitle>
              <CardDescription>
                Build complex options strategies with multiple legs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Quick Strategy Templates */}
              <div>
                <Label className="text-[#A1A1AA] mb-2 block">Quick Load Strategy</Label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {['Bull Call Spread', 'Bear Put Spread', 'Straddle', 'Iron Condor'].map(strat => (
                    <Button
                      key={strat}
                      variant="outline"
                      size="sm"
                      onClick={() => loadPredefinedStrategy(strat)}
                      className="border-[#1F1F1F]"
                    >
                      {strat}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Strategy Legs */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-[#A1A1AA]">Strategy Legs</Label>
                  <Button
                    onClick={addLegToStrategy}
                    size="sm"
                    variant="outline"
                    className="border-[#FF9500] text-[#FF9500]"
                  >
                    <BookOpen size={16} className="mr-2" />
                    Add Leg
                  </Button>
                </div>

                {strategyLegs.length === 0 ? (
                  <Card className="bg-[#121212] border-[#1F1F1F]">
                    <CardContent className="py-8 text-center">
                      <p className="text-[#666] mb-3">No legs added yet</p>
                      <Button
                        onClick={addLegToStrategy}
                        size="sm"
                        className="bg-[#FF9500] text-black"
                      >
                        Add First Leg
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {strategyLegs.map((leg, index) => (
                      <Card key={leg.id} className="bg-[#121212] border-[#1F1F1F]">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-bold text-[#FF9500]">Leg {index + 1}</span>
                            <Button
                              onClick={() => removeLegFromStrategy(leg.id)}
                              size="sm"
                              variant="ghost"
                              className="text-[#FF0055] h-6"
                            >
                              Remove
                            </Button>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                            <Select
                              value={leg.action}
                              onValueChange={(v) => updateStrategyLeg(leg.id, 'action', v)}
                            >
                              <SelectTrigger className="bg-[#0A0A0A] border-[#1F1F1F] h-8 text-xs">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                                <SelectItem value="buy">Buy</SelectItem>
                                <SelectItem value="sell">Sell</SelectItem>
                              </SelectContent>
                            </Select>

                            <Select
                              value={leg.option_type}
                              onValueChange={(v) => updateStrategyLeg(leg.id, 'option_type', v)}
                            >
                              <SelectTrigger className="bg-[#0A0A0A] border-[#1F1F1F] h-8 text-xs">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                                <SelectItem value="call">Call</SelectItem>
                                <SelectItem value="put">Put</SelectItem>
                              </SelectContent>
                            </Select>

                            <Input
                              type="number"
                              value={leg.strike_price}
                              onChange={(e) => updateStrategyLeg(leg.id, 'strike_price', parseFloat(e.target.value))}
                              className="bg-[#0A0A0A] border-[#1F1F1F] h-8 text-xs"
                              placeholder="Strike"
                            />

                            <Select
                              value={leg.expiry_date}
                              onValueChange={(v) => updateStrategyLeg(leg.id, 'expiry_date', v)}
                            >
                              <SelectTrigger className="bg-[#0A0A0A] border-[#1F1F1F] h-8 text-xs">
                                <SelectValue placeholder="Expiry" />
                              </SelectTrigger>
                              <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                                {chain?.expiries?.map((exp) => (
                                  <SelectItem key={exp.date} value={exp.date}>
                                    {exp.date}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>

                            <Input
                              type="number"
                              value={leg.quantity}
                              onChange={(e) => updateStrategyLeg(leg.id, 'quantity', parseFloat(e.target.value))}
                              className="bg-[#0A0A0A] border-[#1F1F1F] h-8 text-xs"
                              placeholder="Qty"
                              min={0.1}
                              step={0.1}
                            />
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Strategy Summary */}
              {strategyLegs.length > 0 && (() => {
                const payoff = calculateStrategyPayoff();
                return payoff ? (
                  <Card className="bg-[#121212] border-[#FF9500]/30">
                    <CardContent className="p-4">
                      <h4 className="text-sm font-bold text-[#FF9500] mb-3">Strategy Summary</h4>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                        <div>
                          <p className="text-[#666]">Net Cost</p>
                          <p className={`font-data font-bold ${parseFloat(payoff.totalCost) < 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                            ${payoff.totalCost}
                          </p>
                        </div>
                        <div>
                          <p className="text-[#666]">Net Delta</p>
                          <p className="font-data text-white">{payoff.netGreeks.delta.toFixed(4)}</p>
                        </div>
                        <div>
                          <p className="text-[#666]">Net Gamma</p>
                          <p className="font-data text-white">{payoff.netGreeks.gamma.toFixed(6)}</p>
                        </div>
                        <div>
                          <p className="text-[#666]">Net Theta</p>
                          <p className="font-data text-[#FF0055]">{payoff.netGreeks.theta.toFixed(4)}</p>
                        </div>
                        <div>
                          <p className="text-[#666]">Net Vega</p>
                          <p className="font-data text-white">{payoff.netGreeks.vega.toFixed(4)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ) : null;
              })()}

              {/* Execute Strategy */}
              {strategyLegs.length > 0 && (
                <Button
                  onClick={executeStrategy}
                  className="w-full bg-[#FF9500] text-black font-bold"
                >
                  Execute Strategy ({strategyLegs.length} legs)
                </Button>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Positions Tab */}
        <TabsContent value="positions" className="space-y-4">
          {positions.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <Target size={48} className="mx-auto mb-4 text-[#FF9500] opacity-50" />
                <p className="text-[#A1A1AA]">No open positions</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {positions.map((pos) => {
                const isShort = pos.quantity < 0;
                const absQuantity = Math.abs(pos.quantity);
                return (
                  <Card key={pos.position_id} className="bg-[#0A0A0A] border-[#1F1F1F]">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="flex gap-2">
                            <Badge className={pos.option_type === 'call' ? 'bg-[#00FF94] text-black' : 'bg-[#FF0055]'}>
                              {pos.option_type.toUpperCase()}
                            </Badge>
                            <Badge className={isShort ? 'bg-[#FF9500] text-black' : 'bg-[#007AFF]'}>
                              {isShort ? 'SHORT' : 'LONG'}
                            </Badge>
                          </div>
                          <div>
                            <h3 className="font-bold text-white">{pos.symbol} ${pos.strike_price}</h3>
                            <p className="text-sm text-[#A1A1AA]">
                              Exp: {pos.expiry_date} ({pos.days_to_expiry}d) • Qty: {absQuantity}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-data ${pos.pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                            {pos.pnl >= 0 ? '+' : ''}${pos.pnl} ({pos.pnl_pct}%)
                          </p>
                          <p className="text-sm text-[#A1A1AA]">
                            Entry: ${pos.entry_price} → ${pos.current_price}
                          </p>
                        </div>
                        <Button
                          onClick={() => handleClosePosition(pos.position_id)}
                          variant="outline"
                          className="border-[#FF0055] text-[#FF0055]"
                          size="sm"
                        >
                          Close
                        </Button>
                      </div>
                      {/* Greeks */}
                      <div className="mt-3 pt-3 border-t border-[#1F1F1F]">
                        <div className="grid grid-cols-5 gap-4 text-center text-sm">
                          <div>
                            <p className="text-[#666]">Delta</p>
                            <p className="font-data text-white">{pos.greeks?.delta}</p>
                          </div>
                          <div>
                            <p className="text-[#666]">Gamma</p>
                            <p className="font-data text-white">{pos.greeks?.gamma}</p>
                          </div>
                          <div>
                            <p className="text-[#666]">Theta</p>
                            <p className="font-data text-[#FF0055]">{pos.greeks?.theta}</p>
                          </div>
                          <div>
                            <p className="text-[#666]">Vega</p>
                            <p className="font-data text-white">{pos.greeks?.vega}</p>
                          </div>
                          <div>
                            <p className="text-[#666]">Rho</p>
                            <p className="font-data text-white">{pos.greeks?.rho}</p>
                          </div>
                        </div>
                        
                        {/* Analytics Toggle */}
                        <div className="mt-3 text-center">
                          <Button
                            onClick={() => togglePositionDetails(pos.position_id)}
                            variant="ghost"
                            size="sm"
                            className="text-[#FF9500] text-xs"
                          >
                            {expandedPosition === pos.position_id ? 'Hide' : 'Show'} P&L Breakdown
                            <ChevronDown 
                              size={14} 
                              className={`ml-1 transition-transform ${expandedPosition === pos.position_id ? 'rotate-180' : ''}`}
                            />
                          </Button>
                        </div>
                      </div>

                      {/* Expanded Analytics */}
                      {expandedPosition === pos.position_id && positionAnalytics && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3 pt-3 border-t border-[#1F1F1F]"
                        >
                          <h4 className="text-sm font-bold text-[#FF9500] mb-3">P&L Attribution by Greeks</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                            <div className="bg-[#121212] p-3 rounded border border-[#1F1F1F]">
                              <p className="text-[#666] text-xs mb-1">Delta P&L</p>
                              <p className={`font-data font-bold ${positionAnalytics.pnl_breakdown.delta_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                ${positionAnalytics.pnl_breakdown.delta_pnl}
                              </p>
                              <p className="text-[#666] text-xs mt-1">Price movement</p>
                            </div>
                            <div className="bg-[#121212] p-3 rounded border border-[#1F1F1F]">
                              <p className="text-[#666] text-xs mb-1">Theta P&L</p>
                              <p className={`font-data font-bold ${positionAnalytics.pnl_breakdown.theta_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                ${positionAnalytics.pnl_breakdown.theta_pnl}
                              </p>
                              <p className="text-[#666] text-xs mt-1">Time decay ({pos.days_held}d)</p>
                            </div>
                            <div className="bg-[#121212] p-3 rounded border border-[#1F1F1F]">
                              <p className="text-[#666] text-xs mb-1">Vega P&L</p>
                              <p className={`font-data font-bold ${positionAnalytics.pnl_breakdown.vega_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                ${positionAnalytics.pnl_breakdown.vega_pnl}
                              </p>
                              <p className="text-[#666] text-xs mt-1">IV change</p>
                            </div>
                            <div className="bg-[#121212] p-3 rounded border border-[#1F1F1F]">
                              <p className="text-[#666] text-xs mb-1">Gamma/Other</p>
                              <p className={`font-data font-bold ${positionAnalytics.pnl_breakdown.gamma_other >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                ${positionAnalytics.pnl_breakdown.gamma_other}
                              </p>
                              <p className="text-[#666] text-xs mt-1">Second order</p>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Strategies Tab */}
        <TabsContent value="strategies" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((strategy, i) => (
              <Card key={i} className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <CardDescription>{strategy.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Max Profit:</span>
                    <span className="text-[#00FF94]">{strategy.max_profit}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Max Loss:</span>
                    <span className="text-[#FF0055]">{strategy.max_loss}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#A1A1AA]">Best For:</span>
                    <span className="text-white">{strategy.best_for}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Warning */}
      <Card className="bg-[#FFB800]/10 border-[#FFB800]/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-[#FFB800] flex-shrink-0" />
            <div>
              <h4 className="font-bold text-[#FFB800]">Options Trading Risk</h4>
              <p className="text-sm text-[#A1A1AA]">
                Options are complex instruments. You can lose 100% of your premium. Prices shown are simulated.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OptionsTrading;
