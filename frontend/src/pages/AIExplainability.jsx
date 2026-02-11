import React, { useState, useEffect } from 'react';
import { Brain, Info, BarChart3, Target, AlertTriangle, Lightbulb, ChevronDown, TrendingUp, TrendingDown, Minus, HelpCircle, Zap } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const AIExplainability = () => {
  const [symbol, setSymbol] = useState('BTC');
  const [explanation, setExplanation] = useState(null);
  const [historicalAccuracy, setHistoricalAccuracy] = useState(null);
  const [modelPerformance, setModelPerformance] = useState(null);
  const [whatIfScenario, setWhatIfScenario] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState('price_up_10');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('explain');

  const symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'LINK', 'MATIC'];

  useEffect(() => {
    fetchData();
  }, [symbol, selectedScenario]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [explainRes, accuracyRes, perfRes, whatIfRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/ai-explainability/explain/${symbol}`),
        fetch(`${BACKEND_URL}/api/ai-explainability/historical-accuracy/${symbol}`),
        fetch(`${BACKEND_URL}/api/ai-explainability/model-performance`),
        fetch(`${BACKEND_URL}/api/ai-explainability/what-if/${symbol}?scenario=${selectedScenario}`)
      ]);

      if (explainRes.ok) setExplanation(await explainRes.json());
      if (accuracyRes.ok) setHistoricalAccuracy(await accuracyRes.json());
      if (perfRes.ok) setModelPerformance(await perfRes.json());
      if (whatIfRes.ok) setWhatIfScenario(await whatIfRes.json());
    } catch (error) {
      console.error('Error fetching explainability data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'BUY': return 'text-green-400 bg-green-500/20';
      case 'SELL': return 'text-red-400 bg-red-500/20';
      default: return 'text-yellow-400 bg-yellow-500/20';
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'BUY': return <TrendingUp className="w-5 h-5" />;
      case 'SELL': return <TrendingDown className="w-5 h-5" />;
      default: return <Minus className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20">
            <Brain className="w-8 h-8 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">AI Explainability</h1>
            <p className="text-gray-400">Understand how AI makes trading decisions</p>
          </div>
        </div>
      </div>

      {/* Symbol Selector */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm text-gray-400">Analyze:</span>
        <div className="flex gap-2">
          {symbols.map(s => (
            <button
              key={s}
              onClick={() => setSymbol(s)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                symbol === s
                  ? 'bg-cyan-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {['explain', 'accuracy', 'what-if', 'models'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-cyan-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {tab === 'explain' && 'Prediction Explanation'}
            {tab === 'accuracy' && 'Historical Accuracy'}
            {tab === 'what-if' && 'What-If Analysis'}
            {tab === 'models' && 'Model Performance'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <>
          {/* Explanation Tab */}
          {activeTab === 'explain' && explanation && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Prediction Card */}
              <div className="lg:col-span-2 space-y-6">
                {/* Prediction Summary */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-semibold text-white">{symbol}/USD Prediction</h2>
                      <p className="text-sm text-gray-400">{explanation.timeframe} timeframe</p>
                    </div>
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${getActionColor(explanation.prediction?.action)}`}>
                      {getActionIcon(explanation.prediction?.action)}
                      <span className="text-lg font-bold">{explanation.prediction?.action}</span>
                    </div>
                  </div>

                  {/* Confidence */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-400">Confidence Level</span>
                      <span className="text-sm font-medium text-white">{(explanation.prediction?.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
                        style={{ width: `${explanation.prediction?.confidence * 100}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">{explanation.confidence_interval?.interpretation}</p>
                  </div>

                  {/* Reasoning */}
                  <div className="bg-gray-900/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Lightbulb className="w-4 h-4 text-yellow-400" />
                      <span className="font-medium text-white">AI Reasoning</span>
                    </div>
                    <p className="text-gray-300 mb-3">{explanation.reasoning?.summary}</p>
                    <ul className="space-y-2">
                      {explanation.reasoning?.key_factors?.map((factor, i) => (
                        <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                          <span className="text-cyan-400 mt-1">•</span>
                          {factor}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm text-yellow-400">{explanation.reasoning?.risk_note}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature Importance */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Feature Importance</h3>
                  <div className="space-y-4">
                    {explanation.feature_importance?.map((feat, i) => (
                      <div key={i} className="group">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="text-white font-medium">{feat.name}</span>
                            <button className="opacity-0 group-hover:opacity-100 transition-opacity">
                              <HelpCircle className="w-4 h-4 text-gray-500" />
                            </button>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              feat.signal === 'bullish' ? 'bg-green-500/20 text-green-400' :
                              feat.signal === 'bearish' ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {feat.signal}
                            </span>
                            <span className="text-sm text-gray-400">{(feat.importance * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-500 ${
                              feat.signal === 'bullish' ? 'bg-green-500' :
                              feat.signal === 'bearish' ? 'bg-red-500' :
                              'bg-gray-500'
                            }`}
                            style={{ width: `${feat.importance * 100}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{feat.interpretation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Model Info */}
                <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                  <h3 className="font-medium text-white mb-3">Model Information</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Model</span>
                      <span className="text-sm text-white">{explanation.model_info?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Version</span>
                      <span className="text-sm text-white">{explanation.model_info?.version}</span>
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <p className="text-xs text-gray-400 mb-2">Ensemble Components</p>
                    {explanation.model_info?.components?.map((comp, i) => (
                      <div key={i} className="flex justify-between text-xs py-1">
                        <span className="text-gray-400">{comp.name}</span>
                        <span className="text-white">{(comp.weight * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-gradient-to-br from-cyan-900/30 to-blue-900/30 border border-cyan-500/20 rounded-xl p-4">
                  <h3 className="font-medium text-white mb-3">Quick Actions</h3>
                  <div className="space-y-2">
                    <button className="w-full py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors">
                      View Trade History
                    </button>
                    <button className="w-full py-2 bg-gray-700/50 text-gray-300 rounded-lg text-sm hover:bg-gray-700 transition-colors">
                      Run Backtest
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Historical Accuracy Tab */}
          {activeTab === 'accuracy' && historicalAccuracy && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Overall Accuracy */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Overall Accuracy</h3>
                <div className="text-center py-6">
                  <p className="text-5xl font-bold text-cyan-400">{historicalAccuracy.overall_accuracy}%</p>
                  <p className="text-gray-400 mt-2">Last {historicalAccuracy.period_days} days</p>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="text-center p-3 bg-gray-900/50 rounded-lg">
                    <p className="text-2xl font-bold text-white">{historicalAccuracy.profit_factor}</p>
                    <p className="text-xs text-gray-400">Profit Factor</p>
                  </div>
                  <div className="text-center p-3 bg-gray-900/50 rounded-lg">
                    <p className="text-2xl font-bold text-white">{historicalAccuracy.sharpe_ratio}</p>
                    <p className="text-xs text-gray-400">Sharpe Ratio</p>
                  </div>
                </div>
              </div>

              {/* By Action */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Accuracy by Action</h3>
                <div className="space-y-4">
                  {Object.entries(historicalAccuracy.by_action || {}).map(([action, data]) => (
                    <div key={action}>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`font-medium ${
                          action === 'BUY' ? 'text-green-400' :
                          action === 'SELL' ? 'text-red-400' :
                          'text-yellow-400'
                        }`}>{action}</span>
                        <span className="text-white">{data.accuracy}%</span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${
                            action === 'BUY' ? 'bg-green-500' :
                            action === 'SELL' ? 'bg-red-500' :
                            'bg-yellow-500'
                          }`}
                          style={{ width: `${data.accuracy}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{data.correct}/{data.predictions} correct</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* By Market Condition */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">By Market Condition</h3>
                <div className="space-y-3">
                  {Object.entries(historicalAccuracy.by_market_condition || {}).map(([condition, data]) => (
                    <div key={condition} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                      <span className="text-gray-300 capitalize">{condition.replace('_', ' ')}</span>
                      <div className="text-right">
                        <span className="text-white font-medium">{data.accuracy}%</span>
                        <p className="text-xs text-gray-500">{data.predictions} predictions</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* By Timeframe */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">By Timeframe</h3>
                <div className="space-y-3">
                  {Object.entries(historicalAccuracy.by_timeframe || {}).map(([tf, data]) => (
                    <div key={tf} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                      <span className="text-gray-300">{tf}</span>
                      <div className="text-right">
                        <span className="text-white font-medium">{data.accuracy}%</span>
                        <p className="text-xs text-gray-500">{data.predictions} predictions</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* What-If Tab */}
          {activeTab === 'what-if' && (
            <div className="max-w-3xl">
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">What-If Scenario Analysis</h3>
                
                {/* Scenario Selector */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-6">
                  {[
                    { id: 'price_up_10', label: 'Price +10%' },
                    { id: 'price_down_10', label: 'Price -10%' },
                    { id: 'volume_spike', label: 'Volume Spike' },
                    { id: 'sentiment_shift', label: 'Sentiment Shift' }
                  ].map(scenario => (
                    <button
                      key={scenario.id}
                      onClick={() => setSelectedScenario(scenario.id)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedScenario === scenario.id
                          ? 'bg-cyan-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {scenario.label}
                    </button>
                  ))}
                </div>

                {whatIfScenario && (
                  <div className="bg-gray-900/50 rounded-lg p-6">
                    <h4 className="text-white font-medium mb-2">{whatIfScenario.name}</h4>
                    <p className="text-gray-400 mb-4">{whatIfScenario.description}</p>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="p-4 bg-gray-800 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Current Prediction</p>
                        <span className={`text-lg font-bold ${getActionColor(whatIfScenario.current_prediction).split(' ')[0]}`}>
                          {whatIfScenario.current_prediction}
                        </span>
                      </div>
                      <div className="p-4 bg-gray-800 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">New Prediction</p>
                        <span className={`text-lg font-bold ${getActionColor(whatIfScenario.new_prediction).split(' ')[0]}`}>
                          {whatIfScenario.new_prediction}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-gray-400">Confidence Change:</span>
                      <span className={`font-medium ${
                        whatIfScenario.confidence_change >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {whatIfScenario.confidence_change >= 0 ? '+' : ''}{(whatIfScenario.confidence_change * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Info className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-blue-300">{whatIfScenario.reasoning}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Models Tab */}
          {activeTab === 'models' && modelPerformance && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Overall Performance */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Ensemble Performance</h3>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(modelPerformance.overall || {}).map(([metric, value]) => (
                    <div key={metric} className="p-3 bg-gray-900/50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-white">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </p>
                      <p className="text-xs text-gray-400 capitalize">{metric.replace('_', ' ')}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Individual Models */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Individual Model Performance</h3>
                <div className="space-y-3">
                  {modelPerformance.by_model?.map((model, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Zap className="w-4 h-4 text-cyan-400" />
                        <span className="text-white">{model.name}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-white">{model.accuracy}%</p>
                          <p className="text-xs text-gray-500">Accuracy</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-white">{model.sharpe}</p>
                          <p className="text-xs text-gray-500">Sharpe</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-cyan-400 mt-4">{modelPerformance.ensemble_improvement}</p>
              </div>

              {/* Backtest Results */}
              <div className="lg:col-span-2 bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Backtest Results</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-900/50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-green-400">+{modelPerformance.backtest_results?.total_return}%</p>
                    <p className="text-xs text-gray-400">Total Return</p>
                  </div>
                  <div className="p-4 bg-gray-900/50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-red-400">{modelPerformance.backtest_results?.max_drawdown}%</p>
                    <p className="text-xs text-gray-400">Max Drawdown</p>
                  </div>
                  <div className="p-4 bg-gray-900/50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-white">{modelPerformance.backtest_results?.win_rate}%</p>
                    <p className="text-xs text-gray-400">Win Rate</p>
                  </div>
                  <div className="p-4 bg-gray-900/50 rounded-lg text-center">
                    <p className="text-3xl font-bold text-cyan-400">{modelPerformance.backtest_results?.profit_factor}</p>
                    <p className="text-xs text-gray-400">Profit Factor</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4">Period: {modelPerformance.backtest_results?.period}</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AIExplainability;
