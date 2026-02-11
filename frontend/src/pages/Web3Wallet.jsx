import React, { useState, useEffect } from 'react';
import { Wallet, Link2, Unlink, RefreshCw, ChevronDown, ExternalLink, Coins, Image, Layers, PieChart } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const Web3Wallet = () => {
  const [wallets, setWallets] = useState([]);
  const [balances, setBalances] = useState([]);
  const [defiPositions, setDefiPositions] = useState([]);
  const [nfts, setNfts] = useState([]);
  const [portfolioSummary, setPortfolioSummary] = useState(null);
  const [chains, setChains] = useState([]);
  const [selectedChain, setSelectedChain] = useState(1);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tokens');
  const [connectingWallet, setConnectingWallet] = useState(false);

  useEffect(() => {
    fetchChains();
    fetchWallets();
  }, []);

  const fetchChains = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/web3-wallet/chains`);
      if (response.ok) {
        const data = await response.json();
        setChains(data.chains || []);
      }
    } catch (error) {
      console.error('Error fetching chains:', error);
    }
  };

  const fetchWallets = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/web3-wallet/wallets`);
      if (response.ok) {
        const data = await response.json();
        setWallets(data.wallets || []);
        if (data.wallets?.length > 0) {
          fetchWalletData(data.wallets[0].address);
        }
      }
    } catch (error) {
      console.error('Error fetching wallets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWalletData = async (address) => {
    setLoading(true);
    try {
      const [balRes, defiRes, nftRes, summaryRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/web3-wallet/balances/${address}?chain_id=${selectedChain}`),
        fetch(`${BACKEND_URL}/api/web3-wallet/defi-positions/${address}?chain_id=${selectedChain}`),
        fetch(`${BACKEND_URL}/api/web3-wallet/nfts/${address}?chain_id=${selectedChain}`),
        fetch(`${BACKEND_URL}/api/web3-wallet/portfolio-summary/${address}`)
      ]);

      if (balRes.ok) setBalances((await balRes.json()).balances || []);
      if (defiRes.ok) setDefiPositions((await defiRes.json()).positions || []);
      if (nftRes.ok) setNfts((await nftRes.json()).nfts || []);
      if (summaryRes.ok) setPortfolioSummary(await summaryRes.json());
    } catch (error) {
      console.error('Error fetching wallet data:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWallet = async () => {
    setConnectingWallet(true);
    try {
      if (typeof window.ethereum !== 'undefined') {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        
        const response = await fetch(`${BACKEND_URL}/api/web3-wallet/connect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            address: accounts[0],
            chain_id: parseInt(chainId, 16),
            wallet_type: 'metamask'
          })
        });
        
        if (response.ok) {
          fetchWallets();
        }
      } else {
        alert('Please install MetaMask to connect your wallet');
      }
    } catch (error) {
      console.error('Error connecting wallet:', error);
    } finally {
      setConnectingWallet(false);
    }
  };

  const disconnectWallet = async (walletId) => {
    try {
      await fetch(`${BACKEND_URL}/api/web3-wallet/disconnect/${walletId}`, { method: 'DELETE' });
      fetchWallets();
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500/20 to-amber-500/20">
            <Wallet className="w-8 h-8 text-orange-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Web3 Wallet</h1>
            <p className="text-gray-400">Track your DeFi positions, tokens, and NFTs</p>
          </div>
        </div>

        <button
          onClick={connectWallet}
          disabled={connectingWallet}
          className="flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
        >
          {connectingWallet ? (
            <RefreshCw className="w-5 h-5 animate-spin" />
          ) : (
            <Link2 className="w-5 h-5" />
          )}
          Connect MetaMask
        </button>
      </div>

      {/* Connected Wallets */}
      {wallets.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Connected Wallets</h3>
          <div className="flex flex-wrap gap-3">
            {wallets.map(wallet => (
              <div key={wallet.wallet_id} className="flex items-center gap-3 px-4 py-2 bg-gray-800 rounded-lg">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <Wallet className="w-4 h-4 text-orange-400" />
                </div>
                <div>
                  <p className="text-sm text-white font-mono">
                    {wallet.address?.slice(0, 6)}...{wallet.address?.slice(-4)}
                  </p>
                  <p className="text-xs text-gray-500">{wallet.chain_name}</p>
                </div>
                <button
                  onClick={() => disconnectWallet(wallet.wallet_id)}
                  className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                >
                  <Unlink className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chain Selector */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm text-gray-400">Chain:</span>
        <div className="relative">
          <select
            value={selectedChain}
            onChange={(e) => {
              setSelectedChain(parseInt(e.target.value));
              if (wallets[0]) fetchWalletData(wallets[0].address);
            }}
            className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            {chains.map(chain => (
              <option key={chain.id} value={chain.id}>{chain.name}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Portfolio Summary */}
      {portfolioSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <PieChart className="w-4 h-4" />
              Total Portfolio
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(portfolioSummary.total_value_usd || 0)}
            </p>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <Coins className="w-4 h-4" />
              Tokens
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(portfolioSummary.tokens?.value_usd || 0)}
            </p>
            <p className="text-xs text-gray-500">{portfolioSummary.tokens?.count || 0} tokens</p>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <Layers className="w-4 h-4" />
              DeFi
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(portfolioSummary.defi?.value_usd || 0)}
            </p>
            <p className="text-xs text-gray-500">{portfolioSummary.defi?.positions_count || 0} positions</p>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <Image className="w-4 h-4" />
              NFTs
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(portfolioSummary.nfts?.floor_value_usd || 0)}
            </p>
            <p className="text-xs text-gray-500">{portfolioSummary.nfts?.count || 0} NFTs</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {['tokens', 'defi', 'nfts'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-orange-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {tab === 'tokens' && <Coins className="w-4 h-4" />}
            {tab === 'defi' && <Layers className="w-4 h-4" />}
            {tab === 'nfts' && <Image className="w-4 h-4" />}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 text-orange-400 animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading wallet data...</p>
          </div>
        ) : activeTab === 'tokens' ? (
          <div className="divide-y divide-gray-700">
            {balances.map((token, i) => (
              <div key={i} className="flex items-center justify-between p-4 hover:bg-gray-700/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center overflow-hidden">
                    {token.logo ? (
                      <img src={token.logo} alt={token.symbol} className="w-full h-full object-cover" />
                    ) : (
                      <Coins className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-white">{token.token}</p>
                    <p className="text-xs text-gray-500">{token.balance} {token.symbol}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-white">{formatCurrency(token.value_usd)}</p>
                  <p className="text-xs text-gray-500">${token.price_usd?.toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === 'defi' ? (
          <div className="divide-y divide-gray-700">
            {defiPositions.map((position, i) => (
              <div key={i} className="p-4 hover:bg-gray-700/30">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold text-white">{position.protocol}</span>
                    <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded">{position.type}</span>
                  </div>
                  <span className="text-lg font-bold text-white">{formatCurrency(position.value_usd)}</span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  {position.pool && <div><span className="text-gray-500">Pool:</span> <span className="text-white">{position.pool}</span></div>}
                  {position.asset && <div><span className="text-gray-500">Asset:</span> <span className="text-white">{position.asset}</span></div>}
                  {position.apr && <div><span className="text-gray-500">APR:</span> <span className="text-green-400">{position.apr}%</span></div>}
                  {position.apy && <div><span className="text-gray-500">APY:</span> <span className="text-green-400">{position.apy}%</span></div>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {nfts.map((nft, i) => (
              <div key={i} className="bg-gray-700/30 rounded-xl overflow-hidden">
                <div className="aspect-square bg-gray-800">
                  {nft.image_url && (
                    <img src={nft.image_url} alt={nft.name} className="w-full h-full object-cover" />
                  )}
                </div>
                <div className="p-3">
                  <p className="text-xs text-gray-500">{nft.collection}</p>
                  <p className="font-medium text-white">{nft.name}</p>
                  <p className="text-sm text-gray-400 mt-1">Floor: {nft.floor_price_eth} ETH</p>
                  <p className="text-xs text-gray-500">{formatCurrency(nft.floor_price_usd)}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && wallets.length === 0 && (
          <div className="p-8 text-center">
            <Wallet className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-white font-medium">No Wallet Connected</p>
            <p className="text-sm text-gray-400 mt-1">Connect your MetaMask wallet to view your assets</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Web3Wallet;
