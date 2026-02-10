import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { motion } from 'framer-motion';
import {
  Users, TrendingUp, Trophy, Star, UserPlus, UserMinus, Settings2,
  DollarSign, Percent, Target, History, RefreshCw, Search, Filter,
  ChevronRight, Award, Zap, Shield
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';

const CopyTrading = ({ embedded = false }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [following, setFollowing] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('leaderboard');
  const [timeframe, setTimeframe] = useState('30d');
  const [sortBy, setSortBy] = useState('roi');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTrader, setSelectedTrader] = useState(null);
  const [copyAmount, setCopyAmount] = useState(100);
  const [copyPercentage, setCopyPercentage] = useState(100);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [leaderboardRes, followingRes, statsRes] = await Promise.all([
        api.get(`/copy-trading/leaderboard?timeframe=${timeframe}&sort_by=${sortBy}`).catch(() => ({ data: { leaderboard: [] } })),
        api.get('/copy-trading/following').catch(() => ({ data: { following: [] } })),
        api.get('/copy-trading/stats').catch(() => ({ data: {} }))
      ]);

      setLeaderboard(leaderboardRes.data.leaderboard || []);
      setFollowing(followingRes.data.following || []);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error loading copy trading data:', error);
    } finally {
      setLoading(false);
    }
  }, [timeframe, sortBy]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFollow = async (trader) => {
    if (copyAmount < (trader.min_copy_amount || 50)) {
      toast.error(`Minimum copy amount is $${trader.min_copy_amount || 50}`);
      return;
    }

    const loadingToast = toast.loading(`Following ${trader.display_name}...`);
    try {
      await api.post('/copy-trading/follow', {
        trader_id: trader.trader_id,
        copy_amount: copyAmount,
        copy_percentage: copyPercentage
      });
      toast.dismiss(loadingToast);
      toast.success(`Now copying ${trader.display_name}!`, {
        description: `Allocating $${copyAmount} at ${copyPercentage}%`
      });
      setSelectedTrader(null);
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to follow trader', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  const handleUnfollow = async (traderId, traderName) => {
    if (!window.confirm(`Stop copying ${traderName}?`)) return;

    const loadingToast = toast.loading('Unfollowing...');
    try {
      await api.post(`/copy-trading/unfollow/${traderId}`);
      toast.dismiss(loadingToast);
      toast.success('Unfollowed successfully');
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to unfollow');
    }
  };

  const getRankBadge = (index) => {
    if (index === 0) return <Badge className="bg-[#FFD700] text-black">🥇 #1</Badge>;
    if (index === 1) return <Badge className="bg-[#C0C0C0] text-black">🥈 #2</Badge>;
    if (index === 2) return <Badge className="bg-[#CD7F32] text-black">🥉 #3</Badge>;
    return <Badge variant="outline" className="border-[#1F1F1F]">#{index + 1}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Copy Trading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="copy-trading-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Users size={40} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Copy</span> Trading
          </h1>
          <p className="text-[#A1A1AA]">
            Follow successful traders and automatically copy their trades
          </p>
        </div>
        <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]" data-testid="refresh-btn">
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Users size={20} className="text-[#9D00FF]" />
                <span className="text-sm text-[#A1A1AA]">Following</span>
              </div>
              <div className="text-3xl font-data font-bold text-white">
                {stats.traders_following || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign size={20} className="text-[#00FF94]" />
                <span className="text-sm text-[#A1A1AA]">Allocated</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#00FF94]">
                ${stats.total_allocated || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp size={20} className="text-[#007AFF]" />
                <span className="text-sm text-[#A1A1AA]">Total Profit</span>
              </div>
              <div className={`text-3xl font-data font-bold ${stats.total_profit >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                ${stats.total_profit || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Zap size={20} className="text-[#FFB800]" />
                <span className="text-sm text-[#A1A1AA]">Trades Copied</span>
              </div>
              <div className="text-3xl font-data font-bold text-white">
                {stats.total_trades_copied || 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="leaderboard" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Trophy size={16} className="mr-2" />
            Leaderboard
          </TabsTrigger>
          <TabsTrigger value="following" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Users size={16} className="mr-2" />
            Following ({following.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <History size={16} className="mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-4 items-center">
            <Select value={timeframe} onValueChange={setTimeframe}>
              <SelectTrigger className="w-32 bg-[#121212] border-[#1F1F1F]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="30d">30 Days</SelectItem>
                <SelectItem value="90d">90 Days</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40 bg-[#121212] border-[#1F1F1F]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                <SelectItem value="roi">ROI</SelectItem>
                <SelectItem value="win_rate">Win Rate</SelectItem>
                <SelectItem value="total_trades">Total Trades</SelectItem>
                <SelectItem value="copiers">Copiers</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Trader Cards */}
          <div className="grid gap-4">
            {leaderboard.map((trader, index) => (
              <motion.div
                key={trader.trader_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-colors" data-testid={`trader-${trader.trader_id}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4 flex-1">
                        {/* Rank Badge */}
                        <div className="flex flex-col items-center gap-2">
                          {getRankBadge(index)}
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#9D00FF]/30 to-[#00FF94]/30 flex items-center justify-center border border-[#9D00FF]/50">
                            <span className="text-lg font-bold text-white">{trader.display_name?.[0] || 'T'}</span>
                          </div>
                        </div>

                        {/* Trader Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold text-white text-lg">{trader.display_name}</h3>
                            {trader.stats?.roi > 100 && <Star size={16} className="text-[#FFD700]" fill="#FFD700" />}
                          </div>
                          <p className="text-sm text-[#A1A1AA] line-clamp-2 mb-3">{trader.bio}</p>

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            <div>
                              <p className="text-xs text-[#A1A1AA]">ROI</p>
                              <p className={`font-data font-bold ${trader.stats?.roi >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                                {trader.stats?.roi >= 0 ? '+' : ''}{trader.stats?.roi?.toFixed(1)}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA]">Win Rate</p>
                              <p className="font-data font-bold text-white">{trader.stats?.win_rate}%</p>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA]">Trades</p>
                              <p className="font-data font-bold text-white">{trader.stats?.total_trades}</p>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA]">Copiers</p>
                              <p className="font-data font-bold text-[#9D00FF]">{trader.copiers}</p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Action Button */}
                      <div className="flex flex-col gap-2">
                        <Button
                          onClick={() => setSelectedTrader(trader)}
                          className="bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                          data-testid={`copy-${trader.trader_id}`}
                        >
                          <UserPlus size={16} className="mr-2" />
                          Copy
                        </Button>
                        <span className="text-xs text-[#A1A1AA] text-center">
                          {trader.profit_share_pct}% profit share
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Following Tab */}
        <TabsContent value="following" className="space-y-4">
          {following.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <Users size={48} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
                <p className="text-[#A1A1AA] mb-4">You're not following any traders yet</p>
                <Button onClick={() => setActiveTab('leaderboard')} className="bg-[#9D00FF]">
                  Browse Traders
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {following.map((rel) => (
                <Card key={rel.relationship_id} className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`following-${rel.trader_id}`}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#9D00FF]/20 flex items-center justify-center">
                          <span className="font-bold text-[#9D00FF]">{rel.trader_name?.[0] || 'T'}</span>
                        </div>
                        <div>
                          <h3 className="font-bold text-white">{rel.trader_name || rel.trader_id}</h3>
                          <div className="flex items-center gap-4 mt-1 text-sm text-[#A1A1AA]">
                            <span>Allocated: ${rel.copy_amount}</span>
                            <span>Copy: {rel.copy_percentage}%</span>
                            <span>P/L: ${rel.total_profit || 0}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={rel.enabled !== false}
                          onCheckedChange={() => {}}
                          data-testid={`toggle-${rel.trader_id}`}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleUnfollow(rel.trader_id, rel.trader_name)}
                          className="text-[#FF0055] hover:bg-[#FF0055]/10"
                        >
                          <UserMinus size={16} />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardContent className="py-12 text-center">
              <History size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
              <p className="text-[#A1A1AA]">No copied trades yet</p>
              <p className="text-sm text-[#666] mt-2">Start following traders to see your copy history</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Copy Modal */}
      {selectedTrader && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedTrader(null)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-6 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
            data-testid="copy-modal"
          >
            <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
              <UserPlus className="text-[#00FF94]" />
              Copy {selectedTrader.display_name}
            </h2>
            <p className="text-[#A1A1AA] text-sm mb-6">{selectedTrader.bio}</p>

            <div className="space-y-6">
              <div>
                <label className="text-sm text-[#A1A1AA] mb-2 block">Copy Amount (USD)</label>
                <Input
                  type="number"
                  value={copyAmount}
                  onChange={(e) => setCopyAmount(parseFloat(e.target.value) || 0)}
                  className="bg-[#121212] border-[#1F1F1F]"
                  placeholder="100"
                />
                <p className="text-xs text-[#666] mt-1">Min: ${selectedTrader.min_copy_amount || 50}</p>
              </div>

              <div>
                <label className="text-sm text-[#A1A1AA] mb-2 block">
                  Copy Percentage: {copyPercentage}%
                </label>
                <Slider
                  value={[copyPercentage]}
                  onValueChange={([val]) => setCopyPercentage(val)}
                  min={10}
                  max={100}
                  step={10}
                  className="py-4"
                />
                <p className="text-xs text-[#666]">Copy {copyPercentage}% of each trade proportionally</p>
              </div>

              <div className="p-4 bg-[#9D00FF]/10 border border-[#9D00FF]/30 rounded-lg">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[#A1A1AA]">Profit Share:</span>
                  <span className="text-white">{selectedTrader.profit_share_pct}%</span>
                </div>
                <p className="text-xs text-[#A1A1AA]">
                  You keep {100 - selectedTrader.profit_share_pct}% of profits from copied trades
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => handleFollow(selectedTrader)}
                  className="flex-1 bg-[#00FF94] hover:bg-[#00FF94]/80 text-black font-bold"
                >
                  Start Copying
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedTrader(null)}
                  className="border-[#1F1F1F]"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Info Card */}
      <Card className="bg-[#9D00FF]/10 border-[#9D00FF]/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="text-[#9D00FF] flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-[#9D00FF] mb-1">How Copy Trading Works</h4>
              <p className="text-sm text-[#A1A1AA]">
                When you follow a trader, their trades are automatically copied to your account proportionally. 
                Set your copy amount and percentage to control risk. You can stop copying at any time.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CopyTrading;
