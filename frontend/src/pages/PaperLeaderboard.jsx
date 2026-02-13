import React, { useState, useEffect } from 'react';
import { Trophy, Medal, TrendingUp, Users, Crown, Award, Target, Calendar, ChevronDown, Star } from 'lucide-react';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const PaperLeaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [competitions, setCompetitions] = useState([]);
  const [myRank, setMyRank] = useState(null);
  const [stats, setStats] = useState(null);
  const [period, setPeriod] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [period]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [leaderRes, compRes, rankRes, statsRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/paper-leaderboard/top?period=${period}&limit=20`),
        fetch(`${BACKEND_URL}/api/paper-leaderboard/competitions`),
        fetch(`${BACKEND_URL}/api/paper-leaderboard/my-rank`),
        fetch(`${BACKEND_URL}/api/paper-leaderboard/stats`)
      ]);

      if (leaderRes.ok) {
        const data = await leaderRes.json();
        setLeaderboard(data.leaderboard || []);
      }
      if (compRes.ok) {
        const data = await compRes.json();
        setCompetitions(data.competitions || []);
      }
      if (rankRes.ok) {
        const data = await rankRes.json();
        setMyRank(data);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankStyle = (rank) => {
    switch (rank) {
      case 1: return 'bg-gradient-to-r from-yellow-500/20 to-yellow-600/20 border-yellow-500/50';
      case 2: return 'bg-gradient-to-r from-gray-400/20 to-gray-500/20 border-gray-400/50';
      case 3: return 'bg-gradient-to-r from-amber-600/20 to-amber-700/20 border-amber-600/50';
      default: return 'bg-gray-800/50 border-gray-700/50';
    }
  };

  const formatPnL = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500/20 to-orange-500/20">
            <Trophy className="w-8 h-8 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Paper Trading Leaderboard</h1>
            <p className="text-gray-400">Compete risk-free and prove your skills</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-blue-400" />
              <div>
                <p className="text-xs text-gray-400">Total Participants</p>
                <p className="text-xl font-bold text-white">{stats.total_participants || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-5 h-5 text-green-400" />
              <div>
                <p className="text-xs text-gray-400">Avg. Return</p>
                <p className="text-xl font-bold text-white">{(stats.avg_pnl || 0).toFixed(1)}%</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Target className="w-5 h-5 text-purple-400" />
              <div>
                <p className="text-xs text-gray-400">Avg. Win Rate</p>
                <p className="text-xl font-bold text-white">{(stats.avg_win_rate || 0).toFixed(1)}%</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <Award className="w-5 h-5 text-yellow-400" />
              <div>
                <p className="text-xs text-gray-400">Total Trades</p>
                <p className="text-xl font-bold text-white">{(stats.total_trades || 0).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Leaderboard */}
        <div className="lg:col-span-2">
          {/* Period Filter */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Top Traders</h2>
            <div className="relative">
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-8 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="daily">Today</option>
                <option value="weekly">This Week</option>
                <option value="monthly">This Month</option>
                <option value="all">All Time</option>
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Leaderboard Table */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
              </div>
            ) : (
              <div className="divide-y divide-gray-800">
                {leaderboard.map((trader, index) => (
                  <div 
                    key={trader.user_id || index}
                    className={`flex items-center gap-4 p-4 ${getRankStyle(trader.rank)} border-l-2 transition-colors hover:bg-gray-800/50`}
                  >
                    {/* Rank */}
                    <div className="w-12 text-center">
                      <span className="text-2xl">{trader.badge}</span>
                      <p className="text-xs text-gray-500">#{trader.rank}</p>
                    </div>

                    {/* User */}
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-xl">
                        {trader.avatar_emoji}
                      </div>
                      <div>
                        <p className="font-medium text-white">{trader.display_name}</p>
                        <p className="text-xs text-gray-500">{trader.total_trades} trades</p>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="text-right">
                      <p className={`text-lg font-bold ${trader.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPnL(trader.pnl_percent)}
                      </p>
                      <p className="text-xs text-gray-500">{trader.win_rate}% win rate</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* My Rank */}
          {myRank && myRank.rank && (
            <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Crown className="w-5 h-5 text-blue-400" />
                  <span className="text-white">Your Rank: #{myRank.rank}</span>
                </div>
                <span className={`font-bold ${myRank.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatPnL(myRank.pnl_percent || 0)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Competitions */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-4">Active Competitions</h2>
          <div className="space-y-4">
            {competitions.map((comp) => (
              <div key={comp.id} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-white">{comp.name}</h3>
                    <p className="text-xs text-gray-400 mt-1">{comp.description}</p>
                  </div>
                  <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                    {comp.status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">
                    <Users className="w-4 h-4 inline mr-1" />
                    {comp.participants} participants
                  </span>
                  <span className="text-yellow-400">
                    <Star className="w-4 h-4 inline mr-1" />
                    {comp.prize}
                  </span>
                </div>
                <button className="w-full mt-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-medium hover:bg-blue-500/30 transition-colors">
                  Join Competition
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaperLeaderboard;
