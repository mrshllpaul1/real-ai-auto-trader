import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Wand2, 
  FileCode, 
  Play, 
  Save, 
  Trash2, 
  Plus, 
  Sparkles, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Loader2,
  MessageSquare,
  Send,
  Bot,
  Settings,
  Target,
  Shield
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../services/api';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const StrategyBuilder = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('ai-builder');
  const [templates, setTemplates] = useState([]);
  const [savedStrategies, setSavedStrategies] = useState([]);
  const [indicators, setIndicators] = useState({});
  const [loading, setLoading] = useState(false);
  
  // AI Builder state
  const [aiDescription, setAiDescription] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [generatedStrategy, setGeneratedStrategy] = useState(null);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const chatEndRef = useRef(null);
  
  // Manual builder state
  const [manualStrategy, setManualStrategy] = useState({
    name: '',
    description: '',
    entry_conditions: [],
    exit_conditions: [],
    risk_params: {
      stop_loss_pct: 10,
      take_profit_pct: 30,
      position_size_pct: 10,
      max_positions: 5
    },
    coins: ['BTC', 'ETH'],
    timeframe: '4h'
  });

  useEffect(() => {
    fetchTemplates();
    fetchStrategies();
    fetchIndicators();
    
    // Initial AI greeting
    setChatMessages([{
      role: 'assistant',
      content: "👋 Hi! I'm your AI Strategy Builder assistant. I can help you create custom trading strategies using natural language. Try describing your trading idea, like:\n\n• \"Buy BTC when RSI is oversold and sell at 20% profit\"\n• \"Follow whale movements and accumulate during fear\"\n• \"Use moving average crossovers with volume confirmation\""
    }]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/templates`);
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/strategies`);
      const data = await response.json();
      setSavedStrategies(data);
    } catch (error) {
      console.error('Failed to fetch strategies:', error);
    }
  };

  const fetchIndicators = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/indicators`);
      const data = await response.json();
      setIndicators(data);
    } catch (error) {
      console.error('Failed to fetch indicators:', error);
    }
  };

  const handleAIBuild = async () => {
    if (!aiDescription.trim()) {
      toast.error('Please describe your strategy');
      return;
    }

    setAiGenerating(true);
    setChatMessages(prev => [...prev, { role: 'user', content: aiDescription }]);

    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/from-description`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: aiDescription })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGeneratedStrategy(data.strategy);
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ I've created a strategy based on your description!\n\n**${data.strategy.name}**\n${data.strategy.description}\n\nEntry: ${data.strategy.entry_conditions?.length || 0} conditions\nExit: ${data.strategy.exit_conditions?.length || 0} conditions\nRisk: ${data.strategy.risk_params?.stop_loss_pct}% SL / ${data.strategy.risk_params?.take_profit_pct}% TP\n\nWould you like me to adjust anything?`
        }]);
        toast.success('Strategy created!');
      } else {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ I had some trouble creating the strategy: ${data.message || data.error}\n\nCould you try rephrasing? Be specific about:\n• What indicators to use\n• When to buy/sell\n• Risk parameters (optional)`
        }]);
        toast.error('Failed to create strategy');
      }
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Sorry, there was an error processing your request. Please try again.'
      }]);
      toast.error('Error creating strategy');
    } finally {
      setAiGenerating(false);
      setAiDescription('');
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setAiGenerating(true);

    try {
      // Check if this is a modification request or new strategy
      if (generatedStrategy && (
        userMessage.toLowerCase().includes('change') ||
        userMessage.toLowerCase().includes('adjust') ||
        userMessage.toLowerCase().includes('modify') ||
        userMessage.toLowerCase().includes('update')
      )) {
        // Get AI suggestions for the current strategy
        const response = await fetch(`${API_BASE}/api/strategy-builder/suggestions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            strategy: generatedStrategy,
            session_id: 'strategy_builder'
          })
        });
        
        const data = await response.json();
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: data.suggestions || 'I can help you adjust the strategy. What specific changes would you like?'
        }]);
      } else {
        // Create new strategy
        setAiDescription(userMessage);
        await handleAIBuild();
        return; // handleAIBuild handles the chat response
      }
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Error processing request. Please try again.'
      }]);
    } finally {
      setAiGenerating(false);
    }
  };

  const handleTemplateSelect = async (templateName) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/from-template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_name: templateName })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGeneratedStrategy(data.strategy);
        setActiveTab('preview');
        toast.success(`Template "${templateName}" loaded`);
      } else {
        toast.error('Failed to load template');
      }
    } catch (error) {
      toast.error('Error loading template');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveStrategy = async () => {
    if (!generatedStrategy) return;

    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: generatedStrategy })
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('Strategy saved!');
        fetchStrategies();
      } else {
        toast.error('Failed to save: ' + (data.message || 'Unknown error'));
      }
    } catch (error) {
      toast.error('Error saving strategy');
    }
  };

  const handleActivateStrategy = async (strategyId) => {
    try {
      const response = await fetch(`${API_BASE}/api/strategy-builder/strategies/${strategyId}/activate`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('Strategy activated!');
        fetchStrategies();
      } else {
        toast.error('Failed to activate');
      }
    } catch (error) {
      toast.error('Error activating strategy');
    }
  };

  const addCondition = (type) => {
    const newCondition = {
      indicator: '',
      operator: '>',
      value: ''
    };
    
    if (type === 'entry') {
      setManualStrategy(prev => ({
        ...prev,
        entry_conditions: [...prev.entry_conditions, newCondition]
      }));
    } else {
      setManualStrategy(prev => ({
        ...prev,
        exit_conditions: [...prev.exit_conditions, newCondition]
      }));
    }
  };

  const removeCondition = (type, index) => {
    if (type === 'entry') {
      setManualStrategy(prev => ({
        ...prev,
        entry_conditions: prev.entry_conditions.filter((_, i) => i !== index)
      }));
    } else {
      setManualStrategy(prev => ({
        ...prev,
        exit_conditions: prev.exit_conditions.filter((_, i) => i !== index)
      }));
    }
  };

  const renderCondition = (condition, index, type) => (
    <div key={index} className="flex items-center gap-2 p-2 bg-slate-800/50 rounded-lg">
      <Select 
        value={condition.indicator}
        onValueChange={(value) => {
          const conditions = type === 'entry' ? [...manualStrategy.entry_conditions] : [...manualStrategy.exit_conditions];
          conditions[index].indicator = value;
          setManualStrategy(prev => ({
            ...prev,
            [type === 'entry' ? 'entry_conditions' : 'exit_conditions']: conditions
          }));
        }}
      >
        <SelectTrigger className="w-[180px] bg-slate-900 border-slate-700">
          <SelectValue placeholder="Indicator" />
        </SelectTrigger>
        <SelectContent className="bg-slate-900 border-slate-700">
          {Object.entries(indicators).map(([category, items]) => (
            items.map(indicator => (
              <SelectItem key={indicator} value={indicator}>
                {indicator}
              </SelectItem>
            ))
          ))}
        </SelectContent>
      </Select>
      
      <Select
        value={condition.operator}
        onValueChange={(value) => {
          const conditions = type === 'entry' ? [...manualStrategy.entry_conditions] : [...manualStrategy.exit_conditions];
          conditions[index].operator = value;
          setManualStrategy(prev => ({
            ...prev,
            [type === 'entry' ? 'entry_conditions' : 'exit_conditions']: conditions
          }));
        }}
      >
        <SelectTrigger className="w-[100px] bg-slate-900 border-slate-700">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="bg-slate-900 border-slate-700">
          <SelectItem value=">">{'>'}</SelectItem>
          <SelectItem value="<">{'<'}</SelectItem>
          <SelectItem value=">=">{'>='}</SelectItem>
          <SelectItem value="<=">{'<='}</SelectItem>
          <SelectItem value="==">{'=='}</SelectItem>
          <SelectItem value="crosses_above">Crosses Above</SelectItem>
          <SelectItem value="crosses_below">Crosses Below</SelectItem>
        </SelectContent>
      </Select>
      
      <Input
        type="text"
        value={condition.value}
        onChange={(e) => {
          const conditions = type === 'entry' ? [...manualStrategy.entry_conditions] : [...manualStrategy.exit_conditions];
          conditions[index].value = e.target.value;
          setManualStrategy(prev => ({
            ...prev,
            [type === 'entry' ? 'entry_conditions' : 'exit_conditions']: conditions
          }));
        }}
        placeholder="Value"
        className="w-[100px] bg-slate-900 border-slate-700"
      />
      
      <Button
        variant="ghost"
        size="icon"
        onClick={() => removeCondition(type, index)}
        className="text-red-400 hover:text-red-300"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
              <Wand2 className="h-8 w-8 text-purple-400" />
              Custom Strategy Builder
            </h1>
            <p className="text-slate-400 mt-1">Create trading strategies with AI assistance</p>
          </div>
          
          <Badge variant="outline" className="border-purple-500 text-purple-400">
            <Sparkles className="h-3 w-3 mr-1" />
            AI-Powered
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Builder Section */}
          <div className="lg:col-span-2">
            <Card className="bg-slate-900/50 border-slate-800">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <CardHeader className="pb-2">
                  <TabsList className="bg-slate-800/50">
                    <TabsTrigger value="ai-builder" className="data-[state=active]:bg-purple-600">
                      <Bot className="h-4 w-4 mr-2" />
                      AI Builder
                    </TabsTrigger>
                    <TabsTrigger value="templates" className="data-[state=active]:bg-purple-600">
                      <FileCode className="h-4 w-4 mr-2" />
                      Templates
                    </TabsTrigger>
                    <TabsTrigger value="manual" className="data-[state=active]:bg-purple-600">
                      <Settings className="h-4 w-4 mr-2" />
                      Manual
                    </TabsTrigger>
                    <TabsTrigger value="preview" className="data-[state=active]:bg-purple-600">
                      <Target className="h-4 w-4 mr-2" />
                      Preview
                    </TabsTrigger>
                  </TabsList>
                </CardHeader>

                <CardContent className="pt-4">
                  {/* AI Builder Tab */}
                  <TabsContent value="ai-builder" className="space-y-4 mt-0">
                    <div className="bg-slate-800/30 rounded-xl p-4 h-[400px] flex flex-col">
                      <ScrollArea className="flex-1 pr-4">
                        <div className="space-y-4">
                          {chatMessages.map((msg, idx) => (
                            <div
                              key={idx}
                              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div
                                className={`max-w-[80%] p-3 rounded-xl ${
                                  msg.role === 'user'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-slate-700 text-slate-100'
                                }`}
                              >
                                <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
                              </div>
                            </div>
                          ))}
                          {aiGenerating && (
                            <div className="flex justify-start">
                              <div className="bg-slate-700 p-3 rounded-xl">
                                <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
                              </div>
                            </div>
                          )}
                          <div ref={chatEndRef} />
                        </div>
                      </ScrollArea>
                      
                      <div className="flex gap-2 mt-4">
                        <Textarea
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          placeholder="Describe your trading strategy... (e.g., 'Buy when RSI < 30 and sell at 20% profit')"
                          className="bg-slate-800 border-slate-700 resize-none"
                          rows={2}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleChatSend();
                            }
                          }}
                        />
                        <Button
                          onClick={handleChatSend}
                          disabled={aiGenerating || !chatInput.trim()}
                          className="bg-purple-600 hover:bg-purple-700"
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </TabsContent>

                  {/* Templates Tab */}
                  <TabsContent value="templates" className="space-y-4 mt-0">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {templates.map((template) => (
                        <Card
                          key={template.name}
                          className="bg-slate-800/50 border-slate-700 hover:border-purple-500 cursor-pointer transition-all"
                          onClick={() => handleTemplateSelect(template.name)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="font-semibold text-white">{template.display_name}</h3>
                                <p className="text-sm text-slate-400 mt-1">{template.description}</p>
                              </div>
                              <Badge variant="outline" className="border-slate-600">
                                {template.indicators?.length || 0} indicators
                              </Badge>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-3">
                              {template.indicators?.slice(0, 4).map(ind => (
                                <Badge key={ind} className="bg-slate-700 text-xs">
                                  {ind}
                                </Badge>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>

                  {/* Manual Builder Tab */}
                  <TabsContent value="manual" className="space-y-4 mt-0">
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm text-slate-400 mb-1 block">Strategy Name</label>
                          <Input
                            value={manualStrategy.name}
                            onChange={(e) => setManualStrategy(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="My Strategy"
                            className="bg-slate-800 border-slate-700"
                          />
                        </div>
                        <div>
                          <label className="text-sm text-slate-400 mb-1 block">Timeframe</label>
                          <Select
                            value={manualStrategy.timeframe}
                            onValueChange={(value) => setManualStrategy(prev => ({ ...prev, timeframe: value }))}
                          >
                            <SelectTrigger className="bg-slate-800 border-slate-700">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-900 border-slate-700">
                              <SelectItem value="1h">1 Hour</SelectItem>
                              <SelectItem value="4h">4 Hours</SelectItem>
                              <SelectItem value="1d">1 Day</SelectItem>
                              <SelectItem value="1w">1 Week</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Entry Conditions */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-medium text-green-400 flex items-center gap-2">
                            <TrendingUp className="h-4 w-4" />
                            Entry Conditions
                          </label>
                          <Button variant="ghost" size="sm" onClick={() => addCondition('entry')}>
                            <Plus className="h-4 w-4 mr-1" />
                            Add
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {manualStrategy.entry_conditions.map((cond, idx) => 
                            renderCondition(cond, idx, 'entry')
                          )}
                          {manualStrategy.entry_conditions.length === 0 && (
                            <p className="text-sm text-slate-500 italic">No entry conditions defined</p>
                          )}
                        </div>
                      </div>

                      {/* Exit Conditions */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-medium text-red-400 flex items-center gap-2">
                            <TrendingDown className="h-4 w-4" />
                            Exit Conditions
                          </label>
                          <Button variant="ghost" size="sm" onClick={() => addCondition('exit')}>
                            <Plus className="h-4 w-4 mr-1" />
                            Add
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {manualStrategy.exit_conditions.map((cond, idx) => 
                            renderCondition(cond, idx, 'exit')
                          )}
                          {manualStrategy.exit_conditions.length === 0 && (
                            <p className="text-sm text-slate-500 italic">No exit conditions defined</p>
                          )}
                        </div>
                      </div>

                      {/* Risk Parameters */}
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-yellow-400 flex items-center gap-2">
                          <Shield className="h-4 w-4" />
                          Risk Parameters
                        </label>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div>
                            <label className="text-xs text-slate-400">Stop Loss %</label>
                            <Input
                              type="number"
                              value={manualStrategy.risk_params.stop_loss_pct}
                              onChange={(e) => setManualStrategy(prev => ({
                                ...prev,
                                risk_params: { ...prev.risk_params, stop_loss_pct: parseFloat(e.target.value) }
                              }))}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">Take Profit %</label>
                            <Input
                              type="number"
                              value={manualStrategy.risk_params.take_profit_pct}
                              onChange={(e) => setManualStrategy(prev => ({
                                ...prev,
                                risk_params: { ...prev.risk_params, take_profit_pct: parseFloat(e.target.value) }
                              }))}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">Position Size %</label>
                            <Input
                              type="number"
                              value={manualStrategy.risk_params.position_size_pct}
                              onChange={(e) => setManualStrategy(prev => ({
                                ...prev,
                                risk_params: { ...prev.risk_params, position_size_pct: parseFloat(e.target.value) }
                              }))}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">Max Positions</label>
                            <Input
                              type="number"
                              value={manualStrategy.risk_params.max_positions}
                              onChange={(e) => setManualStrategy(prev => ({
                                ...prev,
                                risk_params: { ...prev.risk_params, max_positions: parseInt(e.target.value) }
                              }))}
                              className="bg-slate-800 border-slate-700"
                            />
                          </div>
                        </div>
                      </div>

                      <Button
                        className="w-full bg-purple-600 hover:bg-purple-700"
                        onClick={() => {
                          setGeneratedStrategy(manualStrategy);
                          setActiveTab('preview');
                        }}
                      >
                        <Target className="h-4 w-4 mr-2" />
                        Preview Strategy
                      </Button>
                    </div>
                  </TabsContent>

                  {/* Preview Tab */}
                  <TabsContent value="preview" className="space-y-4 mt-0">
                    {generatedStrategy ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xl font-bold text-white">{generatedStrategy.name}</h3>
                          <div className="flex gap-2">
                            <Button variant="outline" onClick={handleSaveStrategy}>
                              <Save className="h-4 w-4 mr-2" />
                              Save
                            </Button>
                            <Button className="bg-green-600 hover:bg-green-700">
                              <Play className="h-4 w-4 mr-2" />
                              Backtest
                            </Button>
                          </div>
                        </div>

                        <p className="text-slate-400">{generatedStrategy.description}</p>

                        <div className="grid grid-cols-2 gap-4">
                          {/* Entry Conditions */}
                          <Card className="bg-slate-800/50 border-slate-700">
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm text-green-400 flex items-center gap-2">
                                <TrendingUp className="h-4 w-4" />
                                Entry Conditions
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              {generatedStrategy.entry_conditions?.map((cond, idx) => (
                                <div key={idx} className="text-sm text-slate-300 py-1">
                                  {cond.indicator} {cond.operator} {cond.value}
                                </div>
                              ))}
                            </CardContent>
                          </Card>

                          {/* Exit Conditions */}
                          <Card className="bg-slate-800/50 border-slate-700">
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm text-red-400 flex items-center gap-2">
                                <TrendingDown className="h-4 w-4" />
                                Exit Conditions
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              {generatedStrategy.exit_conditions?.map((cond, idx) => (
                                <div key={idx} className="text-sm text-slate-300 py-1">
                                  {cond.indicator} {cond.operator} {cond.value}
                                </div>
                              ))}
                            </CardContent>
                          </Card>
                        </div>

                        {/* Risk Parameters */}
                        <Card className="bg-slate-800/50 border-slate-700">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm text-yellow-400 flex items-center gap-2">
                              <Shield className="h-4 w-4" />
                              Risk Parameters
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-4 gap-4 text-center">
                              <div>
                                <p className="text-2xl font-bold text-red-400">{generatedStrategy.risk_params?.stop_loss_pct}%</p>
                                <p className="text-xs text-slate-500">Stop Loss</p>
                              </div>
                              <div>
                                <p className="text-2xl font-bold text-green-400">{generatedStrategy.risk_params?.take_profit_pct}%</p>
                                <p className="text-xs text-slate-500">Take Profit</p>
                              </div>
                              <div>
                                <p className="text-2xl font-bold text-blue-400">{generatedStrategy.risk_params?.position_size_pct}%</p>
                                <p className="text-xs text-slate-500">Position Size</p>
                              </div>
                              <div>
                                <p className="text-2xl font-bold text-purple-400">{generatedStrategy.risk_params?.max_positions || 5}</p>
                                <p className="text-xs text-slate-500">Max Positions</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    ) : (
                      <div className="text-center py-12 text-slate-500">
                        <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No strategy to preview</p>
                        <p className="text-sm">Use the AI Builder or Templates to create one</p>
                      </div>
                    )}
                  </TabsContent>
                </CardContent>
              </Tabs>
            </Card>
          </div>

          {/* Saved Strategies Sidebar */}
          <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileCode className="h-5 w-5 text-purple-400" />
                  Saved Strategies
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  <div className="space-y-3 pr-4">
                    {savedStrategies.length > 0 ? (
                      savedStrategies.map((strategy, idx) => (
                        <Card
                          key={idx}
                          className="bg-slate-800/50 border-slate-700 cursor-pointer hover:border-purple-500"
                          onClick={() => {
                            setGeneratedStrategy(strategy);
                            setActiveTab('preview');
                          }}
                        >
                          <CardContent className="p-3">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium text-white text-sm">{strategy.name}</h4>
                              <Badge
                                className={
                                  strategy.status === 'active'
                                    ? 'bg-green-600'
                                    : strategy.status === 'inactive'
                                    ? 'bg-red-600'
                                    : 'bg-slate-600'
                                }
                              >
                                {strategy.status || 'draft'}
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-500 mt-1 truncate">
                              {strategy.description || 'No description'}
                            </p>
                            {strategy.status !== 'active' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="mt-2 text-green-400 hover:text-green-300 p-0 h-auto"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleActivateStrategy(strategy._id);
                                }}
                              >
                                <Play className="h-3 w-3 mr-1" />
                                Activate
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      ))
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        <FileCode className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">No saved strategies</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-yellow-400" />
                  AI Builder Tips
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-slate-400 space-y-2">
                <p>• Be specific about entry/exit conditions</p>
                <p>• Include risk parameters if needed</p>
                <p>• Mention timeframes for better accuracy</p>
                <p>• Ask for suggestions to improve strategies</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyBuilder;
