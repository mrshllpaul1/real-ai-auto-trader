import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Globe, Plus, Sparkles, TrendingUp, Search, Loader2, 
  ChevronDown, ChevronUp, Bot, User, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const CoinUniverseManager = () => {
  const [stats, setStats] = useState(null);
  const [discoveredCoins, setDiscoveredCoins] = useState([]);
  const [gemCandidates, setGemCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [adding, setAdding] = useState(false);
  
  // Add coin form
  const [newCoin, setNewCoin] = useState({
    coin_id: '',
    symbol: '',
    reason: '',
    potential_score: 75
  });

  const loadData = useCallback(async () => {
    try {
      const [statsRes, discoveredRes, gemsRes] = await Promise.all([
        api.get('/ai-universe/stats'),
        api.get('/ai-universe/coins/discovered'),
        api.get('/ai-universe/coins/gems')
      ]);
      setStats(statsRes.data);
      setDiscoveredCoins(discoveredRes.data.coins || []);
      setGemCandidates(gemsRes.data.coins || []);
    } catch (error) {
      console.error('Load universe data error:', error);
      toast.error('Failed to load coin universe data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddCoin = async () => {
    if (!newCoin.coin_id || !newCoin.symbol) {
      toast.error('Coin ID and Symbol are required');
      return;
    }

    setAdding(true);
    try {
      await api.post('/ai-universe/coins/ai-discover', {
        coin_id: newCoin.coin_id.toLowerCase().replace(/\s+/g, '-'),
        symbol: newCoin.symbol.toUpperCase(),
        reason: newCoin.reason || 'Manually discovered potential gem',
        potential_score: newCoin.potential_score
      });
      
      toast.success(`${newCoin.symbol} added to coin universe!`);
      setNewCoin({ coin_id: '', symbol: '', reason: '', potential_score: 75 });
      setShowAddForm(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add coin');
    } finally {
      setAdding(false);
    }
  };

  const handleDeactivate = async (coinId) => {
    try {
      await api.delete(`/ai-universe/coin/${coinId}`, {
        params: { reason: 'User removed' }
      });
      toast.success(`Removed ${coinId} from universe`);
      loadData();
    } catch (error) {
      toast.error('Failed to remove coin');
    }
  };

  const categoryColors = {
    major: 'bg-[#00FF94]/20 text-[#00FF94]',
    large: 'bg-[#007AFF]/20 text-[#007AFF]',
    mid: 'bg-[#9D00FF]/20 text-[#9D00FF]',
    defi: 'bg-[#FF9500]/20 text-[#FF9500]',
    gaming: 'bg-pink-500/20 text-pink-400',
    ai: 'bg-cyan-500/20 text-cyan-400',
    meme: 'bg-yellow-500/20 text-yellow-400',
    new: 'bg-emerald-500/20 text-emerald-400',
    discovered: 'bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 text-[#00FF94]'
  };

  if (loading) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="animate-spin mr-2" />
          Loading universe...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Globe className="text-[#9D00FF]" size={20} />
            AI Coin Universe
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-[#A1A1AA]"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#00FF94]">{stats?.total_coins || 0}</div>
            <div className="text-xs text-[#71717A]">Total Coins</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#9D00FF]">{stats?.ai_discovered || 0}</div>
            <div className="text-xs text-[#71717A]">AI Discovered</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#FF9500]">{gemCandidates.length}</div>
            <div className="text-xs text-[#71717A]">Gem Candidates</div>
          </div>
        </div>

        {/* Categories breakdown */}
        {stats?.by_category && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {Object.entries(stats.by_category).map(([cat, count]) => (
              <Badge 
                key={cat} 
                variant="outline" 
                className={`text-xs ${categoryColors[cat] || 'bg-[#1F1F1F] text-[#A1A1AA]'}`}
              >
                {cat}: {count}
              </Badge>
            ))}
          </div>
        )}

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              {/* AI Discovered Coins */}
              {discoveredCoins.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Bot size={14} className="text-[#9D00FF]" />
                    AI Discovered Coins
                  </h4>
                  <div className="space-y-2">
                    {discoveredCoins.map((coin) => (
                      <div 
                        key={coin.coin_id}
                        className="flex items-center justify-between p-2 rounded-lg bg-[#1F1F1F]/50 border border-[#9D00FF]/20"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#9D00FF] to-[#00FF94] flex items-center justify-center text-xs font-bold">
                            {coin.symbol?.slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-sm">{coin.symbol}</div>
                            <div className="text-xs text-[#71717A]">{coin.coin_id}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {coin.metadata?.potential_score && (
                            <Badge className="bg-[#00FF94]/20 text-[#00FF94] text-xs">
                              {coin.metadata.potential_score}% potential
                            </Badge>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeactivate(coin.coin_id)}
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 w-7 p-0"
                          >
                            <X size={14} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add New Coin Form */}
              {showAddForm ? (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-lg bg-[#1F1F1F]/50 border border-[#9D00FF]/30 space-y-3"
                >
                  <h4 className="font-medium text-sm flex items-center gap-2">
                    <Sparkles className="text-[#9D00FF]" size={14} />
                    Add New Coin to Universe
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      placeholder="Coin ID (e.g., kaspa)"
                      value={newCoin.coin_id}
                      onChange={(e) => setNewCoin({...newCoin, coin_id: e.target.value})}
                      className="bg-[#0A0A0A] border-[#2F2F2F] text-sm"
                    />
                    <Input
                      placeholder="Symbol (e.g., KAS)"
                      value={newCoin.symbol}
                      onChange={(e) => setNewCoin({...newCoin, symbol: e.target.value})}
                      className="bg-[#0A0A0A] border-[#2F2F2F] text-sm"
                    />
                  </div>
                  <Input
                    placeholder="Why is this coin promising?"
                    value={newCoin.reason}
                    onChange={(e) => setNewCoin({...newCoin, reason: e.target.value})}
                    className="bg-[#0A0A0A] border-[#2F2F2F] text-sm"
                  />
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[#71717A]">Potential:</span>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={newCoin.potential_score}
                      onChange={(e) => setNewCoin({...newCoin, potential_score: parseInt(e.target.value)})}
                      className="flex-1 accent-[#9D00FF]"
                    />
                    <span className="text-sm font-medium text-[#9D00FF]">{newCoin.potential_score}%</span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleAddCoin}
                      disabled={adding}
                      className="flex-1 bg-[#9D00FF] hover:bg-[#7A00CC]"
                    >
                      {adding ? <Loader2 className="animate-spin mr-2" size={14} /> : <Plus size={14} className="mr-2" />}
                      Add Coin
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowAddForm(false)}
                      className="border-[#2F2F2F]"
                    >
                      Cancel
                    </Button>
                  </div>
                </motion.div>
              ) : (
                <Button
                  onClick={() => setShowAddForm(true)}
                  variant="outline"
                  className="w-full border-[#9D00FF]/30 text-[#9D00FF] hover:bg-[#9D00FF]/10"
                >
                  <Plus size={16} className="mr-2" />
                  Add Coin to Universe
                </Button>
              )}

              {/* Top Gem Candidates Preview */}
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <TrendingUp size={14} className="text-[#00FF94]" />
                  Top Gem Candidates ({gemCandidates.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {gemCandidates.slice(0, 12).map((coin) => (
                    <Badge 
                      key={coin}
                      variant="outline"
                      className="bg-[#1F1F1F]/50 text-[#E4E4E7] border-[#2F2F2F]"
                    >
                      {coin}
                    </Badge>
                  ))}
                  {gemCandidates.length > 12 && (
                    <Badge variant="outline" className="text-[#71717A] border-[#2F2F2F]">
                      +{gemCandidates.length - 12} more
                    </Badge>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};

export default CoinUniverseManager;
