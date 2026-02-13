import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import api from '../services/api';
import toast from '../utils/toast';
import { 
  Share2, Image, Link2, Eye, Trash2, Copy, Download,
  TrendingUp, TrendingDown, PieChart, Lock, Unlock,
  RefreshCcw, Calendar, Award, CheckCircle
} from 'lucide-react';

const PortfolioShare = ({ embedded = false }) => {
  const [shareConfig, setShareConfig] = useState({
    show_holdings: true,
    show_pnl: true,
    show_allocation: true,
    show_total_value: false,
    theme: 'dark',
    include_watermark: true
  });
  const [myShares, setMyShares] = useState([]);
  const [generatedShare, setGeneratedShare] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadMyShares();
  }, []);

  const loadMyShares = async () => {
    try {
      const response = await api.get('/portfolio-share/my-shares');
      setMyShares(response.data.shares || []);
    } catch (error) {
      console.error('Error loading shares:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateShare = async () => {
    setGenerating(true);
    try {
      const response = await api.post('/portfolio-share/generate', shareConfig);
      setGeneratedShare(response.data);
      toast.success('Portfolio share generated', {
        description: `Share ID: ${response.data.share_id}`
      });
      loadMyShares();
    } catch (error) {
      toast.error('Failed to generate share');
    } finally {
      setGenerating(false);
    }
  };

  const generateTradeCard = async () => {
    // This would typically be called with a specific trade ID
    toast.info('Select a trade to share', {
      description: 'Go to your trade history and click share on a specific trade'
    });
  };

  const generatePerformanceCard = async (period) => {
    setGenerating(true);
    try {
      const response = await api.post(`/portfolio-share/performance-card?period=${period}`);
      setGeneratedShare(response.data);
      toast.success(`${period} performance card generated`);
    } catch (error) {
      toast.error('Failed to generate performance card');
    } finally {
      setGenerating(false);
    }
  };

  const copyShareLink = (shareId) => {
    const link = `${window.location.origin}/shared/${shareId}`;
    navigator.clipboard.writeText(link);
    toast.success('Link copied to clipboard');
  };

  const deleteShare = async (shareId) => {
    try {
      await api.delete(`/portfolio-share/${shareId}`);
      toast.success('Share deleted');
      loadMyShares();
      if (generatedShare?.share_id === shareId) {
        setGeneratedShare(null);
      }
    } catch (error) {
      toast.error('Failed to delete share');
    }
  };

  const viewShare = async (shareId) => {
    try {
      const response = await api.get(`/portfolio-share/view/${shareId}`);
      setGeneratedShare(response.data);
    } catch (error) {
      toast.error('Failed to load share');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
      </div>
    );
  }

  return (
    <div className={embedded ? '' : 'min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6'}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-5xl mx-auto space-y-6"
      >
        {!embedded && (
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Portfolio Sharing</h1>
              <p className="text-slate-400">Create shareable portfolio cards and performance snapshots</p>
            </div>
            <Badge variant="outline" className="text-cyan-400 border-cyan-400/50">
              <Share2 className="w-3 h-3 mr-1" />
              Share
            </Badge>
          </div>
        )}

        <Tabs defaultValue="create" className="space-y-6">
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="create">Create Share</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="history">My Shares</TabsTrigger>
          </TabsList>

          {/* Create Tab */}
          <TabsContent value="create" className="space-y-6">
            {/* Share Types */}
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="bg-slate-800/50 border-slate-700 hover:border-cyan-500/50 transition-colors cursor-pointer"
                    onClick={generateShare}>
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center mx-auto mb-4">
                    <PieChart className="w-6 h-6 text-cyan-400" />
                  </div>
                  <h3 className="font-medium text-white mb-2">Portfolio Snapshot</h3>
                  <p className="text-sm text-slate-400">Share your current holdings and allocation</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 hover:border-green-500/50 transition-colors cursor-pointer"
                    onClick={() => generatePerformanceCard('30d')}>
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                    <TrendingUp className="w-6 h-6 text-green-400" />
                  </div>
                  <h3 className="font-medium text-white mb-2">Performance Card</h3>
                  <p className="text-sm text-slate-400">Share your trading performance stats</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 hover:border-purple-500/50 transition-colors cursor-pointer"
                    onClick={generateTradeCard}>
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center mx-auto mb-4">
                    <Award className="w-6 h-6 text-purple-400" />
                  </div>
                  <h3 className="font-medium text-white mb-2">Trade Card</h3>
                  <p className="text-sm text-slate-400">Share a specific winning trade</p>
                </CardContent>
              </Card>
            </div>

            {/* Portfolio Share Options */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Portfolio Share Options</CardTitle>
                <CardDescription>Customize what to include in your share</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div className="flex items-center gap-3">
                      <PieChart className="w-5 h-5 text-cyan-400" />
                      <Label className="text-white">Show Holdings</Label>
                    </div>
                    <Switch
                      checked={shareConfig.show_holdings}
                      onCheckedChange={(checked) => setShareConfig(prev => ({ ...prev, show_holdings: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div className="flex items-center gap-3">
                      <TrendingUp className="w-5 h-5 text-green-400" />
                      <Label className="text-white">Show P&L</Label>
                    </div>
                    <Switch
                      checked={shareConfig.show_pnl}
                      onCheckedChange={(checked) => setShareConfig(prev => ({ ...prev, show_pnl: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div className="flex items-center gap-3">
                      <PieChart className="w-5 h-5 text-purple-400" />
                      <Label className="text-white">Show Allocation</Label>
                    </div>
                    <Switch
                      checked={shareConfig.show_allocation}
                      onCheckedChange={(checked) => setShareConfig(prev => ({ ...prev, show_allocation: checked }))}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div className="flex items-center gap-3">
                      {shareConfig.show_total_value ? (
                        <Unlock className="w-5 h-5 text-amber-400" />
                      ) : (
                        <Lock className="w-5 h-5 text-slate-400" />
                      )}
                      <div>
                        <Label className="text-white">Show Total Value</Label>
                        <p className="text-xs text-slate-500">Privacy setting</p>
                      </div>
                    </div>
                    <Switch
                      checked={shareConfig.show_total_value}
                      onCheckedChange={(checked) => setShareConfig(prev => ({ ...prev, show_total_value: checked }))}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4 pt-4">
                  <div className="flex-1">
                    <Label className="text-slate-400 text-sm">Theme</Label>
                    <Select
                      value={shareConfig.theme}
                      onValueChange={(value) => setShareConfig(prev => ({ ...prev, theme: value }))}
                    >
                      <SelectTrigger className="bg-slate-900 border-slate-600 mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="gradient">Gradient</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-3 pt-6">
                    <Label className="text-white">Include Watermark</Label>
                    <Switch
                      checked={shareConfig.include_watermark}
                      onCheckedChange={(checked) => setShareConfig(prev => ({ ...prev, include_watermark: checked }))}
                    />
                  </div>
                </div>

                <Button onClick={generateShare} className="w-full mt-4" disabled={generating}>
                  {generating ? (
                    <RefreshCcw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Image className="w-4 h-4 mr-2" />
                  )}
                  Generate Portfolio Share
                </Button>
              </CardContent>
            </Card>

            {/* Performance Period Options */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Performance Cards</CardTitle>
                <CardDescription>Generate performance snapshots for different periods</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-3">
                  {['7d', '30d', '90d', 'all'].map((period) => (
                    <Button
                      key={period}
                      variant="outline"
                      onClick={() => generatePerformanceCard(period)}
                      disabled={generating}
                      className="flex flex-col py-4 h-auto"
                    >
                      <Calendar className="w-5 h-5 mb-1" />
                      <span className="text-xs">
                        {period === 'all' ? 'All Time' : period.replace('d', ' Days')}
                      </span>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Share Preview</CardTitle>
                <CardDescription>
                  {generatedShare ? `Share ID: ${generatedShare.share_id || generatedShare.card_id}` : 'Generate a share to see preview'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {generatedShare ? (
                  <div className="space-y-6">
                    {/* Share Card Preview */}
                    <div className={`p-6 rounded-xl ${
                      shareConfig.theme === 'dark' ? 'bg-gradient-to-br from-slate-900 to-slate-800' :
                      shareConfig.theme === 'light' ? 'bg-gradient-to-br from-white to-gray-100' :
                      'bg-gradient-to-br from-cyan-900 via-purple-900 to-pink-900'
                    } border border-slate-600`}>
                      {/* Header */}
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <h3 className={`text-lg font-bold ${shareConfig.theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                            {generatedShare.type === 'performance' ? 'Performance Snapshot' : 'Portfolio Snapshot'}
                          </h3>
                          <p className={`text-sm ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>
                            {new Date(generatedShare.generated_at).toLocaleDateString()}
                          </p>
                        </div>
                        {shareConfig.include_watermark && (
                          <Badge className="bg-cyan-500/20 text-cyan-400">Tethys</Badge>
                        )}
                      </div>

                      {/* Content based on type */}
                      {generatedShare.type === 'performance' ? (
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-3 rounded-lg bg-black/20">
                            <p className={`text-xs ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>Total Trades</p>
                            <p className={`text-xl font-bold ${shareConfig.theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                              {generatedShare.stats?.total_trades || 0}
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-black/20">
                            <p className={`text-xs ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>Win Rate</p>
                            <p className={`text-xl font-bold ${shareConfig.theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                              {generatedShare.stats?.win_rate || 0}%
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-black/20">
                            <p className={`text-xs ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>Total P&L</p>
                            <p className={`text-xl font-bold ${(generatedShare.stats?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              ${(generatedShare?.stats?.total_pnl ?? 0).toFixed(2) || '0'}
                            </p>
                          </div>
                          <div className="p-3 rounded-lg bg-black/20">
                            <p className={`text-xs ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>Best Trade</p>
                            <p className="text-xl font-bold text-green-400">
                              ${(generatedShare?.stats?.best_trade ?? 0).toFixed(2) || '0'}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {/* Total Value */}
                          {(shareConfig.show_total_value || generatedShare.data?.total_value_masked) && (
                            <div className="text-center p-4 rounded-lg bg-black/20">
                              <p className={`text-sm ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>
                                Portfolio Value
                              </p>
                              <p className={`text-3xl font-bold ${shareConfig.theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                                {generatedShare.data?.total_value_masked || `$${(generatedShare?.data?.total_value ?? 0).toLocaleString()}`}
                              </p>
                            </div>
                          )}

                          {/* Top Holdings */}
                          {shareConfig.show_holdings && generatedShare.data?.top_holdings?.length > 0 && (
                            <div>
                              <p className={`text-sm mb-2 ${shareConfig.theme === 'light' ? 'text-gray-500' : 'text-slate-400'}`}>
                                Top Holdings
                              </p>
                              <div className="space-y-2">
                                {generatedShare.data.top_holdings.map((holding, i) => (
                                  <div key={i} className="flex items-center justify-between p-2 rounded bg-black/20">
                                    <span className={shareConfig.theme === 'light' ? 'text-gray-900' : 'text-white'}>
                                      {holding.asset}
                                    </span>
                                    <span className={`${(holding.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                      {holding.percentage}%
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                      <Button onClick={() => copyShareLink(generatedShare.share_id || generatedShare.card_id)} className="flex-1">
                        <Copy className="w-4 h-4 mr-2" />
                        Copy Link
                      </Button>
                      <Button variant="outline" className="flex-1">
                        <Download className="w-4 h-4 mr-2" />
                        Download Image
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Share2 className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No share generated yet</p>
                    <p className="text-sm text-slate-500 mt-2">Create a share in the Create tab</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">My Shares</CardTitle>
                <CardDescription>Previously generated portfolio shares</CardDescription>
              </CardHeader>
              <CardContent>
                {myShares.length > 0 ? (
                  <div className="space-y-3">
                    {myShares.map((share) => (
                      <motion.div
                        key={share.share_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-between p-4 rounded-lg bg-slate-900/50"
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-cyan-500/20">
                            <Share2 className="w-5 h-5 text-cyan-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              Share #{share.share_id}
                            </p>
                            <p className="text-sm text-slate-400">
                              {new Date(share.created_at).toLocaleDateString()} • {share.views || 0} views
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" variant="ghost" onClick={() => viewShare(share.share_id)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => copyShareLink(share.share_id)}>
                            <Copy className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300" 
                                  onClick={() => deleteShare(share.share_id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Image className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No shares created yet</p>
                    <p className="text-sm text-slate-500 mt-2">Create your first portfolio share above</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default PortfolioShare;
