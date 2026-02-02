import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Newspaper, TrendingUp, TrendingDown, Flame, 
  ExternalLink, RefreshCw, Loader2, Clock
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const formatTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

const NewsItem = ({ item }) => (
  <motion.a
    href={item.url}
    target="_blank"
    rel="noopener noreferrer"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="block p-3 rounded-lg bg-[#1F1F1F]/50 hover:bg-[#1F1F1F] transition-colors border border-transparent hover:border-[#2F2F2F]"
  >
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-white line-clamp-2 mb-1">
          {item.title}
        </h4>
        <div className="flex items-center gap-2 text-xs text-[#71717A]">
          <span>{item.source}</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Clock size={10} />
            {formatTime(item.published_at)}
          </span>
        </div>
      </div>
      <div className="flex flex-col items-end gap-1">
        {item.currencies?.length > 0 && (
          <div className="flex gap-1">
            {item.currencies.slice(0, 3).map((curr, i) => (
              <Badge 
                key={i}
                variant="outline"
                className="text-[10px] px-1.5 py-0 border-[#2F2F2F] text-[#A1A1AA]"
              >
                {curr}
              </Badge>
            ))}
          </div>
        )}
        {item.panic_score !== null && item.panic_score !== undefined && (
          <Badge 
            className={`text-[10px] ${
              item.panic_score >= 60 
                ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                : item.panic_score <= 40 
                  ? 'bg-red-500/20 text-red-400'
                  : 'bg-[#1F1F1F] text-[#A1A1AA]'
            }`}
          >
            Score: {item.panic_score}
          </Badge>
        )}
        <ExternalLink size={12} className="text-[#71717A]" />
      </div>
    </div>
    {item.votes && (item.votes.positive > 0 || item.votes.negative > 0) && (
      <div className="flex items-center gap-3 mt-2 text-xs">
        {item.votes.positive > 0 && (
          <span className="text-[#00FF94]">👍 {item.votes.positive}</span>
        )}
        {item.votes.negative > 0 && (
          <span className="text-red-400">👎 {item.votes.negative}</span>
        )}
        {item.votes.important > 0 && (
          <span className="text-[#FFB800]">⭐ {item.votes.important}</span>
        )}
      </div>
    )}
  </motion.a>
);

const CryptoNewsFeed = () => {
  const [activeTab, setActiveTab] = useState('trending');
  const [trendingNews, setTrendingNews] = useState([]);
  const [bullishNews, setBullishNews] = useState([]);
  const [bearishNews, setBearishNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadNews = useCallback(async () => {
    try {
      const [trendingRes, bullishRes, bearishRes] = await Promise.all([
        api.get('/sentiment/trending?limit=15'),
        api.get('/sentiment/news/bullish'),
        api.get('/sentiment/news/bearish')
      ]);
      
      setTrendingNews(trendingRes.data.news || []);
      setBullishNews(bullishRes.data.news || []);
      setBearishNews(bearishRes.data.news || []);
    } catch (error) {
      console.error('News load error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadNews();
    // Refresh every 5 minutes
    const interval = setInterval(loadNews, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadNews]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadNews();
    toast.success('News refreshed');
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const NewsItem = ({ item, type }) => (
    <motion.a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="block p-3 rounded-lg bg-[#1F1F1F]/50 hover:bg-[#1F1F1F] transition-colors border border-transparent hover:border-[#2F2F2F]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-white line-clamp-2 mb-1">
            {item.title}
          </h4>
          <div className="flex items-center gap-2 text-xs text-[#71717A]">
            <span>{item.source}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock size={10} />
              {formatTime(item.published_at)}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {item.currencies?.length > 0 && (
            <div className="flex gap-1">
              {item.currencies.slice(0, 3).map((curr, i) => (
                <Badge 
                  key={i}
                  variant="outline"
                  className="text-[10px] px-1.5 py-0 border-[#2F2F2F] text-[#A1A1AA]"
                >
                  {curr}
                </Badge>
              ))}
            </div>
          )}
          {item.panic_score !== null && item.panic_score !== undefined && (
            <Badge 
              className={`text-[10px] ${
                item.panic_score >= 60 
                  ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                  : item.panic_score <= 40 
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-[#1F1F1F] text-[#A1A1AA]'
              }`}
            >
              Score: {item.panic_score}
            </Badge>
          )}
          <ExternalLink size={12} className="text-[#71717A]" />
        </div>
      </div>
      {item.votes && (item.votes.positive > 0 || item.votes.negative > 0) && (
        <div className="flex items-center gap-3 mt-2 text-xs">
          {item.votes.positive > 0 && (
            <span className="text-[#00FF94]">👍 {item.votes.positive}</span>
          )}
          {item.votes.negative > 0 && (
            <span className="text-red-400">👎 {item.votes.negative}</span>
          )}
          {item.votes.important > 0 && (
            <span className="text-[#FFB800]">⭐ {item.votes.important}</span>
          )}
        </div>
      )}
    </motion.a>
  );

  if (loading) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="animate-spin mr-2" />
          Loading crypto news...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Newspaper className="text-[#007AFF]" size={20} />
            Crypto News Feed
            <Badge className="bg-[#007AFF]/20 text-[#007AFF] text-xs">Live</Badge>
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-[#A1A1AA]"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-3 bg-[#1F1F1F] mb-4">
            <TabsTrigger 
              value="trending"
              className="data-[state=active]:bg-[#007AFF] data-[state=active]:text-white"
            >
              <Flame size={14} className="mr-1" />
              Trending
            </TabsTrigger>
            <TabsTrigger 
              value="bullish"
              className="data-[state=active]:bg-[#00FF94] data-[state=active]:text-black"
            >
              <TrendingUp size={14} className="mr-1" />
              Bullish
            </TabsTrigger>
            <TabsTrigger 
              value="bearish"
              className="data-[state=active]:bg-red-500 data-[state=active]:text-white"
            >
              <TrendingDown size={14} className="mr-1" />
              Bearish
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trending" className="space-y-2 max-h-[400px] overflow-y-auto">
            {trendingNews.length > 0 ? (
              trendingNews.map((item, i) => (
                <NewsItem key={i} item={item} type="trending" />
              ))
            ) : (
              <div className="text-center py-8 text-[#71717A]">
                <Newspaper size={32} className="mx-auto mb-2 opacity-50" />
                <p>No trending news available</p>
                <p className="text-xs mt-1">Configure CRYPTOPANIC_API_KEY for live news</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="bullish" className="space-y-2 max-h-[400px] overflow-y-auto">
            {bullishNews.length > 0 ? (
              bullishNews.map((item, i) => (
                <NewsItem key={i} item={item} type="bullish" />
              ))
            ) : (
              <div className="text-center py-8 text-[#71717A]">
                <TrendingUp size={32} className="mx-auto mb-2 opacity-50 text-[#00FF94]" />
                <p>No bullish news available</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="bearish" className="space-y-2 max-h-[400px] overflow-y-auto">
            {bearishNews.length > 0 ? (
              bearishNews.map((item, i) => (
                <NewsItem key={i} item={item} type="bearish" />
              ))
            ) : (
              <div className="text-center py-8 text-[#71717A]">
                <TrendingDown size={32} className="mx-auto mb-2 opacity-50 text-red-400" />
                <p>No bearish news available</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* CryptoPanic Attribution */}
        <div className="text-center text-xs text-[#71717A] mt-4 pt-3 border-t border-[#1F1F1F]">
          Powered by{' '}
          <a 
            href="https://cryptopanic.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-[#007AFF] hover:underline"
          >
            CryptoPanic
          </a>
        </div>
      </CardContent>
    </Card>
  );
};

export default CryptoNewsFeed;
