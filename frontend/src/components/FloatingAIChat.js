import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Loader2, Sparkles, Minimize2, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const FloatingAIChat = ({ contextHint = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `floating_${Date.now()}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        type: 'ai',
        content: `Hi! I'm your AI assistant with deep learning capabilities. I can help with:\n\n• **Price Predictions** - LSTM-powered forecasts\n• **Hidden Gems** - AI-discovered opportunities\n• **Pattern Analysis** - Chart pattern detection\n• **Sentiment** - News sentiment analysis\n\nAsk me anything!`,
        timestamp: new Date().toISOString()
      }]);
    }
  }, [isOpen, messages.length]);

  const sendMessage = async (message) => {
    if (!message.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // Use deep learning enhanced endpoint
      const response = await api.post('/ai-chat/ask-deep', {
        query: message,
        session_id: sessionId,
        context_hint: contextHint,
        include_predictions: true,
        include_gems: true
      }, { timeout: 90000 });

      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        coins: response.data.coins_mentioned,
        predictions: response.data.predictions,
        gems: response.data.gems,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
      // Fallback to regular endpoint
      try {
        const fallbackResponse = await api.post('/ai-chat/ask', {
          query: message,
          session_id: sessionId
        }, { timeout: 60000 });
        
        setMessages(prev => [...prev, {
          type: 'ai',
          content: fallbackResponse.data.response,
          coins: fallbackResponse.data.coins_mentioned,
          timestamp: fallbackResponse.data.timestamp
        }]);
      } catch (fallbackError) {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: 'Sorry, I encountered an error. Please try again.',
          isError: true,
          timestamp: new Date().toISOString()
        }]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const quickQuestions = [
    "What are today's hidden gems?",
    "Give me a price prediction for BTC",
    "What patterns do you see in the market?"
  ];

  const formatMessage = (content) => {
    return content.split('\n').map((line, i) => {
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return <li key={i} className="ml-3 text-xs" dangerouslySetInnerHTML={{ __html: line.substring(2) }} />;
      }
      return <p key={i} className="text-xs mb-1" dangerouslySetInnerHTML={{ __html: line }} />;
    });
  };

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-[#9D00FF] to-[#00FF94] shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center group"
            data-testid="floating-ai-btn"
          >
            <MessageCircle size={24} className="text-white" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#00FF94] rounded-full flex items-center justify-center">
              <Sparkles size={10} className="text-black" />
            </span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={`fixed z-50 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl shadow-2xl overflow-hidden ${
              isMinimized 
                ? 'bottom-6 right-6 w-72 h-14' 
                : 'bottom-6 right-6 w-96 h-[500px] max-h-[80vh]'
            }`}
            data-testid="floating-ai-window"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-[#1F1F1F] bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#9D00FF] to-[#00FF94] flex items-center justify-center">
                  <Sparkles size={16} className="text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">AI Assistant</h3>
                  {!isMinimized && <p className="text-xs text-[#A1A1AA]">Deep Learning Powered</p>}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                >
                  {isMinimized ? <Maximize2 size={14} className="text-[#A1A1AA]" /> : <Minimize2 size={14} className="text-[#A1A1AA]" />}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                >
                  <X size={14} className="text-[#A1A1AA]" />
                </button>
              </div>
            </div>

            {/* Messages */}
            {!isMinimized && (
              <>
                <div className="flex-1 overflow-y-auto p-3 space-y-3 h-[calc(100%-120px)]">
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-xl p-3 ${
                          msg.type === 'user'
                            ? 'bg-[#9D00FF] text-white'
                            : msg.isError
                            ? 'bg-[#FF0055]/10 border border-[#FF0055]/30 text-white'
                            : 'bg-[#121212] border border-[#1F1F1F] text-white'
                        }`}
                      >
                        {msg.type === 'ai' && (
                          <div className="flex items-center gap-1 mb-1">
                            <Sparkles size={12} className="text-[#9D00FF]" />
                            <span className="text-[10px] font-bold text-[#9D00FF]">AI</span>
                          </div>
                        )}
                        <div className="leading-relaxed">{formatMessage(msg.content)}</div>
                        {msg.coins && msg.coins.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {msg.coins.slice(0, 3).map((coin, i) => (
                              <Badge key={i} variant="outline" className="text-[10px] border-[#9D00FF]/30 text-[#9D00FF] py-0">
                                {coin}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {msg.predictions && (
                          <div className="mt-2 p-2 bg-black/30 rounded-lg">
                            <div className="text-[10px] text-[#00FF94] font-bold">📈 Prediction</div>
                            <div className="text-xs">{msg.predictions.summary}</div>
                          </div>
                        )}
                        {msg.gems && msg.gems.length > 0 && (
                          <div className="mt-2 p-2 bg-black/30 rounded-lg">
                            <div className="text-[10px] text-[#FF9500] font-bold">💎 Hidden Gems</div>
                            <div className="text-xs">{msg.gems.slice(0, 2).join(', ')}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-[#121212] border border-[#1F1F1F] rounded-xl p-3">
                        <div className="flex items-center gap-2">
                          <Loader2 size={14} className="animate-spin text-[#9D00FF]" />
                          <span className="text-xs text-[#A1A1AA]">Analyzing with AI...</span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Quick Questions */}
                {messages.length <= 1 && !loading && (
                  <div className="px-3 pb-2">
                    <div className="flex flex-wrap gap-1">
                      {quickQuestions.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => sendMessage(q)}
                          className="text-[10px] px-2 py-1 bg-[#1F1F1F] hover:bg-[#333] rounded-full text-[#A1A1AA] hover:text-white transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input */}
                <div className="p-3 border-t border-[#1F1F1F]">
                  <form onSubmit={handleSubmit} className="flex gap-2">
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Ask about predictions, gems..."
                      className="flex-1 h-9 text-sm bg-[#121212] border-[#1F1F1F] focus:border-[#9D00FF] rounded-full px-3"
                      disabled={loading}
                    />
                    <Button
                      type="submit"
                      disabled={loading || !inputValue.trim()}
                      size="sm"
                      className="h-9 w-9 p-0 bg-[#9D00FF] hover:bg-[#8B00E6] rounded-full"
                    >
                      {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                    </Button>
                  </form>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingAIChat;
