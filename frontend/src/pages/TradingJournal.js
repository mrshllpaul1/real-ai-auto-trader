import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BookOpen, TrendingUp, TrendingDown, Calendar, Target, 
  Zap, Sparkles, BarChart3, Brain, Lightbulb, Filter
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const TradingJournal = () => {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    loadData();
  }, [selectedPeriod]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [entriesRes, statsRes, insightsRes, dailyRes] = await Promise.all([
        api.get('/journal/entries?limit=50'),
        api.get(`/journal/stats?days=${selectedPeriod}`),
        api.get(`/journal/ai-insights?days=${selectedPeriod}`),
        api.get('/journal/daily')
      ]);
      setEntries(entriesRes.data.entries || []);
      setStats(statsRes.data);
      setAiInsights(insightsRes.data);
      setDailySummary(dailyRes.data);
    } catch (error) {
      console.error('Error loading journal:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPnl = (pnl) => {
    if (!pnl) return '$0.00';
    const sign = pnl >= 0 ? '+' : '';
    return `${sign}$${pnl.toFixed(2)}`;
  };

  return (
    <div className="min-h-screen bg-[#000000] text-white p-4 md:p-8">
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <h1 className="text-4xl md:text-5xl font-bold mb-2 flex items-center gap-3">
          <BookOpen className="text-[#9D00FF]" />
          Trading Journal
        </h1>
        <p className="text-[#A1A1AA]">Track performance • Understand AI decisions • Learn from every trade</p>
      </motion.div>

      {/* Period Selector */}
      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm text-[#A1A1AA]">Period:</span>
        {[7, 30, 90].map(days => (
          <Button
            key={days}
            variant={selectedPeriod === days ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedPeriod(days)}
            className={selectedPeriod === days ? "bg-[#9D00FF]" : "border-[#333]"}
          >
            {days}d
          </Button>
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="entries">Trade Log</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                    <BarChart3 size={16} />
                    <span className="text-xs">Total Trades</span>
                  </div>
                  <div className="text-2xl font-bold">{stats?.total_trades || 0}</div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                    <TrendingUp size={16} />
                    <span className="text-xs">Total P/L</span>
                  </div>
                  <div className={`text-2xl font-bold ${(stats?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {formatPnl(stats?.total_pnl)}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                    <Target size={16} />
                    <span className="text-xs">Win Rate</span>
                  </div>
                  <div className={`text-2xl font-bold ${(stats?.win_rate || 0) >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {stats?.win_rate || 0}%
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
                    <Sparkles size={16} />
                    <span className="text-xs">Most Traded</span>
                  </div>
                  <div className="text-2xl font-bold text-[#FFD700]">
                    {stats?.most_traded_coin?.toUpperCase() || '-'}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Best/Worst Trades */}
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingUp className="text-[#00FF94]" />
                  Best Trade
                </CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.best_trade ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-bold">{stats.best_trade.coin_id?.toUpperCase()}</span>
                      <span className="text-[#A1A1AA] ml-2 text-sm">{stats.best_trade.date}</span>
                    </div>
                    <div className="text-[#00FF94] font-bold">
                      +${stats.best_trade.pnl_usd?.toFixed(2)} ({stats.best_trade.pnl_pct?.toFixed(1)}%)
                    </div>
                  </div>
                ) : (
                  <p className="text-[#A1A1AA]">No trades yet</p>
                )}
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingDown className="text-[#FF0055]" />
                  Worst Trade
                </CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.worst_trade ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-bold">{stats.worst_trade.coin_id?.toUpperCase()}</span>
                      <span className="text-[#A1A1AA] ml-2 text-sm">{stats.worst_trade.date}</span>
                    </div>
                    <div className="text-[#FF0055] font-bold">
                      ${stats.worst_trade.pnl_usd?.toFixed(2)} ({stats.worst_trade.pnl_pct?.toFixed(1)}%)
                    </div>
                  </div>
                ) : (
                  <p className="text-[#A1A1AA]">No trades yet</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Today's Summary */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="text-[#007AFF]" />
                Today's Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{dailySummary?.total_trades || 0}</div>
                  <div className="text-xs text-[#A1A1AA]">Trades</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[#00FF94]">{dailySummary?.winners || 0}</div>
                  <div className="text-xs text-[#A1A1AA]">Winners</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[#FF0055]">{dailySummary?.losers || 0}</div>
                  <div className="text-xs text-[#A1A1AA]">Losers</div>
                </div>
                <div>
                  <div className={`text-2xl font-bold ${(dailySummary?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {formatPnl(dailySummary?.total_pnl)}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">P/L</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{dailySummary?.win_rate || 0}%</div>
                  <div className="text-xs text-[#A1A1AA]">Win Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trade Log Tab */}
        <TabsContent value="entries">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="text-[#9D00FF]" />
                Trade Log
                <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] ml-2">{entries.length} entries</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {entries.length === 0 ? (
                <p className="text-[#A1A1AA] text-center py-8">No trades recorded yet. Start trading to build your journal!</p>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {entries.map((entry, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="p-4 bg-[#121212] rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge className={entry.trade_type === 'OPEN' ? 'bg-[#007AFF]/20 text-[#007AFF]' : 'bg-[#FF9500]/20 text-[#FF9500]'}>
                            {entry.trade_type}
                          </Badge>
                          <span className="font-bold">{entry.coin_id?.toUpperCase()}</span>
                          {entry.is_gem && (
                            <Badge className="bg-[#FFD700]/20 text-[#FFD700]">
                              <Sparkles size={10} className="mr-1" />GEM
                            </Badge>
                          )}
                          {entry.is_paper && (
                            <Badge className="bg-[#333] text-[#A1A1AA]">PAPER</Badge>
                          )}
                        </div>
                        <span className="text-sm text-[#A1A1AA]">{new Date(entry.timestamp).toLocaleString()}</span>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-4">
                          <span>{entry.action} ${entry.amount_usd} @ ${entry.price?.toFixed(4)}</span>
                        </div>
                        {entry.performance && (
                          <span className={entry.performance.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                            {formatPnl(entry.performance.pnl_usd)} ({entry.performance.pnl_pct?.toFixed(1)}%)
                          </span>
                        )}
                      </div>

                      {entry.ai_insights?.reasoning && (
                        <div className="mt-2 p-2 bg-[#0A0A0A] rounded text-sm">
                          <div className="flex items-center gap-1 text-[#9D00FF] mb-1">
                            <Brain size={12} />
                            <span className="text-xs">AI Reasoning</span>
                          </div>
                          <p className="text-[#A1A1AA]">{entry.ai_insights.reasoning}</p>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          {/* Key Insights */}
          {aiInsights?.insights?.length > 0 && (
            <Card className="bg-gradient-to-r from-[#9D00FF]/10 to-[#007AFF]/10 border-[#9D00FF]/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="text-[#FFD700]" />
                  Key Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {aiInsights.insights.map((insight, i) => (
                  <div key={i} className={`p-3 rounded-lg ${
                    insight.type === 'positive' ? 'bg-[#00FF94]/10 border border-[#00FF94]/30' :
                    insight.type === 'warning' ? 'bg-[#FF9500]/10 border border-[#FF9500]/30' :
                    'bg-[#007AFF]/10 border border-[#007AFF]/30'
                  }`}>
                    <div className="font-bold mb-1">{insight.title}</div>
                    <p className="text-sm text-[#A1A1AA]">{insight.message}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Confidence Accuracy */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="text-[#007AFF]" />
                AI Confidence Accuracy
              </CardTitle>
              <CardDescription>How accurate is the AI at different confidence levels?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {['high', 'medium', 'low'].map(level => {
                  const data = aiInsights?.confidence_accuracy?.[level] || {};
                  const color = level === 'high' ? '#00FF94' : level === 'medium' ? '#FF9500' : '#FF0055';
                  return (
                    <div key={level} className="p-4 bg-[#121212] rounded-lg text-center">
                      <div className="text-sm text-[#A1A1AA] mb-2 capitalize">{level} Confidence (
                        {level === 'high' ? '70%+' : level === 'medium' ? '50-70%' : '<50%'}
                      )</div>
                      <div className="text-3xl font-bold mb-1" style={{ color }}>{data.win_rate || 0}%</div>
                      <div className="text-sm text-[#A1A1AA]">{data.trades || 0} trades • Avg {formatPnl(data.avg_pnl)}</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Gem vs Regular Performance */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="text-[#FFD700]" />
                Gem vs Regular Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-gradient-to-r from-[#FFD700]/10 to-transparent rounded-lg border border-[#FFD700]/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="text-[#FFD700]" size={16} />
                    <span className="font-bold">Hidden Gems</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-[#FFD700]">{aiInsights?.gem_performance?.gem_win_rate || 0}%</div>
                      <div className="text-xs text-[#A1A1AA]">Win Rate</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${(aiInsights?.gem_performance?.gem_avg_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {formatPnl(aiInsights?.gem_performance?.gem_avg_pnl)}
                      </div>
                      <div className="text-xs text-[#A1A1AA]">Avg P/L</div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-[#121212] rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 className="text-[#007AFF]" size={16} />
                    <span className="font-bold">Regular Trades</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-[#007AFF]">{aiInsights?.gem_performance?.regular_win_rate || 0}%</div>
                      <div className="text-xs text-[#A1A1AA]">Win Rate</div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${(aiInsights?.gem_performance?.regular_avg_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {formatPnl(aiInsights?.gem_performance?.regular_avg_pnl)}
                      </div>
                      <div className="text-xs text-[#A1A1AA]">Avg P/L</div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Factor Performance */}
          {aiInsights?.factor_performance && Object.keys(aiInsights.factor_performance).length > 0 && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="text-[#9D00FF]" />
                  Factor Performance
                </CardTitle>
                <CardDescription>Which AI factors lead to the best trades?</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(aiInsights.factor_performance).map(([factor, data]) => (
                    <div key={factor} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="capitalize font-medium">{factor}</span>
                        <span className="text-sm text-[#A1A1AA]">({data.trades} trades)</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={data.win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                          {data.win_rate}% win
                        </span>
                        <span className={data.total_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>
                          {formatPnl(data.total_pnl)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TradingJournal;
