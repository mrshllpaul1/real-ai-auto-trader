import React, { useState, useEffect } from 'react';
import { MessageSquare, Heart, Share2, UserPlus, TrendingUp, TrendingDown, Users, Trophy, Clock, Send } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const SocialFeed = () => {
  const [feed, setFeed] = useState([]);
  const [topTraders, setTopTraders] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [filter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [feedRes, tradersRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/social/feed?filter_type=${filter}&limit=20`),
        fetch(`${BACKEND_URL}/api/social/top-traders?period=weekly&limit=5`)
      ]);

      if (feedRes.ok) {
        const data = await feedRes.json();
        setFeed(data.feed || []);
      }
      if (tradersRes.ok) {
        const data = await tradersRes.json();
        setTopTraders(data.top_traders || []);
      }
    } catch (error) {
      console.error('Error fetching social data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (tradeId) => {
    try {
      await fetch(`${BACKEND_URL}/api/social/trades/${tradeId}/like`, { method: 'POST' });
      fetchData();
    } catch (error) {
      console.error('Error liking trade:', error);
    }
  };

  const handleFollow = async (userId) => {
    try {
      await fetch(`${BACKEND_URL}/api/social/follow/${userId}`, { method: 'POST' });
      fetchData();
    } catch (error) {
      console.error('Error following user:', error);
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = (now - date) / 1000;

    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500/20 to-purple-500/20">
            <Users className="w-8 h-8 text-pink-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Social Trading</h1>
            <p className="text-gray-400">Follow traders, share ideas, learn together</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Feed */}
        <div className="lg:col-span-2">
          {/* Filter Tabs */}
          <div className="flex gap-2 mb-4">
            {['all', 'following', 'top_traders'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === f
                    ? 'bg-pink-500 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {f === 'all' && 'All Trades'}
                {f === 'following' && 'Following'}
                {f === 'top_traders' && 'Top Traders'}
              </button>
            ))}
          </div>

          {/* Feed */}
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-gray-800/50 rounded-xl p-6 animate-pulse">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gray-700 rounded-full" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-700 rounded w-1/4 mb-2" />
                      <div className="h-3 bg-gray-700 rounded w-1/6" />
                    </div>
                  </div>
                  <div className="h-16 bg-gray-700 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {feed.map((trade) => (
                <div key={trade.trade_id} className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden">
                  {/* Header */}
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-xl">
                        {trade.user?.avatar_emoji || '👤'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">{trade.user?.display_name}</span>
                          {trade.user?.verified && (
                            <span className="text-blue-400">✓</span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">{formatTimeAgo(trade.shared_at)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleFollow(trade.user_id)}
                      className="px-3 py-1 bg-pink-500/20 text-pink-400 rounded-lg text-sm hover:bg-pink-500/30 transition-colors"
                    >
                      <UserPlus className="w-4 h-4 inline mr-1" />
                      Follow
                    </button>
                  </div>

                  {/* Trade Details */}
                  <div className="px-4 pb-4">
                    <div className="flex items-center gap-3 mb-3">
                      <span className={`px-3 py-1 rounded-lg text-sm font-medium ${
                        trade.side === 'BUY'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.side}
                      </span>
                      <span className="text-lg font-bold text-white">{trade.symbol}</span>
                      <span className={`flex items-center gap-1 ${
                        (trade.pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {(trade.pnl_percent || 0) >= 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        {(trade.pnl_percent || 0) >= 0 ? '+' : ''}{(trade.pnl_percent || 0).toFixed(2)}%
                      </span>
                    </div>

                    {trade.comment && (
                      <p className="text-gray-300 mb-3">{trade.comment}</p>
                    )}

                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span className="px-2 py-0.5 bg-gray-700 rounded">{trade.strategy || 'manual'}</span>
                      <span>· Entry: ${trade.entry_price?.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="px-4 py-3 border-t border-gray-700/50 flex items-center gap-6">
                    <button
                      onClick={() => handleLike(trade.trade_id)}
                      className={`flex items-center gap-2 text-sm transition-colors ${
                        trade.user_liked ? 'text-pink-400' : 'text-gray-400 hover:text-pink-400'
                      }`}
                    >
                      <Heart className={`w-4 h-4 ${trade.user_liked ? 'fill-current' : ''}`} />
                      {trade.likes_count || 0}
                    </button>
                    <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-blue-400 transition-colors">
                      <MessageSquare className="w-4 h-4" />
                      {trade.comments_count || 0}
                    </button>
                    <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-green-400 transition-colors">
                      <Share2 className="w-4 h-4" />
                      Share
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div>
          {/* Top Traders */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="w-5 h-5 text-yellow-400" />
              <h3 className="font-semibold text-white">Top Traders This Week</h3>
            </div>
            <div className="space-y-3">
              {topTraders.map((trader, i) => (
                <div key={trader.user_id} className="flex items-center gap-3">
                  <span className="text-lg w-6">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}</span>
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm">
                    {trader.avatar_emoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{trader.display_name}</p>
                    <p className="text-xs text-gray-500">{trader.trades_count} trades</p>
                  </div>
                  <span className={`text-sm font-medium ${
                    (trader.avg_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {(trader.avg_pnl || 0) >= 0 ? '+' : ''}{(trader.avg_pnl || 0).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Share Your Trade */}
          <div className="bg-gradient-to-br from-pink-900/30 to-purple-900/30 border border-pink-500/20 rounded-xl p-4">
            <h3 className="font-semibold text-white mb-2">Share Your Trade</h3>
            <p className="text-sm text-gray-400 mb-4">Let the community see your latest moves</p>
            <button className="w-full py-2.5 bg-pink-500 hover:bg-pink-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
              <Send className="w-4 h-4" />
              Share Trade
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SocialFeed;
