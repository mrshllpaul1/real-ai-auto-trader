import React, { useState, useEffect, useMemo } from 'react';
import { 
  Newspaper, TrendingUp, TrendingDown, AlertCircle, RefreshCw, Filter,
  Clock, ExternalLink, ThumbsUp, ThumbsDown, MessageSquare, Flame,
  ArrowUpRight, BarChart3, Zap, Globe
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const NewsSentiment = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [trendingNews, setTrendingNews] = useState([]);
  const [bullishNews, setBullishNews] = useState([]);
  const [bearishNews, setBearishNews] = useState([]);
  const [coinSentiment, setCoinSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [trendingSearch, setTrendingSearch] = useState('');
  const [bullishSearch, setBullishSearch] = useState('');
  const [bearishSearch, setBearishSearch] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState('');

  const coins = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin' },
    { id: 'ethereum', symbol: 'ETH', name: 'Ethereum' },
    { id: 'solana', symbol: 'SOL', name: 'Solana' },
    { id: 'ripple', symbol: 'XRP', name: 'Ripple' },
    { id: 'binancecoin', symbol: 'BNB', name: 'BNB' }
  ];

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedCoin) {
      fetchCoinSentiment(selectedCoin);
    }
  }, [selectedCoin]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [marketRes, trendingRes, bullishRes, bearishRes] = await Promise.all([
        fetch(`${API_URL}/api/sentiment/market`),
        fetch(`${API_URL}/api/sentiment/trending?limit=15`),
        fetch(`${API_URL}/api/sentiment/news/bullish`),
        fetch(`${API_URL}/api/sentiment/news/bearish`)
      ]);

      if (marketRes.ok) setMarketSentiment(await marketRes.json());
      if (trendingRes.ok) {
        const data = await trendingRes.json();
        setTrendingNews(data.news || []);
      }
      if (bullishRes.ok) {
        const data = await bullishRes.json();
        setBullishNews(data.news || []);
      }
      if (bearishRes.ok) {
        const data = await bearishRes.json();
        setBearishNews(data.news || []);
      }
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error('Error fetching sentiment data:', err);
      setError('Unable to refresh sentiment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCoinSentiment = async (coinId) => {
    try {
      const coin = coins.find(c => c.id === coinId);
      const res = await fetch(`${API_URL}/api/sentiment/coin/${coinId}?symbol=${coin?.symbol || ''}`);
      if (res.ok) {
        setCoinSentiment(await res.json());
      }
    } catch (err) {
      console.error('Error fetching coin sentiment:', err);
    }
  };

  const getSentimentColor = (score) => {
    if (score >= 70) return 'text-[#00FF94]';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSentimentBg = (score) => {
    if (score >= 70) return 'bg-[#00FF94]/20 border-[#00FF94]/50';
    if (score >= 50) return 'bg-yellow-500/20 border-yellow-500/50';
    return 'bg-red-500/20 border-red-500/50';
  };

  const getSentimentLabel = (label) => {
    const labels = {
      very_bullish: { text: 'Very Bullish', color: 'text-[#00FF94]', icon: TrendingUp },
      bullish: { text: 'Bullish', color: 'text-[#00FF94]', icon: TrendingUp },
      neutral: { text: 'Neutral', color: 'text-yellow-400', icon: BarChart3 },
      bearish: { text: 'Bearish', color: 'text-red-400', icon: TrendingDown },
      very_bearish: { text: 'Very Bearish', color: 'text-red-400', icon: TrendingDown }
    };
    return labels[label] || labels.neutral;
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  const tabs = [
    { id: 'overview', label: 'Market Overview', icon: Globe },
    { id: 'trending', label: 'Trending', icon: Flame },
    { id: 'bullish', label: 'Bullish', icon: TrendingUp },
    { id: 'bearish', label: 'Bearish', icon: TrendingDown },
    { id: 'coin', label: 'Coin Analysis', icon: BarChart3 }
  ];

  const filterNews = (items = [], termValue = '') => {
    if (!termValue) return items;
    const term = termValue.toLowerCase();
    return items.filter((n) =>
      (n.title || '').toLowerCase().includes(term) ||
      (n.source || '').toLowerCase().includes(term) ||
      (n.currencies || []).some((c) => c.toLowerCase().includes(term))
    );
  };

  const filteredTrending = useMemo(
    () => filterNews(trendingNews, trendingSearch),
    [trendingNews, trendingSearch]
  );

  const filteredBullish = useMemo(
    () => filterNews(bullishNews, bullishSearch),
    [bullishNews, bullishSearch]
  );

  const filteredBearish = useMemo(
    () => filterNews(bearishNews, bearishSearch),
    [bearishNews, bearishSearch]
  );

  const renderSearchBar = (value, onChange, count) => (
    <div className="flex flex-col md:flex-row md:items-center gap-3 mb-4">
      <div className="flex items-center gap-2 bg-[#1F1F1F] border border-[#333] rounded-lg px-3 py-2 w-full md:w-1/2">
        <Filter size={16} className="text-[#A1A1AA]" />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Filter by keyword, source, or coin (e.g., bitcoin, ETF, SEC)"
          className="bg-transparent text-white text-sm outline-none flex-1 placeholder:text-[#555]"
          data-testid="news-filter-input"
        />
      </div>
      <div className="text-xs text-[#A1A1AA]">
        Showing {count} articles
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="news-sentiment-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Newspaper className="text-[#9D00FF]" />
            News & Sentiment
          </h1>
          <p className="text-[#A1A1AA] mt-1">AI-powered market sentiment analysis</p>
          {lastUpdated && (
            <p className="text-xs text-[#555] mt-1">
              Last updated {formatTimeAgo(lastUpdated)}
            </p>
          )}
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
          data-testid="refresh-sentiment-btn"
        >
          <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          <span className="text-[#A1A1AA]">Refresh</span>
        </button>
      </div>

      {/* Market Sentiment Overview */}
      {error && (
        <div className="mb-4 p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-200 text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        </div>
      )}

      {loading && (
        <div className="mb-4 p-3 rounded-lg border border-[#333] bg-[#0F0F0F] text-[#A1A1AA] text-sm flex items-center gap-2">
          <RefreshCw size={14} className="animate-spin" />
          Refreshing sentiment...
        </div>
      )}

      {marketSentiment && (
        <div className={`mb-6 p-6 rounded-xl border ${getSentimentBg(marketSentiment.market_score)}`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-[#A1A1AA] mb-1">Overall Market Sentiment</p>
              <div className="flex items-center gap-3">
                <span className={`text-4xl font-bold ${getSentimentColor(marketSentiment.market_score)}`}>
                  {marketSentiment.market_score}
                </span>
                <span className={`text-2xl font-semibold capitalize ${getSentimentColor(marketSentiment.market_score)}`}>
                  {marketSentiment.market_label}
                </span>
              </div>
              <p className="text-sm text-[#A1A1AA] mt-1">
                Confidence: {marketSentiment.confidence}%
              </p>
            </div>
            <div className="flex gap-4">
              {marketSentiment.coin_sentiments && Object.entries(marketSentiment.coin_sentiments).slice(0, 5).map(([coinId, data]) => (
                <div key={coinId} className="text-center">
                  <p className="text-xs text-[#A1A1AA] uppercase">{coinId.slice(0, 3)}</p>
                  <p className={`text-lg font-bold ${getSentimentColor(data.score)}`}>{data.score}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
              activeTab === tab.id
                ? 'bg-[#9D00FF]/20 text-[#9D00FF] border border-[#9D00FF]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent hover:bg-[#2a2a2a]'
            }`}
            data-testid={`tab-${tab.id}`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            {/* Coin Sentiments */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Coin Sentiments</h2>
              <div className="space-y-3">
                {marketSentiment?.coin_sentiments && Object.entries(marketSentiment.coin_sentiments).map(([coinId, data]) => {
                  const sentimentInfo = getSentimentLabel(data.label);
                  return (
                    <div
                      key={coinId}
                      className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg cursor-pointer hover:border-[#555]"
                      onClick={() => {
                        setSelectedCoin(coinId);
                        setActiveTab('coin');
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#333] rounded-full flex items-center justify-center">
                          <span className="text-xs font-bold uppercase">{coinId.slice(0, 3)}</span>
                        </div>
                        <div>
                          <p className="text-white font-medium capitalize">{coinId}</p>
                          <p className={`text-sm ${sentimentInfo.color}`}>{sentimentInfo.text}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-2xl font-bold ${getSentimentColor(data.score)}`}>{data.score}</p>
                        <p className="text-xs text-[#A1A1AA]">{data.confidence}% conf</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Latest Headlines */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Latest Headlines</h2>
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {trendingNews.slice(0, 8).map((news, i) => (
                  <div
                    key={i}
                    className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg hover:border-[#555] transition"
                  >
                    <p className="text-white text-sm line-clamp-2">{news.title}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-[#A1A1AA]">
                      <span>{news.source}</span>
                      <span>•</span>
                      <span>{formatTimeAgo(news.published_at)}</span>
                      {news.currencies?.length > 0 && (
                        <>
                          <span>•</span>
                          <span className="text-[#9D00FF]">{news.currencies.join(', ')}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'trending' && (
          <motion.div
            key="trending"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-4">
              <Flame className="text-orange-400" />
              <h2 className="text-lg font-semibold text-white">Trending News</h2>
            </div>
            {renderSearchBar(trendingSearch, setTrendingSearch, filteredTrending.length)}
            <div className="space-y-3">
              {filteredTrending.map((news, i) => (
                <div
                  key={i}
                  className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg hover:border-[#555] transition"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-white font-medium">{news.title}</p>
                      <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-[#A1A1AA]">
                        <span className="bg-[#333] px-2 py-0.5 rounded">{news.source}</span>
                        <span>{formatTimeAgo(news.published_at)}</span>
                        {news.currencies?.length > 0 && (
                          <span className="text-[#9D00FF]">${news.currencies.join(', $')}</span>
                        )}
                      </div>
                    </div>
                    {news.votes && (
                      <div className="flex items-center gap-3 text-sm">
                        <span className="flex items-center gap-1 text-[#00FF94]">
                          <ThumbsUp size={14} />
                          {news.votes.positive || 0}
                        </span>
                        <span className="flex items-center gap-1 text-red-400">
                          <ThumbsDown size={14} />
                          {news.votes.negative || 0}
                        </span>
                      </div>
                    )}
                  </div>
                  {news.url && (
                    <a
                      href={news.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-2 text-sm text-[#9D00FF] hover:underline"
                    >
                      Read more <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'bullish' && (
          <motion.div
            key="bullish"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="text-[#00FF94]" />
              <h2 className="text-lg font-semibold text-white">Bullish News</h2>
              <span className="text-sm text-[#A1A1AA]">({bullishNews.length} articles)</span>
            </div>
            {renderSearchBar(bullishSearch, setBullishSearch, filteredBullish.length)}
            {filteredBullish.length === 0 ? (
              <div className="text-center py-8 text-[#A1A1AA]">No bullish news at the moment</div>
            ) : (
              <div className="space-y-3">
                {filteredBullish.map((news, i) => (
                  <div
                    key={i}
                    className="p-4 bg-[#00FF94]/5 border border-[#00FF94]/20 rounded-lg"
                  >
                    <p className="text-white">{news.title}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-[#A1A1AA]">
                      <span>{news.source}</span>
                      <span>•</span>
                      <span>{formatTimeAgo(news.published_at)}</span>
                      {news.currencies?.length > 0 && (
                        <span className="text-[#00FF94]">${news.currencies.join(', $')}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'bearish' && (
          <motion.div
            key="bearish"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="text-red-400" />
              <h2 className="text-lg font-semibold text-white">Bearish News</h2>
              <span className="text-sm text-[#A1A1AA]">({bearishNews.length} articles)</span>
            </div>
            {renderSearchBar(bearishSearch, setBearishSearch, filteredBearish.length)}
            {filteredBearish.length === 0 ? (
              <div className="text-center py-8 text-[#A1A1AA]">No bearish news at the moment</div>
            ) : (
              <div className="space-y-3">
                {filteredBearish.map((news, i) => (
                  <div
                    key={i}
                    className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg"
                  >
                    <p className="text-white">{news.title}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-[#A1A1AA]">
                      <span>{news.source}</span>
                      <span>•</span>
                      <span>{formatTimeAgo(news.published_at)}</span>
                      {news.currencies?.length > 0 && (
                        <span className="text-red-400">${news.currencies.join(', $')}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'coin' && (
          <motion.div
            key="coin"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Coin Selector */}
            <div className="flex gap-2 flex-wrap">
              {coins.map((coin) => (
                <button
                  key={coin.id}
                  onClick={() => setSelectedCoin(coin.id)}
                  className={`px-4 py-2 rounded-lg transition ${
                    selectedCoin === coin.id
                      ? 'bg-[#9D00FF] text-white'
                      : 'bg-[#1F1F1F] text-[#A1A1AA] hover:bg-[#2a2a2a]'
                  }`}
                >
                  {coin.symbol}
                </button>
              ))}
            </div>

            {coinSentiment && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Sentiment Score */}
                <div className={`p-6 rounded-xl border ${getSentimentBg(coinSentiment.score)}`}>
                  <div className="text-center">
                    <p className="text-sm text-[#A1A1AA] mb-2">Sentiment Score</p>
                    <p className={`text-6xl font-bold ${getSentimentColor(coinSentiment.score)}`}>
                      {coinSentiment.score}
                    </p>
                    <p className={`text-xl mt-2 capitalize ${getSentimentColor(coinSentiment.score)}`}>
                      {coinSentiment.label?.replace('_', ' ')}
                    </p>
                    <p className="text-sm text-[#A1A1AA] mt-2">
                      Confidence: {coinSentiment.confidence}% | {coinSentiment.news_count} news analyzed
                    </p>
                  </div>
                </div>

                {/* Summary & Factors */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-3">Analysis Summary</h3>
                  <p className="text-[#A1A1AA] mb-4">{coinSentiment.summary}</p>
                  
                  {coinSentiment.key_factors?.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm text-[#A1A1AA] mb-2">Key Factors:</p>
                      <ul className="space-y-1">
                        {coinSentiment.key_factors.map((factor, i) => (
                          <li key={i} className="text-white text-sm flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-[#9D00FF] rounded-full" />
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    {coinSentiment.bullish_signals?.length > 0 && (
                      <div>
                        <p className="text-sm text-[#00FF94] mb-2 flex items-center gap-1">
                          <TrendingUp size={14} /> Bullish Signals
                        </p>
                        <ul className="space-y-1">
                          {coinSentiment.bullish_signals.map((signal, i) => (
                            <li key={i} className="text-xs text-[#A1A1AA]">• {signal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {coinSentiment.bearish_signals?.length > 0 && (
                      <div>
                        <p className="text-sm text-red-400 mb-2 flex items-center gap-1">
                          <TrendingDown size={14} /> Bearish Signals
                        </p>
                        <ul className="space-y-1">
                          {coinSentiment.bearish_signals.map((signal, i) => (
                            <li key={i} className="text-xs text-[#A1A1AA]">• {signal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                {/* Recent Headlines */}
                <div className="md:col-span-2 bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-3">Recent Headlines</h3>
                  <div className="space-y-2">
                    {coinSentiment.recent_headlines?.map((headline, i) => (
                      <div
                        key={i}
                        className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                      >
                        <p className="text-white text-sm">{headline}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NewsSentiment;
