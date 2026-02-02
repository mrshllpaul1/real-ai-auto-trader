import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, TrendingUp, Calendar, Target, Sparkles, BarChart3, Brain, Lightbulb } from 'lucide-react';
import api from '../services/api';

const TradingJournal = () => {
  const [data, setData] = useState({ entries: [], stats: null, insights: null, daily: null });
  const [tab, setTab] = useState('overview');
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    const load = async () => {
      try {
        const [e, s, i, d] = await Promise.all([
          api.get('/journal/entries?limit=50'),
          api.get('/journal/stats?days=' + period),
          api.get('/journal/ai-insights?days=' + period),
          api.get('/journal/daily')
        ]);
        setData({ entries: e.data.entries || [], stats: s.data, insights: i.data, daily: d.data });
      } catch (err) { console.error(err); }
    };
    load();
  }, [period]);

  const fmtPnl = (p) => (!p ? '$0' : (p >= 0 ? '+$' : '-$') + Math.abs(p).toFixed(2));
  const pnlColor = (p) => (p >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]');

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-8">
      <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
        <BookOpen className="text-[#9D00FF]" />Trading Journal
      </h1>
      <p className="text-[#A1A1AA] mb-6">Track performance • AI insights • Learn from trades</p>

      <div className="flex gap-2 mb-4">
        {[7, 30, 90].map(d => (
          <Button key={d} size="sm" onClick={() => setPeriod(d)} className={period === d ? "bg-[#9D00FF]" : "bg-[#1F1F1F]"}>{d}d</Button>
        ))}
      </div>

      <div className="flex gap-4 mb-6 border-b border-[#1F1F1F] pb-2">
        <Button variant="ghost" onClick={() => setTab('overview')} className={tab === 'overview' ? "text-[#00FF94]" : ""}>Overview</Button>
        <Button variant="ghost" onClick={() => setTab('entries')} className={tab === 'entries' ? "text-[#00FF94]" : ""}>Trade Log</Button>
        <Button variant="ghost" onClick={() => setTab('insights')} className={tab === 'insights' ? "text-[#00FF94]" : ""}>AI Insights</Button>
      </div>

      {tab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={BarChart3} label="Total Trades" value={data.stats?.total_trades || 0} />
            <StatCard icon={TrendingUp} label="Total P/L" value={fmtPnl(data.stats?.total_pnl)} color={pnlColor(data.stats?.total_pnl)} />
            <StatCard icon={Target} label="Win Rate" value={(data.stats?.win_rate || 0) + '%'} color={pnlColor((data.stats?.win_rate || 0) - 50)} />
            <StatCard icon={Sparkles} label="Most Traded" value={data.stats?.most_traded_coin?.toUpperCase() || '-'} color="text-[#FFD700]" />
          </div>
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader><CardTitle className="flex items-center gap-2"><Calendar className="text-[#007AFF]" />Today</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4 text-center">
                <div><div className="text-xl font-bold">{data.daily?.total_trades || 0}</div><div className="text-xs text-[#A1A1AA]">Trades</div></div>
                <div><div className="text-xl font-bold text-[#00FF94]">{data.daily?.winners || 0}</div><div className="text-xs text-[#A1A1AA]">Won</div></div>
                <div><div className="text-xl font-bold text-[#FF0055]">{data.daily?.losers || 0}</div><div className="text-xs text-[#A1A1AA]">Lost</div></div>
                <div><div className={`text-xl font-bold ${pnlColor(data.daily?.total_pnl)}`}>{fmtPnl(data.daily?.total_pnl)}</div><div className="text-xs text-[#A1A1AA]">P/L</div></div>
                <div><div className="text-xl font-bold">{data.daily?.win_rate || 0}%</div><div className="text-xs text-[#A1A1AA]">Rate</div></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === 'entries' && (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader><CardTitle><BookOpen className="inline mr-2 text-[#9D00FF]" />Trade Log ({data.entries.length})</CardTitle></CardHeader>
          <CardContent>
            {data.entries.length === 0 ? (
              <p className="text-[#A1A1AA] text-center py-8">No trades yet. Start trading!</p>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {data.entries.map((e, i) => (
                  <TradeEntry key={i} entry={e} fmtPnl={fmtPnl} pnlColor={pnlColor} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'insights' && (
        <div className="space-y-6">
          <InsightsCard insights={data.insights?.insights} />
          <ConfidenceCard confidence={data.insights?.confidence_accuracy} />
          <GemCard gem={data.insights?.gem_performance} fmtPnl={fmtPnl} pnlColor={pnlColor} />
        </div>
      )}
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, color = "text-white" }) => (
  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
    <CardContent className="p-4">
      <div className="flex items-center gap-2 text-[#A1A1AA] mb-1"><Icon size={16} /><span className="text-xs">{label}</span></div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </CardContent>
  </Card>
);

const TradeEntry = ({ entry, fmtPnl, pnlColor }) => (
  <div className="p-4 bg-[#121212] rounded-lg">
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <Badge className={entry.trade_type === 'OPEN' ? 'bg-[#007AFF]/20 text-[#007AFF]' : 'bg-[#FF9500]/20 text-[#FF9500]'}>{entry.trade_type}</Badge>
        <span className="font-bold">{entry.coin_id?.toUpperCase()}</span>
        {entry.is_gem && <Badge className="bg-[#FFD700]/20 text-[#FFD700]">GEM</Badge>}
      </div>
      <span className="text-sm text-[#A1A1AA]">{new Date(entry.timestamp).toLocaleDateString()}</span>
    </div>
    <div className="flex justify-between text-sm">
      <span>${entry.amount_usd} @ ${entry.price?.toFixed(4)}</span>
      {entry.performance && <span className={pnlColor(entry.performance.pnl_usd)}>{fmtPnl(entry.performance.pnl_usd)}</span>}
    </div>
    {entry.ai_insights?.reasoning && (
      <div className="mt-2 p-2 bg-[#0A0A0A] rounded text-sm text-[#A1A1AA]">
        <Brain size={12} className="inline mr-1 text-[#9D00FF]" />{entry.ai_insights.reasoning}
      </div>
    )}
  </div>
);

const InsightsCard = ({ insights }) => {
  if (!insights || insights.length === 0) return null;
  return (
    <Card className="bg-[#9D00FF]/10 border-[#9D00FF]/30">
      <CardHeader><CardTitle><Lightbulb className="inline mr-2 text-[#FFD700]" />Key Insights</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {insights.map((ins, i) => (
          <div key={i} className="p-3 bg-[#00FF94]/10 rounded-lg border border-[#00FF94]/30">
            <div className="font-bold">{ins.title}</div>
            <p className="text-sm text-[#A1A1AA]">{ins.message}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const ConfidenceCard = ({ confidence }) => (
  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
    <CardHeader><CardTitle><Target className="inline mr-2 text-[#007AFF]" />AI Confidence Accuracy</CardTitle></CardHeader>
    <CardContent>
      <div className="grid grid-cols-3 gap-4">
        <ConfLevel level="High (70%+)" data={confidence?.high} color="#00FF94" />
        <ConfLevel level="Medium (50-70%)" data={confidence?.medium} color="#FF9500" />
        <ConfLevel level="Low (<50%)" data={confidence?.low} color="#FF0055" />
      </div>
    </CardContent>
  </Card>
);

const ConfLevel = ({ level, data, color }) => (
  <div className="p-4 bg-[#121212] rounded-lg text-center">
    <div className="text-sm text-[#A1A1AA] mb-2">{level}</div>
    <div className="text-3xl font-bold" style={{ color }}>{data?.win_rate || 0}%</div>
    <div className="text-sm text-[#A1A1AA]">{data?.trades || 0} trades</div>
  </div>
);

const GemCard = ({ gem, fmtPnl, pnlColor }) => (
  <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
    <CardHeader><CardTitle><Sparkles className="inline mr-2 text-[#FFD700]" />Gem vs Regular</CardTitle></CardHeader>
    <CardContent>
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-[#FFD700]/10 rounded-lg border border-[#FFD700]/30 text-center">
          <div className="font-bold mb-2">Gems</div>
          <div className="text-2xl font-bold text-[#FFD700]">{gem?.gem_win_rate || 0}%</div>
          <div className={`text-lg ${pnlColor(gem?.gem_avg_pnl)}`}>{fmtPnl(gem?.gem_avg_pnl)} avg</div>
        </div>
        <div className="p-4 bg-[#121212] rounded-lg text-center">
          <div className="font-bold mb-2">Regular</div>
          <div className="text-2xl font-bold text-[#007AFF]">{gem?.regular_win_rate || 0}%</div>
          <div className={`text-lg ${pnlColor(gem?.regular_avg_pnl)}`}>{fmtPnl(gem?.regular_avg_pnl)} avg</div>
        </div>
      </div>
    </CardContent>
  </Card>
);

export default TradingJournal;
