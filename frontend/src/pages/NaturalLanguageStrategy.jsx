import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, Sparkles, Play, Pause, Trash2, Settings, ChevronRight,
  AlertTriangle, CheckCircle, Info, TrendingUp, TrendingDown,
  Target, Shield, Clock, Zap, BookOpen, Send, RefreshCw
} from 'lucide-react';
import api from '../services/api';
import { useToast } from '../hooks/use-toast';

const NaturalLanguageStrategy = () => {
  const { toast } = useToast();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [parsedStrategy, setParsedStrategy] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [examples, setExamples] = useState([]);
  const [tips, setTips] = useState([]);
  const [indicators, setIndicators] = useState([]);
  const [showExamples, setShowExamples] = useState(true);

  useEffect(() => {
    fetchExamples();
    fetchStrategies();
  }, []);

  const fetchExamples = async () => {
    try {
      const res = await api.get('/nl-strategy/examples');
      setExamples(res.data.examples || []);
      setTips(res.data.tips || []);
      setIndicators(res.data.available_indicators || []);
    } catch (err) {
      console.error('Failed to fetch examples:', err);
    }
  };

  const fetchStrategies = async () => {
    try {
      const res = await api.get('/nl-strategy/list');
      setStrategies(res.data.strategies || []);
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
    }
  };

  const parseStrategy = async () => {
    if (!input.trim() || input.length < 10) {
      toast({
        title: 'Input too short',
        description: 'Please describe your strategy in more detail',
        variant: 'destructive'
      });
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/nl-strategy/parse', { input });
      if (res.data.status === 'success') {
        setParsedStrategy(res.data);
        fetchStrategies();
        toast({
          title: 'Strategy Parsed!',
          description: 'Review your strategy below',
        });
      } else {
        toast({
          title: 'Parsing Failed',
          description: res.data.error || 'Could not parse strategy',
          variant: 'destructive'
        });
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to parse strategy',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const activateStrategy = async (strategyId) => {
    try {
      await api.post(`/nl-strategy/${strategyId}/activate`);
      fetchStrategies();
      toast({ title: 'Strategy Activated!' });
    } catch (err) {
      toast({ title: 'Failed to activate', variant: 'destructive' });
    }
  };

  const deactivateStrategy = async (strategyId) => {
    try {
      await api.post(`/nl-strategy/${strategyId}/deactivate`);
      fetchStrategies();
      toast({ title: 'Strategy Deactivated' });
    } catch (err) {
      toast({ title: 'Failed to deactivate', variant: 'destructive' });
    }
  };

  const deleteStrategy = async (strategyId) => {
    try {
      await api.delete(`/nl-strategy/${strategyId}`);
      fetchStrategies();
      if (parsedStrategy?.strategy_id === strategyId) {
        setParsedStrategy(null);
      }
      toast({ title: 'Strategy Deleted' });
    } catch (err) {
      toast({ title: 'Failed to delete', variant: 'destructive' });
    }
  };

  const useExample = (exampleInput) => {
    setInput(exampleInput);
    setShowExamples(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Natural Language Strategy Builder</h1>
          </div>
          <p className="text-gray-400">Describe your trading strategy in plain English</p>
        </motion.div>

        {/* Main Input Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700"
        >
          <div className="flex items-start gap-4">
            <Sparkles className="w-6 h-6 text-purple-400 mt-3 flex-shrink-0" />
            <div className="flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Example: Buy BTC when RSI drops below 30, set stop loss at 5% and take profit at 15%..."
                className="w-full h-32 bg-gray-900/50 border border-gray-600 rounded-xl p-4 text-white placeholder-gray-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              />
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-500">
                  {input.length} characters {input.length < 10 && '(min 10)'}
                </div>
                <button
                  onClick={parseStrategy}
                  disabled={loading || input.length < 10}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <Zap className="w-5 h-5" />
                  )}
                  {loading ? 'Parsing...' : 'Generate Strategy'}
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Examples Section */}
        {showExamples && examples.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800/30 rounded-xl p-6 border border-gray-700/50"
          >
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-semibold text-white">Example Strategies</h3>
            </div>
            <div className="grid md:grid-cols-2 gap-3">
              {examples.map((ex, idx) => (
                <button
                  key={idx}
                  onClick={() => useExample(ex.input)}
                  className="text-left p-4 bg-gray-900/50 rounded-lg border border-gray-700 hover:border-purple-500 transition-all group"
                >
                  <p className="text-white group-hover:text-purple-300 transition-colors">{ex.input}</p>
                  <p className="text-sm text-gray-500 mt-1">{ex.description}</p>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Parsed Strategy Result */}
        <AnimatePresence>
          {parsedStrategy && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 border border-purple-500/30"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <h3 className="text-xl font-bold text-white">
                    {parsedStrategy.strategy?.strategy_name || 'Parsed Strategy'}
                  </h3>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  parsedStrategy.strategy?.status === 'active'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-600/20 text-gray-400'
                }`}>
                  {parsedStrategy.strategy?.status || 'parsed'}
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Entry Conditions */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-green-400">
                    <TrendingUp className="w-5 h-5" />
                    <span className="font-semibold">Entry Conditions</span>
                  </div>
                  {parsedStrategy.strategy?.entry_conditions?.length > 0 ? (
                    <div className="space-y-2">
                      {parsedStrategy.strategy.entry_conditions.map((cond, idx) => (
                        <div key={idx} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700">
                          <span className="text-white">
                            {cond.indicator} {cond.operator} {cond.value}
                          </span>
                          {cond.timeframe && (
                            <span className="text-gray-500 ml-2">({cond.timeframe})</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">No entry conditions defined</p>
                  )}
                </div>

                {/* Exit Conditions */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-red-400">
                    <TrendingDown className="w-5 h-5" />
                    <span className="font-semibold">Exit Conditions</span>
                  </div>
                  {parsedStrategy.strategy?.exit_conditions?.length > 0 ? (
                    <div className="space-y-2">
                      {parsedStrategy.strategy.exit_conditions.map((cond, idx) => (
                        <div key={idx} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700">
                          <span className="text-white">
                            {cond.indicator} {cond.operator} {cond.value}
                          </span>
                          {cond.timeframe && (
                            <span className="text-gray-500 ml-2">({cond.timeframe})</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">No exit conditions defined</p>
                  )}
                </div>
              </div>

              {/* Risk Management */}
              <div className="mt-6 p-4 bg-gray-900/50 rounded-xl border border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-5 h-5 text-blue-400" />
                  <span className="font-semibold text-white">Risk Management</span>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-400">
                      {parsedStrategy.strategy?.risk_management?.stop_loss_percent || 5}%
                    </div>
                    <div className="text-sm text-gray-500">Stop Loss</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">
                      {parsedStrategy.strategy?.risk_management?.take_profit_percent || 15}%
                    </div>
                    <div className="text-sm text-gray-500">Take Profit</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">
                      {parsedStrategy.strategy?.risk_management?.position_size_percent || 10}%
                    </div>
                    <div className="text-sm text-gray-500">Position Size</div>
                  </div>
                </div>
              </div>

              {/* Coins & Actions */}
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-yellow-400" />
                  <span className="text-gray-400">Coins:</span>
                  <div className="flex gap-2">
                    {(parsedStrategy.strategy?.coins || ['BTC']).map((coin) => (
                      <span key={coin} className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm font-medium">
                        {coin}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  {parsedStrategy.strategy?.status !== 'active' ? (
                    <button
                      onClick={() => activateStrategy(parsedStrategy.strategy_id)}
                      className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                    >
                      <Play className="w-4 h-4" /> Activate
                    </button>
                  ) : (
                    <button
                      onClick={() => deactivateStrategy(parsedStrategy.strategy_id)}
                      className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 text-orange-400 rounded-lg hover:bg-orange-500/30 transition-colors"
                    >
                      <Pause className="w-4 h-4" /> Pause
                    </button>
                  )}
                  <button
                    onClick={() => deleteStrategy(parsedStrategy.strategy_id)}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                </div>
              </div>

              {/* Suggestions */}
              {parsedStrategy.suggestions?.length > 0 && (
                <div className="mt-4 p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                  <div className="flex items-center gap-2 text-blue-400 mb-2">
                    <Info className="w-4 h-4" />
                    <span className="font-medium">Suggestions</span>
                  </div>
                  <ul className="space-y-1">
                    {parsedStrategy.suggestions.map((sug, idx) => (
                      <li key={idx} className="text-sm text-gray-300">• {sug}</li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Saved Strategies */}
        {strategies.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-gray-800/30 rounded-xl p-6 border border-gray-700/50"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Saved Strategies</h3>
            <div className="space-y-3">
              {strategies.map((strat) => (
                <div
                  key={strat.id}
                  className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{strat.strategy_name}</span>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        strat.status === 'active'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-600/20 text-gray-400'
                      }`}>
                        {strat.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1 truncate">{strat.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {strat.status !== 'active' ? (
                      <button
                        onClick={() => activateStrategy(strat.id)}
                        className="p-2 text-green-400 hover:bg-green-500/20 rounded-lg transition-colors"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => deactivateStrategy(strat.id)}
                        className="p-2 text-orange-400 hover:bg-orange-500/20 rounded-lg transition-colors"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteStrategy(strat.id)}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Tips Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 border border-purple-500/20"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Tips for Better Strategies</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {tips.map((tip, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <ChevronRight className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300">{tip}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default NaturalLanguageStrategy;
