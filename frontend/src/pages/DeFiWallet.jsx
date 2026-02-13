import React, { useState, useEffect } from 'react';
import { 
  Wallet, Link2, Unlink, RefreshCw, ExternalLink, Copy, Check,
  Coins, ImageIcon, ArrowUpRight, ArrowDownRight, Shield, Layers,
  ChevronRight, AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const DeFiWallet = ({ embedded = false }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [wallets, setWallets] = useState([]);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [balances, setBalances] = useState(null);
  const [positions, setPositions] = useState(null);
  const [nfts, setNfts] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [copiedAddress, setCopiedAddress] = useState(null);
  const [supportedChains, setSupportedChains] = useState([]);

  useEffect(() => {
    fetchWallets();
    fetchSupported();
  }, []);

  useEffect(() => {
    if (selectedWallet) {
      fetchWalletData(selectedWallet.wallet_address);
    }
  }, [selectedWallet]);

  const fetchWallets = async () => {
    try {
      const res = await fetch(`${API_URL}/api/defi-wallet/wallets`);
      if (res.ok) {
        const data = await res.json();
        setWallets(data.wallets || []);
        if (data.wallets?.length > 0) {
          setSelectedWallet(data.wallets[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching wallets:', err);
    }
  };

  const fetchSupported = async () => {
    try {
      const res = await fetch(`${API_URL}/api/defi-wallet/supported`);
      if (res.ok) {
        const data = await res.json();
        setSupportedChains(data.chains || []);
      }
    } catch (err) {
      console.error('Error fetching supported chains:', err);
    }
  };

  const fetchWalletData = async (address) => {
    setLoading(true);
    try {
      const [balRes, posRes, nftRes, txRes] = await Promise.all([
        fetch(`${API_URL}/api/defi-wallet/balances/${address}`),
        fetch(`${API_URL}/api/defi-wallet/positions/${address}`),
        fetch(`${API_URL}/api/defi-wallet/nfts/${address}`),
        fetch(`${API_URL}/api/defi-wallet/transactions/${address}?limit=10`)
      ]);

      if (balRes.ok) setBalances(await balRes.json());
      if (posRes.ok) setPositions(await posRes.json());
      if (nftRes.ok) setNfts(await nftRes.json());
      if (txRes.ok) {
        const txData = await txRes.json();
        setTransactions(txData.transactions || []);
      }
    } catch (err) {
      console.error('Error fetching wallet data:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWallet = async () => {
    setConnecting(true);
    try {
      // Check if MetaMask is available
      if (typeof window.ethereum === 'undefined') {
        toast.error('MetaMask not detected. Please install MetaMask extension.');
        window.open('https://metamask.io/download/', '_blank');
        return;
      }

      // Request account access
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const walletAddress = accounts[0];

      // Get chain ID
      const chainId = await window.ethereum.request({ method: 'eth_chainId' });
      const chainName = getChainName(parseInt(chainId, 16));

      // Register with backend
      const res = await fetch(`${API_URL}/api/defi-wallet/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: walletAddress,
          wallet_type: 'metamask',
          chain: chainName
        })
      });

      if (res.ok) {
        toast.success('Wallet connected successfully!');
        fetchWallets();
      }
    } catch (err) {
      if (err.code === 4001) {
        toast.error('Connection rejected by user');
      } else {
        toast.error('Failed to connect wallet');
        console.error(err);
      }
    } finally {
      setConnecting(false);
    }
  };

  const disconnectWallet = async (walletId) => {
    try {
      await fetch(`${API_URL}/api/defi-wallet/disconnect/${walletId}`, { method: 'DELETE' });
      toast.success('Wallet disconnected');
      fetchWallets();
      setSelectedWallet(null);
    } catch (err) {
      toast.error('Failed to disconnect wallet');
    }
  };

  const getChainName = (chainId) => {
    const chains = {
      1: 'ethereum',
      56: 'bsc',
      137: 'polygon',
      42161: 'arbitrum',
      10: 'optimism',
      43114: 'avalanche',
      8453: 'base'
    };
    return chains[chainId] || 'ethereum';
  };

  const copyAddress = (address) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(address);
    setTimeout(() => setCopiedAddress(null), 2000);
    toast.success('Address copied');
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Wallet },
    { id: 'tokens', label: 'Tokens', icon: Coins },
    { id: 'defi', label: 'DeFi Positions', icon: Layers },
    { id: 'nfts', label: 'NFTs', icon: ImageIcon },
    { id: 'activity', label: 'Activity', icon: ArrowUpRight }
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="defi-wallet-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">DeFi Wallet</h1>
          <p className="text-[#A1A1AA] mt-1">Connect MetaMask & track DeFi positions</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => selectedWallet && fetchWalletData(selectedWallet.wallet_address)}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a] transition"
            data-testid="refresh-wallet-btn"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={connectWallet}
            disabled={connecting}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#FF9500] to-[#FF5500] text-white font-semibold rounded-lg hover:opacity-90 transition disabled:opacity-50"
            data-testid="connect-wallet-btn"
          >
            <Wallet size={18} />
            {connecting ? 'Connecting...' : 'Connect MetaMask'}
          </button>
        </div>
      </div>

      {/* Connected Wallets */}
      {wallets.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm text-[#A1A1AA] mb-3">Connected Wallets</h2>
          <div className="flex flex-wrap gap-3">
            {wallets.map((wallet) => (
              <motion.div
                key={wallet.wallet_id}
                onClick={() => setSelectedWallet(wallet)}
                className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition ${
                  selectedWallet?.wallet_id === wallet.wallet_id
                    ? 'bg-[#00FF94]/10 border-[#00FF94]/50'
                    : 'bg-[#1F1F1F] border-[#333] hover:border-[#555]'
                }`}
                whileHover={{ scale: 1.02 }}
                data-testid={`wallet-${wallet.wallet_id}`}
              >
                <div className="w-8 h-8 bg-gradient-to-br from-[#FF9500] to-[#FF5500] rounded-full flex items-center justify-center">
                  <Wallet size={16} className="text-white" />
                </div>
                <div>
                  <p className="text-white font-medium">{formatAddress(wallet.wallet_address)}</p>
                  <p className="text-xs text-[#A1A1AA] capitalize">{wallet.chain}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    copyAddress(wallet.wallet_address);
                  }}
                  className="p-1.5 hover:bg-white/10 rounded"
                >
                  {copiedAddress === wallet.wallet_address ? (
                    <Check size={14} className="text-[#00FF94]" />
                  ) : (
                    <Copy size={14} className="text-[#A1A1AA]" />
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    disconnectWallet(wallet.wallet_id);
                  }}
                  className="p-1.5 hover:bg-red-500/20 rounded"
                >
                  <Unlink size={14} className="text-red-400" />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* No Wallet Connected */}
      {wallets.length === 0 && (
        <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-12 text-center mb-6">
          <Wallet size={64} className="mx-auto text-[#333] mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Connect Your Wallet</h2>
          <p className="text-[#A1A1AA] mb-6 max-w-md mx-auto">
            Connect your MetaMask wallet to view your DeFi positions, token balances, and NFTs across multiple chains.
          </p>
          <button
            onClick={connectWallet}
            disabled={connecting}
            className="px-6 py-3 bg-gradient-to-r from-[#FF9500] to-[#FF5500] text-white font-semibold rounded-lg hover:opacity-90 transition"
          >
            {connecting ? 'Connecting...' : 'Connect MetaMask'}
          </button>
          <div className="mt-6 flex justify-center gap-4">
            {supportedChains.slice(0, 5).map((chain) => (
              <div key={chain.id} className="flex items-center gap-1 text-xs text-[#A1A1AA]">
                <span>{chain.icon}</span>
                <span>{chain.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      {selectedWallet && (
        <>
          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
                  activeTab === tab.id
                    ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/50'
                    : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent hover:bg-[#2a2a2a]'
                }`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <AnimatePresence mode="wait">
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
              >
                {/* Total Value */}
                <div className="md:col-span-3 bg-gradient-to-r from-[#1F1F1F] to-[#2a2a2a] border border-[#333] rounded-xl p-6">
                  <p className="text-[#A1A1AA] mb-2">Total Portfolio Value</p>
                  <p className="text-4xl font-bold text-white">
                    ${((balances?.total_value_usd || 0) + (positions?.summary?.total_value_usd || 0) + (nfts?.total_floor_value_usd || 0)).toLocaleString()}
                  </p>
                  <div className="flex gap-6 mt-4">
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Tokens</p>
                      <p className="text-lg text-white">${(balances?.total_value_usd ?? 0).toLocaleString() || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">DeFi</p>
                      <p className="text-lg text-[#00FF94]">${positions?.(summary?.total_value_usd ?? 0).toLocaleString() || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">NFTs</p>
                      <p className="text-lg text-[#9D00FF]">${(nfts?.total_floor_value_usd ?? 0).toLocaleString() || 0}</p>
                    </div>
                  </div>
                </div>

                {/* Top Tokens */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-3">Top Tokens</h3>
                  <div className="space-y-2">
                    {balances?.balances?.slice(0, 4).map((token, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-[#333] rounded-full flex items-center justify-center">
                            <span className="text-xs">{token.symbol?.slice(0, 2)}</span>
                          </div>
                          <span className="text-white">{token.symbol}</span>
                        </div>
                        <span className="text-[#A1A1AA]">${(token?.value_usd ?? 0).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top DeFi Positions */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-3">Top DeFi Positions</h3>
                  <div className="space-y-2">
                    {positions?.positions?.slice(0, 4).map((pos, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <div>
                          <p className="text-white text-sm">{pos.protocol}</p>
                          <p className="text-xs text-[#A1A1AA]">{pos.position_type}</p>
                        </div>
                        <span className="text-[#00FF94]">${(pos?.current_value_usd ?? 0).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <h3 className="text-white font-semibold mb-3">Recent Activity</h3>
                  <div className="space-y-2">
                    {transactions.slice(0, 4).map((tx, i) => (
                      <div key={i} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {tx.type === 'swap' ? (
                            <ArrowUpRight size={16} className="text-[#00FF94]" />
                          ) : (
                            <ArrowDownRight size={16} className="text-[#9D00FF]" />
                          )}
                          <span className="text-white text-sm capitalize">{tx.type}</span>
                        </div>
                        <span className="text-xs text-[#A1A1AA]">{tx.protocol}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'tokens' && (
              <motion.div
                key="tokens"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Token Balances</h2>
                  <span className="text-[#00FF94] font-bold">${(balances?.total_value_usd ?? 0).toLocaleString()}</span>
                </div>
                <div className="space-y-3">
                  {balances?.balances?.map((token, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#333] rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold">{token.symbol?.slice(0, 2)}</span>
                        </div>
                        <div>
                          <p className="text-white font-medium">{token.name}</p>
                          <p className="text-sm text-[#A1A1AA]">{token.balance} {token.symbol}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-medium">${(token?.value_usd ?? 0).toLocaleString()}</p>
                        <p className="text-sm text-[#A1A1AA]">${token.price_usd}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'defi' && (
              <motion.div
                key="defi"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Total Value</p>
                      <p className="text-xl font-bold text-white">${positions?.(summary?.total_value_usd ?? 0).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Total PnL</p>
                      <p className={`text-xl font-bold ${(positions?.summary?.total_pnl_usd || 0) >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                        ${positions?.(summary?.total_pnl_usd ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Positions</p>
                      <p className="text-xl font-bold text-white">{positions?.summary?.total_positions}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#A1A1AA]">Protocols</p>
                      <p className="text-xl font-bold text-white">{positions?.summary?.protocols_used?.length}</p>
                    </div>
                  </div>
                </div>

                {positions?.positions?.map((pos, i) => (
                  <div
                    key={i}
                    className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#333] rounded-full flex items-center justify-center">
                          <Layers size={20} className="text-[#00FF94]" />
                        </div>
                        <div>
                          <p className="text-white font-medium">{pos.protocol}</p>
                          <p className="text-sm text-[#A1A1AA] capitalize">{pos.position_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-bold">${(pos?.current_value_usd ?? 0).toLocaleString()}</p>
                        {pos.apy && <p className="text-sm text-[#00FF94]">{pos.apy}% APY</p>}
                      </div>
                    </div>
                    {pos.pnl_usd !== undefined && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-sm text-[#A1A1AA]">PnL:</span>
                        <span className={`text-sm font-medium ${pos.pnl_usd >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                          ${pos.pnl_usd} ({pos.pnl_pct}%)
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </motion.div>
            )}

            {activeTab === 'nfts' && (
              <motion.div
                key="nfts"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">NFT Collection</h2>
                  <span className="text-[#9D00FF] font-bold">Floor: ${(nfts?.total_floor_value_usd ?? 0).toLocaleString()}</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {nfts?.nfts?.map((nft, i) => (
                    <div
                      key={i}
                      className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl overflow-hidden"
                    >
                      <div className="aspect-square bg-gradient-to-br from-[#333] to-[#1F1F1F] flex items-center justify-center">
                        <ImageIcon size={48} className="text-[#555]" />
                      </div>
                      <div className="p-3">
                        <p className="text-white font-medium text-sm truncate">{nft.name}</p>
                        <p className="text-xs text-[#A1A1AA]">{nft.collection}</p>
                        <p className="text-[#9D00FF] font-bold mt-1">{nft.floor_price_eth} ETH</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'activity' && (
              <motion.div
                key="activity"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6"
              >
                <h2 className="text-lg font-semibold text-white mb-4">Recent Transactions</h2>
                <div className="space-y-3">
                  {transactions.map((tx, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 bg-[#0A0A0A] border border-[#333] rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          tx.type === 'swap' ? 'bg-[#00FF94]/20' : 'bg-[#9D00FF]/20'
                        }`}>
                          {tx.type === 'swap' ? (
                            <ArrowUpRight size={18} className="text-[#00FF94]" />
                          ) : (
                            <ArrowDownRight size={18} className="text-[#9D00FF]" />
                          )}
                        </div>
                        <div>
                          <p className="text-white font-medium capitalize">{tx.type}</p>
                          <p className="text-sm text-[#A1A1AA]">{tx.protocol}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        {tx.from_amount && (
                          <p className="text-white">{tx.from_amount} {tx.from_token} → {tx.to_amount} {tx.to_token}</p>
                        )}
                        {tx.amount && (
                          <p className="text-white">{tx.amount} {tx.token}</p>
                        )}
                        <p className="text-xs text-[#A1A1AA]">Gas: ${tx.gas_used_usd}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
};

export default DeFiWallet;
