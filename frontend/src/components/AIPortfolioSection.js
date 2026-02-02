import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Brain, DollarSign } from 'lucide-react';

const AIPortfolioSection = () => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-[#121212] rounded-lg border border-[#9D00FF]/30">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="text-[#9D00FF]" size={20} />
            <span className="font-bold text-white">AI Status</span>
          </div>
          <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] border-[#9D00FF]/30">
            LEARNING
          </Badge>
        </div>
        
        <div className="p-4 bg-[#121212] rounded-lg border border-[#00FF94]/30">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="text-[#00FF94]" size={20} />
            <span className="font-bold text-white">Allocated Funds</span>
          </div>
          <div className="text-2xl font-bold text-[#00FF94]">$0.00</div>
        </div>
        
        <div className="p-4 bg-[#121212] rounded-lg border border-[#007AFF]/30">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="text-[#007AFF]" size={20} />
            <span className="font-bold text-white">Performance</span>
          </div>
          <div className="text-2xl font-bold text-[#007AFF]">+0.00%</div>
        </div>
      </div>
      
      <div className="bg-[#9D00FF]/10 border border-[#9D00FF]/30 rounded-lg p-4">
        <div className="text-sm text-[#9D00FF]">
          <p className="font-bold mb-2">AI Portfolio Manager Features:</p>
          <ul className="space-y-1 ml-4">
            <li>• Autonomous decision making based on market analysis</li>
            <li>• Dynamic portfolio rebalancing</li>
            <li>• Risk management with stop-loss protection</li>
            <li>• Machine learning from market patterns</li>
            <li>• Separate from manual trading strategies</li>
          </ul>
        </div>
      </div>
      
      <Button
        className="w-full bg-[#9D00FF] hover:bg-[#8000CC] text-white font-bold rounded-full"
        disabled
      >
        <Brain size={16} className="mr-2" />
        Configure AI Portfolio (Coming Soon)
      </Button>
    </div>
  );
};

export default AIPortfolioSection;