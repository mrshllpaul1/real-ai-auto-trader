import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, TrendingUp, TrendingDown, Calendar, Target, Zap, Sparkles, BarChart3, Brain, Lightbulb } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const TradingJournal = () => {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    loadData();
  }, [period]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [e, s, i, d] = await Promise.all([
        api.get('/journal/entries?limit=50'),
        api.get(`/journal/stats?days=${period}`),
        api.get(`/journal/ai-insights?days=${period}`),
        api.get('/journal/daily')
      ]);
      setEntries(e.data.entries || []);
      setStats(s.data);
      setAiInsights(i.data);
      setDailySummary(d.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fmtPnl = (pnl) => {
    if (!pnl) return '$0.00';
    return (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
  };

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-8">
      <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mb-8">
        <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
          <BookOpen className="text-[#9D00FF]" />
          Trading Journal
        </h1>
        <p className="text-[#A1A1AA]">Track performance • Understand AI decisions • Learn from every trade</p>
      </motion.div>

      <div className="flex gap-2 mb-6">
        <span className="text-sm text-[#A1A1AA] mr-2">Period:</span>
        {[7, 30, 90].map(d => (
          <Button key={d} size="sm" variant={period === d ? "default" : "outline"} onClick={() => setPeriod(d)}
            className={period === d ? "bg-[#9D00FF]" : "border-[#333]"}>{d}d</Button>
        ))}
      </div>

      <div className="flex gap-2 mb-6 border-b border-[#1F1F1F] pb-2">
        {['overview', 'entries', 'insights'].map(t => (
          <Button key={t} variant="ghost" onClick={() => setTab(t)}
            className={tab === t ? "text-[#00FF94] border-b-2 border-[#00FF94] rounded-none" : "text-[#A1A1AA]"}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </Button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-[#A1A1AA] mb-1"><BarChart3 size={16} /><span className="text-xs">Total Trades</span></div>
                <div className="text-2xl font-bold">{stats?.total_trades || 0}</div>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-[#A1A1AA] mb-1"><TrendingUp size={16} /><span className="text-xs">Total P/L</span></div>
                <div className={`text-2xl font-bold ${(stats?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>{fmtPnl(stats?.total_pnl)}</div>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-[#A1A1AA] mb-1"><Target size={16} /><span className="text-xs">Win Rate</span></div>
                <div className={`text-2xl font-bold ${(stats?.win_rate || 0) >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>{stats?.win_rate || 0}%</div>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-[#A1A1AA] mb-1"><Sparkles size={16} /><span className="text-xs">Most Traded</span></div>
                <div className="text-2xl font-bold text-[#FFD700]">{stats?.most_traded_coin?.toUpperCase() || '-'}</div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader><CardTitle className="flex items-center gap-2"><Calendar className="text-[#007AFF]" />Today's Summary</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4 text-center">
                <div><div className="text-2xl font-bold">{dailySummary?.total_trades || 0}</div><div className="text-xs text-[#A1A1AA]">Trades</div></div>
                <div><div className="text-2xl font-bold text-[#00FF94]">{dailySummary?.winners || 0}</div><div className="text-xs text-[#A1A1AA]">Winners</div></div>
                <div><div className="text-2xl font-bold text-[#FF0055]">{dailySummary?.losers || 0}</div><div className="text-xs text-[#A1A1AA]">Losers</div></div>
                <div><div className={`text-2xl font-bold ${(dailySummary?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>{fmtPnl(dailySummary?.total_pnl)}</div><div className="text-xs text-[#A1A1AA]">P/L</div></div>
                <div><div className="text-2xl font-bold">{dailySummary?.win_rate || 0}%</div><div className="text-xs text-[#A1A1AA]">Win Rate</div></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === 'entries' && (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader><CardTitle className="flex items-center gap-2"><BookOpen className="text-[#9D00FF]" />Trade Log<Badge className="ml-2 bg-[#9D00FF]/20 text-[#9D00FF]">{entries.length}</Badge></CardTitle></CardHeader>
          <CardContent>
            {entries.length === 0 ? (
              <p className="text-[#A1A1AA] text-center py-8">No trades recorded yet. Start trading to build your journal!</p>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {entries.map((e, i) => (
                  <div key={i} className="p-4 bg-[#121212] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={e.trade_type === 'OPEN' ? 'bg-[#007AFF]/20 text-[#007AFF]' : 'bg-[#FF9500]/20 text-[#FF9500]'}>{e.trade_type}</Badge>
                        <span className="font-bold">{e.coin_id?.toUpperCase()}</span>
                        {e.is_gem && <Badge className="bg-[#FFD700]/20 text-[#FFD700]">GEM</Badge>}
                        {e.is_paper && <Badge className="bg-[#333] text-[#A1A1AA]">PAPER</Badge>}
                      </div>
                      <span className="text-sm text-[#A1A1AA]">{new Date(e.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>{e.action} ${e.amount_usd} @ ${e.price?.toFixed(4)}</span>
                      {e.performance && <span className={e.performance.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}>{fmtPnl(e.performance.pnl_usd)}</span>}
                    </div>
                    {e.ai_insights?.reasoning && (
                      <div className="mt-2 p-2 bg-[#0A0A0A] rounded text-sm">
                        <div className="flex items-center gap-1 text-[#9D00FF] mb-1"><Brain size={12} /><span className="text-xs">AI Reasoning</span></div>
                        <p className="text-[#A1A1AA]">{e.ai_insights.reasoning}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'insights' && (
        <div className="space-y-6">
          {aiInsights?.insights?.length > 0 && (
            <Card className="bg-gradient-to-r from-[#9D00FF]/10 to-[#007AFF]/10 border-[#9D00FF]/30">
              <CardHeader><CardTitle className="flex items-center gap-2"><Lightbulb className="text-[#FFD700]" />Key Insights</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {aiInsights.insights.map((ins, i) => (
                  <div key={i} className={`p-3 rounded-lg ${ins.type === 'positive' ? 'bg-[#00FF94]/10 border border-[#00FF94]/30' : 'bg-[#007AFF]/10 border border-[#007AFF]/30'}`}>
                    <div className="font-bold mb-1">{ins.title}</div>
                    <p className="text-sm text-[#A1A1AA]">{ins.message}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader><CardTitle className="flex items-center gap-2"><Target className="text-[#007AFF]" />AI Confidence Accuracy</CardTitle></CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {['high', 'medium', 'low'].map(level => {
                  const d = aiInsights?.confidence_accuracy?.[level] || {};
                  const c = level === 'high' ? '#00FF94' : level === 'medium' ? '#FF9500' : '#FF0055';
                  return (
                    <div key={level} className="p-4 bg-[#121212] rounded-lg text-center">
                      <div className="text-sm text-[#A1A1AA] mb-2 capitalize">{level} ({level === 'high' ? '70%+' : level === 'medium' ? '50-70%' : '<50%'})</div>
                      <div className="text-3xl font-bold mb-1" style={{ color: c }}>{d.win_rate || 0}%</div>
                      <div className="text-sm text-[#A1A1AA]">{d.trades || 0} trades</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="text-[#FFD700]" />Gem vs Regular</CardTitle></CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-[#FFD700]/10 rounded-lg border border-[#FFD700]/30">
                  <div className="font-bold mb-2">Hidden Gems</div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div><div className="text-2xl font-bold text-[#FFD700]">{aiInsights?.gem_performance?.gem_win_rate || 0}%</div><div className="text-xs text-[#A1A1AA]">Win Rate</div></div>
                    <div><div className={`text-2xl font-bold ${(aiInsights?.gem_performance?.gem_avg_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>{fmtPnl(aiInsights?.gem_performance?.gem_avg_pnl)}</div><div className="text-xs text-[#A1A1AA]">Avg P/L</div></div>
                  </div>
                </div>
                <div className="p-4 bg-[#121212] rounded-lg">
                  <div className="font-bold mb-2">Regular Trades</div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div><div className="text-2xl font-bold text-[#007AFF]">{aiInsights?.gem_performance?.regular_win_rate || 0}%</div><div className="text-xs text-[#A1A1AA]">Win Rate</div></div>
                    <div><div className={`text-2xl font-bold ${(aiInsights?.gem_performance?.regular_avg_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>{fmtPnl(aiInsights?.gem_performance?.regular_avg_pnl)}</div><div className="text-xs text-[#A1A1AA]">Avg P/L</div></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TradingJournal;
