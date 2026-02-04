import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Zap, Bell, TrendingUp, TrendingDown, AlertTriangle, Clock,
  Plus, Trash2, Play, Pause, History, Target, RefreshCw,
  Check, X, DollarSign, Filter, Search, Settings2, Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const EventTriggers = () => {
  const [status, setStatus] = useState(null);
  const [triggers, setTriggers] = useState([]);
  const [templates, setTemplates] = useState({});
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('triggers');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [newTrigger, setNewTrigger] = useState({
    trigger_id: '',
    name: '',
    keywords: '',
    coins: '',
    action: 'alert',
    amount_usd: '',
    sentiment_filter: 'any',
    cooldown_hours: 24,
    enabled: true
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, triggersRes, templatesRes, historyRes] = await Promise.all([
        api.get('/triggers/status').catch(() => ({ data: null })),
        api.get('/triggers/list').catch(() => ({ data: { triggers: [] } })),
        api.get('/triggers/templates').catch(() => ({ data: { templates: {} } })),
        api.get('/triggers/history/all?limit=50').catch(() => ({ data: { history: [] } }))
      ]);

      setStatus(statusRes.data);
      setTriggers(triggersRes.data?.triggers || []);
      setTemplates(templatesRes.data?.templates || {});
      setHistory(historyRes.data?.history || []);
    } catch (error) {
      console.error('Error loading event triggers:', error);
      toast.error('Failed to load event triggers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCheckNow = async () => {
    try {
      toast.info('Checking news events...');
      const response = await api.post('/triggers/check-now');
      if (response.data.triggers_executed > 0) {
        toast.success(`${response.data.triggers_executed} trigger(s) matched!`);
      } else {
        toast.info('No matching events found');
      }
      loadData();
    } catch (error) {
      toast.error('Failed to check events');
    }
  };

  const handleToggleTrigger = async (triggerId, enabled) => {
    try {
      await api.post(`/triggers/${triggerId}/${enabled ? 'enable' : 'disable'}`);
      toast.success(`Trigger ${enabled ? 'enabled' : 'disabled'}`);
      loadData();
    } catch (error) {
      toast.error('Failed to update trigger');
    }
  };

  const handleDeleteTrigger = async (triggerId) => {
    if (!window.confirm('Are you sure you want to delete this trigger?')) return;
    try {
      await api.delete(`/triggers/${triggerId}`);
      toast.success('Trigger deleted');
      loadData();
    } catch (error) {
      toast.error('Failed to delete trigger');
    }
  };

  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate) {
      toast.error('Please select a template');
      return;
    }
    const triggerId = `${selectedTemplate}_${Date.now()}`;
    try {
      await api.post('/triggers/create-from-template', {
        template_name: selectedTemplate,
        trigger_id: triggerId,
        amount_usd: parseFloat(newTrigger.amount_usd) || 50,
        enabled: true
      });
      toast.success('Trigger created from template!');
      setShowCreateModal(false);
      setSelectedTemplate('');
      setNewTrigger({ ...newTrigger, amount_usd: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create trigger');
    }
  };

  const handleCreateCustom = async () => {
    if (!newTrigger.trigger_id || !newTrigger.name || !newTrigger.keywords || !newTrigger.coins) {
      toast.error('Please fill all required fields');
      return;
    }
    try {
      await api.post('/triggers/create', {
        trigger_id: newTrigger.trigger_id.replace(/\s+/g, '_').toLowerCase(),
        name: newTrigger.name,
        keywords: newTrigger.keywords.split(',').map(k => k.trim()),
        coins: newTrigger.coins.split(',').map(c => c.trim().toUpperCase()),
        action: newTrigger.action,
        amount_usd: parseFloat(newTrigger.amount_usd) || null,
        sentiment_filter: newTrigger.sentiment_filter === 'any' ? null : newTrigger.sentiment_filter,
        cooldown_hours: parseInt(newTrigger.cooldown_hours) || 24,
        enabled: newTrigger.enabled
      });
      toast.success('Custom trigger created!');
      setShowCreateModal(false);
      setNewTrigger({
        trigger_id: '', name: '', keywords: '', coins: '', action: 'alert',
        amount_usd: '', sentiment_filter: 'any', cooldown_hours: 24, enabled: true
      });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create trigger');
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'buy': return <TrendingUp className="text-[#00FF94]" size={16} />;
      case 'sell': return <TrendingDown className="text-[#FF0055]" size={16} />;
      default: return <Bell className="text-[#FFB800]" size={16} />;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'buy': return 'bg-[#00FF94]/20 text-[#00FF94] border-[#00FF94]/30';
      case 'sell': return 'bg-[#FF0055]/20 text-[#FF0055] border-[#FF0055]/30';
      default: return 'bg-[#FFB800]/20 text-[#FFB800] border-[#FFB800]/30';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Event Triggers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="event-triggers-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Zap size={40} className="text-[#FFB800]" />
            <span className="text-[#FFB800]">Event</span> Triggers
          </h1>
          <p className="text-[#A1A1AA]">
            Automated trading based on real-time news events
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleCheckNow}
            className="bg-[#9D00FF] hover:bg-[#9D00FF]/80"
            data-testid="check-now-btn"
          >
            <Play size={16} className="mr-2" />
            Check Now
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
            data-testid="create-trigger-btn"
          >
            <Plus size={16} className="mr-2" />
            New Trigger
          </Button>
          <Button
            onClick={loadData}
            variant="outline"
            className="border-[#1F1F1F]"
            data-testid="refresh-btn"
          >
            <RefreshCw size={16} />
          </Button>
        </div>
      </motion.div>

      {/* Status Cards */}
      {status && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="total-triggers-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Target size={20} className="text-[#9D00FF]" />
                <span className="text-sm text-[#A1A1AA]">Total Triggers</span>
              </div>
              <div className="text-3xl font-data font-bold text-white">
                {status.total_triggers || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="enabled-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Check size={20} className="text-[#00FF94]" />
                <span className="text-sm text-[#A1A1AA]">Enabled</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#00FF94]">
                {status.enabled_triggers || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="executions-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <History size={20} className="text-[#007AFF]" />
                <span className="text-sm text-[#A1A1AA]">Executions</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#007AFF]">
                {status.total_executions || 0}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="success-rate-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Sparkles size={20} className="text-[#FFB800]" />
                <span className="text-sm text-[#A1A1AA]">Success Rate</span>
              </div>
              <div className="text-3xl font-data font-bold text-[#FFB800]">
                {status.success_rate || 0}%
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="templates-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Settings2 size={20} className="text-[#A1A1AA]" />
                <span className="text-sm text-[#A1A1AA]">Templates</span>
              </div>
              <div className="text-3xl font-data font-bold text-white">
                {status.available_templates?.length || 0}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="triggers" className="data-[state=active]:bg-[#FFB800] data-[state=active]:text-black">
            My Triggers ({triggers.length})
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-[#FFB800] data-[state=active]:text-black">
            Templates ({Object.keys(templates).length})
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-[#FFB800] data-[state=active]:text-black">
            History ({history.length})
          </TabsTrigger>
        </TabsList>

        {/* My Triggers Tab */}
        <TabsContent value="triggers" className="space-y-4">
          {triggers.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <Zap size={48} className="mx-auto mb-4 text-[#FFB800] opacity-50" />
                <p className="text-[#A1A1AA] mb-4">No triggers configured yet</p>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                >
                  <Plus size={16} className="mr-2" />
                  Create Your First Trigger
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {triggers.map((trigger) => (
                <motion.div
                  key={trigger.trigger_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`trigger-${trigger.trigger_id}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <div className={`p-2 rounded-lg ${trigger.enabled ? 'bg-[#00FF94]/20' : 'bg-[#1F1F1F]'}`}>
                              {getActionIcon(trigger.action)}
                            </div>
                            <div>
                              <h3 className="font-bold text-white">{trigger.name}</h3>
                              <p className="text-xs text-[#A1A1AA]">ID: {trigger.trigger_id}</p>
                            </div>
                            <Badge className={`${getActionColor(trigger.action)} border`}>
                              {trigger.action.toUpperCase()}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                            <div>
                              <p className="text-xs text-[#A1A1AA] mb-1">Keywords</p>
                              <div className="flex flex-wrap gap-1">
                                {trigger.keywords.slice(0, 3).map((kw, i) => (
                                  <Badge key={i} variant="outline" className="text-xs border-[#1F1F1F]">
                                    {kw}
                                  </Badge>
                                ))}
                                {trigger.keywords.length > 3 && (
                                  <Badge variant="outline" className="text-xs border-[#1F1F1F]">
                                    +{trigger.keywords.length - 3}
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA] mb-1">Coins</p>
                              <div className="flex flex-wrap gap-1">
                                {trigger.coins.map((coin, i) => (
                                  <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF] text-xs">
                                    {coin}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA] mb-1">Amount</p>
                              <p className="text-white font-data">
                                {trigger.amount_usd ? `$${trigger.amount_usd}` : trigger.amount_pct ? `${trigger.amount_pct}%` : 'N/A'}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-[#A1A1AA] mb-1">Cooldown</p>
                              <p className="text-white font-data">{trigger.cooldown_hours}h</p>
                            </div>
                          </div>

                          {trigger.last_triggered && (
                            <p className="text-xs text-[#A1A1AA] mt-3">
                              <Clock size={12} className="inline mr-1" />
                              Last triggered: {new Date(trigger.last_triggered).toLocaleString()}
                            </p>
                          )}
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          <Switch
                            checked={trigger.enabled}
                            onCheckedChange={(enabled) => handleToggleTrigger(trigger.trigger_id, enabled)}
                            data-testid={`toggle-${trigger.trigger_id}`}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteTrigger(trigger.trigger_id)}
                            className="text-[#FF0055] hover:bg-[#FF0055]/10"
                            data-testid={`delete-${trigger.trigger_id}`}
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(templates).map(([key, template]) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#FFB800]/50 transition-colors" data-testid={`template-${key}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          {getActionIcon(template.action)}
                          <h3 className="font-bold text-white">{template.name}</h3>
                          <Badge className={`${getActionColor(template.action)} border`}>
                            {template.action.toUpperCase()}
                          </Badge>
                        </div>
                        <p className="text-sm text-[#A1A1AA] mb-3">{template.description}</p>
                        <div className="flex flex-wrap gap-1 mb-2">
                          {template.keywords.slice(0, 5).map((kw, i) => (
                            <Badge key={i} variant="outline" className="text-xs border-[#1F1F1F]">
                              {kw}
                            </Badge>
                          ))}
                        </div>
                        <div className="flex gap-1">
                          {template.coins.map((coin, i) => (
                            <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF] text-xs">
                              {coin}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedTemplate(key);
                          setShowCreateModal(true);
                        }}
                        className="border-[#FFB800] text-[#FFB800] hover:bg-[#FFB800]/10"
                        data-testid={`use-template-${key}`}
                      >
                        <Plus size={14} className="mr-1" />
                        Use
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {history.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <History size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
                <p className="text-[#A1A1AA]">No execution history yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {history.map((execution, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`execution-${index}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${execution.success ? 'bg-[#00FF94]/20' : 'bg-[#FF0055]/20'}`}>
                            {execution.success ? (
                              <Check size={20} className="text-[#00FF94]" />
                            ) : (
                              <X size={20} className="text-[#FF0055]" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-white">{execution.trigger_name}</h4>
                              <Badge className={`${getActionColor(execution.action)} border text-xs`}>
                                {execution.action.toUpperCase()}
                              </Badge>
                            </div>
                            <p className="text-sm text-[#A1A1AA] mt-1 line-clamp-1">
                              {execution.event_title}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2 mb-1">
                            {execution.coins?.map((coin, i) => (
                              <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF] text-xs">
                                {coin}
                              </Badge>
                            ))}
                          </div>
                          <p className="text-xs text-[#A1A1AA]">
                            {new Date(execution.executed_at).toLocaleString()}
                          </p>
                          {execution.result?.status && (
                            <Badge variant="outline" className="text-xs mt-1 border-[#FFB800] text-[#FFB800]">
                              {execution.result.status}
                            </Badge>
                          )}
                        </div>
                      </div>
                      {execution.keyword_matches && execution.keyword_matches.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-[#1F1F1F]">
                          <p className="text-xs text-[#A1A1AA]">
                            Matched: {execution.keyword_matches.join(', ')} • Confidence: {execution.match_confidence}%
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Trigger Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowCreateModal(false)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            data-testid="create-trigger-modal"
          >
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Plus className="text-[#00FF94]" />
              Create Trigger
            </h2>

            <Tabs defaultValue={selectedTemplate ? 'template' : 'custom'} className="space-y-4">
              <TabsList className="w-full bg-[#121212]">
                <TabsTrigger value="template" className="flex-1 data-[state=active]:bg-[#FFB800] data-[state=active]:text-black">
                  From Template
                </TabsTrigger>
                <TabsTrigger value="custom" className="flex-1 data-[state=active]:bg-[#FFB800] data-[state=active]:text-black">
                  Custom
                </TabsTrigger>
              </TabsList>

              <TabsContent value="template" className="space-y-4">
                <div>
                  <label className="text-sm text-[#A1A1AA] mb-2 block">Select Template</label>
                  <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F]">
                      <SelectValue placeholder="Choose a template..." />
                    </SelectTrigger>
                    <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                      {Object.entries(templates).map(([key, template]) => (
                        <SelectItem key={key} value={key}>
                          {template.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedTemplate && templates[selectedTemplate] && (
                  <div className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                    <p className="text-sm text-[#A1A1AA]">{templates[selectedTemplate].description}</p>
                    <div className="mt-2 flex gap-1">
                      <Badge className={getActionColor(templates[selectedTemplate].action)}>
                        {templates[selectedTemplate].action}
                      </Badge>
                      {templates[selectedTemplate].coins.map((c, i) => (
                        <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF]">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-2 block">Trade Amount (USD)</label>
                  <Input
                    type="number"
                    placeholder="50"
                    value={newTrigger.amount_usd}
                    onChange={(e) => setNewTrigger({ ...newTrigger, amount_usd: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F]"
                  />
                </div>

                <Button
                  onClick={handleCreateFromTemplate}
                  className="w-full bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                  disabled={!selectedTemplate}
                >
                  Create from Template
                </Button>
              </TabsContent>

              <TabsContent value="custom" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Trigger ID *</label>
                    <Input
                      placeholder="my_trigger"
                      value={newTrigger.trigger_id}
                      onChange={(e) => setNewTrigger({ ...newTrigger, trigger_id: e.target.value })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Name *</label>
                    <Input
                      placeholder="My Custom Trigger"
                      value={newTrigger.name}
                      onChange={(e) => setNewTrigger({ ...newTrigger, name: e.target.value })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-2 block">Keywords * (comma-separated)</label>
                  <Input
                    placeholder="bitcoin, halving, mining"
                    value={newTrigger.keywords}
                    onChange={(e) => setNewTrigger({ ...newTrigger, keywords: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F]"
                  />
                </div>

                <div>
                  <label className="text-sm text-[#A1A1AA] mb-2 block">Coins * (comma-separated)</label>
                  <Input
                    placeholder="BTC, ETH"
                    value={newTrigger.coins}
                    onChange={(e) => setNewTrigger({ ...newTrigger, coins: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Action</label>
                    <Select value={newTrigger.action} onValueChange={(v) => setNewTrigger({ ...newTrigger, action: v })}>
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="alert">Alert Only</SelectItem>
                        <SelectItem value="buy">Buy</SelectItem>
                        <SelectItem value="sell">Sell</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Sentiment Filter</label>
                    <Select value={newTrigger.sentiment_filter} onValueChange={(v) => setNewTrigger({ ...newTrigger, sentiment_filter: v })}>
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="any">Any</SelectItem>
                        <SelectItem value="positive">Positive Only</SelectItem>
                        <SelectItem value="negative">Negative Only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Amount (USD)</label>
                    <Input
                      type="number"
                      placeholder="50"
                      value={newTrigger.amount_usd}
                      onChange={(e) => setNewTrigger({ ...newTrigger, amount_usd: e.target.value })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-[#A1A1AA] mb-2 block">Cooldown (hours)</label>
                    <Input
                      type="number"
                      placeholder="24"
                      value={newTrigger.cooldown_hours}
                      onChange={(e) => setNewTrigger({ ...newTrigger, cooldown_hours: e.target.value })}
                      className="bg-[#121212] border-[#1F1F1F]"
                    />
                  </div>
                </div>

                <Button
                  onClick={handleCreateCustom}
                  className="w-full bg-[#00FF94] hover:bg-[#00FF94]/80 text-black"
                >
                  Create Custom Trigger
                </Button>
              </TabsContent>
            </Tabs>

            <Button
              variant="outline"
              className="w-full mt-4 border-[#1F1F1F]"
              onClick={() => {
                setShowCreateModal(false);
                setSelectedTemplate('');
              }}
            >
              Cancel
            </Button>
          </motion.div>
        </div>
      )}

      {/* Safety Warning */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-[#FF0055]/10 border-[#FF0055]/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-[#FF0055] flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-[#FF0055] mb-1">Safety Notice</h4>
                <p className="text-sm text-[#A1A1AA]">
                  Buy/Sell triggers create trade intents with <span className="text-[#FFB800]">pending_confirmation</span> status. 
                  For safety, real trades require manual confirmation through the AI Chat. Alert triggers send notifications only.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default EventTriggers;
