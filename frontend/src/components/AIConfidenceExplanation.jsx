import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp,
  Info,
  BarChart3,
  Lightbulb,
  Shield,
  Target,
  Activity,
  RefreshCw
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

/**
 * Signal Direction Icon
 */
function DirectionIcon({ direction, size = 'sm' }) {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
  
  if (direction === 'bullish') {
    return <TrendingUp className={`${sizeClass} text-emerald-400`} />;
  } else if (direction === 'bearish') {
    return <TrendingDown className={`${sizeClass} text-red-400`} />;
  }
  return <Minus className={`${sizeClass} text-gray-400`} />;
}

/**
 * Confidence Bar
 */
function ConfidenceBar({ confidence, size = 'md' }) {
  const heightClass = size === 'sm' ? 'h-1.5' : 'h-2';
  const percentage = Math.round(confidence * 100);
  
  let colorClass = 'bg-gray-500';
  if (percentage >= 70) colorClass = 'bg-emerald-500';
  else if (percentage >= 50) colorClass = 'bg-yellow-500';
  else if (percentage >= 30) colorClass = 'bg-orange-500';
  else colorClass = 'bg-red-500';
  
  return (
    <div className={`w-full bg-gray-700 rounded-full ${heightClass}`}>
      <div 
        className={`${heightClass} rounded-full ${colorClass} transition-all duration-500`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

/**
 * Contribution Item
 */
function ContributionItem({ feature }) {
  const [expanded, setExpanded] = useState(false);
  
  const contributionColor = feature.contribution > 0.1 
    ? 'text-emerald-400' 
    : feature.contribution < -0.1 
      ? 'text-red-400' 
      : 'text-gray-400';
  
  return (
    <div className="border-b border-gray-700/50 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between py-2.5 px-1 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <DirectionIcon direction={feature.direction} />
          <span className="text-sm text-gray-200">{feature.name}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-medium ${contributionColor}`}>
            {feature.contribution > 0 ? '+' : ''}{(feature.contribution * 100).toFixed(0)}%
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </div>
      </button>
      
      {expanded && (
        <div className="px-1 pb-3 text-xs text-gray-400 animate-in fade-in slide-in-from-top-1">
          <p className="mb-2">{feature.explanation}</p>
          <div className="flex items-center justify-between text-gray-500">
            <span>Value: {typeof feature.value === 'number' ? feature.value.toFixed(2) : JSON.stringify(feature.value)}</span>
            <span>Importance: {(feature.importance * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Category Card
 */
function CategoryCard({ category, features }) {
  const [expanded, setExpanded] = useState(false);
  
  const categoryLabels = {
    technical: { label: 'Technical Analysis', icon: BarChart3 },
    sentiment: { label: 'Market Sentiment', icon: Activity },
    on_chain: { label: 'On-Chain Metrics', icon: Target },
    market_structure: { label: 'Market Structure', icon: Shield }
  };
  
  const { label, icon: Icon } = categoryLabels[category] || { label: category, icon: Info };
  
  const bullishCount = features.filter(f => f.direction === 'bullish').length;
  const bearishCount = features.filter(f => f.direction === 'bearish').length;
  
  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
            <Icon className="w-4 h-4 text-purple-400" />
          </div>
          <span className="font-medium text-white">{label}</span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-emerald-400">{bullishCount} bullish</span>
            <span className="text-gray-500">|</span>
            <span className="text-red-400">{bearishCount} bearish</span>
          </div>
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>
      
      {expanded && (
        <div className="px-4 pb-4 animate-in fade-in slide-in-from-top-2">
          {features.map((feature, idx) => (
            <ContributionItem key={idx} feature={feature} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Key Drivers Display
 */
function KeyDrivers({ drivers }) {
  if (!drivers || drivers.length === 0) return null;
  
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
        <Lightbulb className="w-4 h-4 text-yellow-400" />
        Key Drivers
      </h4>
      <div className="space-y-1.5">
        {drivers.map((driver, idx) => (
          <div 
            key={idx}
            className="flex items-start gap-2 p-2 rounded-lg bg-gray-800/50"
          >
            <span className="text-xs font-medium text-purple-400 mt-0.5">#{idx + 1}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <DirectionIcon direction={driver.direction} />
                <span className="text-sm text-white">{driver.feature}</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{driver.explanation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Risk Factors Display
 */
function RiskFactors({ risks }) {
  if (!risks || risks.length === 0) return null;
  
  const levelColors = {
    high: 'bg-red-500/20 border-red-500/30 text-red-400',
    medium: 'bg-orange-500/20 border-orange-500/30 text-orange-400',
    low: 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400'
  };
  
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-orange-400" />
        Risk Factors
      </h4>
      <div className="space-y-2">
        {risks.map((risk, idx) => (
          <div 
            key={idx}
            className={`p-3 rounded-lg border ${levelColors[risk.level] || levelColors.medium}`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-sm">{risk.factor}</span>
              <span className="text-xs uppercase">{risk.level}</span>
            </div>
            <p className="text-xs text-gray-300">{risk.description}</p>
            {risk.mitigation && (
              <p className="text-xs text-gray-400 mt-1">
                <span className="text-gray-500">Mitigation:</span> {risk.mitigation}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Insights Display
 */
function Insights({ insights }) {
  if (!insights || insights.length === 0) return null;
  
  const typeIcons = {
    strength: { icon: TrendingUp, color: 'text-emerald-400' },
    warning: { icon: AlertTriangle, color: 'text-orange-400' },
    caution: { icon: Shield, color: 'text-yellow-400' },
    divergence: { icon: Activity, color: 'text-purple-400' }
  };
  
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
        <Target className="w-4 h-4 text-cyan-400" />
        Actionable Insights
      </h4>
      <div className="space-y-2">
        {insights.map((insight, idx) => {
          const { icon: Icon, color } = typeIcons[insight.type] || typeIcons.strength;
          return (
            <div key={idx} className="flex items-start gap-3 p-2 rounded-lg bg-gray-800/30">
              <Icon className={`w-4 h-4 mt-0.5 ${color}`} />
              <div>
                <p className="text-sm text-gray-200">{insight.message}</p>
                {insight.action && (
                  <p className="text-xs text-gray-400 mt-0.5">{insight.action}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Main AI Confidence Explanation Component
 */
export function AIConfidenceExplanation({ symbol, compact = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(!compact);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/confidence-explain/${symbol}`);
      if (!response.ok) throw new Error('Failed to fetch explanation');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchExplanation();
    }
  }, [symbol]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-4 p-4" data-testid="confidence-explanation-loading">
        <div className="h-6 bg-gray-700 rounded w-3/4"></div>
        <div className="h-2 bg-gray-700 rounded w-full"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-700 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-xl" data-testid="confidence-explanation-error">
        <p className="text-red-400 text-sm">{error}</p>
        <button 
          onClick={fetchExplanation}
          className="text-xs text-red-300 hover:text-white mt-2"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const signalColors = {
    buy: 'text-emerald-400',
    strong_buy: 'text-emerald-300',
    sell: 'text-red-400',
    strong_sell: 'text-red-300',
    hold: 'text-yellow-400'
  };

  // Compact view for dashboard cards
  if (compact && !expanded) {
    return (
      <div 
        className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-4"
        data-testid="confidence-explanation-compact"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <span className="font-semibold text-white">{symbol} AI Analysis</span>
          </div>
          <button
            onClick={() => setExpanded(true)}
            className="text-xs text-purple-400 hover:text-purple-300"
          >
            See details
          </button>
        </div>
        
        <div className="flex items-center gap-4 mb-3">
          <div>
            <span className="text-xs text-gray-400">Signal</span>
            <p className={`font-semibold uppercase ${signalColors[data.signal] || 'text-gray-400'}`}>
              {data.signal}
            </p>
          </div>
          <div className="flex-1">
            <span className="text-xs text-gray-400">Confidence</span>
            <div className="flex items-center gap-2">
              <ConfidenceBar confidence={data.confidence} size="sm" />
              <span className="text-sm text-white">{Math.round(data.confidence * 100)}%</span>
            </div>
          </div>
        </div>
        
        <p className="text-sm text-gray-300">{data.summary}</p>
        
        {data.key_drivers && data.key_drivers.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-700/50">
            <p className="text-xs text-gray-400 mb-1">Top Driver</p>
            <div className="flex items-center gap-2">
              <DirectionIcon direction={data.key_drivers[0].direction} />
              <span className="text-sm text-white">{data.key_drivers[0].feature}</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full expanded view
  return (
    <div 
      className="bg-gray-900/50 rounded-2xl border border-gray-700/50 overflow-hidden"
      data-testid="confidence-explanation-full"
    >
      {/* Header */}
      <div className="p-5 border-b border-gray-700/50 bg-gradient-to-r from-purple-900/30 to-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-lg">AI Confidence Explained</h3>
              <p className="text-sm text-gray-400">{symbol} Analysis</p>
            </div>
          </div>
          
          <button
            onClick={fetchExplanation}
            className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
        </div>
        
        {/* Signal & Confidence */}
        <div className="mt-4 flex items-center gap-6">
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider">Signal</span>
            <p className={`text-2xl font-bold uppercase ${signalColors[data.signal] || 'text-gray-400'}`}>
              {data.signal.replace('_', ' ')}
            </p>
          </div>
          <div className="flex-1 max-w-xs">
            <span className="text-xs text-gray-400 uppercase tracking-wider">Confidence</span>
            <div className="flex items-center gap-3 mt-1">
              <ConfidenceBar confidence={data.confidence} />
              <span className="text-xl font-bold text-white">{Math.round(data.confidence * 100)}%</span>
            </div>
            <span className="text-xs text-gray-500 capitalize">{data.confidence_level?.replace('_', ' ')} confidence</span>
          </div>
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider">Agreement</span>
            <p className="text-xl font-bold text-white">{data.agreement_score}%</p>
            <span className="text-xs text-gray-500">of indicators agree</span>
          </div>
        </div>
      </div>
      
      {/* Explanation */}
      <div className="p-5 border-b border-gray-700/50 bg-gray-800/30">
        <p className="text-gray-200 leading-relaxed">{data.explanation}</p>
      </div>
      
      {/* Main Content */}
      <div className="p-5 space-y-6">
        {/* Key Drivers */}
        <KeyDrivers drivers={data.key_drivers} />
        
        {/* Feature Contributions */}
        {data.contributions && data.contributions.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              Feature Contributions
            </h4>
            <div className="space-y-2">
              {data.contributions.map((cat, idx) => (
                <CategoryCard 
                  key={idx} 
                  category={cat.category} 
                  features={cat.features} 
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Insights */}
        <Insights insights={data.insights} />
        
        {/* Risk Factors */}
        <RiskFactors risks={data.risk_factors} />
      </div>
      
      {/* Footer */}
      <div className="px-5 py-3 bg-gray-800/50 border-t border-gray-700/50 flex items-center justify-between text-xs text-gray-500">
        <span>Last updated: {new Date(data.timestamp).toLocaleString()}</span>
        {compact && (
          <button
            onClick={() => setExpanded(false)}
            className="text-purple-400 hover:text-purple-300"
          >
            Collapse
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Mini confidence badge for lists/tables
 */
export function ConfidenceBadge({ confidence, signal, onClick }) {
  const percentage = Math.round(confidence * 100);
  
  let bgColor = 'bg-gray-700';
  if (percentage >= 70) bgColor = 'bg-emerald-600';
  else if (percentage >= 50) bgColor = 'bg-yellow-600';
  else if (percentage >= 30) bgColor = 'bg-orange-600';
  else bgColor = 'bg-red-600';
  
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full ${bgColor} text-white text-xs font-medium hover:opacity-90 transition-opacity`}
      title="Click for AI explanation"
      data-testid="confidence-badge"
    >
      <Brain className="w-3 h-3" />
      {percentage}%
    </button>
  );
}

export default AIConfidenceExplanation;
