import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Globe, TrendingUp, DollarSign, BarChart3, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';

const MarketOverview = () => {
  const [globalMetrics, setGlobalMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGlobalMetrics();
    const interval = setInterval(loadGlobalMetrics, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const loadGlobalMetrics = async () => {
    try {
      const response = await api.get('/market/global');
      setGlobalMetrics(response.data);
    } catch (error) {
      console.error('Error loading global metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatLargeNumber = (num) => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  if (loading) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#00FF94]" />
        </CardContent>
      </Card>
    );
  }

  if (!globalMetrics) return null;

  const metrics = globalMetrics.global_metrics || {};

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      data-testid="market-overview"
    >
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Globe className="text-[#00FF94]" size={24} />
              <div>
                <CardTitle className="text-xl font-heading">Global Crypto Market</CardTitle>
                <CardDescription>
                  Real-time data from {globalMetrics.sources?.join(', ')}
                </CardDescription>
              </div>
            </div>
            <Badge className="bg-[#00FF94]/20 text-[#00FF94] border-[#00FF94]/30">
              <Zap size={12} className="mr-1" />
              Live
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Total Market Cap */}
            <div className="p-4 bg-[#121212] rounded-lg border border-[#00FF94]/20">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign size={16} className="text-[#00FF94]" />
                <span className="text-xs text-[#A1A1AA]">Total Market Cap</span>
              </div>
              <div className="text-2xl font-data font-bold text-[#00FF94]">
                {formatLargeNumber(metrics.total_market_cap || 0)}
              </div>
            </div>

            {/* 24h Volume */}
            <div className="p-4 bg-[#121212] rounded-lg border border-[#007AFF]/20">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 size={16} className="text-[#007AFF]" />
                <span className="text-xs text-[#A1A1AA]">24h Volume</span>
              </div>
              <div className="text-2xl font-data font-bold text-[#007AFF]">
                {formatLargeNumber(metrics.total_volume_24h || 0)}
              </div>
            </div>

            {/* BTC Dominance */}
            <div className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-[#9D00FF]" />
                <span className="text-xs text-[#A1A1AA]">BTC Dominance</span>
              </div>
              <div className="text-2xl font-data font-bold text-[#9D00FF]">
                {(metrics.bitcoin_dominance || 0).toFixed(1)}%
              </div>
            </div>

            {/* Active Cryptos */}
            <div className="p-4 bg-[#121212] rounded-lg border border-[#FF0055]/20">
              <div className="flex items-center gap-2 mb-2">
                <Globe size={16} className="text-[#FF0055]" />
                <span className="text-xs text-[#A1A1AA]">Active Coins</span>
              </div>
              <div className="text-2xl font-data font-bold text-[#FF0055]">
                {(metrics.active_cryptocurrencies || 0).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Additional Metrics */}
          {metrics.ethereum_dominance && (
            <div className="mt-4 p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#A1A1AA]">ETH Dominance:</span>
                <span className="font-data font-bold text-white">
                  {metrics.ethereum_dominance.toFixed(1)}%
                </span>
              </div>
              {metrics.active_exchanges && (
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-[#A1A1AA]">Active Exchanges:</span>
                  <span className="font-data font-bold text-white">
                    {metrics.active_exchanges.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default MarketOverview;
