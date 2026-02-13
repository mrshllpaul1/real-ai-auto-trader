import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { 
  Wallet, TrendingUp, TrendingDown, RefreshCw, Settings, X,
  Target, Shield, DollarSign, Activity, AlertTriangle, Check,
  Edit2, Lock, ArrowUpRight, ArrowDownRight, Zap, Clock,
  BarChart3, Percent, Crosshair
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const PositionManagement = ({ embedded = false }) => {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingPosition, setEditingPosition] = useState(null);
  const [editValues, setEditValues] = useState({ stop_loss: '', take_profit: '' });
  const [closingPosition, setClosingPosition] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load from Kraken spot balance and pairs data (for 24h change)
      const [spotBalanceRes, pairsRes, trailingRes, partialRes] = await Promise.all([
        api.get('/spot/balance').catch(() => ({ data: { holdings: [] } })),
        api.get('/spot/pairs').catch(() => ({ data: { pairs: [] } })),
        api.get('/automation/trailing-stop/positions').catch(() => ({ data: { positions: [] } })),
        api.get('/automation/partial-tp/positions').catch(() => ({ data: { positions: [] } }))
      ]);
      
      // Create a map of symbol to 24h change from pairs data
      const pairsMap = new Map();
      (pairsRes.data?.pairs || []).forEach(pair => {
        pairsMap.set(pair.symbol, pair.change_24h || 0);
      });
      
      // Transform Kraken holdings to position format
      // Use real entry price data if available, otherwise use 24h P&L
      const krakenPositions = (spotBalanceRes.data?.holdings || [])
        .filter(h => h.usd_value > 1) // Filter out dust
        .map(holding => {
          // Check if we have real entry price data from tracking
          const hasRealEntry = holding.has_entry_price && holding.entry_price;
          
          let entryPrice, pnl, pnlPct;
          
          if (hasRealEntry) {
            // Use actual tracked entry price
            entryPrice = holding.entry_price;
            pnl = holding.unrealized_pnl || 0;
            pnlPct = holding.pnl_percent || 0;
          } else {
            // Fallback to 24h change calculation
            const change24h = pairsMap.get(holding.symbol) || 0;
            entryPrice = change24h !== 0 
              ? holding.price / (1 + change24h / 100)
              : holding.price;
            pnl = holding.usd_value * (change24h / 100);
            pnlPct = change24h;
          }
          
          return {
            position_id: holding.symbol,
            coin_id: holding.symbol,
            symbol: holding.symbol,
            name: holding.name,
            side: 'long',
            quantity: holding.amount,
            entry_price: entryPrice,
            current_price: holding.price,
            usd_value: holding.usd_value,
            pnl: pnl,
            pnl_pct: pnlPct,
            status: 'open',
            kraken_currency: holding.kraken_currency,
            has_real_entry: hasRealEntry,
            is_24h_data: !hasRealEntry,
            cost_basis: holding.cost_basis,
            realized_pnl: holding.realized_pnl || 0,
            total_buys: holding.total_buys || 0,
            total_sells: holding.total_sells || 0
          };
        });
      
      const mergedPositions = mergePositionData(
        krakenPositions,
        trailingRes.data?.positions || [],
        partialRes.data?.positions || []
      );
      
      setPositions(mergedPositions);
    } catch (error) {
      console.error('Error loading positions:', error);
      toast.error('Failed to load positions');
    } finally {
      setLoading(false);
    }
  }, []);

  const mergePositionData = (base, trailing, partial) => {
    const positionMap = new Map();
    
    base.forEach(pos => {
      positionMap.set(pos.position_id || pos.coin_id, { ...pos });
    });
    
    trailing.forEach(t => {
      const key = t.position_id || t.coin_id;
      if (positionMap.has(key)) {
        positionMap.set(key, { ...positionMap.get(key), ...t, trailing_data: t });
      } else {
        positionMap.set(key, { ...t, trailing_data: t });
      }
    });
    
    partial.forEach(p => {
      const key = p.position_id || p.coin_id;
      if (positionMap.has(key)) {
        positionMap.set(key, { ...positionMap.get(key), ...p, partial_tp_data: p });
      } else {
        positionMap.set(key, { ...p, partial_tp_data: p });
      }
    });
    
    return Array.from(positionMap.values());
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleUpdateLevels = async (positionId) => {
    try {
      const updates = {};
      if (editValues.stop_loss) updates.stop_loss_price = parseFloat(editValues.stop_loss);
      if (editValues.take_profit) updates.take_profit_price = parseFloat(editValues.take_profit);
      
      if (Object.keys(updates).length === 0) {
        toast.error('Please enter at least one value to update');
        return;
      }
      
      await api.post('/automation/update-levels', {
        position_id: positionId,
        ...updates
      });
      
      toast.success('Position levels updated');
      setEditingPosition(null);
      setEditValues({ stop_loss: '', take_profit: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update levels');
    }
  };

  const handleClosePosition = async (positionId, coinId) => {
    setClosingPosition(positionId);
    try {
      await api.post('/isolated-portfolio/close-position', {
        position_id: positionId,
        exit_price: 0,
        reason: 'manual_close'
      });
      
      toast.success(`${coinId?.toUpperCase()} position closed`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to close position');
    } finally {
      setClosingPosition(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#050505]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Positions...</p>
        </div>
      </div>
    );
  }

  const totalValue = positions.reduce((sum, p) => sum + (p.usd_value || p.current_value || p.amount_usd || 0), 0);
  const totalPnl = positions.reduce((sum, p) => sum + (p.pnl || p.pnl_usd || 0), 0);
  const totalPnlPct = totalValue > 0 ? (totalPnl / (totalValue - totalPnl)) * 100 : 0;
  const profitableCount = positions.filter(p => (p.pnl_pct || 0) > 0).length;

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="position-management-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/20 border border-[#9D00FF]/30">
                <Wallet size={32} className="text-[#9D00FF]" />
              </div>
              <span className="text-white">Position</span>
              <span className="bg-gradient-to-r from-[#9D00FF] to-[#00FF94] bg-clip-text text-transparent">Manager</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Monitor and manage your AI trading positions with precision
            </p>
          </div>
          <Button
            onClick={loadData}
            variant="outline"
            className="border-[#1F1F1F] hover:border-[#9D00FF]/50 hover:bg-[#9D00FF]/10"
            data-testid="refresh-btn"
          >
            <RefreshCw size={16} className="mr-2" />
            Refresh
          </Button>
        </div>
      </motion.div>

      {/* Portfolio Summary Cards */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
          <div className="absolute top-0 right-0 w-20 h-20 bg-[#9D00FF]/10 rounded-full blur-2xl" />
          <CardContent className="p-4 relative">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={18} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Open Positions</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">{positions.length}</div>
            <p className="text-xs text-[#A1A1AA] mt-1">{profitableCount} profitable</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
          <div className="absolute top-0 right-0 w-20 h-20 bg-[#00FF94]/10 rounded-full blur-2xl" />
          <CardContent className="p-4 relative">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Total Value</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">${totalValue.toFixed(2)}</div>
            <p className="text-xs text-[#A1A1AA] mt-1">across all positions</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
          <div className={`absolute top-0 right-0 w-20 h-20 ${totalPnl >= 0 ? 'bg-[#00FF94]/10' : 'bg-[#FF0055]/10'} rounded-full blur-2xl`} />
          <CardContent className="p-4 relative">
            <div className="flex items-center gap-2 mb-2">
              {totalPnl >= 0 ? (
                <TrendingUp size={18} className="text-[#00FF94]" />
              ) : (
                <TrendingDown size={18} className="text-[#FF0055]" />
              )}
              <span className="text-sm text-[#A1A1AA]">Total P&L</span>
            </div>
            <div className={`text-3xl font-data font-bold ${totalPnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}
            </div>
            <p className={`text-xs mt-1 ${totalPnlPct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#111] border-[#1F1F1F] overflow-hidden relative">
          <div className="absolute top-0 right-0 w-20 h-20 bg-[#FFB800]/10 rounded-full blur-2xl" />
          <CardContent className="p-4 relative">
            <div className="flex items-center gap-2 mb-2">
              <Target size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Win Rate</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FFB800]">
              {positions.length > 0 ? ((profitableCount / positions.length) * 100).toFixed(0) : 0}%
            </div>
            <p className="text-xs text-[#A1A1AA] mt-1">{profitableCount}/{positions.length} positions</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Position Cards Grid */}
      {positions.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-[#1F1F1F] flex items-center justify-center">
            <Wallet size={40} className="text-[#A1A1AA]" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">No Open Positions</h3>
          <p className="text-[#A1A1AA] max-w-md mx-auto">
            Positions opened by the AI trader will appear here. Set your trading budget to get started.
          </p>
        </motion.div>
      ) : (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
        >
          {positions.map((pos, index) => {
            const pnlPct = pos.pnl_pct || 0;
            const pnlUsd = pos.pnl_usd || 0;
            const isProfit = pnlPct >= 0;
            const hasTrailingStop = pos.trailing_stop_active || pos.trailing_stop_price > 0;
            const partialTpTaken = pos.partial_tp_taken?.length || pos.levels_taken || 0;
            const isEditing = editingPosition !== null && editingPosition === (pos.position_id || pos.coin_id);
            const isClosing = closingPosition === pos.position_id;
            
            return (
              <motion.div
                key={pos.position_id || pos.coin_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={`bg-[#0A0A0A] border-[#1F1F1F] overflow-hidden hover:border-[#333] transition-all duration-300 ${
                  isProfit ? 'hover:shadow-[0_0_30px_rgba(0,255,148,0.1)]' : 'hover:shadow-[0_0_30px_rgba(255,0,85,0.1)]'
                }`}>
                  {/* Card Header with Coin Info */}
                  <div className={`p-4 border-b border-[#1F1F1F] bg-gradient-to-r ${
                    isProfit ? 'from-[#00FF94]/5 to-transparent' : 'from-[#FF0055]/5 to-transparent'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg ${
                          isProfit ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'
                        }`}>
                          {pos.coin_id?.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-white text-lg">{pos.coin_id?.toUpperCase()}</h3>
                            {pos.is_gem && (
                              <Badge className="bg-[#FFB800]/20 text-[#FFB800] text-xs">GEM</Badge>
                            )}
                          </div>
                          <p className="text-xs text-[#A1A1AA]">{pos.symbol}</p>
                        </div>
                      </div>
                      <div className={`flex items-center gap-1 px-3 py-1.5 rounded-full ${
                        isProfit ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'
                      }`}>
                        {isProfit ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                        <span className="font-data font-bold">{isProfit ? '+' : ''}{pnlPct.toFixed(2)}%</span>
                        <span className="text-xs opacity-70">24h</span>
                      </div>
                    </div>
                  </div>

                  <CardContent className="p-4 space-y-4">
                    {/* Position Value & P&L */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-[#111] border border-[#1F1F1F]">
                        <p className="text-xs text-[#A1A1AA] mb-1">Position Value</p>
                        <p className="text-xl font-data font-bold text-white">
                          ${(pos.usd_value || pos.current_value || pos.amount_usd || 0).toFixed(2)}
                        </p>
                      </div>
                      <div className={`p-3 rounded-lg border ${
                        isProfit ? 'bg-[#00FF94]/5 border-[#00FF94]/20' : 'bg-[#FF0055]/5 border-[#FF0055]/20'
                      }`}>
                        <p className="text-xs text-[#A1A1AA] mb-1">
                          {pos.has_real_entry ? 'Unrealized P&L' : '24h P&L'}
                        </p>
                        <p className={`text-xl font-data font-bold ${isProfit ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {isProfit ? '+' : ''}${(pos.pnl || pnlUsd || 0).toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {/* Entry & Current Price */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-[#A1A1AA] mb-1 flex items-center gap-1">
                          <Clock size={12} /> 
                          {pos.has_real_entry ? 'Entry Price' : 'Price 24h Ago'}
                          {pos.has_real_entry && (
                            <span className="ml-1 px-1 py-0.5 bg-green-500/20 text-green-400 text-[10px] rounded">
                              Tracked
                            </span>
                          )}
                        </p>
                        <p className="font-data text-white">${(pos?.entry_price ?? 0).toFixed(4)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-[#A1A1AA] mb-1 flex items-center gap-1">
                          <BarChart3 size={12} /> Current Price
                        </p>
                        <p className="font-data text-white">${(pos?.current_price ?? 0).toFixed(4) || 'N/A'}</p>
                      </div>
                    </div>

                    {/* Quantity */}
                    <div className="p-3 rounded-lg bg-[#111] border border-[#1F1F1F]">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-[#A1A1AA]">Quantity</span>
                        <span className="font-data text-white">{(pos?.quantity ?? 0).toFixed(6)}</span>
                      </div>
                    </div>

                    {/* Risk Management Badges */}
                    <div className="flex flex-wrap gap-2">
                      {hasTrailingStop && (
                        <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] border border-[#9D00FF]/30">
                          <Zap size={12} className="mr-1" /> Trailing Stop
                        </Badge>
                      )}
                      {partialTpTaken > 0 && (
                        <Badge className="bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/30">
                          <Target size={12} className="mr-1" /> {partialTpTaken} TP Taken
                        </Badge>
                      )}
                      {pos.stop_at_breakeven && (
                        <Badge className="bg-[#007AFF]/20 text-[#007AFF] border border-[#007AFF]/30">
                          <Lock size={12} className="mr-1" /> Breakeven
                        </Badge>
                      )}
                    </div>

                    {/* Stop Loss & Take Profit */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg bg-[#FF0055]/5 border border-[#FF0055]/20">
                        <div className="flex items-center gap-1 mb-1">
                          <Shield size={12} className="text-[#FF0055]" />
                          <span className="text-xs text-[#FF0055]">Stop Loss</span>
                        </div>
                        <p className="font-data text-[#FF0055] font-bold">
                          ${(pos.trailing_stop_price || pos.stop_loss_price || 0).toFixed(4)}
                        </p>
                        {hasTrailingStop && (
                          <p className="text-xs text-[#A1A1AA] mt-1">Trailing active</p>
                        )}
                      </div>
                      <div className="p-3 rounded-lg bg-[#00FF94]/5 border border-[#00FF94]/20">
                        <div className="flex items-center gap-1 mb-1">
                          <Target size={12} className="text-[#00FF94]" />
                          <span className="text-xs text-[#00FF94]">Take Profit</span>
                        </div>
                        <p className="font-data text-[#00FF94] font-bold">
                          ${(pos?.take_profit_price ?? 0).toFixed(4) || 'N/A'}
                        </p>
                      </div>
                    </div>

                    {/* Trailing Stop Details */}
                    {hasTrailingStop && pos.highest_price && (
                      <div className="p-3 rounded-lg bg-[#9D00FF]/5 border border-[#9D00FF]/20">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-[#A1A1AA]">Highest Price</span>
                          <span className="text-[#9D00FF] font-data">${(pos?.highest_price ?? 0).toFixed(4)}</span>
                        </div>
                        {pos.distance_to_trailing_stop && (
                          <div className="flex items-center justify-between text-sm mt-2">
                            <span className="text-[#A1A1AA]">Distance to Stop</span>
                            <span className="text-white font-data">{(pos?.distance_to_trailing_stop ?? 0).toFixed(2)}%</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Partial TP Progress */}
                    {(partialTpTaken > 0 || pos.next_level) && (
                      <div className="p-3 rounded-lg bg-[#00FF94]/5 border border-[#00FF94]/20">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-[#00FF94]">Partial Take Profit Progress</span>
                          <span className="text-xs text-white">{partialTpTaken}/3</span>
                        </div>
                        <Progress value={(partialTpTaken / 3) * 100} className="h-2 bg-[#1F1F1F]" />
                        {pos.next_level && (
                          <p className="text-xs text-[#A1A1AA] mt-2">
                            Next: {pos.next_level.close_pct}% at {pos.next_level.at_profit_pct}% profit
                          </p>
                        )}
                      </div>
                    )}

                    {/* Edit Mode */}
                    <AnimatePresence>
                      {isEditing && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="p-4 rounded-lg bg-[#111] border border-[#1F1F1F] space-y-3"
                        >
                          <p className="text-sm text-white font-medium">Edit Position Levels</p>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-xs text-[#A1A1AA] mb-1 block">Stop-Loss Price</label>
                              <Input
                                type="number"
                                step="0.0001"
                                placeholder={pos.stop_loss_price?.toString() || '0'}
                                value={editValues.stop_loss}
                                onChange={(e) => setEditValues({ ...editValues, stop_loss: e.target.value })}
                                className="bg-[#0A0A0A] border-[#1F1F1F]"
                                data-testid={`edit-sl-${pos.position_id || pos.coin_id}`}
                              />
                            </div>
                            <div>
                              <label className="text-xs text-[#A1A1AA] mb-1 block">Take-Profit Price</label>
                              <Input
                                type="number"
                                step="0.0001"
                                placeholder={pos.take_profit_price?.toString() || '0'}
                                value={editValues.take_profit}
                                onChange={(e) => setEditValues({ ...editValues, take_profit: e.target.value })}
                                className="bg-[#0A0A0A] border-[#1F1F1F]"
                                data-testid={`edit-tp-${pos.position_id || pos.coin_id}`}
                              />
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => handleUpdateLevels(pos.position_id || pos.coin_id)}
                              size="sm"
                              className="flex-1 bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                              data-testid={`save-levels-${pos.position_id || pos.coin_id}`}
                            >
                              <Check size={14} className="mr-1" /> Save
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditingPosition(null);
                                setEditValues({ stop_loss: '', take_profit: '' });
                              }}
                              className="flex-1 border-[#1F1F1F]"
                            >
                              Cancel
                            </Button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Action Buttons */}
                    {!isEditing && (
                      <div className="flex gap-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingPosition(pos.position_id || pos.coin_id);
                            setEditValues({
                              stop_loss: pos.stop_loss_price?.toString() || '',
                              take_profit: pos.take_profit_price?.toString() || ''
                            });
                          }}
                          className="flex-1 border-[#1F1F1F] hover:border-[#9D00FF]/50 hover:bg-[#9D00FF]/10"
                          data-testid={`edit-btn-${pos.position_id || pos.coin_id}`}
                        >
                          <Edit2 size={14} className="mr-1" /> Edit Levels
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleClosePosition(pos.position_id || pos.coin_id, pos.coin_id)}
                          disabled={isClosing}
                          className="flex-1 border-[#FF0055]/30 text-[#FF0055] hover:bg-[#FF0055]/10"
                          data-testid={`close-btn-${pos.position_id || pos.coin_id}`}
                        >
                          {isClosing ? (
                            <RefreshCw size={14} className="mr-1 animate-spin" />
                          ) : (
                            <X size={14} className="mr-1" />
                          )}
                          Close
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
};

export default PositionManagement;
