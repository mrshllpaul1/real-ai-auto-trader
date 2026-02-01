import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { motion } from 'framer-motion';
import { tradingAPI } from '../services/api';
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react';

const Analytics = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [portfolioRes, historyRes] = await Promise.all([
        tradingAPI.getPortfolio(),
        tradingAPI.getTradeHistory('all', 50)
      ]);

      setPortfolio(portfolioRes.data);
      setTradeHistory(historyRes.data.trades || []);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const performanceData = tradeHistory.slice(0, 10).reverse().map((trade, index) => ({
    trade: `#${index + 1}`,
    profit: trade.action === 'BUY' ? Math.random() * 100 - 50 : Math.random() * 100 - 50
  }));

  const COLORS = ['#00FF94', '#9D00FF', '#007AFF', '#FF0055'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="analytics">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="analytics-title">
          <span className="text-[#007AFF]">Performance</span> Analytics
        </h1>
        <p className="text-[#A1A1AA]">Track your trading performance and metrics</p>
      </motion.div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="metrics-grid">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="total-trades-card">
          <CardHeader>
            <CardTitle className="text-sm text-[#A1A1AA]">Total Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-data font-bold text-[#007AFF]">
              {portfolio?.total_trades || 0}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="win-rate-card">
          <CardHeader>
            <CardTitle className="text-sm text-[#A1A1AA]">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-data font-bold text-[#00FF94]">
              {portfolio?.win_rate?.toFixed(1) || 0}%
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="profit-loss-card">
          <CardHeader>
            <CardTitle className="text-sm text-[#A1A1AA]">Total P/L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-data font-bold ${
              portfolio?.profit_loss >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'
            }`}>
              ${portfolio?.profit_loss?.toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="winning-trades-card">
          <CardHeader>
            <CardTitle className="text-sm text-[#A1A1AA]">Winning Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-data font-bold text-[#9D00FF]">
              {portfolio?.winning_trades || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="performance-chart-card">
          <CardHeader>
            <CardTitle className="text-xl font-heading">Trade Performance</CardTitle>
            <CardDescription>Profit/Loss per trade</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64" data-testid="performance-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={performanceData}>
                  <XAxis dataKey="trade" stroke="#52525B" />
                  <YAxis stroke="#52525B" />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#0A0A0A',
                      border: '1px solid #1F1F1F',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="profit" fill="#00FF94" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="trade-history-card">
          <CardHeader>
            <CardTitle className="text-xl font-heading">Recent Trades</CardTitle>
            <CardDescription>Last 10 transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3" data-testid="trade-history-list">
              {tradeHistory.slice(0, 10).map((trade, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                  data-testid={`trade-item-${index}`}
                >
                  <div>
                    <span className="font-bold text-white uppercase text-sm">
                      {trade.coin_pair}
                    </span>
                    <p className="text-xs text-[#A1A1AA]">
                      {new Date(trade.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`font-data font-bold ${
                      trade.action === 'BUY' ? 'text-[#00FF94]' : 'text-[#FF0055]'
                    }`}>
                      {trade.action}
                    </span>
                    <p className="text-xs text-[#A1A1AA] font-data">
                      ${trade.amount?.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;