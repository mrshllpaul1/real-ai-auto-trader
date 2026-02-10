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
import TradingPairSelector from '../components/TradingPairSelector';

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
    quantity: 1
  });

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
      toast.success('Option order placed!', {
        description: `${orderForm.option_type.toUpperCase()} ${orderForm.symbol} @ $${orderForm.strike_price}`
      });
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to place order');
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

  const filteredOptions = chain?.options?.filter(opt => opt.expiry === selectedExpiry) || [];

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
          <TradingPairSelector 
            value={`${selectedSymbol}/USD`} 
            onValueChange={(v) => setSelectedSymbol(v.replace('/USD', ''))}
            className="w-40"
          />
          <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
            <RefreshCw size={16} />
          </Button>
        </div>
      </motion.div>

      {/* Current Price Banner */}
      {chain && (
        <Card className="bg-gradient-to-r from-[#FF9500]/20 to-[#FF9500]/5 border-[#FF9500]/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[#A1A1AA]">{selectedSymbol} Current Price</span>
                <div className="text-3xl font-data font-bold text-white">
                  ${chain.current_price?.toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <span className="text-[#A1A1AA]">Implied Volatility</span>
                <div className="text-2xl font-data text-[#FF9500]">
                  {(chain.volatility * 100).toFixed(1)}%
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
          <TabsTrigger value="positions" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Positions ({positions.length})
          </TabsTrigger>
          <TabsTrigger value="strategies" className="data-[state=active]:bg-[#FF9500] data-[state=active]:text-black">
            Strategies
          </TabsTrigger>
        </TabsList>

        {/* Option Chain Tab */}
        <TabsContent value="chain" className="space-y-4">
          {/* Expiry Selector */}
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
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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

              <Button 
                onClick={handlePlaceOrder} 
                className={`w-full font-bold ${orderForm.option_type === 'call' ? 'bg-[#00FF94] text-black' : 'bg-[#FF0055] text-white'}`}
              >
                Buy {orderForm.option_type.toUpperCase()} Option
              </Button>
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
              {positions.map((pos) => (
                <Card key={pos.position_id} className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Badge className={pos.option_type === 'call' ? 'bg-[#00FF94] text-black' : 'bg-[#FF0055]'}>
                          {pos.option_type.toUpperCase()}
                        </Badge>
                        <div>
                          <h3 className="font-bold text-white">{pos.symbol} ${pos.strike_price}</h3>
                          <p className="text-sm text-[#A1A1AA]">Exp: {pos.expiry_date} ({pos.days_to_expiry}d)</p>
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
                    <div className="mt-3 pt-3 border-t border-[#1F1F1F] grid grid-cols-5 gap-4 text-center text-sm">
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
                  </CardContent>
                </Card>
              ))}
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
                Options are complex instruments. You can lose 100% of your premium. Prices are from live Kraken data.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OptionsTrading;
