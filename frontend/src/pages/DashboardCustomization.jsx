import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { motion } from 'framer-motion';
import {
  Layout, Palette, Settings2, Grid3X3, Save, RotateCcw,
  Sun, Moon, Monitor, Sparkles, Check, Plus, Trash2,
  Move, Eye, EyeOff, RefreshCw
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const DashboardCustomization = ({ embedded = false }) => {
  const [layout, setLayout] = useState(null);
  const [layouts, setLayouts] = useState([]);
  const [theme, setTheme] = useState(null);
  const [themePresets, setThemePresets] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [availableWidgets, setAvailableWidgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('layout');
  const [layoutName, setLayoutName] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [layoutRes, layoutsRes, themeRes, presetsRes, prefsRes, widgetsRes] = await Promise.all([
        api.get('/dashboard/layout').catch(() => ({ data: null })),
        api.get('/dashboard/layouts').catch(() => ({ data: { layouts: [] } })),
        api.get('/dashboard/theme').catch(() => ({ data: null })),
        api.get('/dashboard/theme/presets').catch(() => ({ data: { presets: [] } })),
        api.get('/dashboard/preferences').catch(() => ({ data: null })),
        api.get('/dashboard/widgets').catch(() => ({ data: { widgets: [] } }))
      ]);

      setLayout(layoutRes.data);
      setLayouts(layoutsRes.data.layouts || []);
      setTheme(themeRes.data);
      setThemePresets(presetsRes.data.presets || []);
      setPreferences(prefsRes.data);
      setAvailableWidgets(widgetsRes.data.widgets || []);
      setLayoutName(layoutRes.data?.name || 'Custom Layout');
    } catch (error) {
      console.error('Error loading dashboard settings:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSaveLayout = async () => {
    const loadingToast = toast.loading('Saving layout...');
    try {
      await api.post('/dashboard/layout', {
        name: layoutName,
        widgets: layout?.widgets || [],
        columns: layout?.columns || 12,
        row_height: layout?.row_height || 100
      });
      toast.dismiss(loadingToast);
      toast.success('Layout saved!');
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save layout');
    }
  };

  const handleSaveTheme = async () => {
    const loadingToast = toast.loading('Saving theme...');
    try {
      await api.post('/dashboard/theme', theme);
      toast.dismiss(loadingToast);
      toast.success('Theme saved!', {
        description: 'Refresh the page to see changes'
      });
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save theme');
    }
  };

  const handleApplyThemePreset = async (preset) => {
    setTheme({ ...theme, ...preset.config });
    toast.info(`Applied "${preset.name}" theme`);
  };

  const handleSavePreferences = async () => {
    const loadingToast = toast.loading('Saving preferences...');
    try {
      await api.post('/dashboard/preferences', preferences);
      toast.dismiss(loadingToast);
      toast.success('Preferences saved!');
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save preferences');
    }
  };

  const handleToggleWidget = (widgetId) => {
    if (!layout?.widgets) return;
    
    const updatedWidgets = layout.widgets.map(w => 
      w.widget_id === widgetId ? { ...w, visible: !w.visible } : w
    );
    setLayout({ ...layout, widgets: updatedWidgets });
  };

  const handleAddWidget = async (widgetType) => {
    const widget = availableWidgets.find(w => w.type === widgetType);
    if (!widget) return;

    const newWidget = {
      widget_id: `${widgetType}_${Date.now()}`,
      type: widgetType,
      title: widget.name,
      position: { x: 0, y: 0, ...widget.default_size },
      settings: {},
      visible: true
    };

    const updatedWidgets = [...(layout?.widgets || []), newWidget];
    setLayout({ ...layout, widgets: updatedWidgets });
    toast.success(`Added ${widget.name} widget`);
  };

  const handleRemoveWidget = (widgetId) => {
    const updatedWidgets = (layout?.widgets || []).filter(w => w.widget_id !== widgetId);
    setLayout({ ...layout, widgets: updatedWidgets });
    toast.info('Widget removed');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Dashboard Settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="dashboard-customization-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Layout size={40} className="text-[#9D00FF]" />
            <span className="text-[#9D00FF]">Dashboard</span> Customization
          </h1>
          <p className="text-[#A1A1AA]">
            Personalize your trading dashboard layout and theme
          </p>
        </div>
        <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="layout" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Grid3X3 size={16} className="mr-2" />
            Layout
          </TabsTrigger>
          <TabsTrigger value="widgets" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Plus size={16} className="mr-2" />
            Widgets
          </TabsTrigger>
          <TabsTrigger value="theme" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Palette size={16} className="mr-2" />
            Theme
          </TabsTrigger>
          <TabsTrigger value="preferences" className="data-[state=active]:bg-[#9D00FF] data-[state=active]:text-white">
            <Settings2 size={16} className="mr-2" />
            Preferences
          </TabsTrigger>
        </TabsList>

        {/* Layout Tab */}
        <TabsContent value="layout" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Dashboard Layout</CardTitle>
              <CardDescription>Manage your widgets and their positions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-center">
                <div className="flex-1">
                  <Label className="text-[#A1A1AA]">Layout Name</Label>
                  <Input
                    value={layoutName}
                    onChange={(e) => setLayoutName(e.target.value)}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                    placeholder="My Custom Layout"
                  />
                </div>
                <Button onClick={handleSaveLayout} className="bg-[#00FF94] text-black mt-6">
                  <Save size={16} className="mr-2" />
                  Save Layout
                </Button>
              </div>

              {/* Widget List */}
              <div className="space-y-2 mt-4">
                <Label className="text-[#A1A1AA]">Active Widgets ({layout?.widgets?.length || 0})</Label>
                <div className="grid gap-2">
                  {layout?.widgets?.map((widget) => (
                    <div
                      key={widget.widget_id}
                      className="flex items-center justify-between p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                    >
                      <div className="flex items-center gap-3">
                        <Move size={16} className="text-[#666] cursor-grab" />
                        <div>
                          <span className="font-medium text-white">{widget.title}</span>
                          <span className="text-xs text-[#666] ml-2">({widget.type})</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleWidget(widget.widget_id)}
                          className={widget.visible ? 'text-[#00FF94]' : 'text-[#666]'}
                        >
                          {widget.visible ? <Eye size={16} /> : <EyeOff size={16} />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveWidget(widget.widget_id)}
                          className="text-[#FF0055] hover:bg-[#FF0055]/10"
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Saved Layouts */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Saved Layouts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {layouts.map((savedLayout) => (
                  <div
                    key={savedLayout.layout_id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      savedLayout.is_active 
                        ? 'border-[#00FF94] bg-[#00FF94]/10' 
                        : 'border-[#1F1F1F] hover:border-[#9D00FF]/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-white">{savedLayout.name}</span>
                      {savedLayout.is_active && <Check size={16} className="text-[#00FF94]" />}
                    </div>
                    <span className="text-xs text-[#666]">
                      {savedLayout.is_default ? 'Default' : `${savedLayout.widgets?.length || 0} widgets`}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Widgets Tab */}
        <TabsContent value="widgets" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Available Widgets</CardTitle>
              <CardDescription>Add widgets to your dashboard</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {availableWidgets.map((widget) => (
                  <motion.div
                    key={widget.type}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Card className="bg-[#121212] border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-white">{widget.name}</h3>
                          <Badge variant="outline" className="border-[#1F1F1F] text-xs">
                            {widget.default_size?.w}x{widget.default_size?.h}
                          </Badge>
                        </div>
                        <p className="text-sm text-[#A1A1AA] mb-4">{widget.description}</p>
                        <Button
                          onClick={() => handleAddWidget(widget.type)}
                          className="w-full bg-[#9D00FF] hover:bg-[#9D00FF]/80"
                          size="sm"
                        >
                          <Plus size={14} className="mr-1" />
                          Add Widget
                        </Button>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Theme Tab */}
        <TabsContent value="theme" className="space-y-4">
          {/* Theme Presets */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Theme Presets</CardTitle>
              <CardDescription>Choose a preset theme or customize your own</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {themePresets.map((preset) => (
                  <motion.div
                    key={preset.name}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                  >
                    <Card 
                      className="bg-[#121212] border-[#1F1F1F] hover:border-[#9D00FF]/50 transition-colors cursor-pointer"
                      onClick={() => handleApplyThemePreset(preset)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          {preset.config.mode === 'light' ? (
                            <Sun size={18} className="text-[#FFB800]" />
                          ) : preset.config.mode === 'dark' ? (
                            <Moon size={18} className="text-[#9D00FF]" />
                          ) : (
                            <Monitor size={18} className="text-[#007AFF]" />
                          )}
                          <h3 className="font-bold text-white">{preset.name}</h3>
                        </div>
                        <p className="text-sm text-[#A1A1AA] mb-3">{preset.description}</p>
                        <div className="flex gap-1">
                          <div 
                            className="w-6 h-6 rounded-full border border-[#333]" 
                            style={{ backgroundColor: preset.config.accent_color }}
                          />
                          <div 
                            className="w-6 h-6 rounded-full border border-[#333]" 
                            style={{ backgroundColor: preset.config.secondary_color }}
                          />
                          <div 
                            className="w-6 h-6 rounded-full border border-[#333]" 
                            style={{ backgroundColor: preset.config.danger_color }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Custom Theme */}
          {theme && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Custom Theme Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-[#A1A1AA]">Mode</Label>
                    <Select value={theme.mode} onValueChange={(v) => setTheme({ ...theme, mode: v })}>
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Accent Color</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        type="color"
                        value={theme.accent_color}
                        onChange={(e) => setTheme({ ...theme, accent_color: e.target.value })}
                        className="w-12 h-10 p-1 bg-[#121212] border-[#1F1F1F]"
                      />
                      <Input
                        value={theme.accent_color}
                        onChange={(e) => setTheme({ ...theme, accent_color: e.target.value })}
                        className="flex-1 bg-[#121212] border-[#1F1F1F] font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Secondary Color</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        type="color"
                        value={theme.secondary_color}
                        onChange={(e) => setTheme({ ...theme, secondary_color: e.target.value })}
                        className="w-12 h-10 p-1 bg-[#121212] border-[#1F1F1F]"
                      />
                      <Input
                        value={theme.secondary_color}
                        onChange={(e) => setTheme({ ...theme, secondary_color: e.target.value })}
                        className="flex-1 bg-[#121212] border-[#1F1F1F] font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Danger Color</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        type="color"
                        value={theme.danger_color}
                        onChange={(e) => setTheme({ ...theme, danger_color: e.target.value })}
                        className="w-12 h-10 p-1 bg-[#121212] border-[#1F1F1F]"
                      />
                      <Input
                        value={theme.danger_color}
                        onChange={(e) => setTheme({ ...theme, danger_color: e.target.value })}
                        className="flex-1 bg-[#121212] border-[#1F1F1F] font-mono"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={theme.background_blur}
                      onCheckedChange={(v) => setTheme({ ...theme, background_blur: v })}
                    />
                    <Label className="text-white">Background Blur</Label>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={theme.animations_enabled}
                      onCheckedChange={(v) => setTheme({ ...theme, animations_enabled: v })}
                    />
                    <Label className="text-white">Animations</Label>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={theme.compact_mode}
                      onCheckedChange={(v) => setTheme({ ...theme, compact_mode: v })}
                    />
                    <Label className="text-white">Compact Mode</Label>
                  </div>
                </div>

                <Button onClick={handleSaveTheme} className="bg-[#00FF94] text-black">
                  <Save size={16} className="mr-2" />
                  Save Theme
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-4">
          {preferences && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle>Dashboard Preferences</CardTitle>
                <CardDescription>General settings and behavior</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-[#A1A1AA]">Default Page</Label>
                    <Select 
                      value={preferences.default_page} 
                      onValueChange={(v) => setPreferences({ ...preferences, default_page: v })}
                    >
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="/">Command Center</SelectItem>
                        <SelectItem value="/ai-center">AI Center</SelectItem>
                        <SelectItem value="/portfolio-dashboard">Portfolio</SelectItem>
                        <SelectItem value="/spot-trading">Spot Trading</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Currency</Label>
                    <Select 
                      value={preferences.currency} 
                      onValueChange={(v) => setPreferences({ ...preferences, currency: v })}
                    >
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="USD">USD ($)</SelectItem>
                        <SelectItem value="EUR">EUR (€)</SelectItem>
                        <SelectItem value="GBP">GBP (£)</SelectItem>
                        <SelectItem value="BTC">BTC (₿)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Auto Refresh Interval (seconds)</Label>
                    <Input
                      type="number"
                      value={preferences.refresh_interval}
                      onChange={(e) => setPreferences({ ...preferences, refresh_interval: parseInt(e.target.value) || 30 })}
                      className="bg-[#121212] border-[#1F1F1F] mt-1"
                      min={10}
                      max={300}
                    />
                  </div>

                  <div>
                    <Label className="text-[#A1A1AA]">Notifications Position</Label>
                    <Select 
                      value={preferences.notifications_position} 
                      onValueChange={(v) => setPreferences({ ...preferences, notifications_position: v })}
                    >
                      <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                        <SelectItem value="top-center">Top Center</SelectItem>
                        <SelectItem value="top-right">Top Right</SelectItem>
                        <SelectItem value="bottom-center">Bottom Center</SelectItem>
                        <SelectItem value="bottom-right">Bottom Right</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={preferences.auto_refresh}
                      onCheckedChange={(v) => setPreferences({ ...preferences, auto_refresh: v })}
                    />
                    <Label className="text-white">Auto Refresh Data</Label>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={preferences.sidebar_collapsed}
                      onCheckedChange={(v) => setPreferences({ ...preferences, sidebar_collapsed: v })}
                    />
                    <Label className="text-white">Sidebar Collapsed by Default</Label>
                  </div>
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={preferences.show_portfolio_value}
                      onCheckedChange={(v) => setPreferences({ ...preferences, show_portfolio_value: v })}
                    />
                    <Label className="text-white">Show Portfolio Value</Label>
                  </div>
                </div>

                <Button onClick={handleSavePreferences} className="bg-[#00FF94] text-black">
                  <Save size={16} className="mr-2" />
                  Save Preferences
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DashboardCustomization;
