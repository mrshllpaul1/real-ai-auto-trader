import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  MessageCircle, 
  Send, 
  Loader2, 
  Sparkles, 
  TrendingUp,
  BarChart3,
  Newspaper,
  Lightbulb,
  RefreshCw,
  Trash2,
  ChevronDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [sessionId] = useState(() => `chat_${Date.now()}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadSuggestions();
    // Add welcome message
    setMessages([{
      type: 'ai',
      content: `👋 Hello! I'm your AI crypto trading assistant. I can help you with:

• **Coin Analysis** - Get insights on any cryptocurrency
• **Market Overview** - Understand current market conditions
• **Trading Strategies** - Get AI-powered trading advice
• **News & Sentiment** - Stay updated on market sentiment
• **Technical Analysis** - Understand chart patterns

Ask me anything about crypto trading!`,
      timestamp: new Date().toISOString()
    }]);
  }, []);

  const loadSuggestions = async () => {
    try {
      const response = await api.get('/ai-chat/suggestions');
      setSuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const sendMessage = useCallback(async (message) => {
    if (!message.trim()) return;

    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setShowSuggestions(false);
    setLoading(true);

    try {
      const response = await api.post('/ai-chat/ask', {
        query: message,
        session_id: sessionId,
        include_market_data: true,
        include_news: true
      }, { timeout: 60000 });

      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        coins: response.data.coins_mentioned,
        context: response.data.context,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        isError: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to get AI response');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !loading) {
      sendMessage(inputValue);
    }
  };

  const handleSuggestionClick = (query) => {
    sendMessage(query);
  };

  const clearChat = () => {
    setMessages([{
      type: 'ai',
      content: 'Chat cleared. How can I help you today?',
      timestamp: new Date().toISOString()
    }]);
    setShowSuggestions(true);
    toast.success('Chat cleared');
  };

  const quickActions = [
    { label: 'Bitcoin Analysis', query: "What's your analysis of Bitcoin right now?", icon: TrendingUp },
    { label: 'Market Overview', query: 'How is the crypto market looking today?', icon: BarChart3 },
    { label: 'Latest News', query: "What's the latest important crypto news?", icon: Newspaper },
    { label: 'Strategy Advice', query: 'What trading strategy do you recommend for current market?', icon: Lightbulb },
  ];

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Bold
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Bullet points
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return <li key={i} className="ml-4" dangerouslySetInnerHTML={{ __html: line.substring(2) }} />;
        }
        // Numbered lists
        if (/^\d+\.\s/.test(line)) {
          return <li key={i} className="ml-4" dangerouslySetInnerHTML={{ __html: line.replace(/^\d+\.\s/, '') }} />;
        }
        return <p key={i} className="mb-1" dangerouslySetInnerHTML={{ __html: line }} />;
      });
  };

  return (
    <div className="p-4 lg:p-8 h-[calc(100vh-4rem)] flex flex-col" data-testid="ai-chat-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between mb-4"
      >
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#9D00FF] to-[#00FF94] flex items-center justify-center">
            <MessageCircle size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl lg:text-3xl font-heading font-black tracking-tight" data-testid="page-title">
              <span className="text-[#9D00FF]">AI</span> Assistant
            </h1>
            <p className="text-sm text-[#A1A1AA]">Ask about coins, strategies, market & more</p>
          </div>
        </div>
        <Button
          onClick={clearChat}
          variant="outline"
          size="sm"
          className="border-[#FF0055]/30 text-[#FF0055] hover:bg-[#FF0055]/10 rounded-full"
          data-testid="clear-chat-btn"
        >
          <Trash2 size={14} className="mr-2" />
          Clear
        </Button>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap gap-2 mb-4"
      >
        {quickActions.map((action, i) => (
          <Button
            key={i}
            onClick={() => handleSuggestionClick(action.query)}
            variant="outline"
            size="sm"
            className="border-[#1F1F1F] hover:border-[#9D00FF]/50 hover:bg-[#9D00FF]/10 rounded-full text-xs"
            disabled={loading}
            data-testid={`quick-action-${i}`}
          >
            <action.icon size={14} className="mr-1 text-[#9D00FF]" />
            {action.label}
          </Button>
        ))}
      </motion.div>

      {/* Chat Container */}
      <Card className="flex-1 bg-[#0A0A0A] border-[#1F1F1F] flex flex-col overflow-hidden" data-testid="chat-container">
        {/* Messages */}
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="messages-container">
          <AnimatePresence>
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] lg:max-w-[70%] rounded-2xl p-4 ${
                    msg.type === 'user'
                      ? 'bg-[#9D00FF] text-white'
                      : msg.isError
                      ? 'bg-[#FF0055]/10 border border-[#FF0055]/30 text-white'
                      : 'bg-[#121212] border border-[#1F1F1F] text-white'
                  }`}
                  data-testid={`message-${msg.type}-${index}`}
                >
                  {msg.type === 'ai' && (
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles size={16} className="text-[#9D00FF]" />
                      <span className="text-xs font-bold text-[#9D00FF]">AI Assistant</span>
                    </div>
                  )}
                  <div className="text-sm leading-relaxed">
                    {formatMessage(msg.content)}
                  </div>
                  {msg.coins && msg.coins.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {msg.coins.map((coin, i) => (
                        <Badge key={i} variant="outline" className="text-xs border-[#9D00FF]/30 text-[#9D00FF]">
                          {coin}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-[#121212] border border-[#1F1F1F] rounded-2xl p-4">
                <div className="flex items-center gap-3">
                  <Loader2 size={20} className="animate-spin text-[#9D00FF]" />
                  <span className="text-sm text-[#A1A1AA]">AI is thinking...</span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Suggestions */}
        {showSuggestions && suggestions && messages.length <= 1 && (
          <div className="px-4 pb-2">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="flex items-center gap-2 text-sm text-[#A1A1AA] hover:text-white mb-2"
            >
              <ChevronDown size={14} className={showSuggestions ? 'rotate-180' : ''} />
              Suggested Questions
            </button>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {suggestions.slice(0, 2).map((category, catIndex) => (
                <div key={catIndex} className="space-y-1">
                  <div className="text-xs font-bold text-[#9D00FF]">{category.category}</div>
                  {category.queries.slice(0, 2).map((query, qIndex) => (
                    <button
                      key={qIndex}
                      onClick={() => handleSuggestionClick(query)}
                      className="block w-full text-left text-xs text-[#A1A1AA] hover:text-white hover:bg-[#1F1F1F] p-2 rounded-lg transition-colors"
                      disabled={loading}
                    >
                      {query}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-[#1F1F1F]">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about any coin, strategy, market..."
              className="flex-1 bg-[#121212] border-[#1F1F1F] focus:border-[#9D00FF] rounded-full px-4"
              disabled={loading}
              data-testid="chat-input"
            />
            <Button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full px-6"
              data-testid="send-btn"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </Button>
          </form>
          <p className="text-xs text-[#666] mt-2 text-center">
            AI responses are for informational purposes only. Always do your own research.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default AIChat;
