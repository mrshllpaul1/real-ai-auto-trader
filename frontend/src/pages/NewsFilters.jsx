import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Newspaper, TrendingUp, TrendingDown, AlertTriangle, 
  Search, RefreshCw, ExternalLink, Clock, Filter,
  Flame, Star, Zap, BarChart3, Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const NewsFilters = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('trending');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCoin, setSelectedCoin] = useState('all');
  const [marketOverview, setMarketOverview] = useState(null);
  const [coinSentiment, setCoinSentiment] = useState(null);

  // Popular coins for filtering
  const popularCoins = [
    { id: 'all', name: 'All Coins' },
    { id: 'BTC', name: 'Bitcoin' },
    { id: 'ETH', name: 'Ethereum' },
    { id: 'SOL', name: 'Solana' },
    { id: 'XRP', name: 'Ripple' },
    { id: 'ADA', name: 'Cardano' },
    { id: 'DOGE', name: 'Dogecoin' },
    { id: 'DOT', name: 'Polkadot' },
    { id: 'AVAX', name: 'Avalanche' },
  ];

  const loadNews = useCallback(async (filter = activeFilter) => {
    setLoading(true);
    try {
      let endpoint = `/news/${filter}`;
      if (selectedCoin !== 'all') {
        endpoint = `/news/coin/${selectedCoin}?filter=${filter}`;
      }
      
      const response = await api.get(endpoint, { params: { limit: 30 } });
      setNews(response.data?.news || []);
    } catch (error) {
      console.error('Error loading news:', error);
      toast.error('Failed to load news');
    } finally {
      setLoading(false);
    }
  }, [activeFilter, selectedCoin]);

  const loadMarketOverview = async () => {
    try {
      const response = await api.get('/news/market-overview');
      setMarketOverview(response.data);
    } catch (error) {
      console.error('Error loading market overview:', error);
    }
  };

  const loadCoinSentiment = async (coin) => {
    if (coin === 'all') {
      setCoinSentiment(null);
      return;
    }
    try {
      const response = await api.get(`/news/sentiment/${coin}`);
      setCoinSentiment(response.data);
    } catch (error) {
      console.error('Error loading coin sentiment:', error);
    }
  };

  useEffect(() => {
    loadNews();
    loadMarketOverview();
    
    const interval = setInterval(() => {
      loadNews();
      loadMarketOverview();
    }, 60000); // Refresh every minute
    
    return () => clearInterval(interval);
  }, [loadNews]);

  useEffect(() => {
    loadCoinSentiment(selectedCoin);
  }, [selectedCoin]);

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
    loadNews(filter);
  };

  const handleCoinChange = (coin) => {
    setSelectedCoin(coin);
  };

  const filteredNews = news.filter(item => {
    if (!searchTerm) return true;
    return item.title?.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'text-[#A1A1AA]';
    if (sentiment.includes('bullish') || sentiment === 'positive') return 'text-[#00FF94]';
    if (sentiment.includes('bearish') || sentiment === 'negative') return 'text-[#FF0055]';
    return 'text-[#FFB800]';
  };

  const getSentimentBg = (score) => {
    if (score >= 70) return 'bg-[#00FF94]/20 border-[#00FF94]/30';
    if (score <= 30) return 'bg-[#FF0055]/20 border-[#FF0055]/30';
    return 'bg-[#FFB800]/20 border-[#FFB800]/30';
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="news-filters-page">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between flex-wrap gap-4"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2">
            <Newspaper className="inline mr-3 text-[#9D00FF]" size={48} />
            <span className="text-[#9D00FF]">News</span> & Sentiment
          </h1>
          <p className="text-[#A1A1AA]">Real-time crypto news filtered by sentiment • Powered by CryptoPanic</p>
        </div>
        <Button 
          onClick={() => { loadNews(); loadMarketOverview(); }} 
          variant="outline" 
          className="border-[#1F1F1F]"
          disabled={loading}
        >
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </motion.div>

      {/* Market Overview */}
      {marketOverview && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className={`border ${getSentimentBg(marketOverview.market_sentiment_score)}`}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-3">
                <BarChart3 className="text-[#9D00FF]" />
                Market Sentiment Overview
                <Badge className={getSentimentColor(marketOverview.market_sentiment_label)}>
                  {marketOverview.market_sentiment_label?.toUpperCase()}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-white">
                    {(marketOverview?.market_sentiment_score ?? 0).toFixed(0)}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">Sentiment Score</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-[#00FF94]">
                    {marketOverview.bullish_news_count || 0}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">Bullish News</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-[#FF0055]">
                    {marketOverview.bearish_news_count || 0}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">Bearish News</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-[#FFB800]">
                    {marketOverview.important_news_count || 0}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">Important</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-[#007AFF]">
                    {marketOverview.trending_news_count || 0}
                  </div>
                  <div className="text-xs text-[#A1A1AA]">Trending</div>
                </div>
              </div>
              
              {/* Top Currencies */}
              {marketOverview.top_currencies?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#1F1F1F]">
                  <div className="text-xs text-[#A1A1AA] mb-2">Top Mentioned Coins</div>
                  <div className="flex flex-wrap gap-2">
                    {marketOverview.top_currencies.slice(0, 8).map((coin, i) => (
                      <Badge 
                        key={i} 
                        variant="outline" 
                        className="border-[#1F1F1F] cursor-pointer hover:border-[#9D00FF]"
                        onClick={() => handleCoinChange(coin.symbol)}
                      >
                        {coin.symbol} ({coin.mentions})
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Coin Sentiment (when a specific coin is selected) */}
      {coinSentiment && selectedCoin !== 'all' && (
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <Card className={`border ${getSentimentBg(coinSentiment.sentiment === 'bullish' ? 80 : coinSentiment.sentiment === 'bearish' ? 20 : 50)}`}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-3">
                <Sparkles className="text-[#FFB800]" />
                {selectedCoin} AI Sentiment Analysis
                <Badge className={getSentimentColor(coinSentiment.sentiment)}>
                  {coinSentiment.sentiment?.toUpperCase()}
                </Badge>
                <span className="text-sm text-[#A1A1AA]">
                  Confidence: {(coinSentiment.confidence * 100)?.toFixed(0)}%
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {coinSentiment.ai_analysis && (
                <p className="text-sm text-[#A1A1AA] whitespace-pre-wrap">
                  {coinSentiment.ai_analysis}
                </p>
              )}
              {coinSentiment.recent_headlines?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#1F1F1F]">
                  <div className="text-xs text-[#A1A1AA] mb-2">Recent Headlines</div>
                  {coinSentiment.recent_headlines.slice(0, 3).map((headline, i) => (
                    <div key={i} className="text-sm text-white py-1">• {headline}</div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex flex-col md:flex-row gap-4"
      >
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" size={18} />
          <Input
            placeholder="Search news..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-[#0A0A0A] border-[#1F1F1F]"
            data-testid="news-search"
          />
        </div>

        {/* Coin Filter */}
        <Select value={selectedCoin} onValueChange={handleCoinChange}>
          <SelectTrigger className="w-[200px] bg-[#0A0A0A] border-[#1F1F1F]" data-testid="coin-filter">
            <Filter size={16} className="mr-2" />
            <SelectValue placeholder="Filter by coin" />
          </SelectTrigger>
          <SelectContent className="bg-[#0A0A0A] border-[#1F1F1F]">
            {popularCoins.map(coin => (
              <SelectItem key={coin.id} value={coin.id}>{coin.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </motion.div>

      {/* News Tabs */}
      <Tabs value={activeFilter} onValueChange={handleFilterChange} className="w-full">
        <TabsList className="grid grid-cols-5 bg-[#0A0A0A] p-1" data-testid="news-tabs">
          <TabsTrigger value="trending" className="data-[state=active]:bg-[#9D00FF]">
            <Flame size={16} className="mr-2" />
            Trending
          </TabsTrigger>
          <TabsTrigger value="hot" className="data-[state=active]:bg-[#FF9500]">
            <Zap size={16} className="mr-2" />
            Hot
          </TabsTrigger>
          <TabsTrigger value="bullish" className="data-[state=active]:bg-[#00FF94]">
            <TrendingUp size={16} className="mr-2" />
            Bullish
          </TabsTrigger>
          <TabsTrigger value="bearish" className="data-[state=active]:bg-[#FF0055]">
            <TrendingDown size={16} className="mr-2" />
            Bearish
          </TabsTrigger>
          <TabsTrigger value="important" className="data-[state=active]:bg-[#FFB800]">
            <Star size={16} className="mr-2" />
            Important
          </TabsTrigger>
        </TabsList>

        {/* News Content */}
        <TabsContent value={activeFilter} className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw size={32} className="animate-spin text-[#9D00FF]" />
            </div>
          ) : filteredNews.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-20 text-center">
                <Newspaper size={48} className="mx-auto mb-4 text-[#A1A1AA]" />
                <p className="text-[#A1A1AA]">No news found for this filter</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              <AnimatePresence mode="popLayout">
                {filteredNews.map((item, index) => (
                  <motion.div
                    key={item.id || index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="font-bold text-white mb-2 leading-tight">
                              {item.title}
                            </h3>
                            <div className="flex flex-wrap items-center gap-2 text-xs text-[#A1A1AA]">
                              {item.source && (
                                <Badge variant="outline" className="border-[#1F1F1F]">
                                  {item.source}
                                </Badge>
                              )}
                              {item.published_at && (
                                <span className="flex items-center gap-1">
                                  <Clock size={12} />
                                  {new Date(item.published_at).toLocaleDateString()}
                                </span>
                              )}
                              {item.currencies?.length > 0 && (
                                <div className="flex gap-1">
                                  {item.currencies.slice(0, 3).map((c, i) => (
                                    <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF]">
                                      {c}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                          {item.url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="shrink-0"
                              onClick={() => window.open(item.url, '_blank')}
                            >
                              <ExternalLink size={16} />
                            </Button>
                          )}
                        </div>
                        
                        {/* Vote sentiment if available */}
                        {item.votes?.sentiment && (
                          <div className="mt-3 pt-3 border-t border-[#1F1F1F]">
                            <span className={`text-xs ${getSentimentColor(item.votes.sentiment)}`}>
                              Community: {item.votes.sentiment.toUpperCase()}
                            </span>
                            {item.votes.positive > 0 && (
                              <span className="ml-3 text-xs text-[#A1A1AA]">
                                👍 {item.votes.positive} 👎 {item.votes.negative}
                              </span>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NewsFilters;
