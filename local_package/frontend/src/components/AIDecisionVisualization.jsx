import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, TrendingDown, Activity, BarChart3, 
  Zap, Target, Clock, Sparkles, RefreshCw, Brain,
  ChevronDown, ChevronUp, Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = process.env.REACT_APP_BACKEND_URL;

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


/**
 * Complete AI Decision Visualization Dashboard
 * Fetches and displays AI trading decisions with full explanations
 */
const AIDecisionVisualization = () => {
  const [decisions, setDecisions] = useState([]);
  const [gemCandidates, setGemCandidates] = useState([]);
  const [factors, setFactors] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCoin, setExpandedCoin] = useState(null);
  const [coinExplanation, setCoinExplanation] = useState(null);

  const fetchDecisions = useCallback(async () => {
    setLoading(true);
    try {
      const [decisionsRes, factorsRes] = await Promise.all([
        fetch(`${API_URL}/api/ai-decisions/recent?limit=15`),
        fetch(`${API_URL}/api/ai-decisions/factors`)
      ]);
      
      const decisionsData = await decisionsRes.json();
      const factorsData = await factorsRes.json();
      
      setDecisions(decisionsData.decisions || []);
      setGemCandidates(decisionsData.gem_candidates || []);
      setFactors(factorsData);
    } catch (error) {
      console.error('Failed to fetch AI decisions:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchCoinExplanation = async (coinId) => {
    if (expandedCoin === coinId) {
      setExpandedCoin(null);
      setCoinExplanation(null);
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/ai-decisions/explain/${coinId}`);
      const data = await res.json();
      setCoinExplanation(data);
      setExpandedCoin(coinId);
    } catch (error) {
      console.error('Failed to fetch coin explanation:', error);
    }
  };

  useEffect(() => {
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchDecisions]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#9D00FF]/20 rounded-lg">
            <Brain className="text-[#9D00FF]" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold">AI Decision Transparency</h2>
            <p className="text-sm text-[#A1A1AA]">Understand why AI makes each trading decision</p>
          </div>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={fetchDecisions}
          disabled={loading}
          className="border-[#1F1F1F] hover:bg-[#1F1F1F]"
        >
          <RefreshCw size={14} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Factor Performance Summary */}
      {factors && (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-[#A1A1AA]">
              AI Factor Performance (Based on {factors.total_patterns_analyzed?.toLocaleString()} patterns)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(factors.factors || {}).map(([name, stats]) => (
                <div key={name} className="p-3 bg-[#121212] rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    {name === 'momentum' && <TrendingUp size={14} className="text-[#007AFF]" />}
                    {name === 'volume' && <BarChart3 size={14} className="text-[#9D00FF]" />}
                    {name === 'trend' && <Activity size={14} className="text-[#00FF94]" />}
                    {name === 'sentiment' && <Zap size={14} className="text-[#FFD700]" />}
                    {name === 'volatility' && <Target size={14} className="text-[#FF9500]" />}
                    <span className="text-xs capitalize">{name}</span>
                  </div>
                  <div className="text-lg font-bold">
                    {stats.success_rate || 0}%
                  </div>
                  <div className="text-xs text-[#A1A1AA]">
                    {stats.successful || 0}/{stats.total || 0} signals
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 text-xs text-[#A1A1AA]">
              Most reliable factor: <span className="text-[#00FF94] font-medium capitalize">{factors.most_reliable}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Hidden Gem Candidates */}
      {gemCandidates.length > 0 && (
        <Card className="bg-gradient-to-br from-[#FFD700]/10 to-[#0A0A0A] border-[#FFD700]/30">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="text-[#FFD700]" />
              Hidden Gem Candidates
              <Badge className="bg-[#FFD700]/20 text-[#FFD700] ml-2">
                {gemCandidates.length} found
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {gemCandidates.map((gem, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="p-3 bg-[#0A0A0A] border border-[#FFD700]/20 rounded-lg cursor-pointer hover:border-[#FFD700]/50 transition-colors"
                  onClick={() => fetchCoinExplanation(gem.coin_id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold">{gem.coin_id?.toUpperCase()}</span>
                    <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                      {gem.potential_multiplier?.toFixed(1)}x potential
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {gem.entry_signals?.slice(0, 3).map((signal, j) => (
                      <Badge key={j} variant="outline" className="text-xs border-[#1F1F1F]">
                        {signal}
                      </Badge>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Decisions */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="text-[#9D00FF]" />
            Recent AI Decisions
            <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] ml-2">
              {decisions.length} decisions
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 max-h-[500px] overflow-y-auto">
          <AnimatePresence>
            {decisions.map((decision, i) => (
              <motion.div
                key={`${decision.coin_id}-${i}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ delay: i * 0.05 }}
              >
                <div 
                  className="p-4 bg-[#121212] border border-[#1F1F1F] rounded-lg cursor-pointer hover:border-[#9D00FF]/50 transition-colors"
                  onClick={() => fetchCoinExplanation(decision.coin_id)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-lg">{decision.coin_id?.toUpperCase()}</span>
                      {decision.is_gem && (
                        <Badge className="bg-[#FFD700]/20 text-[#FFD700]">
                          <Sparkles size={10} className="mr-1" />GEM
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs border-[#1F1F1F]">
                        {decision.type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={`${
                        decision.action === 'BUY' ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                        decision.action === 'SELL' ? 'bg-[#FF0055]/20 text-[#FF0055]' :
                        'bg-[#FF9500]/20 text-[#FF9500]'
                      }`}>
                        {decision.action}
                      </Badge>
                      <span className={`text-sm font-bold ${
                        decision.confidence >= 70 ? 'text-[#00FF94]' : 
                        decision.confidence >= 50 ? 'text-[#FF9500]' : 'text-[#FF0055]'
                      }`}>
                        {decision.confidence?.toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Factor Pills */}
                  {decision.factors?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {decision.factors.slice(0, 4).map((factor, j) => (
                        <div key={j} className="flex items-center gap-1 px-2 py-1 bg-[#0A0A0A] rounded-full text-xs">
                          {factor.type === 'momentum' && <TrendingUp size={10} className="text-[#007AFF]" />}
                          {factor.type === 'volume' && <BarChart3 size={10} className="text-[#9D00FF]" />}
                          {factor.type === 'trend' && <Activity size={10} className="text-[#00FF94]" />}
                          {factor.type === 'sentiment' && <Zap size={10} className="text-[#FFD700]" />}
                          {factor.type === 'volatility' && <Target size={10} className="text-[#FF9500]" />}
                          {factor.type === 'ai_confidence' && <Brain size={10} className="text-[#9D00FF]" />}
                          <span className={`${
                            factor.impact === 'positive' ? 'text-[#00FF94]' : 
                            factor.impact === 'negative' ? 'text-[#FF0055]' : 'text-[#A1A1AA]'
                          }`}>
                            {factor.name}: {factor.value || `${factor.score?.toFixed(0)}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reasoning */}
                  <p className="text-sm text-[#A1A1AA] line-clamp-2">{decision.reasoning}</p>
                  
                  {/* Timestamp */}
                  <div className="flex items-center gap-1 mt-2 text-xs text-[#71717A]">
                    <Clock size={10} />
                    {new Date(decision.timestamp).toLocaleString()}
                  </div>

                  {/* Expand Icon */}
                  <div className="flex justify-center mt-2">
                    {expandedCoin === decision.coin_id ? (
                      <ChevronUp size={16} className="text-[#A1A1AA]" />
                    ) : (
                      <ChevronDown size={16} className="text-[#A1A1AA]" />
                    )}
                  </div>
                </div>

                {/* Expanded Explanation */}
                <AnimatePresence>
                  {expandedCoin === decision.coin_id && coinExplanation && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 p-4 bg-[#0A0A0A] border border-[#9D00FF]/30 rounded-lg"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Info size={16} className="text-[#9D00FF]" />
                        <span className="font-medium">Detailed AI Analysis</span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        <div className="p-2 bg-[#121212] rounded">
                          <div className="text-xs text-[#A1A1AA]">Technical Signal</div>
                          <div className="font-bold">{coinExplanation.analysis?.technical?.signal}</div>
                        </div>
                        <div className="p-2 bg-[#121212] rounded">
                          <div className="text-xs text-[#A1A1AA]">RSI</div>
                          <div className="font-bold">{coinExplanation.analysis?.technical?.rsi}</div>
                        </div>
                        <div className="p-2 bg-[#121212] rounded">
                          <div className="text-xs text-[#A1A1AA]">Sentiment</div>
                          <div className="font-bold capitalize">{coinExplanation.analysis?.sentiment?.overall}</div>
                        </div>
                        <div className="p-2 bg-[#121212] rounded">
                          <div className="text-xs text-[#A1A1AA]">Pattern Success</div>
                          <div className="font-bold">{coinExplanation.analysis?.historical?.success_rate}%</div>
                        </div>
                      </div>

                      {coinExplanation.is_potential_gem && coinExplanation.gem_analysis && (
                        <div className="p-3 bg-[#FFD700]/10 border border-[#FFD700]/30 rounded-lg mb-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Sparkles size={14} className="text-[#FFD700]" />
                            <span className="font-medium text-[#FFD700]">Hidden Gem Analysis</span>
                          </div>
                          <p className="text-sm text-[#A1A1AA]">
                            Historical {coinExplanation.gem_analysis.historical_multiplier?.toFixed(1)}x multiplier | 
                            Type: {coinExplanation.gem_analysis.gem_type}
                          </p>
                        </div>
                      )}

                      <p className="text-sm text-[#A1A1AA]">{coinExplanation.reasoning}</p>
                      
                      <div className="mt-3 text-xs text-[#71717A]">
                        Data source: {coinExplanation.data_source} | Generated: {new Date(coinExplanation.generated_at).toLocaleString()}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>

          {decisions.length === 0 && !loading && (
            <div className="text-center py-8 text-[#A1A1AA]">
              <Brain size={48} className="mx-auto mb-3 opacity-50" />
              <p>No AI decisions yet. Generate strategies to see AI reasoning.</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <RefreshCw size={24} className="mx-auto animate-spin text-[#9D00FF]" />
              <p className="text-[#A1A1AA] mt-2">Loading AI decisions...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AIDecisionVisualization;
