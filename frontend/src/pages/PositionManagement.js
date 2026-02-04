import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { 
  Wallet, TrendingUp, TrendingDown, RefreshCw, Settings, X,
  Target, Shield, DollarSign, Activity, AlertTriangle, Check,
  ChevronDown, ChevronUp, Edit2, Trash2, Lock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const PositionManagement = () => {
  const [positions, setPositions] = useState([]);
  const [trailingData, setTrailingData] = useState([]);
  const [partialTpData, setPartialTpData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPosition, setExpandedPosition] = useState(null);
  const [editingPosition, setEditingPosition] = useState(null);
  const [editValues, setEditValues] = useState({ stop_loss: '', take_profit: '' });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [positionsRes, trailingRes, partialRes] = await Promise.all([
        api.get('/isolated-portfolio/positions').catch(() => ({ data: { positions: [] } })),
        api.get('/automation/trailing-stop/positions').catch(() => ({ data: { positions: [] } })),
        api.get('/automation/partial-tp/positions').catch(() => ({ data: { positions: [] } }))
      ]);
      
      // Merge data from all sources
      const mergedPositions = mergePositionData(
        positionsRes.data?.positions || [],
        trailingRes.data?.positions || [],
        partialRes.data?.positions || []
      );
      
      setPositions(mergedPositions);
      setTrailingData(trailingRes.data?.positions || []);
      setPartialTpData(partialRes.data?.positions || []);
    } catch (error) {
      console.error('Error loading positions:', error);
      toast.error('Failed to load positions');
    } finally {
      setLoading(false);
    }
  }, []);

  const mergePositionData = (base, trailing, partial) => {
    const positionMap = new Map();
    
    // Start with base positions
    base.forEach(pos => {
      positionMap.set(pos.position_id || pos.coin_id, { ...pos });
    });
    
    // Merge trailing data
    trailing.forEach(t => {
      const key = t.position_id || t.coin_id;
      if (positionMap.has(key)) {
        positionMap.set(key, { ...positionMap.get(key), ...t, trailing_data: t });
      } else {
        positionMap.set(key, { ...t, trailing_data: t });
      }
    });
    
    // Merge partial TP data
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
    if (!window.confirm(`Are you sure you want to close your ${coinId?.toUpperCase()} position?`)) {
      return;
    }
    
    try {
      await api.post('/isolated-portfolio/close-position', {
        position_id: positionId,
        reason: 'manual_close'
      });
      
      toast.success(`${coinId?.toUpperCase()} position closed`);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to close position');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Positions...</p>
        </div>
      </div>
    );
  }

  const totalValue = positions.reduce((sum, p) => sum + (p.current_value || p.amount_usd || 0), 0);
  const totalPnl = positions.reduce((sum, p) => sum + (p.pnl_usd || 0), 0);
  const profitableCount = positions.filter(p => (p.pnl_pct || 0) > 0).length;

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="position-management-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Wallet size={40} className="text-[#9D00FF]" />
            <span className="text-white">Position</span>
            <span className="text-[#9D00FF]">Management</span>
          </h1>
          <p className="text-[#A1A1AA]">
            Manage your AI trading positions, stops, and take-profits
          </p>
        </div>
        <Button
          onClick={loadData}
          variant="outline"
          className="border-[#1F1F1F]"
          data-testid="refresh-btn"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Summary Cards */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity size={18} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Open Positions</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">{positions.length}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign size={18} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Total Value</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">${totalValue.toFixed(2)}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
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
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Check size={18} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Profitable</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FFB800]">
              {profitableCount}/{positions.length}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Positions List */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Target className="text-[#FFB800]" />
              All Positions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <div className="text-center py-12 text-[#A1A1AA]">
                <Wallet size={48} className="mx-auto mb-4 opacity-50" />
                <p>No open positions</p>
                <p className="text-sm">Positions opened by AI will appear here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {positions.map((pos) => {
                  const isExpanded = expandedPosition === pos.position_id;
                  const isEditing = editingPosition === pos.position_id;
                  const pnlPct = pos.pnl_pct || 0;
                  const pnlUsd = pos.pnl_usd || 0;
                  const hasTrailingStop = pos.trailing_stop_active || pos.trailing_stop_price > 0;
                  const partialTpTaken = pos.partial_tp_taken?.length || pos.levels_taken || 0;
                  
                  return (
                    <motion.div
                      key={pos.position_id || pos.coin_id}
                      className="bg-[#121212] rounded-lg border border-[#1F1F1F] overflow-hidden"
                      layout
                    >
                      {/* Main Row */}
                      <div 
                        className="p-4 cursor-pointer hover:bg-[#1A1A1A] transition-colors"
                        onClick={() => setExpandedPosition(isExpanded ? null : pos.position_id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-white font-bold text-lg">{pos.coin_id?.toUpperCase()}</span>
                                {pos.is_gem && <Badge className="bg-[#FFB800]/20 text-[#FFB800]">💎 Gem</Badge>}
                                {hasTrailingStop && (
                                  <Badge className="bg-[#9D00FF]/20 text-[#9D00FF]">Trailing</Badge>
                                )}
                                {partialTpTaken > 0 && (
                                  <Badge className="bg-[#00FF94]/20 text-[#00FF94]">{partialTpTaken} TP</Badge>
                                )}
                                {pos.stop_at_breakeven && (
                                  <Badge className="bg-[#007AFF]/20 text-[#007AFF]">BE</Badge>
                                )}
                              </div>
                              <p className="text-sm text-[#A1A1AA]">
                                {pos.quantity?.toFixed(6)} @ ${pos.entry_price?.toFixed(4)}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <p className="text-white font-data">${(pos.current_value || pos.amount_usd || 0).toFixed(2)}</p>
                              <p className={`text-sm font-data ${pnlPct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}% (${pnlUsd >= 0 ? '+' : ''}{pnlUsd.toFixed(2)})
                              </p>
                            </div>
                            
                            {isExpanded ? <ChevronUp size={20} className="text-[#A1A1AA]" /> : <ChevronDown size={20} className="text-[#A1A1AA]" />}
                          </div>
                        </div>
                      </div>
                      
                      {/* Expanded Details */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-[#1F1F1F]"
                          >
                            <div className="p-4 space-y-4">
                              {/* Price Levels */}
                              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="p-3 bg-[#0A0A0A] rounded-lg">
                                  <p className="text-xs text-[#A1A1AA] mb-1">Entry Price</p>
                                  <p className="text-white font-data">${pos.entry_price?.toFixed(4)}</p>
                                </div>
                                <div className="p-3 bg-[#0A0A0A] rounded-lg">
                                  <p className="text-xs text-[#A1A1AA] mb-1">Current Price</p>
                                  <p className="text-white font-data">${pos.current_price?.toFixed(4) || 'N/A'}</p>
                                </div>
                                <div className="p-3 bg-[#0A0A0A] rounded-lg border border-[#FF0055]/30">
                                  <p className="text-xs text-[#FF0055] mb-1 flex items-center gap-1">
                                    <Shield size={12} /> Stop-Loss
                                  </p>
                                  <p className="text-[#FF0055] font-data">
                                    ${(pos.trailing_stop_price || pos.stop_loss_price || 0).toFixed(4)}
                                  </p>
                                  {hasTrailingStop && (
                                    <p className="text-xs text-[#A1A1AA]">Trailing active</p>
                                  )}
                                </div>
                                <div className="p-3 bg-[#0A0A0A] rounded-lg border border-[#00FF94]/30">
                                  <p className="text-xs text-[#00FF94] mb-1 flex items-center gap-1">
                                    <Target size={12} /> Take-Profit
                                  </p>
                                  <p className="text-[#00FF94] font-data">
                                    ${pos.take_profit_price?.toFixed(4) || 'N/A'}
                                  </p>
                                </div>
                              </div>
                              
                              {/* Trailing Stop Info */}
                              {hasTrailingStop && (
                                <div className="p-3 bg-[#9D00FF]/10 rounded-lg border border-[#9D00FF]/30">
                                  <p className="text-sm text-[#9D00FF] font-medium mb-2">📈 Trailing Stop Active</p>
                                  <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>
                                      <p className="text-[#A1A1AA]">Highest Price</p>
                                      <p className="text-white">${pos.highest_price?.toFixed(4)}</p>
                                    </div>
                                    <div>
                                      <p className="text-[#A1A1AA]">Trailing Stop</p>
                                      <p className="text-[#9D00FF]">${pos.trailing_stop_price?.toFixed(4)}</p>
                                    </div>
                                    <div>
                                      <p className="text-[#A1A1AA]">Distance</p>
                                      <p className="text-white">{pos.distance_to_trailing_stop?.toFixed(2)}%</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                              
                              {/* Partial TP Info */}
                              {(partialTpTaken > 0 || pos.next_level) && (
                                <div className="p-3 bg-[#00FF94]/10 rounded-lg border border-[#00FF94]/30">
                                  <p className="text-sm text-[#00FF94] font-medium mb-2">💰 Partial Take-Profit</p>
                                  <div className="flex items-center gap-4">
                                    <div>
                                      <p className="text-[#A1A1AA] text-sm">Levels Taken</p>
                                      <p className="text-white">{partialTpTaken} / 3</p>
                                    </div>
                                    {pos.next_level && (
                                      <div>
                                        <p className="text-[#A1A1AA] text-sm">Next Level</p>
                                        <p className="text-[#00FF94]">
                                          {pos.next_level.close_pct}% at {pos.next_level.at_profit_pct}% profit
                                          ({pos.next_level.distance_pct > 0 ? `${pos.next_level.distance_pct}% away` : 'Ready!'})
                                        </p>
                                      </div>
                                    )}
                                    {pos.stop_at_breakeven && (
                                      <Badge className="bg-[#007AFF]/20 text-[#007AFF]">
                                        <Lock size={12} className="mr-1" /> Stop at Breakeven
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              )}
                              
                              {/* Edit Section */}
                              {isEditing ? (
                                <div className="p-4 bg-[#0A0A0A] rounded-lg border border-[#1F1F1F]">
                                  <p className="text-white font-medium mb-3">Edit Position Levels</p>
                                  <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                      <label className="text-xs text-[#A1A1AA] mb-1 block">Stop-Loss Price</label>
                                      <Input
                                        type="number"
                                        placeholder={pos.stop_loss_price?.toString() || '0'}
                                        value={editValues.stop_loss}
                                        onChange={(e) => setEditValues({ ...editValues, stop_loss: e.target.value })}
                                        className="bg-[#121212] border-[#1F1F1F]"
                                      />
                                    </div>
                                    <div>
                                      <label className="text-xs text-[#A1A1AA] mb-1 block">Take-Profit Price</label>
                                      <Input
                                        type="number"
                                        placeholder={pos.take_profit_price?.toString() || '0'}
                                        value={editValues.take_profit}
                                        onChange={(e) => setEditValues({ ...editValues, take_profit: e.target.value })}
                                        className="bg-[#121212] border-[#1F1F1F]"
                                      />
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <Button
                                      onClick={() => handleUpdateLevels(pos.position_id)}
                                      className="bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                                    >
                                      <Check size={16} className="mr-2" /> Save
                                    </Button>
                                    <Button
                                      variant="outline"
                                      onClick={() => {
                                        setEditingPosition(null);
                                        setEditValues({ stop_loss: '', take_profit: '' });
                                      }}
                                      className="border-[#1F1F1F]"
                                    >
                                      Cancel
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex gap-2">
                                  <Button
                                    variant="outline"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setEditingPosition(pos.position_id);
                                      setEditValues({
                                        stop_loss: pos.stop_loss_price?.toString() || '',
                                        take_profit: pos.take_profit_price?.toString() || ''
                                      });
                                    }}
                                    className="border-[#1F1F1F]"
                                  >
                                    <Edit2 size={16} className="mr-2" /> Edit Levels
                                  </Button>
                                  <Button
                                    variant="outline"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleClosePosition(pos.position_id, pos.coin_id);
                                    }}
                                    className="border-[#FF0055]/50 text-[#FF0055] hover:bg-[#FF0055]/10"
                                  >
                                    <X size={16} className="mr-2" /> Close Position
                                  </Button>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default PositionManagement;
