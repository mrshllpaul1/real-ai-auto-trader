import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Brain, Wallet, TrendingUp, RefreshCw, Play, Square, DollarSign, PieChart } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

const AIPortfolioSection = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialCapital, setInitialCapital] = useState(500);
  const [isAutonomousRunning, setIsAutonomousRunning] = useState(false);

  useEffect(() => {
    loadPortfolio();
  }, []);

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
      await api.post('/ai-portfolio/initialize', {
        user_id: userId,
        initial_capital: initialCapital
      });
      toast.success(`AI Portfolio initialized with $${initialCapital}!`);
      await loadPortfolio();
    } catch (error) {
      toast.error('Failed to initialize AI portfolio');
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
          <div className="flex gap-3">
            <Input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="bg-[#0A0A0A] border-[#1F1F1F] text-white w-32"
              min={100}
              data-testid="initial-capital-input"
            />
            <Button 
              onClick={initializePortfolio}
              className="bg-[#9D00FF] hover:bg-[#7D00CC] text-white"
              data-testid="init-ai-btn"
            >
              <Wallet className="mr-2" size={16} />
              Initialize ${initialCapital}
            </Button>
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
