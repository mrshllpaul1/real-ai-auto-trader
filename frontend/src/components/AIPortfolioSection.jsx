import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Brain, Wallet, TrendingUp, RefreshCw, Play, Square, DollarSign, PieChart, Plus, Minus } from 'lucide-react';
import api, { tradingAPI } from '../services/api';
import { toast } from 'sonner';

const AIPortfolioSection = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [krakenPortfolio, setKrakenPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialCapital, setInitialCapital] = useState(500);
  const [isAutonomousRunning, setIsAutonomousRunning] = useState(false);

  useEffect(() => {
    loadPortfolio();
    loadKrakenPortfolio();
  }, []);

  const loadKrakenPortfolio = async () => {
    try {
      const response = await tradingAPI.getKrakenPortfolio();
      setKrakenPortfolio(response.data);
    } catch (error) {
      console.error('Error loading Kraken portfolio:', error);
    }
  };

  const loadPortfolio = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'default';
      const response = await api.get(`/ai-portfolio/status/${userId}`);
      setPortfolio(response.data);
    } catch (error) {
      console.error('Error loading AI portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializePortfolio = async () => {
    try {
      setLoading(true);
      const userId = localStorage.getItem('user_id') || 'default';
      const response = await api.post('/ai-portfolio/initialize', {
        user_id: userId,
        initial_capital: initialCapital
      });
      toast.success(`AI Portfolio initialized with $${initialCapital}!`);
      await loadPortfolio();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      console.error('Initialize error:', errorMsg);
      toast.error(`Failed to initialize AI portfolio: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const developStrategy = async () => {
    try {
      toast.loading('AI analyzing markets...');
      const userId = localStorage.getItem('user_id') || 'default';
      await api.post('/ai-portfolio/develop-strategy', { user_id: userId });
      toast.dismiss();
      toast.success('AI developed new strategy!');
      await loadPortfolio();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to develop strategy');
    }
  };

  const executeRebalance = async () => {
    try {
      toast.loading('AI executing trades...');
      const userId = localStorage.getItem('user_id') || 'default';
      const response = await api.post('/ai-portfolio/rebalance', { user_id: userId });
      toast.dismiss();
      toast.success(`${response.data.trades_executed} trades executed!`);
      await loadPortfolio();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to rebalance');
    }
  };

  const startAutonomous = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'default';
      await api.post('/ai-portfolio/start-autonomous', { user_id: userId });
      setIsAutonomousRunning(true);
      toast.success('AI Autonomous Trading started!');
    } catch (error) {
      toast.error('Failed to start');
    }
  };

  const stopAutonomous = async () => {
    try {
      await api.post('/ai-portfolio/stop-autonomous');
      setIsAutonomousRunning(false);
      toast.success('AI stopped');
    } catch (error) {
      toast.error('Failed to stop');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-[#9D00FF]" />
      </div>
    );
  }

  // Not initialized - show setup
  if (!portfolio?.initialized) {
    const presetAmounts = [100, 250, 500, 1000, 2500, 5000, 10000];
    
    const handleAmountChange = (value) => {
      const numValue = parseFloat(value.replace(/[^0-9.]/g, '')) || 0;
      setInitialCapital(Math.max(0, numValue));
    };
    
    const incrementAmount = (delta) => {
      setInitialCapital(prev => Math.max(100, prev + delta));
    };
    
    return (
      <div className="space-y-4">
        <div className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/30">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="text-[#9D00FF]" size={20} />
            <span className="font-bold text-white">Initialize AI Portfolio</span>
          </div>
          <p className="text-sm text-[#A1A1AA] mb-4">
            Allocate funds for AI to manage autonomously with real Kraken trades.
          </p>
          
          {/* Amount Input Section */}
          <div className="space-y-4">
            <Label className="text-sm text-[#A1A1AA]">Investment Amount (USD)</Label>
            
            {/* Main Input with +/- Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => incrementAmount(-100)}
                className="h-10 w-10 bg-[#0A0A0A] border-[#1F1F1F] hover:bg-[#1F1F1F] text-white"
                data-testid="decrease-amount-btn"
              >
                <Minus size={16} />
              </Button>
              
              <div className="relative flex-1">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" size={18} />
                <Input
                  type="text"
                  value={initialCapital.toLocaleString()}
                  onChange={(e) => handleAmountChange(e.target.value)}
                  className="bg-[#0A0A0A] border-[#1F1F1F] text-white text-xl font-bold pl-10 pr-4 h-12 text-center"
                  placeholder="Enter amount"
                  data-testid="initial-capital-input"
                />
              </div>
              
              <Button
                variant="outline"
                size="icon"
                onClick={() => incrementAmount(100)}
                className="h-10 w-10 bg-[#0A0A0A] border-[#1F1F1F] hover:bg-[#1F1F1F] text-white"
                data-testid="increase-amount-btn"
              >
                <Plus size={16} />
              </Button>
            </div>
            
            {/* Preset Amount Buttons */}
            <div className="flex flex-wrap gap-2">
              {presetAmounts.map((amount) => (
                <Button
                  key={amount}
                  variant="outline"
                  size="sm"
                  onClick={() => setInitialCapital(amount)}
                  className={`${
                    initialCapital === amount 
                      ? 'bg-[#9D00FF] border-[#9D00FF] text-white' 
                      : 'bg-[#0A0A0A] border-[#1F1F1F] text-[#A1A1AA] hover:text-white hover:border-[#9D00FF]'
                  }`}
                  data-testid={`preset-${amount}-btn`}
                >
                  ${amount.toLocaleString()}
                </Button>
              ))}
            </div>
            
            {/* Slider for fine-tuning */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-[#A1A1AA]">
                <span>$100</span>
                <span>$10,000+</span>
              </div>
              <Slider
                value={[Math.min(initialCapital, 10000)]}
                onValueChange={([val]) => setInitialCapital(val)}
                min={100}
                max={10000}
                step={100}
                className="w-full"
                data-testid="amount-slider"
              />
            </div>
            
            {/* Custom Amount Input for values > 10000 */}
            {initialCapital > 10000 && (
              <p className="text-xs text-[#9D00FF]">
                Custom amount: ${initialCapital.toLocaleString()} (use input above for large amounts)
              </p>
            )}
            
            {/* Initialize Button */}
            <Button 
              onClick={initializePortfolio}
              className="w-full bg-[#9D00FF] hover:bg-[#7D00CC] text-white h-12 text-lg font-bold"
              disabled={initialCapital < 100}
              data-testid="init-ai-btn"
            >
              <Wallet className="mr-2" size={20} />
              Initialize Portfolio with ${initialCapital.toLocaleString()}
            </Button>
            
            {initialCapital < 100 && (
              <p className="text-xs text-[#FF0055] text-center">Minimum investment: $100</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Portfolio initialized - show status
  const pnlColor = portfolio.profit_loss >= 0 ? '#00FF94' : '#FF0055';
  
  return (
    <div className="space-y-4">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
          <div className="text-xs text-[#A1A1AA]">Initial</div>
          <div className="text-lg font-bold text-white">${portfolio.initial_capital?.toLocaleString()}</div>
        </div>
        <div className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
          <div className="text-xs text-[#A1A1AA]">Current</div>
          <div className="text-lg font-bold text-white">${portfolio.current_value?.toLocaleString()}</div>
        </div>
        <div className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
          <div className="text-xs text-[#A1A1AA]">P/L</div>
          <div className="text-lg font-bold" style={{ color: pnlColor }}>
            {portfolio.profit_loss >= 0 ? '+' : ''}${portfolio.profit_loss?.toFixed(2)}
          </div>
        </div>
        <div className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
          <div className="text-xs text-[#A1A1AA]">Status</div>
          <Badge className={isAutonomousRunning ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#9D00FF]/20 text-[#9D00FF]'}>
            {isAutonomousRunning ? 'AUTO' : 'MANUAL'}
          </Badge>
        </div>
      </div>

      {/* Holdings */}
      <div className="p-3 bg-[#121212] rounded-lg border border-[#1F1F1F]">
        <div className="text-xs font-bold text-white mb-2">Holdings</div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(portfolio.holdings || {}).map(([asset, details]) => (
            <Badge key={asset} className="bg-[#1F1F1F] text-white">
              {asset}: ${typeof details === 'object' ? details.value?.toFixed(0) : details?.toFixed(0)}
            </Badge>
          ))}
        </div>
      </div>

      {/* Kraken Real Holdings */}
      {krakenPortfolio?.holdings?.length > 0 && (
        <div className="p-3 bg-[#121212] rounded-lg border border-[#00FF94]/30">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Wallet className="text-[#00FF94]" size={16} />
              <span className="text-xs font-bold text-[#00FF94]">Kraken Portfolio (Real)</span>
            </div>
            <span className="text-sm font-bold text-[#00FF94]">${krakenPortfolio.total_value_usd?.toLocaleString()}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {krakenPortfolio.holdings.map(h => (
              <div key={h.asset} className="px-2 py-1 bg-[#0A0A0A] rounded border border-[#1F1F1F]">
                <span className="text-white font-bold text-xs">{h.symbol}</span>
                <span className="text-[#A1A1AA] text-xs ml-1">${h.value_usd?.toFixed(0)}</span>
                <span className={`text-xs ml-1 ${h.price_change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                  ({h.price_change_24h >= 0 ? '+' : ''}{h.price_change_24h?.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Target Allocation */}
      {portfolio.target_allocation && (
        <div className="p-3 bg-[#121212] rounded-lg border border-[#9D00FF]/30">
          <div className="text-xs font-bold text-[#9D00FF] mb-2">AI Target</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(portfolio.target_allocation).map(([asset, pct]) => (
              <span key={asset} className="text-xs text-[#A1A1AA]">{asset}:{pct?.toFixed(0)}%</span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        <Button onClick={developStrategy} size="sm" className="bg-[#007AFF] text-white" data-testid="develop-btn">
          <Brain className="mr-1" size={14} /> Strategy
        </Button>
        <Button onClick={executeRebalance} size="sm" className="bg-[#00FF94] text-black font-bold" data-testid="rebalance-btn">
          <RefreshCw className="mr-1" size={14} /> Rebalance
        </Button>
        {isAutonomousRunning ? (
          <Button onClick={stopAutonomous} size="sm" className="bg-[#FF0055] text-white" data-testid="stop-btn">
            <Square className="mr-1" size={14} /> Stop
          </Button>
        ) : (
          <Button onClick={startAutonomous} size="sm" className="bg-[#9D00FF] text-white" data-testid="start-btn">
            <Play className="mr-1" size={14} /> Auto 24/7
          </Button>
        )}
      </div>
    </div>
  );
};

export default AIPortfolioSection;
