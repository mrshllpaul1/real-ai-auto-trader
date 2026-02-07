import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { 
  Search, Sparkles, TrendingUp, Check, X, Loader2, 
  ChevronDown, ChevronUp, Settings, Clock, Zap,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AIDiscoveryPanel = () => {
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  const [settings, setSettings] = useState({
    enabled: true,
    min_score: 70,
    max_daily_additions: 5,
    require_approval: false
  });

  const loadData = useCallback(async () => {
    try {
      const [statsRes, pendingRes, settingsRes] = await Promise.all([
        api.get('/ai-discovery/stats'),
        api.get('/ai-discovery/pending'),
        api.get('/ai-discovery/settings')
      ]);
      setStats(statsRes.data);
      setPending(pendingRes.data.pending || []);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Load discovery data error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const runScan = async () => {
    setScanning(true);
    try {
      const result = await api.post('/ai-discovery/scan');
      toast.success(`Discovery complete! Found ${result.data.candidates_found} candidates`);
      
      if (result.data.coins_added?.length > 0) {
        toast.success(`Added: ${result.data.coins_added.join(', ')}`);
      }
      
      loadData();
    } catch (error) {
      toast.error('Discovery scan failed');
    } finally {
      setScanning(false);
    }
  };

  const approveCoin = async (coinId) => {
    try {
      await api.post(`/ai-discovery/approve/${coinId}`);
      toast.success(`Approved ${coinId}!`);
      loadData();
    } catch (error) {
      toast.error('Failed to approve');
    }
  };

  const rejectCoin = async (coinId) => {
    try {
      await api.post(`/ai-discovery/reject/${coinId}`);
      toast.success(`Rejected ${coinId}`);
      loadData();
    } catch (error) {
      toast.error('Failed to reject');
    }
  };

  const saveSettings = async () => {
    try {
      await api.post('/ai-discovery/settings', settings);
      toast.success('Settings saved!');
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-[#00FF94]';
    if (score >= 70) return 'text-[#FFB800]';
    return 'text-[#A1A1AA]';
  };

  if (loading) {
    return (
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="animate-spin mr-2" />
          Loading discovery...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Search className="text-[#00FF94]" size={20} />
            AI Auto-Discovery
            {settings.enabled && (
              <Badge className="bg-[#00FF94]/20 text-[#00FF94] text-xs ml-2">Active</Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
              className="text-[#A1A1AA]"
            >
              <Settings size={16} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="text-[#A1A1AA]"
            >
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#00FF94]">{stats?.total_discoveries || 0}</div>
            <div className="text-xs text-[#71717A]">Discovered</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#9D00FF]">{stats?.approved || 0}</div>
            <div className="text-xs text-[#71717A]">Added</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-[#FFB800]">{stats?.pending || 0}</div>
            <div className="text-xs text-[#71717A]">Pending</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#1F1F1F]/50">
            <div className="text-2xl font-bold text-white">{stats?.daily_additions_remaining || 0}</div>
            <div className="text-xs text-[#71717A]">Today Left</div>
          </div>
        </div>

        {/* Scan Button */}
        <Button
          onClick={runScan}
          disabled={scanning || !settings.enabled}
          className="w-full bg-gradient-to-r from-[#00FF94] to-[#9D00FF] hover:opacity-90 text-black font-bold mb-4"
        >
          {scanning ? (
            <>
              <Loader2 className="animate-spin mr-2" size={16} />
              Scanning Trending Coins...
            </>
          ) : (
            <>
              <Zap className="mr-2" size={16} />
              Run Discovery Scan Now
            </>
          )}
        </Button>

        <AnimatePresence>
          {/* Settings Panel */}
          {showSettings && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 p-4 rounded-lg bg-[#1F1F1F]/50 border border-[#2F2F2F] space-y-4"
            >
              <h4 className="font-medium text-sm flex items-center gap-2">
                <Settings size={14} className="text-[#9D00FF]" />
                Discovery Settings
              </h4>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">Enable Auto-Discovery</div>
                  <div className="text-xs text-[#71717A]">Run daily scans for new coins</div>
                </div>
                <Switch
                  checked={settings.enabled}
                  onCheckedChange={(checked) => setSettings({...settings, enabled: checked})}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">Require Approval</div>
                  <div className="text-xs text-[#71717A]">Review coins before adding</div>
                </div>
                <Switch
                  checked={settings.require_approval}
                  onCheckedChange={(checked) => setSettings({...settings, require_approval: checked})}
                />
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm">Minimum Score</span>
                  <span className="text-sm font-bold text-[#00FF94]">{settings.min_score}</span>
                </div>
                <Slider
                  value={[settings.min_score]}
                  onValueChange={([value]) => setSettings({...settings, min_score: value})}
                  min={50}
                  max={95}
                  step={5}
                  className="accent-[#00FF94]"
                />
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm">Max Daily Additions</span>
                  <span className="text-sm font-bold text-[#9D00FF]">{settings.max_daily_additions}</span>
                </div>
                <Slider
                  value={[settings.max_daily_additions]}
                  onValueChange={([value]) => setSettings({...settings, max_daily_additions: value})}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>
              
              <Button
                onClick={saveSettings}
                className="w-full bg-[#9D00FF] hover:bg-[#7A00CC]"
                size="sm"
              >
                Save Settings
              </Button>
            </motion.div>
          )}

          {/* Expanded Details */}
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-4"
            >
              {/* Pending Approvals */}
              {pending.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <AlertCircle size={14} className="text-[#FFB800]" />
                    Pending Approval ({pending.length})
                  </h4>
                  <div className="space-y-2">
                    {pending.map((coin) => (
                      <div 
                        key={coin.coin_id}
                        className="flex items-center justify-between p-3 rounded-lg bg-[#1F1F1F]/50 border border-[#FFB800]/30"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#FFB800] to-[#FF6B00] flex items-center justify-center text-xs font-bold text-black">
                            {coin.symbol?.slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-sm flex items-center gap-2">
                              {coin.symbol}
                              <span className={`text-xs ${getScoreColor(coin.score)}`}>
                                {coin.score}%
                              </span>
                            </div>
                            <div className="text-xs text-[#71717A] max-w-[200px] truncate">
                              {coin.reason}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => approveCoin(coin.coin_id)}
                            className="text-[#00FF94] hover:bg-[#00FF94]/10 h-8 w-8 p-0"
                          >
                            <Check size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => rejectCoin(coin.coin_id)}
                            className="text-red-400 hover:bg-red-500/10 h-8 w-8 p-0"
                          >
                            <X size={16} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Runs */}
              {stats?.recent_runs?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Clock size={14} className="text-[#A1A1AA]" />
                    Recent Scans
                  </h4>
                  <div className="space-y-1">
                    {stats.recent_runs.slice(0, 3).map((run, i) => (
                      <div 
                        key={i}
                        className="flex items-center justify-between p-2 rounded bg-[#1F1F1F]/30 text-xs"
                      >
                        <span className="text-[#71717A]">
                          {new Date(run.timestamp).toLocaleString()}
                        </span>
                        <div className="flex items-center gap-3">
                          <span>Found: {run.candidates_found}</span>
                          <span className="text-[#00FF94]">Added: {run.coins_added?.length || 0}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Info Box */}
              <div className="bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg p-3">
                <h4 className="font-bold text-[#00FF94] text-sm mb-1">How AI Discovery Works</h4>
                <ul className="text-xs text-[#A1A1AA] space-y-1">
                  <li>• Scans trending coins on CoinGecko</li>
                  <li>• Analyzes volume, momentum & community</li>
                  <li>• Scores potential from 0-100</li>
                  <li>• Auto-adds coins above threshold (or queue for approval)</li>
                </ul>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
};

export default AIDiscoveryPanel;
