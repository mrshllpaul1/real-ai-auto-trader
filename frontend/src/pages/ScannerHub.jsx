import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Gem, Radar, Cpu, Users
} from 'lucide-react';

// Import existing page components
import GemScanner from './GemScanner';
import GemMLDLComparison from './GemMLDLComparison';
import CopyTrading from './CopyTrading';

const ScannerHub = () => {
  const [activeTab, setActiveTab] = useState('scanner');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">
              Scanner & Social
            </h1>
            <p className="text-slate-400 mt-1">
              Find gems and copy top traders
            </p>
          </div>
          <Badge variant="outline" className="text-pink-400 border-pink-400/50">
            <Gem className="w-3 h-3 mr-1" />
            Scanning
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="scanner" className="data-[state=active]:bg-pink-500/20">
              <Radar className="w-4 h-4 mr-2" />
              Gem Scanner
            </TabsTrigger>
            <TabsTrigger value="ml-dl" className="data-[state=active]:bg-purple-500/20">
              <Cpu className="w-4 h-4 mr-2" />
              ML vs DL
            </TabsTrigger>
            <TabsTrigger value="copy" className="data-[state=active]:bg-blue-500/20">
              <Users className="w-4 h-4 mr-2" />
              Copy Trading
            </TabsTrigger>
          </TabsList>

          <TabsContent value="scanner" className="mt-0">
            <GemScanner embedded={true} />
          </TabsContent>

          <TabsContent value="ml-dl" className="mt-0">
            <GemMLDLComparison embedded={true} />
          </TabsContent>

          <TabsContent value="copy" className="mt-0">
            <CopyTrading embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ScannerHub;
