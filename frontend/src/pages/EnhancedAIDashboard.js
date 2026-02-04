import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, TrendingUp, TrendingDown, RefreshCw, Activity, Zap,
  BarChart3, Target, Shield, AlertTriangle, Clock, Layers,
  ArrowUpRight, ArrowDownRight, Gauge, Eye, Radar
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const EnhancedAIDashboard = () => {
  const [scanResults, setScanResults] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState('BTC');
  const [coinSignal, setCoinSignal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sentRes, scanRes] = await Promise.all([
        api.get('/enhanced-ai/sentiment').catch(() => ({ data: null })),
        api.get('/enhanced-ai/scan-top-coins?limit=15').catch(() => ({ data: null }))
      ]);
      
      setSentiment(sentRes.data);
      setScanResults(scanRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCoinSignal = useCallback(async (coin) => {
    try {
      const res = await api.get(`/enhanced-ai/signal/${coin}`);
      setCoinSignal(res.data);
    } catch (error) {
      console.error('Error loading signal:', error);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (selectedCoin) {
      loadCoinSignal(selectedCoin);
    }
  }, [selectedCoin, loadCoinSignal]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await api.get('/enhanced-ai/scan-top-coins?limit=20');
      setScanResults(res.data);
      toast.success('Scan complete!');
    } catch (error) {
      toast.error('Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const getActionColor = (action) => {
    const colors = {
      'strong_buy': 'bg-[#00FF94] text-black',
      'buy': 'bg-[#00FF94]/70 text-black',
      'weak_buy': 'bg-[#00FF94]/40 text-white',
      'hold': 'bg-[#FFB800]/50 text-white',
      'weak_sell': 'bg-[#FF0055]/40 text-white',
      'sell': 'bg-[#FF0055]/70 text-white',
      'strong_sell': 'bg-[#FF0055] text-white'
    };
    return colors[action] || 'bg-[#1F1F1F] text-white';
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      'extreme_greed': 'text-[#FF0055]',
      'greed': 'text-[#FF6B00]',
      'neutral': 'text-[#FFB800]',
      'fear': 'text-[#00FF94]',
      'extreme_fear': 'text-[#00FF94]'
    };
    return colors[sentiment] || 'text-white';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#050505]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Enhanced AI...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] p-4 lg:p-8" data-testid="enhanced-ai-dashboard">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-[#9D00FF]/20 to-[#00FF94]/20 border border-[#9D00FF]/30">
                <Brain size={32} className="text-[#9D00FF]" />
              </div>
              <span className="text-white">Enhanced</span>
              <span className="bg-gradient-to-r from-[#9D00FF] to-[#00FF94] bg-clip-text text-transparent">AI Brain</span>
            </h1>
            <p className="text-[#A1A1AA]">
              Multi-model ensemble with sentiment, whale tracking & dynamic risk
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleScan}
              disabled={scanning}
              className="bg-[#9D00FF] hover:bg-[#9D00FF]/80"
              data-testid="scan-btn"
            >
              {scanning ? <RefreshCw size={16} className="mr-2 animate-spin" /> : <Radar size={16} className="mr-2" />}
              {scanning ? 'Scanning...' : 'Scan Market'}
            </Button>
            <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
              <RefreshCw size={16} />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Market Sentiment Card */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <Card className="bg-gradient-to-r from-[#0A0A0A] to-[#111] border-[#1F1F1F]">
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl bg-[#FFB800]/20 flex items-center justify-center">
                  <Gauge size={32} className="text-[#FFB800]" />
                </div>
                <div>
                  <p className="text-sm text-[#A1A1AA]">Market Sentiment</p>
                  <p className={`text-3xl font-bold capitalize ${getSentimentColor(sentiment?.sentiment)}`}>
                    {sentiment?.sentiment?.replace('_', ' ') || 'Loading...'}
                  </p>
                </div>
              </div>
              
              <div className="flex-1 max-w-md">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[#00FF94]">Fear</span>
                  <span className="text-white font-data">{sentiment?.overall_score || 50}</span>
                  <span className="text-[#FF0055]">Greed</span>
                </div>
                <div className="h-3 bg-gradient-to-r from-[#00FF94] via-[#FFB800] to-[#FF0055] rounded-full relative">
                  <div 
                    className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full border-2 border-[#1F1F1F] shadow-lg transition-all"
                    style={{ left: `calc(${sentiment?.overall_score || 50}% - 8px)` }}
                  />
                </div>
              </div>
              
              <div className="flex gap-6">
                <div className="text-center">
                  <p className="text-xs text-[#A1A1AA]">Fear & Greed</p>
                  <p className="text-xl font-data text-white">{sentiment?.components?.fear_greed || 50}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-[#A1A1AA]">News</p>
                  <p className="text-xl font-data text-white">{sentiment?.components?.news || 50}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-[#A1A1AA]">Social</p>
                  <p className="text-xl font-data text-white">{sentiment?.components?.social || 50}</p>
                </div>
              </div>
              
              <div className="text-center p-3 rounded-lg bg-[#1F1F1F]">
                <p className="text-xs text-[#A1A1AA]">Trading Bias</p>
                <p className="text-lg font-bold capitalize text-[#FFB800]">
                  {sentiment?.trading_bias?.action || 'hold'}
                </p>
                <p className="text-xs text-[#A1A1AA]">
                  {sentiment?.trading_bias?.size_multiplier || 1}x size
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coin Scanner Results */}
        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Radar className="text-[#9D00FF]" size={20} />
                AI Market Scanner
                <Badge className="ml-2 bg-[#9D00FF]/20 text-[#9D00FF]">
                  {scanResults?.coins_scanned || 0} coins
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {scanResults?.results?.map((coin, idx) => (
                  <div
                    key={coin.symbol}
                    onClick={() => setSelectedCoin(coin.symbol)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedCoin === coin.symbol 
                        ? 'bg-[#9D00FF]/10 border-[#9D00FF]/50' 
                        : 'bg-[#111] border-[#1F1F1F] hover:border-[#333]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                          coin.score > 0 ? 'bg-[#00FF94]/20 text-[#00FF94]' : 
                          coin.score < 0 ? 'bg-[#FF0055]/20 text-[#FF0055]' : 
                          'bg-[#FFB800]/20 text-[#FFB800]'
                        }`}>
                          {idx + 1}
                        </div>
                        <div>
                          <p className="text-white font-bold">{coin.symbol}</p>
                          <p className="text-xs text-[#A1A1AA]">{coin.mtf_alignment?.replace('_', ' ')}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-xs text-[#A1A1AA]">Score</p>
                          <p className={`font-data font-bold ${
                            coin.score > 0 ? 'text-[#00FF94]' : 
                            coin.score < 0 ? 'text-[#FF0055]' : 'text-[#FFB800]'
                          }`}>
                            {coin.score > 0 ? '+' : ''}{coin.score}
                          </p>
                        </div>
                        <Badge className={getActionColor(coin.action)}>
                          {coin.action?.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Selected Coin Details */}
        <motion.div
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Eye className="text-[#00FF94]" size={20} />
                {selectedCoin} Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {coinSignal ? (
                <>
                  {/* Recommendation */}
                  <div className={`p-4 rounded-lg ${getActionColor(coinSignal.recommendation?.action)}`}>
                    <p className="text-sm opacity-80">AI Recommendation</p>
                    <p className="text-2xl font-bold capitalize">
                      {coinSignal.recommendation?.action?.replace('_', ' ')}
                    </p>
                    <p className="text-sm">
                      Confidence: {coinSignal.recommendation?.confidence}%
                    </p>
                  </div>
                  
                  {/* Score Breakdown */}
                  <div className="space-y-3">
                    <p className="text-sm text-[#A1A1AA]">Score Breakdown</p>
                    {Object.entries(coinSignal.recommendation?.score_breakdown || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-[#A1A1AA] capitalize">{key}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-[#1F1F1F] rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${value > 0 ? 'bg-[#00FF94]' : value < 0 ? 'bg-[#FF0055]' : 'bg-[#FFB800]'}`}
                              style={{ width: `${Math.abs(value) * 25}%`, marginLeft: value < 0 ? 'auto' : 0 }}
                            />
                          </div>
                          <span className={`font-data w-8 text-right ${
                            value > 0 ? 'text-[#00FF94]' : value < 0 ? 'text-[#FF0055]' : 'text-[#FFB800]'
                          }`}>
                            {value > 0 ? '+' : ''}{value}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Position Sizing */}
                  <div className="p-3 rounded-lg bg-[#111] border border-[#1F1F1F]">
                    <div className="flex items-center justify-between">
                      <span className="text-[#A1A1AA]">Suggested Position</span>
                      <span className="text-[#9D00FF] font-data font-bold">
                        {coinSignal.position_sizing?.position_pct}%
                      </span>
                    </div>
                    <p className="text-xs text-[#A1A1AA] mt-1">
                      {coinSignal.position_sizing?.reason || 'Based on confidence & risk'}
                    </p>
                  </div>
                  
                  {/* Multi-Timeframe */}
                  <div className="space-y-2">
                    <p className="text-sm text-[#A1A1AA]">Timeframe Analysis</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(coinSignal.multi_timeframe?.timeframes || {}).map(([tf, data]) => (
                        <div key={tf} className="p-2 rounded bg-[#111] border border-[#1F1F1F]">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-[#A1A1AA] uppercase">{tf}</span>
                            <Badge className={
                              data.trend === 'bullish' ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                              data.trend === 'bearish' ? 'bg-[#FF0055]/20 text-[#FF0055]' :
                              'bg-[#FFB800]/20 text-[#FFB800]'
                            }>
                              {data.trend}
                            </Badge>
                          </div>
                          <p className="text-xs text-[#A1A1AA] mt-1">RSI: {data.rsi}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Whale Activity */}
                  {coinSignal.whale_activity && (
                    <div className="p-3 rounded-lg bg-[#111] border border-[#1F1F1F]">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity size={14} className="text-[#007AFF]" />
                        <span className="text-[#A1A1AA]">Whale Activity</span>
                      </div>
                      <Badge className={
                        coinSignal.whale_activity.accumulation_signal?.includes('accumulation') 
                          ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                          : coinSignal.whale_activity.accumulation_signal?.includes('distribution')
                          ? 'bg-[#FF0055]/20 text-[#FF0055]'
                          : 'bg-[#1F1F1F] text-[#A1A1AA]'
                      }>
                        {coinSignal.whale_activity.accumulation_signal || 'neutral'}
                      </Badge>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-[#A1A1AA]">
                  Select a coin to see analysis
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* AI Components Status */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-8"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Layers className="text-[#007AFF]" size={20} />
              AI Enhancement Components
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
              {[
                { name: 'Ensemble Voting', icon: Brain, color: '#9D00FF', status: 'active' },
                { name: '29 Features', icon: BarChart3, color: '#00FF94', status: 'active' },
                { name: 'Sentiment', icon: Gauge, color: '#FFB800', status: 'active' },
                { name: 'Multi-TF', icon: Clock, color: '#007AFF', status: 'active' },
                { name: 'Dynamic Risk', icon: Shield, color: '#FF6B00', status: 'active' },
                { name: 'RL Agent', icon: Zap, color: '#00D4FF', status: 'active' },
                { name: 'Auto-Retrain', icon: RefreshCw, color: '#FF00FF', status: 'scheduled' },
                { name: 'Whale Track', icon: Activity, color: '#00FF94', status: 'active' }
              ].map((component) => (
                <div key={component.name} className="p-3 rounded-lg bg-[#111] border border-[#1F1F1F] text-center">
                  <component.icon size={24} className="mx-auto mb-2" style={{ color: component.color }} />
                  <p className="text-xs text-white font-medium">{component.name}</p>
                  <Badge className={component.status === 'active' ? 'bg-[#00FF94]/20 text-[#00FF94] mt-1' : 'bg-[#FFB800]/20 text-[#FFB800] mt-1'}>
                    {component.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default EnhancedAIDashboard;
