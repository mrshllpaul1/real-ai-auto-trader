import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, Send, Sparkles, RefreshCw, Trash2, MessageCircle,
  TrendingUp, TrendingDown, AlertTriangle, Info, Lightbulb,
  ChevronRight, Clock, Zap, Brain, BarChart2
} from 'lucide-react';
import api from '../services/api';
import { useToast } from '../hooks/use-toast';

const AICopilot = () => {
  const { toast } = useToast();
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [quickInsights, setQuickInsights] = useState([]);
  const [marketContext, setMarketContext] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchQuickInsights();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchQuickInsights = async () => {
    try {
      const res = await api.get('/ai-copilot/quick-insights');
      setQuickInsights(res.data.insights || []);
      setMarketContext(res.data.market_context);
    } catch (err) {
      console.error('Failed to fetch insights:', err);
    }
  };

  const sendMessage = async (text = message) => {
    if (!text.trim()) return;

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setLoading(true);

    try {
      const res = await api.post('/ai-copilot/chat', {
        message: text,
        session_id: sessionId,
        include_market_context: true
      });

      if (!sessionId) {
        setSessionId(res.data.session_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: res.data.response,
        timestamp: res.data.timestamp,
        suggestions: res.data.suggestions
      };

      setMessages(prev => [...prev, assistantMessage]);
      setMarketContext(res.data.market_context);

    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to send message',
        variant: 'destructive'
      });
      // Remove the user message if failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    if (sessionId) {
      try {
        await api.post(`/ai-copilot/session/${sessionId}/clear`);
      } catch (err) {
        console.error('Failed to clear session:', err);
      }
    }
    setMessages([]);
    setSessionId(null);
    toast({ title: 'Chat cleared' });
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, idx) => {
        // Bold
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Bullet points
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return `<li key="${idx}" class="ml-4">${line.substring(2)}</li>`;
        }
        return `<p key="${idx}">${line}</p>`;
      })
      .join('');
  };

  const getInsightIcon = (type) => {
    switch (type) {
      case 'opportunity': return <TrendingUp className="w-5 h-5 text-green-400" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'info': return <Info className="w-5 h-5 text-blue-400" />;
      default: return <Lightbulb className="w-5 h-5 text-purple-400" />;
    }
  };

  const quickQuestions = [
    { text: "What's the market sentiment?", icon: BarChart2 },
    { text: "Should I buy BTC now?", icon: TrendingUp },
    { text: "Help me set a stop loss", icon: AlertTriangle },
    { text: "Explain RSI indicator", icon: Brain }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-5xl mx-auto h-screen flex flex-col p-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between py-4 border-b border-gray-700"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Tethys AI Copilot</h1>
              <p className="text-sm text-gray-400">Your intelligent trading assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchQuickInsights}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Refresh insights"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              onClick={clearChat}
              className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
              title="Clear chat"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </motion.div>

        {/* Market Context Bar */}
        {marketContext && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-4 py-3 px-4 bg-gray-800/50 rounded-lg mt-4 text-sm"
          >
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Fear & Greed:</span>
              <span className={`font-bold ${
                marketContext.fear_greed_index < 25 ? 'text-red-400' :
                marketContext.fear_greed_index < 45 ? 'text-orange-400' :
                marketContext.fear_greed_index < 55 ? 'text-yellow-400' :
                marketContext.fear_greed_index < 75 ? 'text-green-400' : 'text-green-300'
              }`}>
                {marketContext.fear_greed_index} ({marketContext.fear_greed_label})
              </span>
            </div>
            <div className="h-4 w-px bg-gray-600" />
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Sentiment:</span>
              <span className="text-white font-medium">
                {marketContext.market_sentiment}
              </span>
            </div>
          </motion.div>
        )}

        {/* Quick Insights */}
        {quickInsights.length > 0 && messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid md:grid-cols-2 gap-3 mt-4"
          >
            {quickInsights.map((insight, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border ${
                  insight.type === 'opportunity' ? 'bg-green-500/10 border-green-500/30' :
                  insight.type === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30' :
                  'bg-blue-500/10 border-blue-500/30'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {getInsightIcon(insight.type)}
                  <span className="font-semibold text-white">{insight.title}</span>
                </div>
                <p className="text-sm text-gray-300">{insight.description}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="p-4 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-full mb-4">
                <Sparkles className="w-12 h-12 text-cyan-400" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">How can I help you today?</h2>
              <p className="text-gray-400 mb-6 max-w-md">
                Ask me about market analysis, trading strategies, risk management, or anything crypto-related.
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-lg">
                {quickQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(q.text)}
                    className="flex items-center gap-2 p-3 bg-gray-800 hover:bg-gray-700 rounded-xl border border-gray-700 hover:border-cyan-500/50 transition-all text-left"
                  >
                    <q.icon className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                    <span className="text-sm text-gray-300">{q.text}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 rounded-2xl rounded-br-md'
                      : 'bg-gray-800 rounded-2xl rounded-bl-md border border-gray-700'
                  } p-4`}>
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2">
                        <Bot className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm text-cyan-400 font-medium">Tethys AI</span>
                      </div>
                    )}
                    <div
                      className="text-white prose prose-invert prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                    />
                    {msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <p className="text-xs text-gray-400 mb-2">Suggested follow-ups:</p>
                        <div className="flex flex-wrap gap-2">
                          {msg.suggestions.map((sug, sidx) => (
                            <button
                              key={sidx}
                              onClick={() => handleSuggestionClick(sug)}
                              className="text-xs px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white rounded-full transition-colors"
                            >
                              {sug}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-gray-500 mt-2">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-gray-800 rounded-2xl rounded-bl-md border border-gray-700 p-4">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-cyan-400">Tethys AI</span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
                  <span className="text-gray-400">Thinking...</span>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t border-gray-700 pt-4"
        >
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about trading..."
                rows={1}
                className="w-full bg-gray-800 border border-gray-700 rounded-xl p-4 pr-12 text-white placeholder-gray-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
                style={{ minHeight: '56px', maxHeight: '150px' }}
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={loading || !message.trim()}
              className="p-4 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Tethys AI provides insights based on market data. Always do your own research.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default AICopilot;
