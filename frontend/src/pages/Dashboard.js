import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, DollarSign, Activity, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { tradingAPI, marketAPI, strategyAPI } from '../services/api';
import { toast } from 'sonner';
import MarketOverview from '../components/MarketOverview';

const Dashboard = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [prices, setPrices] = useState({});
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [portfolioRes, pricesRes, strategiesRes] = await Promise.all([
        tradingAPI.getPortfolio().catch(() => ({ data: null })),
        marketAPI.getPrices('bitcoin,ethereum,solana').catch(() => ({ data: {} })),
        strategyAPI.getStrategies('active', 3).catch(() => ({ data: { strategies: [] } }))
      ]);

      setPortfolio(portfolioRes.data);
      setPrices(pricesRes.data);
      setStrategies(strategiesRes.data.strategies || []);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Portfolio Value',
      value: portfolio ? `$${portfolio.current_value?.toLocaleString() || '0'}` : '$0',
      change: portfolio?.profit_loss_percentage || 0,
      icon: DollarSign,
      color: '#00FF94'
    },
    {
      title: 'Total Profit/Loss',
      value: portfolio ? `$${portfolio.profit_loss?.toLocaleString() || '0'}` : '$0',
      change: portfolio?.profit_loss_percentage || 0,
      icon: TrendingUp,
      color: portfolio?.profit_loss >= 0 ? '#00FF94' : '#FF0055'
    },
    {
      title: 'Win Rate',
      value: portfolio ? `${portfolio.win_rate?.toFixed(1) || '0'}%` : '0%',
      change: 0,
      icon: Activity,
      color: '#9D00FF'
    },
    {
      title: 'Active Strategies',
      value: strategies.length,
      change: 0,
      icon: Sparkles,
      color: '#007AFF'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="dashboard">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="dashboard-title">
          Dashboard
        </h1>
        <p className="text-[#A1A1AA]">Real-time overview of your trading performance</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="stats-grid">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
          >
            <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#3F3F46] transition-all" data-testid={`stat-card-${index}`}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-[#A1A1AA]">
                  {stat.title}
                </CardTitle>
                <div 
                  className="p-2 rounded-lg" 
                  style={{ backgroundColor: `${stat.color}20` }}
                >
                  <stat.icon size={20} style={{ color: stat.color }} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-data font-bold" style={{ color: stat.color }}>
                  {stat.value}
                </div>
                {stat.change !== 0 && (
                  <div className="flex items-center gap-1 mt-1">
                    {stat.change >= 0 ? (
                      <TrendingUp size={16} className="text-[#00FF94]" />
                    ) : (
                      <TrendingDown size={16} className="text-[#FF0055]" />
                    )}
                    <span className={`text-sm font-data ${stat.change >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                      {stat.change >= 0 ? '+' : ''}{stat.change.toFixed(2)}%
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Strategies */}
        <motion.div
          className="lg:col-span-2"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full" data-testid="active-strategies-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-heading">Active AI Strategies</CardTitle>
                  <CardDescription>Top performing strategies this week</CardDescription>
                </div>
                <Button 
                  className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
                  onClick={() => window.location.href = '/strategies'}
                  data-testid="view-all-strategies-btn"
                >
                  <Sparkles size={16} className="mr-2" />
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {strategies.length === 0 ? (
                <div className="text-center py-12">
                  <Sparkles size={48} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
                  <p className="text-[#A1A1AA]">No active strategies yet</p>
                  <Button 
                    className="mt-4 bg-[#9D00FF] hover:bg-[#8B00E6] rounded-full"
                    onClick={() => window.location.href = '/strategies'}
                    data-testid="generate-strategies-btn"
                  >
                    Generate Strategies
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {strategies.map((strategy, index) => (
                    <div
                      key={strategy.strategy_id}
                      className="p-4 bg-[#121212] border border-[#1F1F1F] rounded-xl hover:border-[#9D00FF]/50 transition-all glow-ai"
                      data-testid={`strategy-item-${index}`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-bold text-white uppercase">{strategy.coin_id}</h3>
                          <Badge className="mt-1" style={{ 
                            backgroundColor: strategy.technical_signal === 'BUY' ? '#00FF9420' : '#FF005520',
                            color: strategy.technical_signal === 'BUY' ? '#00FF94' : '#FF0055',
                            border: `1px solid ${strategy.technical_signal === 'BUY' ? '#00FF94' : '#FF0055'}40`
                          }}>
                            {strategy.technical_signal}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-data font-bold text-[#9D00FF]">
                            {strategy.confidence_score?.toFixed(0)}%
                          </div>
                          <div className="text-xs text-[#A1A1AA]">Confidence</div>
                        </div>
                      </div>
                      <p className="text-sm text-[#A1A1AA] line-clamp-2">
                        {strategy.ai_recommendation?.substring(0, 120)}...
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Market Prices */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.3 }}
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F] h-full" data-testid="market-prices-card">
            <CardHeader>
              <CardTitle className="text-xl font-heading">Market Prices</CardTitle>
              <CardDescription>Real-time cryptocurrency prices</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(prices).map(([coinId, data]) => (
                  <div 
                    key={coinId} 
                    className="flex items-center justify-between p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                    data-testid={`price-item-${coinId}`}
                  >
                    <div>
                      <h4 className="font-bold text-white uppercase">{coinId}</h4>
                      <p className="text-xs text-[#A1A1AA]">
                        Vol: ${(data.volume_24h / 1000000).toFixed(2)}M
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-data font-bold text-white">
                        ${data.price_usd?.toFixed(2)}
                      </div>
                      <div className={`text-sm font-data flex items-center justify-end gap-1 ${
                        data.price_change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
                      }`}>
                        {data.price_change_24h >= 0 ? (
                          <TrendingUp size={14} />
                        ) : (
                          <TrendingDown size={14} />
                        )}
                        {data.price_change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
