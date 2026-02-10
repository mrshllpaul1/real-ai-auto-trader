/**
 * TradingPairSelector - Reusable dropdown component for selecting Kraken trading pairs
 * Use this component throughout the app for consistent trading pair selection
 */
import React, { useState, useMemo } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Search, Loader2 } from 'lucide-react';
import useTradingPairs from '../hooks/useTradingPairs';

const TradingPairSelector = ({ 
  value, 
  onValueChange, 
  placeholder = "Select trading pair",
  className = "",
  showSearch = true,
  maxHeight = "300px"
}) => {
  const { pairs, loading, totalCount } = useTradingPairs();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter pairs based on search
  const filteredPairs = useMemo(() => {
    if (!searchQuery) return pairs;
    const q = searchQuery.toUpperCase();
    return pairs.filter(p => 
      p.symbol.includes(q) || 
      (p.display && p.display.toUpperCase().includes(q))
    );
  }, [pairs, searchQuery]);

  // Group pairs by first letter for easier navigation
  const groupedPairs = useMemo(() => {
    const groups = {};
    filteredPairs.forEach(p => {
      const letter = p.symbol[0].toUpperCase();
      if (!groups[letter]) groups[letter] = [];
      groups[letter].push(p);
    });
    return groups;
  }, [filteredPairs]);

  if (loading) {
    return (
      <div className={`flex items-center gap-2 px-3 py-2 bg-[#121212] border border-[#1F1F1F] rounded-md ${className}`}>
        <Loader2 className="w-4 h-4 animate-spin text-[#A1A1AA]" />
        <span className="text-[#A1A1AA] text-sm">Loading pairs...</span>
      </div>
    );
  }

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className={`bg-[#121212] border-[#1F1F1F] ${className}`}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent 
        className="bg-[#121212] border-[#1F1F1F]"
        style={{ maxHeight }}
      >
        {showSearch && (
          <div className="sticky top-0 bg-[#121212] p-2 border-b border-[#1F1F1F]">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A1A1AA]" />
              <Input
                placeholder={`Search ${totalCount} pairs...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 bg-[#0A0A0A] border-[#1F1F1F] text-sm h-8"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>
        )}
        
        <div className="overflow-y-auto" style={{ maxHeight: showSearch ? `calc(${maxHeight} - 60px)` : maxHeight }}>
          {Object.keys(groupedPairs).sort().map(letter => (
            <div key={letter}>
              <div className="px-2 py-1 text-xs font-bold text-[#9D00FF] bg-[#0A0A0A] sticky top-0">
                {letter}
              </div>
              {groupedPairs[letter].map(pair => (
                <SelectItem 
                  key={pair.symbol} 
                  value={`${pair.symbol}/USD`}
                  className="cursor-pointer"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-medium">{pair.symbol}/USD</span>
                  </div>
                </SelectItem>
              ))}
            </div>
          ))}
          
          {filteredPairs.length === 0 && (
            <div className="p-4 text-center text-[#A1A1AA]">
              No pairs found matching "{searchQuery}"
            </div>
          )}
        </div>
        
        <div className="sticky bottom-0 bg-[#0A0A0A] border-t border-[#1F1F1F] px-2 py-1 text-xs text-[#A1A1AA]">
          {filteredPairs.length} of {totalCount} pairs
        </div>
      </SelectContent>
    </Select>
  );
};

export default TradingPairSelector;
