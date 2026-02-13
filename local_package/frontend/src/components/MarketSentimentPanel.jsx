import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, TrendingDown, Minus, Newspaper, 
  RefreshCw, Loader2, ChevronDown, ChevronUp,
  AlertCircle, CheckCircle, XCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const SentimentIndicator = ({ score, label, size = 'md' }) => {
  const getColor = () => {
    if (score >= 70) return 'text-[#00FF94]';
    if (score >= 55) return 'text-[#90EE90]';
    if (score >= 45) return 'text-[#A1A1AA]';
    if (score >= 30) return 'text-[#FFB800]';
    return 'text-red-500';
  };

  const getIcon = () => {
    if (score >= 60) return <TrendingUp size={size === 'sm' ? 14 : 18} />;
    if (score <= 40) return <TrendingDown size={size === 'sm' ? 14 : 18} />;
    return <Minus size={size === 'sm' ? 14 : 18} />;
  };

  const getBgColor = () => {
    if (score >= 70) return 'bg-[#00FF94]/20';
    if (score >= 55) return 'bg-[#00FF94]/10';
    if (score >= 45) return 'bg-[#1F1F1F]';
    if (score >= 30) return 'bg-[#FFB800]/10';
    return 'bg-red-500/20';
  };

  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${getBgColor()}`}>
      <span className={getColor()}>{getIcon()}</span>
      <span className={`font-bold ${size === 'sm' ? 'text-xs' : 'text-sm'} ${getColor()}`}>
        {score}
      </span>
      {label && (
        <span className={`${size === 'sm' ? 'text-xs' : 'text-sm'} text-[#71717A] capitalize`}>
          {label}
        </span>
      )}
    </div>
  );
};

const MarketSentimentPanel = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const loadMarketSentiment = useCallback(async () => {
    try {
      const response = await api.get('/sentiment/market');
      setMarketData(response.data);
    } catch (error) {
      console.error('Market sentiment error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadMarketSentiment();
    // Refresh every 10 minutes
    const interval = setInterval(loadMarketSentiment, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadMarketSentiment]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadMarketSentiment();
    toast.success('Sentiment refreshed');
  };

  if (loading) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="animate-spin mr-2" />
          Analyzing market sentiment...
        </CardContent>
      </Card>
    );
  }

  const getMarketMood = () => {
    const score = marketData?.market_score || 50;
    if (score >= 70) return { text: 'Bullish', color: 'text-[#00FF94]', bg: 'bg-[#00FF94]/20' };
    if (score >= 55) return { text: 'Slightly Bullish', color: 'text-[#90EE90]', bg: 'bg-[#00FF94]/10' };
    if (score >= 45) return { text: 'Neutral', color: 'text-[#A1A1AA]', bg: 'bg-[#1F1F1F]' };
    if (score >= 30) return { text: 'Slightly Bearish', color: 'text-[#FFB800]', bg: 'bg-[#FFB800]/10' };
    return { text: 'Bearish', color: 'text-red-500', bg: 'bg-red-500/20' };
  };

  const mood = getMarketMood();

  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Newspaper className="text-[#007AFF]" size={20} />
            AI News Sentiment
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-[#A1A1AA]"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="text-[#A1A1AA]"
            >
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Market Overview */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-[#1F1F1F]/50 mb-4">
          <div>
            <div className="text-xs text-[#71717A] mb-1">Market Mood</div>
            <div className={`text-xl font-bold ${mood.color}`}>{mood.text}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-[#71717A] mb-1">Sentiment Score</div>
            <div className={`text-3xl font-bold ${mood.color}`}>
              {marketData?.market_score?.toFixed(0) || 50}
            </div>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-xs text-[#71717A] mb-1">
            <span>Analysis Confidence</span>
            <span>{marketData?.confidence?.toFixed(0) || 50}%</span>
          </div>
          <div className="h-2 bg-[#1F1F1F] rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-[#007AFF] to-[#9D00FF] transition-all duration-500"
              style={{ width: `${marketData?.confidence || 50}%` }}
            />
          </div>
        </div>

        <AnimatePresence>
          {expanded && marketData?.coin_sentiments && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              {/* Individual Coin Sentiments */}
              <div>
                <h4 className="text-sm font-medium mb-2 text-[#A1A1AA]">Top Coins Sentiment</h4>
                <div className="space-y-2">
                  {Object.entries(marketData.coin_sentiments).map(([coinId, sentiment]) => (
                    <div 
                      key={coinId}
                      className="flex items-center justify-between p-2 rounded-lg bg-[#1F1F1F]/30"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white capitalize">
                          {coinId.replace('-', ' ')}
                        </span>
                        <span className="text-xs text-[#71717A]">
                          {sentiment.symbol}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <SentimentIndicator 
                          score={sentiment.score} 
                          label={sentiment.label}
                          size="sm"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sentiment Signals */}
              {Object.values(marketData.coin_sentiments).some(s => s.bullish_signals?.length > 0 || s.bearish_signals?.length > 0) && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <h4 className="text-xs font-medium mb-2 flex items-center gap-1 text-[#00FF94]">
                      <CheckCircle size={12} />
                      Bullish Signals
                    </h4>
                    <div className="space-y-1">
                      {Object.values(marketData.coin_sentiments)
                        .flatMap(s => s.bullish_signals || [])
                        .slice(0, 5)
                        .map((signal, i) => (
                          <div key={i} className="text-xs text-[#A1A1AA] truncate">
                            • {signal}
                          </div>
                        ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium mb-2 flex items-center gap-1 text-red-400">
                      <XCircle size={12} />
                      Bearish Signals
                    </h4>
                    <div className="space-y-1">
                      {Object.values(marketData.coin_sentiments)
                        .flatMap(s => s.bearish_signals || [])
                        .slice(0, 5)
                        .map((signal, i) => (
                          <div key={i} className="text-xs text-[#A1A1AA] truncate">
                            • {signal}
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Info */}
              <div className="text-xs text-[#71717A] text-center">
                Last updated: {new Date(marketData.analyzed_at).toLocaleTimeString()}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};

export { SentimentIndicator };
export default MarketSentimentPanel;
