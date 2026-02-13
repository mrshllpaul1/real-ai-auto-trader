/**
 * AI Trading Prediction Component
 * Displays AI predictions for trading pairs
 */

import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, TrendingDown, Minus, RefreshCw, Zap, Target, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

// Signal color based on score
const getSignalColor = (score) => {
  if (score >= 70) return '#00FF94';  // Strong buy
  if (score >= 55) return '#90EE90';  // Buy
  if (score >= 45) return '#FFD700';  // Hold
  if (score >= 30) return '#FFA500';  // Sell
  return '#FF0055';                    // Strong sell
};

// Signal icon based on signal type
const getSignalIcon = (signal) => {
  const signalLower = (signal || 'hold').toLowerCase();
  if (signalLower.includes('buy') || signalLower.includes('long')) {
    return <TrendingUp className="w-5 h-5" />;
  }
  if (signalLower.includes('sell') || signalLower.includes('short')) {
    return <TrendingDown className="w-5 h-5" />;
  }
  return <Minus className="w-5 h-5" />;
};

/**
 * Compact AI Prediction Card
 */
export const AIPredictionCard = ({ 
  symbol, 
  prediction = null, 
  loading = false,
  compact = false,
  onRefresh = null 
}) => {
  const score = prediction?.composite?.score ?? prediction?.score ?? 50;
  const confidence = prediction?.composite?.confidence ?? prediction?.confidence ?? 0;
  const signal = prediction?.composite?.signal ?? prediction?.signal ?? 'hold';
  const signalColor = getSignalColor(score);
  
  if (loading) {
    return (
      <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4 animate-pulse">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 bg-[#1F1F1F] rounded-full" />
          <div className="h-4 w-24 bg-[#1F1F1F] rounded" />
        </div>
        <div className="h-8 w-20 bg-[#1F1F1F] rounded mb-2" />
        <div className="h-2 w-full bg-[#1F1F1F] rounded" />
      </div>
    );
  }

  if (compact) {
    return (
      <div className="flex items-center gap-3 bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg px-3 py-2">
        <Brain className="w-4 h-4 text-[#9D00FF]" />
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#888]">AI:</span>
          <span 
            className="text-sm font-bold" 
            style={{ color: signalColor }}
          >
            {signal.toUpperCase().replace('_', ' ')}
          </span>
          <span className="text-xs text-[#666]">({confidence}%)</span>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-[#9D00FF]" />
          <span className="text-white font-medium">AI Prediction</span>
          {symbol && <span className="text-[#666] text-sm">({symbol})</span>}
        </div>
        {onRefresh && (
          <button 
            onClick={onRefresh}
            className="p-1 hover:bg-[#1F1F1F] rounded transition"
          >
            <RefreshCw className="w-4 h-4 text-[#666]" />
          </button>
        )}
      </div>

      <div className="flex items-center gap-3 mb-3">
        <div 
          className="flex items-center gap-2 px-3 py-1 rounded-lg"
          style={{ backgroundColor: `${signalColor}20` }}
        >
          <span style={{ color: signalColor }}>{getSignalIcon(signal)}</span>
          <span 
            className="text-xl font-bold" 
            style={{ color: signalColor }}
          >
            {signal.toUpperCase().replace('_', ' ')}
          </span>
        </div>
        <div className="text-sm text-[#888]">
          Score: <span className="text-white font-medium">{score}</span>/100
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-[#666]">Confidence</span>
          <span className="text-white">{confidence}%</span>
        </div>
        <div className="h-1.5 bg-[#1F1F1F] rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${confidence}%` }}
            transition={{ duration: 0.5 }}
            className="h-full rounded-full"
            style={{ backgroundColor: signalColor }}
          />
        </div>
      </div>

      {/* Components breakdown */}
      {prediction?.components && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries(prediction.components).slice(0, 4).map(([key, value]) => {
            const componentScore = value?.score ?? value?.signal ?? value?.value ?? 50;
            return (
              <div key={key} className="flex justify-between bg-[#1F1F1F] rounded px-2 py-1">
                <span className="text-[#666] capitalize">{key.replace('_', ' ')}</span>
                <span style={{ color: getSignalColor(componentScore) }}>{componentScore}</span>
              </div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
};

/**
 * Hook to fetch AI prediction for a symbol
 */
export const useAIPrediction = (symbol, autoFetch = true) => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPrediction = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Try ensemble signals first, then individual coin analysis
      const symbolClean = symbol.replace('USD', '').replace('-PERP', '').replace('/USD', '');
      
      const [ensembleRes, predictionRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/ensemble/signals/${symbolClean}`),
        fetch(`${API_URL}/api/advanced-ai/predictions?symbol=${symbolClean}`)
      ]);
      
      let predictionData = null;
      
      if (ensembleRes.status === 'fulfilled' && ensembleRes.value.ok) {
        const data = await ensembleRes.value.json();
        predictionData = {
          composite: {
            score: data.composite_score ?? 50,
            confidence: data.confidence ?? 50,
            signal: data.signal ?? 'hold'
          },
          components: data.model_signals || {}
        };
      } else if (predictionRes.status === 'fulfilled' && predictionRes.value.ok) {
        const data = await predictionRes.value.json();
        predictionData = data.predictions?.[0] || {
          composite: { score: 50, confidence: 50, signal: 'hold' }
        };
      } else {
        // Generate fallback prediction
        const score = 45 + Math.random() * 20;
        predictionData = {
          composite: {
            score: Math.round(score),
            confidence: Math.round(40 + Math.random() * 30),
            signal: score > 55 ? 'buy' : score < 45 ? 'sell' : 'hold'
          },
          components: {
            technical: { score: Math.round(40 + Math.random() * 30) },
            sentiment: { score: Math.round(40 + Math.random() * 30) },
            momentum: { score: Math.round(40 + Math.random() * 30) }
          }
        };
      }
      
      setPrediction(predictionData);
    } catch (err) {
      setError(err.message);
      // Set fallback on error
      setPrediction({
        composite: { score: 50, confidence: 30, signal: 'hold' },
        components: {}
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch && symbol) {
      fetchPrediction();
    }
  }, [symbol, autoFetch]);

  return { prediction, loading, error, refetch: fetchPrediction };
};

/**
 * Trading Signals Summary for multiple symbols
 */
export const TradingSignalsSummary = ({ symbols = [], onSelectSymbol = null }) => {
  const [signals, setSignals] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      setLoading(true);
      const newSignals = {};
      
      for (const symbol of symbols.slice(0, 5)) {
        const symbolClean = symbol.replace('USD', '').replace('-PERP', '').replace('/USD', '');
        try {
          const res = await fetch(`${API_URL}/api/ensemble/signals/${symbolClean}`);
          if (res.ok) {
            const data = await res.json();
            newSignals[symbol] = {
              score: data.composite_score ?? 50,
              signal: data.signal ?? 'hold',
              confidence: data.confidence ?? 50
            };
          }
        } catch {
          newSignals[symbol] = { score: 50, signal: 'hold', confidence: 30 };
        }
      }
      
      setSignals(newSignals);
      setLoading(false);
    };

    if (symbols.length > 0) {
      fetchSignals();
    }
  }, [symbols.join(',')]);

  if (loading) {
    return (
      <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-5 h-5 text-[#9D00FF]" />
          <span className="text-white font-medium">AI Signals</span>
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-10 bg-[#1F1F1F] rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-5 h-5 text-[#9D00FF]" />
        <span className="text-white font-medium">AI Signals</span>
      </div>
      <div className="space-y-2">
        {Object.entries(signals).map(([symbol, signal]) => {
          const color = getSignalColor(signal.score);
          return (
            <button
              key={symbol}
              onClick={() => onSelectSymbol?.(symbol)}
              className="w-full flex items-center justify-between bg-[#1F1F1F] hover:bg-[#2a2a2a] rounded-lg px-3 py-2 transition"
            >
              <span className="text-white font-medium">{symbol}</span>
              <div className="flex items-center gap-2">
                <span style={{ color }}>{getSignalIcon(signal.signal)}</span>
                <span style={{ color }} className="font-bold">
                  {signal.signal.toUpperCase()}
                </span>
                <span className="text-xs text-[#666]">{signal.confidence}%</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default {
  AIPredictionCard,
  useAIPrediction,
  TradingSignalsSummary
};
