import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageCircle, Send, X, Loader2, Sparkles, Minimize2, Maximize2,
  Search, Plus, Save, TrendingUp, Zap, Settings, BarChart3, Wallet,
  Target, RefreshCw, ArrowRight, Wand2, Bot, Brain, Command
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const API_URL = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const FloatingCommandHub = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [activeTab, setActiveTab] = useState('command');
  
  // Command Center state
  const [cmdMessages, setCmdMessages] = useState([]);
  const [cmdInput, setCmdInput] = useState('');
  const [cmdLoading, setCmdLoading] = useState(false);
  const [cmdSessionId] = useState(() => `cmd_${Date.now()}`);
  
  // AI Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatSessionId] = useState(() => `chat_${Date.now()}`);
  
  // Strategy Builder state
  const [strategyInput, setStrategyInput] = useState('');
  const [strategyLoading, setStrategyLoading] = useState(false);
  const [generatedStrategy, setGeneratedStrategy] = useState(null);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [cmdMessages, chatMessages]);

  // Initialize welcome messages
  useEffect(() => {
    if (isOpen) {
      if (cmdMessages.length === 0) {
        setCmdMessages([{
          type: 'ai',
          content: `⚡ **Command Center**\n\n• "Find hidden gems"\n• "Add BTC to watchlist"\n• "Go to analytics"\n• "Predict ETH price"`,
        }]);
      }
      if (chatMessages.length === 0) {
        setChatMessages([{
          type: 'ai',
          content: `🤖 **AI Assistant**\n\nAsk me about:\n• Coin analysis\n• Market conditions\n• Trading advice\n• News & sentiment`,
        }]);
      }
    }
  }, [isOpen, cmdMessages.length, chatMessages.length]);

  // Command Center - Execute actions
  const executeCommand = async (message) => {
    if (!message.trim()) return;
    
    setCmdMessages(prev => [...prev, { type: 'user', content: message }]);
    setCmdInput('');
    setCmdLoading(true);
    
    const msgLower = message.toLowerCase();
    
    try {
      // Navigation
      if (msgLower.includes('go to') || msgLower.includes('open') || msgLower.includes('show')) {
        const routes = {
          'dashboard': '/', 'growth': '/growth', 'journal': '/journal',
          'scanner': '/scanner', 'trading': '/trading', 'analytics': '/analytics',
          'tethys': '/tethys', 'news': '/news', 'settings': '/settings',
          'portfolio': '/portfolio-dashboard', 'positions': '/positions'
        };
        for (const [key, path] of Object.entries(routes)) {
          if (msgLower.includes(key)) {
            navigate(path);
            setCmdMessages(prev => [...prev, { type: 'ai', content: `✅ Navigating to ${key}...` }]);
            setIsOpen(false);
            return;
          }
        }
      }
      
      // Find gems
      if (msgLower.includes('find') && (msgLower.includes('gem') || msgLower.includes('hidden'))) {
        const res = await api.get('/scanner/scan-quick?limit=5');
        const gems = res.data.results?.slice(0, 3) || [];
        const gemList = gems.map(g => `• **${g.symbol}**: Score ${g.score?.toFixed(0) || 'N/A'}`).join('\n');
        setCmdMessages(prev => [...prev, { 
          type: 'ai', 
          content: gems.length ? `💎 **Top Gems Found:**\n${gemList}` : 'No gems found right now.'
        }]);
        return;
      }
      
      // AI fallback
      const response = await api.post('/ai-chat/command', {
        command: message,
        session_id: cmdSessionId
      }, { timeout: 30000 });
      
      setCmdMessages(prev => [...prev, { type: 'ai', content: response.data.response || 'Command processed.' }]);
      
    } catch (error) {
      setCmdMessages(prev => [...prev, { type: 'ai', content: '❌ Error processing command. Try again.' }]);
    } finally {
      setCmdLoading(false);
    }
  };

  // AI Chat
  const sendChatMessage = async (message) => {
    if (!message.trim()) return;
    
    setChatMessages(prev => [...prev, { type: 'user', content: message }]);
    setChatInput('');
    setChatLoading(true);
    
    try {
      const response = await api.post('/ai-chat/ask', {
        query: message,
        session_id: chatSessionId,
        include_market_data: true
      }, { timeout: 60000 });
      
      setChatMessages(prev => [...prev, { 
        type: 'ai', 
        content: response.data.response,
        coins: response.data.coins_mentioned
      }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { type: 'ai', content: '❌ Error. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Strategy Builder
  const generateStrategy = async () => {
    if (!strategyInput.trim()) return;
    
    setStrategyLoading(true);
    setGeneratedStrategy(null);
    
    try {
      const response = await fetch(`${API_URL}/api/strategy-builder/from-description`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: strategyInput })
      });
      const data = await response.json();
      setGeneratedStrategy(data);
      toast.success('Strategy generated!');
    } catch (error) {
      toast.error('Failed to generate strategy');
    } finally {
      setStrategyLoading(false);
    }
  };

  const saveStrategy = async () => {
    if (!generatedStrategy) return;
    try {
      await fetch(`${API_URL}/api/strategy-builder/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(generatedStrategy)
      });
      toast.success('Strategy saved!');
    } catch (error) {
      toast.error('Failed to save strategy');
    }
  };

  const formatMessage = (content) => {
    if (!content) return null;
    return content.split('\n').map((line, i) => {
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-400">$1</strong>');
      if (line.startsWith('• ') || line.startsWith('- ')) {
        return <li key={i} className="ml-3 text-xs leading-relaxed" dangerouslySetInnerHTML={{ __html: line.substring(2) }} />;
      }
      return <p key={i} className="text-xs leading-relaxed mb-0.5" dangerouslySetInnerHTML={{ __html: line }} />;
    });
  };

  const quickCommands = [
    { icon: '💎', label: 'Find Gems', action: () => executeCommand('Find hidden gems') },
    { icon: '📊', label: 'Analytics', action: () => { navigate('/analytics'); setIsOpen(false); } },
    { icon: '🌊', label: 'Tethys', action: () => { navigate('/tethys'); setIsOpen(false); } },
    { icon: '⚙️', label: 'Settings', action: () => { navigate('/settings'); setIsOpen(false); } },
  ];

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
            className="fixed bottom-20 right-4 z-[60] w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 shadow-lg shadow-purple-500/30 hover:shadow-xl hover:shadow-purple-500/40 transition-all flex items-center justify-center group"
            data-testid="command-hub-btn"
          >
            <Command size={24} className="text-white group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-400 rounded-full flex items-center justify-center animate-pulse">
              <Zap size={12} className="text-black" />
            </span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Command Hub Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={`fixed z-[60] bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden flex flex-col ${
              isMinimized 
                ? 'bottom-20 right-4 w-72 h-12' 
                : 'bottom-4 right-4 w-[92vw] sm:w-[400px] md:w-[440px] lg:w-[480px] h-[60vh] sm:h-[500px] md:h-[550px] lg:h-[600px] max-h-[calc(100vh-100px)]'
            }`}
            data-testid="command-hub-window"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700/50 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-pink-500/10 flex-shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
                  <Command size={16} className="text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Command Hub</h3>
                  <p className="text-[10px] text-slate-400">AI • Strategy • Commands</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                >
                  <Minimize2 size={14} />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsOpen(false)}
                  className="h-7 w-7 p-0 text-slate-400 hover:text-red-400"
                >
                  <X size={14} />
                </Button>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
                  <TabsList className="mx-2 mt-2 bg-slate-800/50 p-0.5 h-9 flex-shrink-0">
                    <TabsTrigger value="command" className="flex-1 text-xs gap-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                      <Zap size={12} /> Commands
                    </TabsTrigger>
                    <TabsTrigger value="chat" className="flex-1 text-xs gap-1 data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-400">
                      <MessageCircle size={12} /> Ask AI
                    </TabsTrigger>
                    <TabsTrigger value="strategy" className="flex-1 text-xs gap-1 data-[state=active]:bg-pink-500/20 data-[state=active]:text-pink-400">
                      <Wand2 size={12} /> Strategy
                    </TabsTrigger>
                  </TabsList>

                  {/* Command Center Tab */}
                  <TabsContent value="command" className="flex-1 flex flex-col overflow-hidden m-0 p-2 mt-0">
                    {/* Quick Actions */}
                    <div className="flex gap-1.5 mb-2 flex-shrink-0">
                      {quickCommands.map((cmd, i) => (
                        <button
                          key={i}
                          onClick={cmd.action}
                          className="flex-1 py-1.5 px-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 text-[10px] text-slate-300 hover:text-white transition-all flex flex-col items-center gap-0.5"
                        >
                          <span>{cmd.icon}</span>
                          <span>{cmd.label}</span>
                        </button>
                      ))}
                    </div>
                    
                    {/* Messages - takes remaining space */}
                    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                      {cmdMessages.length === 0 && !cmdLoading && (
                        <div className="flex justify-start">
                          <div className="max-w-[85%] rounded-xl px-3 py-2 bg-slate-800/80 text-slate-200">
                            <p className="text-xs leading-relaxed mb-1"><strong className="text-cyan-400">Command Center</strong></p>
                            <ul className="space-y-0.5">
                              <li className="ml-3 text-xs leading-relaxed">• "Find hidden gems"</li>
                              <li className="ml-3 text-xs leading-relaxed">• "Add BTC to watchlist"</li>
                              <li className="ml-3 text-xs leading-relaxed">• "Go to analytics"</li>
                              <li className="ml-3 text-xs leading-relaxed">• "Predict ETH price"</li>
                            </ul>
                          </div>
                        </div>
                      )}
                      {cmdMessages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] rounded-xl px-3 py-2 ${
                            msg.type === 'user' 
                              ? 'bg-cyan-500/20 text-cyan-100' 
                              : 'bg-slate-800/80 text-slate-200'
                          }`}>
                            {formatMessage(msg.content)}
                          </div>
                        </div>
                      ))}
                      {cmdLoading && (
                        <div className="flex justify-start">
                          <div className="bg-slate-800/80 rounded-xl px-3 py-2">
                            <Loader2 size={14} className="animate-spin text-cyan-400" />
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>
                    
                    {/* Input - fixed at bottom */}
                    <form onSubmit={(e) => { e.preventDefault(); executeCommand(cmdInput); }} className="flex gap-2 mt-auto pt-2 flex-shrink-0 border-t border-slate-700/30">
                      <Input
                        value={cmdInput}
                        onChange={(e) => setCmdInput(e.target.value)}
                        placeholder="Type a command..."
                        className="flex-1 h-9 bg-slate-800/50 border-slate-700/50 text-sm text-white placeholder:text-slate-400"
                        disabled={cmdLoading}
                      />
                      <Button type="submit" size="sm" disabled={cmdLoading} className="h-9 w-9 p-0 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400">
                        <Send size={14} />
                      </Button>
                    </form>
                  </TabsContent>

                  {/* AI Chat Tab */}
                  <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden m-0 p-2 mt-0">
                    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                      {chatMessages.length === 0 && !chatLoading && (
                        <div className="flex justify-start">
                          <div className="max-w-[85%] rounded-xl px-3 py-2 bg-slate-800/80 text-slate-200">
                            <p className="text-xs leading-relaxed mb-1"><strong className="text-purple-400">AI Assistant</strong></p>
                            <p className="text-xs leading-relaxed mb-1">Ask me about:</p>
                            <ul className="space-y-0.5">
                              <li className="ml-3 text-xs leading-relaxed">• Coin analysis</li>
                              <li className="ml-3 text-xs leading-relaxed">• Market conditions</li>
                              <li className="ml-3 text-xs leading-relaxed">• Trading advice</li>
                              <li className="ml-3 text-xs leading-relaxed">• News & sentiment</li>
                            </ul>
                          </div>
                        </div>
                      )}
                      {chatMessages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[85%] rounded-xl px-3 py-2 ${
                            msg.type === 'user' 
                              ? 'bg-purple-500/20 text-purple-100' 
                              : 'bg-slate-800/80 text-slate-200'
                          }`}>
                            {formatMessage(msg.content)}
                            {msg.coins && msg.coins.length > 0 && (
                              <div className="flex gap-1 mt-1 flex-wrap">
                                {msg.coins.map((coin, j) => (
                                  <Badge key={j} variant="outline" className="text-[10px] border-purple-500/50 text-purple-300">
                                    {coin}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="flex justify-start">
                          <div className="bg-slate-800/80 rounded-xl px-3 py-2">
                            <Loader2 size={14} className="animate-spin text-purple-400" />
                          </div>
                        </div>
                      )}
                      <div ref={messagesEndRef} />
                    </div>
                    
                    <form onSubmit={(e) => { e.preventDefault(); sendChatMessage(chatInput); }} className="flex gap-2 mt-auto pt-2 flex-shrink-0 border-t border-slate-700/30">
                      <Input
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask about crypto..."
                        className="flex-1 h-9 bg-slate-800/50 border-slate-700/50 text-sm text-white placeholder:text-slate-400"
                        disabled={chatLoading}
                      />
                      <Button type="submit" size="sm" disabled={chatLoading} className="h-9 w-9 p-0 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400">
                        <Send size={14} />
                      </Button>
                    </form>
                  </TabsContent>

                  {/* Strategy Builder Tab */}
                  <TabsContent value="strategy" className="flex-1 flex flex-col overflow-hidden m-0 p-2">
                    <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                      <div className="space-y-2">
                        <label className="text-xs text-slate-400">Describe your strategy:</label>
                        <Textarea
                          value={strategyInput}
                          onChange={(e) => setStrategyInput(e.target.value)}
                          placeholder="e.g., Buy BTC when RSI is below 30 and sell at 20% profit with 5% stop loss"
                          className="h-24 bg-slate-800/50 border-slate-700/50 text-sm text-white placeholder:text-slate-400 resize-none"
                        />
                        <Button 
                          onClick={generateStrategy}
                          disabled={strategyLoading || !strategyInput.trim()}
                          className="w-full h-9 bg-gradient-to-r from-pink-500/20 to-purple-500/20 hover:from-pink-500/30 hover:to-purple-500/30 text-pink-300 border border-pink-500/30"
                        >
                          {strategyLoading ? (
                            <><Loader2 size={14} className="animate-spin mr-2" /> Generating...</>
                          ) : (
                            <><Wand2 size={14} className="mr-2" /> Generate Strategy</>
                          )}
                        </Button>
                      </div>

                      {generatedStrategy && (
                        <div className="space-y-2 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-white">{generatedStrategy.name || 'Generated Strategy'}</h4>
                            <Button size="sm" variant="ghost" onClick={saveStrategy} className="h-7 text-xs text-green-400 hover:text-green-300">
                              <Save size={12} className="mr-1" /> Save
                            </Button>
                          </div>
                          
                          <div className="space-y-1.5 text-xs">
                            {generatedStrategy.entry_conditions && (
                              <div>
                                <span className="text-green-400">Entry:</span>
                                <p className="text-slate-300 ml-2">{generatedStrategy.entry_conditions.join(', ')}</p>
                              </div>
                            )}
                            {generatedStrategy.exit_conditions && (
                              <div>
                                <span className="text-red-400">Exit:</span>
                                <p className="text-slate-300 ml-2">{generatedStrategy.exit_conditions.join(', ')}</p>
                              </div>
                            )}
                            {generatedStrategy.risk_params && (
                              <div className="flex gap-2 mt-2">
                                <Badge variant="outline" className="text-[10px] border-yellow-500/50 text-yellow-300">
                                  SL: {generatedStrategy.risk_params.stop_loss_pct}%
                                </Badge>
                                <Badge variant="outline" className="text-[10px] border-green-500/50 text-green-300">
                                  TP: {generatedStrategy.risk_params.take_profit_pct}%
                                </Badge>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Quick Templates */}
                      <div className="space-y-1.5">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wide">Quick Templates</p>
                        {[
                          'RSI oversold bounce with volume confirmation',
                          'Moving average golden cross strategy',
                          'Whale accumulation follower'
                        ].map((template, i) => (
                          <button
                            key={i}
                            onClick={() => setStrategyInput(template)}
                            className="w-full text-left px-2 py-1.5 rounded-lg bg-slate-800/30 hover:bg-slate-700/50 text-xs text-slate-400 hover:text-white transition-all"
                          >
                            {template}
                          </button>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingCommandHub;
