/**
 * AI Position Sizing Component
 * Provides AI-assisted position sizing recommendations based on prediction confidence
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Calculator, TrendingUp, TrendingDown, AlertTriangle, 
  Shield, DollarSign, Percent, Info, Zap, Brain, Target
} from 'lucide-react';
import { motion } from 'framer-motion';

/**
 * Calculate recommended position size based on AI confidence and risk parameters
 */
const calculatePositionSize = ({
  accountBalance,
  aiConfidence,
  aiSignal,
  riskPerTrade = 2, // % of account to risk per trade
  stopLossPercent = 5,
  maxPositionPercent = 20 // max % of account in single position
}) => {
  // Base position size from risk management
  const riskAmount = accountBalance * (riskPerTrade / 100);
  const basePositionSize = riskAmount / (stopLossPercent / 100);
  
  // Confidence multiplier (0.5 to 1.5x based on confidence)
  const confidenceMultiplier = 0.5 + (aiConfidence / 100);
  
  // Signal strength adjustment
  let signalMultiplier = 1;
  const signalLower = aiSignal?.toLowerCase() || 'hold';
  if (signalLower.includes('strong')) {
    signalMultiplier = 1.25;
  } else if (signalLower === 'hold' || signalLower === 'neutral') {
    signalMultiplier = 0.5;
  }
  
  // Calculate recommended size
  let recommendedSize = basePositionSize * confidenceMultiplier * signalMultiplier;
  
  // Apply maximum position limit
  const maxPosition = accountBalance * (maxPositionPercent / 100);
  recommendedSize = Math.min(recommendedSize, maxPosition);
  
  // Risk score (1-10)
  const riskScore = Math.round(
    (100 - aiConfidence) / 10 + 
    (signalMultiplier < 1 ? 2 : 0) +
    (recommendedSize > maxPosition * 0.8 ? 1 : 0)
  );
  
  return {
    recommendedSize: Math.round(recommendedSize * 100) / 100,
    confidenceMultiplier: Math.round(confidenceMultiplier * 100) / 100,
    riskAmount: Math.round(riskAmount * 100) / 100,
    maxPosition,
    riskScore: Math.min(10, Math.max(1, riskScore)),
    breakdown: {
      baseSize: Math.round(basePositionSize * 100) / 100,
      afterConfidence: Math.round(basePositionSize * confidenceMultiplier * 100) / 100,
      afterSignal: Math.round(basePositionSize * confidenceMultiplier * signalMultiplier * 100) / 100,
      final: Math.round(recommendedSize * 100) / 100
    }
  };
};

/**
 * AI Position Sizing Recommendation Card
 */
export const AIPositionSizingCard = ({ 
  symbol,
  currentPrice = 0,
  accountBalance = 1000,
  aiPrediction = null,
  onApplySize = null,
  compact = false
}) => {
  const [customRisk, setCustomRisk] = useState(2);
  const [customStopLoss, setCustomStopLoss] = useState(5);
  
  const aiConfidence = aiPrediction?.composite?.confidence ?? aiPrediction?.confidence ?? 50;
  const aiSignal = aiPrediction?.composite?.signal ?? aiPrediction?.signal ?? 'hold';
  const aiScore = aiPrediction?.composite?.score ?? aiPrediction?.score ?? 50;
  
  const recommendation = useMemo(() => {
    return calculatePositionSize({
      accountBalance,
      aiConfidence,
      aiSignal,
      riskPerTrade: customRisk,
      stopLossPercent: customStopLoss
    });
  }, [accountBalance, aiConfidence, aiSignal, customRisk, customStopLoss]);
  
  const positionUnits = currentPrice > 0 
    ? (recommendation.recommendedSize / currentPrice).toFixed(6) 
    : '0';
  
  const getRiskColor = (score) => {
    if (score <= 3) return '#00FF94';
    if (score <= 6) return '#FFD700';
    return '#FF0055';
  };
  
  const getSignalColor = (signal) => {
    const s = signal?.toLowerCase() || 'hold';
    if (s.includes('buy') || s.includes('long')) return '#00FF94';
    if (s.includes('sell') || s.includes('short')) return '#FF0055';
    return '#FFD700';
  };

  if (compact) {
    return (
      <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#9D00FF]" />
            <span className="text-sm text-white">AI Position Size</span>
          </div>
          <span className="text-xs text-[#666]">{aiConfidence}% conf</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-[#00FF94]">
            ${recommendation.recommendedSize.toLocaleString()}
          </span>
          {onApplySize && (
            <button
              onClick={() => onApplySize(recommendation.recommendedSize, positionUnits)}
              className="text-xs bg-[#9D00FF] px-2 py-1 rounded hover:bg-[#8500DD] transition"
            >
              Apply
            </button>
          )}
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
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-[#9D00FF]" />
          <span className="text-white font-medium">AI Position Sizing</span>
          {symbol && <span className="text-[#666] text-sm">({symbol})</span>}
        </div>
        <div 
          className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs"
          style={{ 
            backgroundColor: `${getRiskColor(recommendation.riskScore)}20`,
            color: getRiskColor(recommendation.riskScore)
          }}
        >
          <Shield className="w-3 h-3" />
          Risk: {recommendation.riskScore}/10
        </div>
      </div>

      {/* AI Signal Info */}
      <div className="bg-[#1F1F1F] rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[#A1A1AA] text-sm">AI Signal</span>
          <div className="flex items-center gap-2">
            <span 
              className="font-bold"
              style={{ color: getSignalColor(aiSignal) }}
            >
              {aiSignal.toUpperCase()}
            </span>
            <span className="text-[#666] text-xs">({aiConfidence}% conf)</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[#A1A1AA] text-sm">Confidence Multiplier</span>
          <span className="text-white font-medium">{recommendation.confidenceMultiplier}x</span>
        </div>
      </div>

      {/* Recommended Position */}
      <div className="bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 rounded-lg p-4 mb-4">
        <div className="text-center">
          <p className="text-[#A1A1AA] text-sm mb-1">Recommended Position Size</p>
          <p className="text-3xl font-bold text-white">
            ${recommendation.recommendedSize.toLocaleString()}
          </p>
          {currentPrice > 0 && (
            <p className="text-[#666] text-sm mt-1">
              ≈ {positionUnits} {symbol?.replace('/USD', '').replace('USD', '')}
            </p>
          )}
        </div>
      </div>

      {/* Risk Parameters */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs text-[#666] block mb-1">Risk per Trade (%)</label>
          <input
            type="number"
            min="0.5"
            max="10"
            step="0.5"
            value={customRisk}
            onChange={(e) => setCustomRisk(parseFloat(e.target.value) || 2)}
            className="w-full bg-[#1F1F1F] border border-[#333] rounded px-2 py-1 text-white text-sm"
          />
        </div>
        <div>
          <label className="text-xs text-[#666] block mb-1">Stop Loss (%)</label>
          <input
            type="number"
            min="1"
            max="20"
            step="0.5"
            value={customStopLoss}
            onChange={(e) => setCustomStopLoss(parseFloat(e.target.value) || 5)}
            className="w-full bg-[#1F1F1F] border border-[#333] rounded px-2 py-1 text-white text-sm"
          />
        </div>
      </div>

      {/* Breakdown */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-[#666]">Base Size (from risk)</span>
          <span className="text-[#A1A1AA]">${recommendation.breakdown.baseSize.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#666]">After Confidence Adj.</span>
          <span className="text-[#A1A1AA]">${recommendation.breakdown.afterConfidence.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[#666]">After Signal Adj.</span>
          <span className="text-[#A1A1AA]">${recommendation.breakdown.afterSignal.toLocaleString()}</span>
        </div>
        <div className="flex justify-between border-t border-[#333] pt-2 mt-2">
          <span className="text-white font-medium">Final Recommendation</span>
          <span className="text-[#00FF94] font-bold">${recommendation.breakdown.final.toLocaleString()}</span>
        </div>
      </div>

      {/* Apply Button */}
      {onApplySize && (
        <button
          onClick={() => onApplySize(recommendation.recommendedSize, positionUnits)}
          className="w-full mt-4 bg-[#9D00FF] hover:bg-[#8500DD] text-white py-2 rounded-lg font-medium transition flex items-center justify-center gap-2"
        >
          <Zap className="w-4 h-4" />
          Apply Recommended Size
        </button>
      )}

      {/* Info */}
      <div className="flex items-start gap-2 mt-3 p-2 bg-[#1F1F1F] rounded-lg">
        <Info className="w-4 h-4 text-[#666] mt-0.5 flex-shrink-0" />
        <p className="text-xs text-[#666]">
          Position size is calculated using {customRisk}% risk per trade, {customStopLoss}% stop loss, 
          and adjusted by AI confidence ({aiConfidence}%) and signal strength.
        </p>
      </div>
    </motion.div>
  );
};

/**
 * Hook to get position sizing recommendation
 */
export const usePositionSizing = ({
  accountBalance,
  aiPrediction,
  riskPerTrade = 2,
  stopLossPercent = 5
}) => {
  const aiConfidence = aiPrediction?.composite?.confidence ?? aiPrediction?.confidence ?? 50;
  const aiSignal = aiPrediction?.composite?.signal ?? aiPrediction?.signal ?? 'hold';
  
  return useMemo(() => {
    return calculatePositionSize({
      accountBalance,
      aiConfidence,
      aiSignal,
      riskPerTrade,
      stopLossPercent
    });
  }, [accountBalance, aiConfidence, aiSignal, riskPerTrade, stopLossPercent]);
};

export default {
  AIPositionSizingCard,
  usePositionSizing,
  calculatePositionSize
};
