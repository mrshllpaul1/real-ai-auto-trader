import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Activity, Wallet, Target,
  Play, Square, Settings, Zap, PieChart, Bell, Waves, LineChart,
  RefreshCw, ArrowUpDown, Shield, MessageCircle, FlaskConical,
  Rocket, Brain, BarChart3, AlertTriangle, CheckCircle, Cpu, Layers,
  Network, Sparkles
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import api, { tradingAPI, marketAPI } from '../services/api';
import { toast } from 'sonner';
import MarketOverview from '../components/MarketOverview';

const UnifiedCommandCenter = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [krakenPortfolio, setKrakenPortfolio] = useState(null);
  const [prices, setPrices] = useState({});
  const [enhancedStatus, setEnhancedStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [portfolioRes, krakenRes, pricesRes, aiStatusRes] = await Promise.all([
        api.get('/portfolio').catch(() => ({ data: null })),
        tradingAPI.getKrakenPortfolio().catch(() => ({ data: null })),
        marketAPI.getPrices(['BTC', 'ETH', 'SOL']).catch(() => ({ data: {} })),
        api.get('/ai/status').catch(() => ({ data: null }))
      ]);

      setPortfolio(portfolioRes.data);
      setKrakenPortfolio(krakenRes.data);
      setPrices(pricesRes.data);
      setEnhancedStatus(aiStatusRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load command center data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Overview Tab Component
  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Portfolio Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Wallet className="w-4 h-4" /> Kraken Portfolio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              ${krakenPortfolio?.total_value_usd?.toFixed(2) || '0.00'}
            </div>
            <div className="text-sm text-gray-400">
              {krakenPortfolio?.holdings_count || krakenPortfolio?.holdings?.length || 0} assets
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" /> 24h Change
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(krakenPortfolio?.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {krakenPortfolio?.change_24h >= 0 ? '+' : ''}{krakenPortfolio?.change_24h?.toFixed(2) || '0.00'}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Activity className="w-4 h-4" /> AI Budget
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              ${portfolio?.current_value?.toFixed(2) || '700.00'}
            </div>
            <div className="text-sm text-gray-400">Isolated trading budget</div>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      <MarketOverview />

      {/* Holdings Table */}
      {krakenPortfolio?.holdings?.length > 0 && (
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white">Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-800">
                    <th className="text-left py-2">Asset</th>
                    <th className="text-right py-2">Amount</th>
                    <th className="text-right py-2">Value (USD)</th>
                    <th className="text-right py-2">24h Change</th>
                  </tr>
                </thead>
                <tbody>
                  {krakenPortfolio.holdings.map((holding, idx) => (
                    <tr key={idx} className="border-b border-gray-800/50">
                      <td className="py-3 text-white font-medium">{holding.asset}</td>
                      <td className="text-right text-gray-300">{holding.balance?.toFixed(6)}</td>
                      <td className="text-right text-gray-300">${holding.value_usd?.toFixed(2)}</td>
                      <td className={`text-right ${(holding.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(holding.change_24h || 0) >= 0 ? '+' : ''}{holding.change_24h?.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // AI Brain Tab Component
  const AIBrainTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
          <CardContent className="pt-4 text-center">
            <Brain className="w-8 h-8 mx-auto mb-2 text-purple-400" />
            <div className="text-2xl font-bold text-white">
              {enhancedStatus?.accuracy?.toFixed(1) || 0}%
            </div>
            <div className="text-sm text-gray-400">AI Accuracy</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4 text-center">
            <Sparkles className="w-8 h-8 mx-auto mb-2 text-cyan-400" />
            <div className="text-2xl font-bold text-white">
              {enhancedStatus?.predictions_today || 0}
            </div>
            <div className="text-sm text-gray-400">Predictions Today</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4 text-center">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 text-green-400" />
            <div className="text-2xl font-bold text-white">
              {enhancedStatus?.win_rate?.toFixed(1) || 0}%
            </div>
            <div className="text-sm text-gray-400">Win Rate</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4 text-center">
            <Layers className="w-8 h-8 mx-auto mb-2 text-orange-400" />
            <div className="text-2xl font-bold text-white">
              {enhancedStatus?.models_active || 8}
            </div>
            <div className="text-sm text-gray-400">Active Models</div>
          </CardContent>
        </Card>
      </div>

      {/* Model Status */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-purple-400" />
            AI Models
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { name: 'Ensemble', status: true, accuracy: 78 },
              { name: 'Transformer', status: true, accuracy: 74 },
              { name: 'RL Agent', status: true, accuracy: 72 },
              { name: 'Regime Predictor', status: true, accuracy: 76 },
              { name: 'Sentiment', status: true, accuracy: 68 },
              { name: 'Technical', status: true, accuracy: 70 },
            ].map((model, idx) => (
              <div key={idx} className="p-3 bg-gray-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">{model.name}</span>
                  <Badge className={model.status ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}>
                    {model.status ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <div className="text-sm text-gray-400">Accuracy: {model.accuracy}%</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent AI Predictions */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-400" />
            Recent Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-sm text-gray-400 text-center py-4">
              Load predictions from API endpoint
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="unified-command-center">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2">
            <span className="text-[#00FF94]">Command</span> Center
          </h1>
          <p className="text-[#A1A1AA]">
            Unified portfolio and AI intelligence dashboard
          </p>
        </div>
        <Button
          onClick={loadData}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="ai-brain" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            AI Brain
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="ai-brain">
          <AIBrainTab />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UnifiedCommandCenter;
