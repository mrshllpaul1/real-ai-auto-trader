import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, TrendingUp, TrendingDown, Zap, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { strategyAPI } from '../services/api';
import { toast } from 'sonner';

const StrategySelector = () => {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const response = await strategyAPI.getStrategies('active', 10);
      setStrategies(response.data.strategies || []);
    } catch (error) {
      console.error('Error loading strategies:', error);
      toast.error('Failed to load strategies');
    } finally {
      setLoading(false);
    }
  };

  const generateStrategies = async () => {
    try {
      setGenerating(true);
      toast.loading('Generating AI strategies...');
      
      const response = await strategyAPI.generateStrategies([
        'bitcoin/USD',
        'ethereum/USD',
        'solana/USD'
      ]);
      
      toast.dismiss();
      toast.success(`Generated ${response.data.count} strategies!`);
      await loadStrategies();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to generate strategies');
      console.error('Error generating strategies:', error);
    } finally {
      setGenerating(false);
    }
  };

  const activateStrategy = async (strategyId) => {
    try {
      await strategyAPI.activateStrategy(strategyId);
      toast.success('Strategy activated!');
      await loadStrategies();
    } catch (error) {
      toast.error('Failed to activate strategy');
    }
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="strategy-selector">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="strategy-title">
            <span className="text-[#9D00FF]">AI</span> Trading Strategies
          </h1>
          <p className="text-[#A1A1AA]">
            Weekly strategy recommendations powered by AI and technical analysis
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={loadStrategies}
            variant="outline"
            className="border-[#1F1F1F] hover:border-[#3F3F46] rounded-full"
            disabled={loading}
            data-testid="refresh-strategies-btn"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </Button>
          <Button
            onClick={generateStrategies}
            className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
            disabled={generating}
            data-testid="generate-new-strategies-btn"
          >
            <Sparkles size={16} className="mr-2" />
            {generating ? 'Generating...' : 'Generate New'}
          </Button>
        </div>
      </motion.div>

      {/* Strategies Grid */}
      {loading && strategies.length === 0 ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#9D00FF]" />
        </div>
      ) : strategies.length === 0 ? (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="text-center py-16">
            <Sparkles size={64} className="mx-auto mb-4 text-[#9D00FF] opacity-50" />
            <h3 className="text-xl font-heading font-bold mb-2">No Strategies Yet</h3>
            <p className="text-[#A1A1AA] mb-6">
              Generate your first AI-powered trading strategies
            </p>
            <Button
              onClick={generateStrategies}
              className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full glow-ai"
              disabled={generating}
            >
              <Sparkles size={16} className="mr-2" />
              {generating ? 'Generating...' : 'Generate Strategies'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="strategies-grid">
          {strategies.map((strategy, index) => (
            <motion.div
              key={strategy.strategy_id}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              <Card 
                className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-all h-full glow-ai"
                data-testid={`strategy-card-${index}`}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl font-heading font-black uppercase">
                        {strategy.coin_id}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        <Badge className="mt-1" style={{ 
                          backgroundColor: strategy.technical_signal === 'BUY' ? '#00FF9420' : 
                                          strategy.technical_signal === 'SELL' ? '#FF005520' : '#007AFF20',
                          color: strategy.technical_signal === 'BUY' ? '#00FF94' : 
                                strategy.technical_signal === 'SELL' ? '#FF0055' : '#007AFF',
                          border: `1px solid ${strategy.technical_signal === 'BUY' ? '#00FF94' : 
                                              strategy.technical_signal === 'SELL' ? '#FF0055' : '#007AFF'}40`
                        }}>
                          {strategy.technical_signal === 'BUY' ? <TrendingUp size={14} className="inline mr-1" /> : 
                           strategy.technical_signal === 'SELL' ? <TrendingDown size={14} className="inline mr-1" /> : null}
                          {strategy.technical_signal}
                        </Badge>
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap size={20} className="text-[#9D00FF]" />
                        <span className="text-3xl font-data font-bold text-[#9D00FF]">
                          {strategy.confidence_score?.toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-[#A1A1AA]">AI Confidence</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* AI Recommendation */}
                    <div className="bg-[#121212] border border-[#9D00FF]/20 rounded-lg p-4">
                      <h4 className="text-sm font-bold text-[#9D00FF] mb-2 flex items-center gap-2">
                        <Sparkles size={14} />
                        AI Recommendation
                      </h4>
                      <p className="text-sm text-[#A1A1AA] whitespace-pre-wrap leading-relaxed">
                        {strategy.ai_recommendation}
                      </p>
                    </div>

                    {/* Action Button */}
                    <Button
                      onClick={() => activateStrategy(strategy.strategy_id)}
                      className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                      disabled={strategy.status === 'active'}
                      data-testid={`activate-strategy-btn-${index}`}
                    >
                      {strategy.status === 'active' ? 'Active' : 'Activate Strategy'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StrategySelector;
