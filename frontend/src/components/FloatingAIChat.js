import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageCircle, Send, X, Loader2, Sparkles, Minimize2, Maximize2,
  Search, Plus, Save, TrendingUp, Zap, Settings, BarChart3, Wallet,
  Target, RefreshCw, ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const FloatingAIChat = ({ contextHint = '' }) => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `cmd_${Date.now()}`);
  const [pendingAction, setPendingAction] = useState(null);
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
        content: `🤖 **AI Command Center**\n\nI can help you:\n• **Find** coins, gems, patterns\n• **Add** coins to watchlist/universe\n• **Analyze** any cryptocurrency\n• **Navigate** to any page\n• **Execute** trades & strategies\n• **Get** predictions & signals\n\nTry: "Find hidden gems" or "Add BTC to watchlist"`,
        timestamp: new Date().toISOString()
      }]);
    }
  }, [isOpen, messages.length]);

  // Parse user intent and execute actions
  const parseAndExecute = useCallback(async (message, aiResponse) => {
    const msgLower = message.toLowerCase();
    const actions = [];
    
    // Navigation commands
    if (msgLower.includes('go to') || msgLower.includes('open') || msgLower.includes('show me')) {
      if (msgLower.includes('dashboard')) actions.push({ type: 'navigate', path: '/' });
      else if (msgLower.includes('growth') || msgLower.includes('500')) actions.push({ type: 'navigate', path: '/growth' });
      else if (msgLower.includes('journal')) actions.push({ type: 'navigate', path: '/journal' });
      else if (msgLower.includes('scanner') || msgLower.includes('gems')) actions.push({ type: 'navigate', path: '/scanner' });
      else if (msgLower.includes('trading')) actions.push({ type: 'navigate', path: '/trading' });
      else if (msgLower.includes('analytics')) actions.push({ type: 'navigate', path: '/analytics' });
      else if (msgLower.includes('deep learning') || msgLower.includes('ai predict')) actions.push({ type: 'navigate', path: '/deep-learning' });
      else if (msgLower.includes('news')) actions.push({ type: 'navigate', path: '/news' });
      else if (msgLower.includes('settings')) actions.push({ type: 'navigate', path: '/settings' });
    }
    
    // Add to watchlist/universe
    if (msgLower.includes('add') && (msgLower.includes('watchlist') || msgLower.includes('universe') || msgLower.includes('track'))) {
      const coinMatch = msgLower.match(/add\s+(\w+)\s+to/i);
      if (coinMatch) {
        actions.push({ type: 'add_coin', coin: coinMatch[1].toUpperCase() });
      }
    }
    
    // Find/Search commands
    if (msgLower.includes('find') || msgLower.includes('search') || msgLower.includes('scan')) {
      if (msgLower.includes('gem') || msgLower.includes('hidden')) {
        actions.push({ type: 'scan_gems' });
      }
    }
    
    // Prediction commands
    if (msgLower.includes('predict') || msgLower.includes('forecast')) {
      const coinMatch = message.match(/(?:predict|forecast)\s+(\w+)/i);
      if (coinMatch) {
        actions.push({ type: 'predict', coin: coinMatch[1].toLowerCase() });
      }
    }
    
    // Execute pending actions
    for (const action of actions) {
      await executeAction(action);
    }
    
    return actions;
  }, []);

  const executeAction = async (action) => {
    switch (action.type) {
      case 'navigate':
        navigate(action.path);
        toast.success(`Navigating to ${action.path}`);
        break;
        
      case 'add_coin':
        try {
          await api.post('/ai-universe/add-coin', { coin_id: action.coin.toLowerCase() });
          toast.success(`Added ${action.coin} to universe`);
          addMessage('ai', `✅ Added **${action.coin}** to your trading universe. You can now track it across the app.`);
        } catch (e) {
          toast.error(`Failed to add ${action.coin}`);
        }
        break;
        
      case 'scan_gems':
        try {
          addMessage('ai', '🔍 Scanning for hidden gems...');
          const response = await api.post('/gems/scan', { limit: 10 });
          if (response.data?.gems?.length > 0) {
            const gems = response.data.gems.slice(0, 5);
            const gemList = gems.map(g => `• **${g.symbol || g.coin_id}** - Score: ${g.score || 'N/A'}`).join('\n');
            addMessage('ai', `💎 **Top Hidden Gems Found:**\n${gemList}\n\nSay "Add [COIN] to watchlist" to track any of these.`);
          }
        } catch (e) {
          addMessage('ai', '⚠️ Gem scan temporarily unavailable. Try the Gem Scanner page.');
        }
        break;
        
      case 'predict':
        navigate(`/deep-learning`);
        toast.info(`Opening predictions for ${action.coin}`);
        break;
        
      default:
        break;
    }
  };

  const addMessage = (type, content, extras = {}) => {
    setMessages(prev => [...prev, {
      type,
      content,
      timestamp: new Date().toISOString(),
      ...extras
    }]);
  };

  const sendMessage = async (message) => {
    if (!message.trim() || loading) return;

    addMessage('user', message);
    setInputValue('');
    setLoading(true);

    try {
      const response = await api.post('/ai-chat/execute-command', {
        query: message,
        session_id: sessionId,
        context_hint: contextHint
      }, { timeout: 90000 });

      const aiResponse = response.data;
      
      addMessage('ai', aiResponse.response, {
        coins: aiResponse.coins_mentioned,
        actions: aiResponse.actions_executed,
        predictions: aiResponse.predictions,
        gems: aiResponse.gems
      });
      
      // Execute any detected actions
      if (aiResponse.actions_to_execute?.length > 0) {
        for (const action of aiResponse.actions_to_execute) {
          await executeAction(action);
        }
      }
      
    } catch (error) {
      // Fallback to regular deep chat
      try {
        const fallback = await api.post('/ai-chat/ask-deep', {
          query: message,
          session_id: sessionId
        }, { timeout: 60000 });
        
        addMessage('ai', fallback.data.response, {
          coins: fallback.data.coins_mentioned
        });
        
        // Still try to parse and execute local actions
        await parseAndExecute(message, fallback.data.response);
        
      } catch (e) {
        addMessage('ai', 'Sorry, I encountered an error. Please try again.', { isError: true });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const quickCommands = [
    { label: '💎 Find Gems', query: 'Find hidden gems with high potential' },
    { label: '📈 BTC Predict', query: 'What is your prediction for Bitcoin?' },
    { label: '🔍 Scan Market', query: 'Scan the market for opportunities' },
    { label: '📊 Analytics', query: 'Go to analytics page' },
  ];

  const formatMessage = (content) => {
    return content.split('\n').map((line, i) => {
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-[#9D00FF]">$1</strong>');
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return <li key={i} className="ml-3 text-xs leading-relaxed" dangerouslySetInnerHTML={{ __html: line.substring(2) }} />;
      }
      return <p key={i} className="text-xs leading-relaxed mb-1" dangerouslySetInnerHTML={{ __html: line }} />;
    });
  };

  // Determine chat window size based on state
  const getChatSize = () => {
    if (isMinimized) return 'w-64 h-12';
    if (isFullscreen) return 'inset-2 w-auto h-auto';
    return 'bottom-4 right-4 w-[90vw] sm:w-96 h-[70vh] sm:h-[500px] max-h-[85vh]';
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
            className="fixed bottom-4 right-4 z-50 w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gradient-to-br from-[#9D00FF] to-[#00FF94] shadow-lg hover:shadow-xl transition-all flex items-center justify-center"
            data-testid="floating-ai-btn"
          >
            <MessageCircle size={22} className="text-white" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#00FF94] rounded-full flex items-center justify-center animate-pulse">
              <Zap size={10} className="text-black" />
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
            className={`fixed z-50 bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl shadow-2xl overflow-hidden flex flex-col ${getChatSize()}`}
            data-testid="floating-ai-window"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-2 sm:p-3 border-b border-[#1F1F1F] bg-gradient-to-r from-[#9D00FF]/10 to-[#00FF94]/10 flex-shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-[#9D00FF] to-[#00FF94] flex items-center justify-center">
                  <Zap size={14} className="text-white" />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-white">AI Command Center</h3>
                  {!isMinimized && <p className="text-[10px] text-[#A1A1AA] hidden sm:block">Find • Add • Execute</p>}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-1.5 hover:bg-[#1F1F1F] rounded-lg transition-colors hidden sm:block"
                >
                  <Maximize2 size={12} className="text-[#A1A1AA]" />
                </button>
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                >
                  <Minimize2 size={12} className="text-[#A1A1AA]" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 hover:bg-[#1F1F1F] rounded-lg transition-colors"
                >
                  <X size={12} className="text-[#A1A1AA]" />
                </button>
              </div>
            </div>

            {/* Messages */}
            {!isMinimized && (
              <>
                <div className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-2 sm:space-y-3 min-h-0">
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[90%] rounded-xl p-2 sm:p-3 ${
                          msg.type === 'user'
                            ? 'bg-[#9D00FF] text-white'
                            : msg.isError
                            ? 'bg-[#FF0055]/10 border border-[#FF0055]/30 text-white'
                            : 'bg-[#121212] border border-[#1F1F1F] text-white'
                        }`}
                      >
                        {msg.type === 'ai' && (
                          <div className="flex items-center gap-1 mb-1">
                            <Sparkles size={10} className="text-[#9D00FF]" />
                            <span className="text-[9px] font-bold text-[#9D00FF]">AI</span>
                          </div>
                        )}
                        <div>{formatMessage(msg.content)}</div>
                        {msg.actions?.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {msg.actions.map((action, i) => (
                              <Badge key={i} className="text-[9px] bg-[#00FF94]/20 text-[#00FF94]">
                                ✓ {action.type}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {msg.coins?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {msg.coins.slice(0, 3).map((coin, i) => (
                              <Badge key={i} variant="outline" className="text-[9px] border-[#9D00FF]/30 text-[#9D00FF] py-0">
                                {coin}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-[#121212] border border-[#1F1F1F] rounded-xl p-2">
                        <div className="flex items-center gap-2">
                          <Loader2 size={12} className="animate-spin text-[#9D00FF]" />
                          <span className="text-[10px] text-[#A1A1AA]">Processing...</span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Quick Commands */}
                {messages.length <= 1 && !loading && (
                  <div className="px-2 sm:px-3 pb-1 flex-shrink-0">
                    <div className="flex flex-wrap gap-1">
                      {quickCommands.map((cmd, i) => (
                        <button
                          key={i}
                          onClick={() => sendMessage(cmd.query)}
                          className="text-[9px] sm:text-[10px] px-2 py-1 bg-[#1F1F1F] hover:bg-[#333] rounded-full text-[#A1A1AA] hover:text-white transition-colors"
                        >
                          {cmd.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input */}
                <div className="p-2 sm:p-3 border-t border-[#1F1F1F] flex-shrink-0">
                  <form onSubmit={handleSubmit} className="flex gap-2">
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Find, add, analyze..."
                      className="flex-1 h-8 sm:h-9 text-xs sm:text-sm bg-[#121212] border-[#1F1F1F] focus:border-[#9D00FF] rounded-full px-3"
                      disabled={loading}
                    />
                    <Button
                      type="submit"
                      disabled={loading || !inputValue.trim()}
                      size="sm"
                      className="h-8 w-8 sm:h-9 sm:w-9 p-0 bg-[#9D00FF] hover:bg-[#8B00E6] rounded-full"
                    >
                      {loading ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
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
