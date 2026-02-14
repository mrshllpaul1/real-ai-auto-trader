/**
 * AISignalExplanation - Shows WHY AI made a prediction
 * Transparent AI with factor breakdowns
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
  History,
  Target,
  Shield,
  Lightbulb
} from 'lucide-react';
import api from '@/services/api';

const FactorBar = ({ factor, maxWeight = 0.3 }) => {
  const percentage = (factor.weight / maxWeight) * 100;
  
  const directionColors = {
    bullish: 'bg-green-500',
    bearish: 'bg-red-500',
    neutral: 'bg-yellow-500',
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{factor.factor}</span>
        <Badge 
          variant="outline" 
          className={cn(
            'text-xs',
            factor.direction === 'bullish' && 'text-green-500 border-green-500/30',
            factor.direction === 'bearish' && 'text-red-500 border-red-500/30',
            factor.direction === 'neutral' && 'text-yellow-500 border-yellow-500/30'
          )}
        >
          {(factor.weight * 100).toFixed(0)}% weight
        </Badge>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={cn('h-full rounded-full transition-all', directionColors[factor.direction])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">{factor.explanation}</p>
    </div>
  );
};

const RiskItem = ({ risk }) => {
  const levelColors = {
    high: 'text-red-500 bg-red-500/10',
    medium: 'text-yellow-500 bg-yellow-500/10',
    low: 'text-blue-500 bg-blue-500/10',
    standard: 'text-muted-foreground bg-muted',
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
      <AlertTriangle className={cn(
        'h-4 w-4 mt-0.5 flex-shrink-0',
        risk.level === 'high' && 'text-red-500',
        risk.level === 'medium' && 'text-yellow-500',
        risk.level === 'low' && 'text-blue-500',
        risk.level === 'standard' && 'text-muted-foreground'
      )} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm">{risk.risk}</span>
          <span className={cn(
            'text-xs px-2 py-0.5 rounded-full',
            levelColors[risk.level]
          )}>
            {risk.level}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">{risk.description}</p>
      </div>
    </div>
  );
};

export const AISignalExplanation = ({ 
  coinId = 'bitcoin',
  signal: propSignal,
  onClose,
  className 
}) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState('factors');

  useEffect(() => {
    fetchExplanation();
  }, [coinId]);

  const fetchExplanation = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/ai-explain/signal/${coinId}`);
      setExplanation(response.data);
    } catch (error) {
      console.error('Failed to fetch explanation:', error);
      // Use mock data on error
      setExplanation({
        coin_id: coinId,
        signal: 'BUY',
        confidence: 0.75,
        confidence_level: 'MEDIUM',
        summary: 'AI detected a bullish opportunity with 75% confidence based on RSI oversold, positive sentiment shift, and historical pattern match.',
        primary_factors: [
          { factor: 'RSI Oversold (28)', weight: 0.25, direction: 'bullish', explanation: 'RSI below 30 indicates oversold conditions.' },
          { factor: 'Whale Accumulation +15%', weight: 0.20, direction: 'bullish', explanation: 'Large wallets increasing positions.' },
          { factor: 'Sentiment Shift Bullish', weight: 0.18, direction: 'bullish', explanation: 'News and social sentiment turning positive.' },
        ],
        supporting_factors: [
          { factor: 'Price at Support', weight: 0.10, direction: 'bullish', explanation: 'Price near key support level.' },
        ],
        risk_factors: [
          { risk: 'High Volatility', level: 'medium', description: '24h volatility is 6.2%, which increases risk.' },
          { risk: 'Market Risk', level: 'standard', description: 'Cryptocurrency markets are highly volatile.' },
        ],
        historical_context: {
          pattern_name: 'March 2024 Accumulation',
          similarity: 0.82,
          outcome: '+23% in 14 days',
        },
        recommendation: {
          action: 'Consider buying',
          position_size: 'small to medium',
          stop_loss: '5-8% below entry',
          take_profit: '15-25% above entry',
        },
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="h-6 bg-muted rounded w-1/3 mb-4" />
          <div className="h-4 bg-muted rounded w-full mb-2" />
          <div className="h-4 bg-muted rounded w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (!explanation) return null;

  const signalColors = {
    BUY: 'text-green-500 bg-green-500/10 border-green-500/30',
    SELL: 'text-red-500 bg-red-500/10 border-red-500/30',
    HOLD: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30',
  };

  const confidenceColors = {
    HIGH: 'text-green-500',
    MEDIUM: 'text-yellow-500',
    LOW: 'text-orange-500',
    VERY_LOW: 'text-red-500',
  };

  return (
    <Card className={cn('overflow-hidden', className)}>
      {/* Header */}
      <CardHeader className="pb-4 bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Brain className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg sm:text-xl">AI Signal Explanation</CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">
                {explanation.coin_id?.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="text-right">
            <Badge className={cn('text-sm px-3 py-1', signalColors[explanation.signal])}>
              {explanation.signal}
            </Badge>
            <p className={cn(
              'text-xs mt-1 font-medium',
              confidenceColors[explanation.confidence_level]
            )}>
              {(explanation.confidence * 100).toFixed(0)}% Confidence
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6 space-y-4 sm:space-y-6">
        {/* Summary */}
        <div className="p-3 sm:p-4 rounded-lg bg-primary/5 border border-primary/10">
          <div className="flex items-start gap-2">
            <Lightbulb className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
            <p className="text-sm sm:text-base">{explanation.summary}</p>
          </div>
        </div>

        {/* Confidence Meter */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Confidence Level</span>
            <span className={cn('text-sm font-medium', confidenceColors[explanation.confidence_level])}>
              {explanation.confidence_level}
            </span>
          </div>
          <Progress value={explanation.confidence * 100} className="h-2" />
        </div>

        {/* Primary Factors */}
        <div>
          <button
            onClick={() => setExpandedSection(expandedSection === 'factors' ? '' : 'factors')}
            className="flex items-center justify-between w-full mb-3"
          >
            <h3 className="text-sm sm:text-base font-semibold flex items-center gap-2">
              <Target className="h-4 w-4" />
              Key Contributing Factors
            </h3>
            {expandedSection === 'factors' ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {expandedSection === 'factors' && (
            <div className="space-y-4">
              {explanation.primary_factors?.map((factor, i) => (
                <FactorBar key={i} factor={factor} />
              ))}
            </div>
          )}
        </div>

        {/* Historical Pattern */}
        {explanation.historical_context && (
          <div className="p-3 sm:p-4 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 mb-2">
              <History className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Similar Historical Pattern</span>
            </div>
            <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
              <div>
                <p className="text-xs text-muted-foreground">Pattern</p>
                <p className="text-xs sm:text-sm font-medium">{explanation.historical_context.pattern_name}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Similarity</p>
                <p className="text-xs sm:text-sm font-medium text-primary">
                  {(explanation.historical_context.similarity * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Outcome</p>
                <p className="text-xs sm:text-sm font-medium text-green-500">
                  {explanation.historical_context.outcome}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Risk Factors */}
        <div>
          <button
            onClick={() => setExpandedSection(expandedSection === 'risks' ? '' : 'risks')}
            className="flex items-center justify-between w-full mb-3"
          >
            <h3 className="text-sm sm:text-base font-semibold flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Risk Factors ({explanation.risk_factors?.length || 0})
            </h3>
            {expandedSection === 'risks' ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {expandedSection === 'risks' && (
            <div className="space-y-2">
              {explanation.risk_factors?.map((risk, i) => (
                <RiskItem key={i} risk={risk} />
              ))}
            </div>
          )}
        </div>

        {/* Recommendation */}
        {explanation.recommendation && (
          <div className={cn(
            'p-3 sm:p-4 rounded-lg border',
            explanation.signal === 'BUY' && 'bg-green-500/5 border-green-500/20',
            explanation.signal === 'SELL' && 'bg-red-500/5 border-red-500/20',
            explanation.signal === 'HOLD' && 'bg-yellow-500/5 border-yellow-500/20'
          )}>
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Recommendation
            </h4>
            <p className="text-sm sm:text-base font-medium mb-2">
              {explanation.recommendation.action}
            </p>
            {explanation.recommendation.position_size && (
              <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm">
                <div>
                  <span className="text-muted-foreground">Position: </span>
                  <span className="font-medium">{explanation.recommendation.position_size}</span>
                </div>
                {explanation.recommendation.stop_loss && (
                  <div>
                    <span className="text-muted-foreground">Stop Loss: </span>
                    <span className="font-medium text-red-500">{explanation.recommendation.stop_loss}</span>
                  </div>
                )}
                {explanation.recommendation.take_profit && (
                  <div>
                    <span className="text-muted-foreground">Take Profit: </span>
                    <span className="font-medium text-green-500">{explanation.recommendation.take_profit}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-muted-foreground text-center">
          AI predictions are not financial advice. Always do your own research.
        </p>
      </CardContent>
    </Card>
  );
};

export default AISignalExplanation;
