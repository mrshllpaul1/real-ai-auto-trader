import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, TrendingDown, Activity, BarChart3, 
  Zap, Target, Clock, Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';

/**
 * AI Decision Visualization Component
 * Shows WHY the AI chose specific coins and strategies
 */
const AIDecisionCard = ({ decision }) => {
  if (!decision) return null;
  
  const {
    coin_id,
    action,
    confidence,
    factors = [],
    reasoning,
    is_gem = false,
    score = 0
  } = decision;
  
  const getActionColor = (action) => {
    switch (action?.toUpperCase()) {
      case 'BUY': return 'text-[#00FF94]';
      case 'SELL': return 'text-[#FF0055]';
      case 'HOLD': return 'text-[#FF9500]';
      default: return 'text-[#A1A1AA]';
    }
  };
  
  const getActionBgColor = (action) => {
    switch (action?.toUpperCase()) {
      case 'BUY': return 'bg-[#00FF94]/20';
      case 'SELL': return 'bg-[#FF0055]/20';
      case 'HOLD': return 'bg-[#FF9500]/20';
      default: return 'bg-[#1F1F1F]';
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg">{coin_id?.toUpperCase()}</span>
          {is_gem && (
            <Badge className="bg-[#FFD700]/20 text-[#FFD700]">
              <Sparkles size={10} className="mr-1" />GEM
            </Badge>
          )}
        </div>
        <Badge className={`${getActionBgColor(action)} ${getActionColor(action)}`}>
          {action}
        </Badge>
      </div>
      
      {/* Confidence Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-[#A1A1AA]">AI Confidence</span>
          <span className={confidence >= 70 ? 'text-[#00FF94]' : confidence >= 50 ? 'text-[#FF9500]' : 'text-[#FF0055]'}>
            {confidence?.toFixed(0) || 0}%
          </span>
        </div>
        <Progress 
          value={confidence || 0} 
          className="h-2 bg-[#1F1F1F]"
        />
      </div>
      
      {/* Factor Breakdown */}
      {factors.length > 0 && (
        <div className="space-y-2 mb-4">
          <div className="text-sm font-medium text-[#A1A1AA]">Decision Factors:</div>
          {factors.map((factor, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {factor.type === 'momentum' && <TrendingUp size={14} className="text-[#007AFF]" />}
                {factor.type === 'volume' && <BarChart3 size={14} className="text-[#9D00FF]" />}
                {factor.type === 'trend' && <Activity size={14} className="text-[#00FF94]" />}
                {factor.type === 'sentiment' && <Zap size={14} className="text-[#FFD700]" />}
                {factor.type === 'volatility' && <Target size={14} className="text-[#FF9500]" />}
                <span className="capitalize">{factor.name || factor.type}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-[#1F1F1F] rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      factor.score >= 70 ? 'bg-[#00FF94]' : 
                      factor.score >= 50 ? 'bg-[#FF9500]' : 'bg-[#FF0055]'
                    }`}
                    style={{ width: `${factor.score || 0}%` }}
                  />
                </div>
                <span className={`text-xs ${
                  factor.impact === 'positive' ? 'text-[#00FF94]' : 
                  factor.impact === 'negative' ? 'text-[#FF0055]' : 'text-[#A1A1AA]'
                }`}>
                  {factor.impact === 'positive' ? '+' : factor.impact === 'negative' ? '-' : ''}
                  {factor.score?.toFixed(0)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* AI Reasoning */}
      {reasoning && (
        <div className="p-3 bg-[#121212] rounded-lg">
          <div className="flex items-center gap-2 mb-1 text-sm font-medium">
            <Zap size={14} className="text-[#9D00FF]" />
            AI Reasoning
          </div>
          <p className="text-sm text-[#A1A1AA]">{reasoning}</p>
        </div>
      )}
      
      {/* Total Score */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-[#1F1F1F]">
        <span className="text-sm text-[#A1A1AA]">Total AI Score</span>
        <span className={`text-lg font-bold ${
          score >= 70 ? 'text-[#00FF94]' : 
          score >= 50 ? 'text-[#FF9500]' : 'text-[#FF0055]'
        }`}>
          {score?.toFixed(1) || 0}/100
        </span>
      </div>
    </motion.div>
  );
};


/**
 * AI Decisions Panel
 * Shows all recent AI decisions with explanations
 */
const AIDecisionsPanel = ({ decisions = [], title = "AI Decisions" }) => {
  if (!decisions || decisions.length === 0) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="text-[#9D00FF]" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-[#A1A1AA] text-center py-8">
            No AI decisions yet. Deploy capital to see AI reasoning.
          </p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Zap className="text-[#9D00FF]" />
          {title}
          <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] ml-2">
            {decisions.length} decisions
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 max-h-[600px] overflow-y-auto">
        {decisions.map((decision, i) => (
          <AIDecisionCard key={i} decision={decision} />
        ))}
      </CardContent>
    </Card>
  );
};


/**
 * Generate AI reasoning from trade data
 */
export const generateAIReasoning = (trade) => {
  const factors = [];
  let reasoning = '';
  
  if (trade.momentum_score) {
    factors.push({
      type: 'momentum',
      name: 'Price Momentum',
      score: trade.momentum_score,
      impact: trade.momentum_score >= 60 ? 'positive' : trade.momentum_score < 40 ? 'negative' : 'neutral'
    });
  }
  
  if (trade.volume_score) {
    factors.push({
      type: 'volume',
      name: 'Trading Volume',
      score: trade.volume_score,
      impact: trade.volume_score >= 60 ? 'positive' : trade.volume_score < 40 ? 'negative' : 'neutral'
    });
  }
  
  if (trade.trend_score) {
    factors.push({
      type: 'trend',
      name: 'Trend Analysis',
      score: trade.trend_score,
      impact: trade.trend_score >= 60 ? 'positive' : trade.trend_score < 40 ? 'negative' : 'neutral'
    });
  }
  
  if (trade.sentiment_score) {
    factors.push({
      type: 'sentiment',
      name: 'Market Sentiment',
      score: trade.sentiment_score,
      impact: trade.sentiment_score >= 60 ? 'positive' : trade.sentiment_score < 40 ? 'negative' : 'neutral'
    });
  }
  
  if (trade.volatility_score) {
    factors.push({
      type: 'volatility',
      name: 'Volatility',
      score: trade.volatility_score,
      impact: trade.volatility_score >= 40 && trade.volatility_score <= 70 ? 'positive' : 'neutral'
    });
  }
  
  // Generate reasoning based on factors
  const positiveFactors = factors.filter(f => f.impact === 'positive');
  const negativeFactors = factors.filter(f => f.impact === 'negative');
  
  if (positiveFactors.length > negativeFactors.length) {
    reasoning = `Strong ${positiveFactors.map(f => f.name.toLowerCase()).join(' and ')} signals indicate favorable conditions for this position.`;
  } else if (negativeFactors.length > positiveFactors.length) {
    reasoning = `Caution advised due to weak ${negativeFactors.map(f => f.name.toLowerCase()).join(' and ')} indicators.`;
  } else {
    reasoning = `Mixed signals detected. Position taken based on overall AI score and risk tolerance settings.`;
  }
  
  if (trade.is_gem) {
    reasoning += ' Identified as a potential hidden gem with high growth potential.';
  }
  
  return {
    coin_id: trade.coin_id,
    action: 'BUY',
    confidence: trade.ai_score || trade.gem_score || 50,
    factors,
    reasoning,
    is_gem: trade.is_gem || false,
    score: trade.ai_score || trade.gem_score || trade.total_score || 50
  };
};

export { AIDecisionCard, AIDecisionsPanel };
export default AIDecisionsPanel;
