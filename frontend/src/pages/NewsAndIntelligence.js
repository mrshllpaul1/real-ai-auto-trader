import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Newspaper, TrendingUp, Brain, History, Zap, AlertCircle, ExternalLink, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import api, { coindeskAPI } from '../services/api';
import { toast } from 'sonner';

const NewsAndIntelligence = () => {
  const [news, setNews] = useState([]);
  const [coindeskNews, setCoindeskNews] = useState([]);
  const [coindeskSentiment, setCoindeskSentiment] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCoin, setSelectedCoin] = useState('bitcoin');
  const [activeTab, setActiveTab] = useState('coindesk');

  useEffect(() => {
    loadData();
    loadCoinDeskData();
  }, [selectedCoin]);

  const loadCoinDeskData = async () => {
    try {
      const [newsRes, sentimentRes] = await Promise.all([
        coindeskAPI.getNews(20).catch(() => ({ data: { articles: [] } })),
        coindeskAPI.getSentiment().catch(() => ({ data: null }))
      ]);
      
      setCoindeskNews(newsRes.data?.articles || []);
      setCoindeskSentiment(sentimentRes.data);
    } catch (error) {
      console.error('Error loading CoinDesk data:', error);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [newsRes, statusRes] = await Promise.all([
        api.get(`/news/all?currencies=${selectedCoin}&limit=10`).catch(() => ({ data: { news: [] } })),
        api.get('/training/status').catch(() => ({ data: { trained: false } }))
      ]);

      setNews(newsRes.data.news || []);
      setTrainingStatus(statusRes.data);

      // Get sentiment for selected coin
      try {
        const sentimentRes = await api.get(`/news/sentiment/${selectedCoin}`);
        setSentiment(sentimentRes.data);
      } catch (e) {
        console.log('Sentiment unavailable');
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerTraining = async () => {
    try {
      toast.loading('Starting historical training...');
      await api.post('/training/train', {
        coins: ['bitcoin', 'ethereum', 'solana'],
        start_year: 2009
      });
      toast.dismiss();
      toast.success('Training started! AI is learning from 16+ years of data.');
      setTimeout(loadData, 5000);
    } catch (error) {
      toast.dismiss();
      toast.error('Training failed');
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return '#00FF94';
      case 'negative': return '#FF0055';
      default: return '#007AFF';
    }
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="news-intelligence">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="news-title">
          <Newspaper className="inline mr-3" size={48} />
          <span className="text-[#00FF94]">Market</span> Intelligence
        </h1>
        <p className="text-[#A1A1AA]">
          Real-time news, sentiment analysis, and historical pattern recognition
        </p>
      </motion.div>

      {/* Training Status Card */}
      {trainingStatus && (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="training-status-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <History className="text-[#9D00FF]" size={24} />
                <div>
                  <CardTitle className="text-xl font-heading">Historical Training</CardTitle>
                  <CardDescription>
                    AI trained on 16+ years of crypto data (2009-2025)
                  </CardDescription>
                </div>
              </div>
              {!trainingStatus.trained && (
                <Button
                  onClick={triggerTraining}
                  className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
                  data-testid="start-training-btn"
                >
                  <Brain size={16} className="mr-2" />
                  Train AI
                </Button>
              )}
            </div>
          </CardHeader>
          {trainingStatus.trained && trainingStatus.summary && (
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Coins Trained</div>
                  <div className="text-2xl font-data font-bold text-[#9D00FF]">
                    {trainingStatus.summary.coins_trained?.length || 0}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Patterns Found</div>
                  <div className="text-2xl font-data font-bold text-[#00FF94]">
                    {trainingStatus.summary.total_patterns || 0}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Success Rate</div>
                  <div className="text-2xl font-data font-bold text-[#007AFF]">
                    {trainingStatus.summary.training_accuracy?.toFixed(1) || 0}%
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Status</div>
                  <Badge className="bg-[#00FF94]/20 text-[#00FF94] border-[#00FF94]/30">
                    <Zap size={12} className="mr-1" />
                    Trained
                  </Badge>
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Coin Selector */}
      <Tabs value={selectedCoin} onValueChange={setSelectedCoin} className="space-y-4">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="bitcoin" data-testid="bitcoin-tab">Bitcoin</TabsTrigger>
          <TabsTrigger value="ethereum" data-testid="ethereum-tab">Ethereum</TabsTrigger>
          <TabsTrigger value="solana" data-testid="solana-tab">Solana</TabsTrigger>
        </TabsList>

        {/* Sentiment Analysis */}
        {sentiment && (
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="sentiment-card">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-3">
                <TrendingUp className="text-[#00FF94]" />
                News Sentiment: {selectedCoin.toUpperCase()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-6 mb-4">
                <div className="flex-1">
                  <div className="text-sm text-[#A1A1AA] mb-2">Overall Sentiment</div>
                  <Badge
                    className="text-lg px-4 py-2"
                    style={{
                      backgroundColor: `${getSentimentColor(sentiment.sentiment)}20`,
                      color: getSentimentColor(sentiment.sentiment),
                      border: `1px solid ${getSentimentColor(sentiment.sentiment)}40`
                    }}
                  >
                    {sentiment.sentiment?.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex-1">
                  <div className="text-sm text-[#A1A1AA] mb-2">Confidence</div>
                  <div className="text-3xl font-data font-bold" style={{ color: getSentimentColor(sentiment.sentiment) }}>
                    {sentiment.confidence?.toFixed(1) || 0}%
                  </div>
                </div>
                <div className="flex-1">
                  <div className="text-sm text-[#A1A1AA] mb-2">News Analyzed</div>
                  <div className="text-3xl font-data font-bold text-white">
                    {sentiment.news_count || 0}
                  </div>
                </div>
              </div>

              {sentiment.ai_analysis && (
                <div className="bg-[#121212] border border-[#9D00FF]/20 rounded-lg p-4">
                  <h4 className="text-sm font-bold text-[#9D00FF] mb-2 flex items-center gap-2">
                    <Brain size={14} />
                    AI Analysis
                  </h4>
                  <p className="text-sm text-[#A1A1AA] whitespace-pre-wrap">
                    {sentiment.ai_analysis?.substring(0, 300)}...
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* News Feed */}
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="news-feed-card">
          <CardHeader>
            <CardTitle className="text-xl font-heading flex items-center gap-3">
              <Newspaper className="text-[#007AFF]" />
              Latest News: {selectedCoin.toUpperCase()}
            </CardTitle>
            <CardDescription>
              Aggregated from multiple crypto news sources
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-48">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#00FF94]" />
              </div>
            ) : news.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle size={48} className="mx-auto mb-4 text-[#007AFF] opacity-50" />
                <p className="text-[#A1A1AA]">
                  No news available at the moment. News sources are updating...
                </p>
              </div>
            ) : (
              <div className="space-y-3" data-testid="news-list">
                {news.map((item, index) => (
                  <div
                    key={index}
                    className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F] hover:border-[#00FF94]/50 transition-all cursor-pointer"
                    onClick={() => item.url && window.open(item.url, '_blank')}
                    data-testid={`news-item-${index}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-bold text-white mb-2">{item.title}</h3>
                        <div className="flex items-center gap-3 text-xs text-[#A1A1AA]">
                          <span>{item.source}</span>
                          <span>•</span>
                          <span>{new Date(item.published_at).toLocaleDateString()}</span>
                          {item.sentiment && (
                            <>
                              <span>•</span>
                              <Badge
                                className="text-xs"
                                style={{
                                  backgroundColor: `${getSentimentColor(item.sentiment)}20`,
                                  color: getSentimentColor(item.sentiment),
                                  border: `1px solid ${getSentimentColor(item.sentiment)}40`
                                }}
                              >
                                {item.sentiment}
                              </Badge>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </Tabs>
    </div>
  );
};

export default NewsAndIntelligence;
