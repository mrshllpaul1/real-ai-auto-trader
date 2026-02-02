import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, TrendingUp, Calendar, Target, Sparkles, BarChart3 } from 'lucide-react';
import api from '../services/api';

export default function TradingJournal() {
  const [stats, setStats] = useState(null);
  const [daily, setDaily] = useState(null);
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const s = await api.get('/journal/stats?days=30');
        const d = await api.get('/journal/daily');
        const i = await api.get('/journal/ai-insights?days=30');
        setStats(s.data);
        setDaily(d.data);
        setInsights(i.data);
      } catch (e) { console.error(e); }
    };
    load();
  }, []);

  const pnl = stats?.total_pnl || 0;
  const winRate = stats?.win_rate || 0;
  const gemWin = insights?.gem_performance?.gem_win_rate || 0;
  const regWin = insights?.gem_performance?.regular_win_rate || 0;

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-8">
      <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
        <BookOpen className="text-[#9D00FF]" />
        Trading Journal
      </h1>
      <p className="text-[#A1A1AA] mb-8">Track performance • AI insights • Learn from trades</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
              <BarChart3 size={16} />
              <span className="text-xs">Total Trades</span>
            </div>
            <div className="text-2xl font-bold">{stats?.total_trades || 0}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
              <TrendingUp size={16} />
              <span className="text-xs">Total P/L</span>
            </div>
            <div className={`text-2xl font-bold ${pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-[#A1A1AA] mb-1">
              <Target size={16} />
              <span className="text-xs">Win Rate</span>
            </div>
            <div className={`text-2xl font-bold ${winRate >= 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              {winRate}%
            </div>
          </CardContent>
        </Card>

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
      </div>

      <Card className="bg-[#0A0A0A] border-[#1F1F1F] mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="text-[#007AFF]" />
            Today's Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{daily?.total_trades || 0}</div>
              <div className="text-xs text-[#A1A1AA]">Trades</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[#00FF94]">{daily?.winners || 0}</div>
              <div className="text-xs text-[#A1A1AA]">Winners</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[#FF0055]">{daily?.losers || 0}</div>
              <div className="text-xs text-[#A1A1AA]">Losers</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${(daily?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                ${(daily?.total_pnl || 0).toFixed(2)}
              </div>
              <div className="text-xs text-[#A1A1AA]">P/L</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{daily?.win_rate || 0}%</div>
              <div className="text-xs text-[#A1A1AA]">Win Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-[#0A0A0A] border-[#1F1F1F] mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="text-[#FFD700]" />
            Gem vs Regular Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-[#FFD700]/10 rounded-lg border border-[#FFD700]/30 text-center">
              <div className="font-bold mb-2">Hidden Gems</div>
              <div className="text-3xl font-bold text-[#FFD700]">{gemWin}%</div>
              <div className="text-sm text-[#A1A1AA]">Win Rate</div>
            </div>
            <div className="p-4 bg-[#121212] rounded-lg text-center">
              <div className="font-bold mb-2">Regular Trades</div>
              <div className="text-3xl font-bold text-[#007AFF]">{regWin}%</div>
              <div className="text-sm text-[#A1A1AA]">Win Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="text-[#007AFF]" />
            AI Confidence Accuracy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-[#121212] rounded-lg">
              <div className="text-sm text-[#A1A1AA] mb-2">High (70%+)</div>
              <div className="text-3xl font-bold text-[#00FF94]">
                {insights?.confidence_accuracy?.high?.win_rate || 0}%
              </div>
              <div className="text-sm text-[#A1A1AA]">
                {insights?.confidence_accuracy?.high?.trades || 0} trades
              </div>
            </div>
            <div className="p-4 bg-[#121212] rounded-lg">
              <div className="text-sm text-[#A1A1AA] mb-2">Medium (50-70%)</div>
              <div className="text-3xl font-bold text-[#FF9500]">
                {insights?.confidence_accuracy?.medium?.win_rate || 0}%
              </div>
              <div className="text-sm text-[#A1A1AA]">
                {insights?.confidence_accuracy?.medium?.trades || 0} trades
              </div>
            </div>
            <div className="p-4 bg-[#121212] rounded-lg">
              <div className="text-sm text-[#A1A1AA] mb-2">Low (&lt;50%)</div>
              <div className="text-3xl font-bold text-[#FF0055]">
                {insights?.confidence_accuracy?.low?.win_rate || 0}%
              </div>
              <div className="text-sm text-[#A1A1AA]">
                {insights?.confidence_accuracy?.low?.trades || 0} trades
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
