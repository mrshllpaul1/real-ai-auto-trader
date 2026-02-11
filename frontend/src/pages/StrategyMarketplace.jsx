import React, { useState, useEffect } from 'react';
import { Store, Star, TrendingUp, Users, Filter, Search, ChevronDown, Sparkles, Shield, Clock, DollarSign } from 'lucide-react';

const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';

const StrategyMarketplace = () => {
  const [strategies, setStrategies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [sortBy, setSortBy] = useState('subscribers');
  const [priceFilter, setPriceFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [selectedCategory, sortBy, priceFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        sort_by: sortBy,
        price_filter: priceFilter,
        limit: '20'
      });
      if (selectedCategory) params.set('category', selectedCategory);

      const [stratRes, catRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/marketplace/strategies?${params}`),
        fetch(`${BACKEND_URL}/api/marketplace/categories`)
      ]);

      if (stratRes.ok) {
        const data = await stratRes.json();
        setStrategies(data.strategies || []);
      }
      if (catRes.ok) {
        const data = await catRes.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error('Error fetching marketplace data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredStrategies = strategies.filter(s => 
    !searchQuery || 
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSubscribe = async (strategyId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/marketplace/strategies/${strategyId}/subscribe`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchData(); // Refresh
      }
    } catch (error) {
      console.error('Error subscribing:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20">
            <Store className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Strategy Marketplace</h1>
            <p className="text-gray-400">Discover and subscribe to proven trading strategies</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search strategies..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Category Filter */}
        <div className="relative">
          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value || null)}
            className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 pr-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        {/* Sort */}
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 pr-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="subscribers">Most Popular</option>
            <option value="rating">Highest Rated</option>
            <option value="returns">Best Returns</option>
            <option value="newest">Newest</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>

        {/* Price Filter */}
        <div className="flex gap-2">
          {['all', 'free', 'paid'].map(filter => (
            <button
              key={filter}
              onClick={() => setPriceFilter(filter)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                priceFilter === filter
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Categories Pills */}
      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(selectedCategory === cat.id ? null : cat.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors ${
              selectedCategory === cat.id
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
          </button>
        ))}
      </div>

      {/* Strategy Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-800/50 rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-gray-700 rounded w-3/4 mb-3" />
              <div className="h-4 bg-gray-700 rounded w-full mb-2" />
              <div className="h-4 bg-gray-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStrategies.map(strategy => (
            <div key={strategy.strategy_id} className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden hover:border-purple-500/50 transition-colors">
              {/* Header */}
              <div className="p-4 border-b border-gray-700/50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-white text-lg">{strategy.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-400">by {strategy.creator?.name}</span>
                      {strategy.creator?.verified && (
                        <Shield className="w-3 h-3 text-blue-400" />
                      )}
                    </div>
                  </div>
                  {strategy.price_monthly === 0 ? (
                    <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">Free</span>
                  ) : (
                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded-full">
                      ${strategy.price_monthly}/mo
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400 line-clamp-2">{strategy.description}</p>
              </div>

              {/* Stats */}
              <div className="p-4 grid grid-cols-2 gap-3">
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                  <p className="text-lg font-bold text-green-400">
                    +{strategy.performance?.total_return?.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">Total Return</p>
                </div>
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                  <p className="text-lg font-bold text-white">
                    {strategy.performance?.win_rate?.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">Win Rate</p>
                </div>
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                  <p className="text-lg font-bold text-blue-400">
                    {strategy.performance?.sharpe_ratio?.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">Sharpe Ratio</p>
                </div>
                <div className="text-center p-2 bg-gray-900/50 rounded-lg">
                  <p className="text-lg font-bold text-red-400">
                    {strategy.performance?.max_drawdown?.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">Max Drawdown</p>
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-gray-700/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      <span className="text-sm text-white">{strategy.avg_rating?.toFixed(1)}</span>
                      <span className="text-xs text-gray-500">({strategy.reviews_count})</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-400">{strategy.subscribers_count?.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {strategy.tags?.slice(0, 2).map(tag => (
                      <span key={tag} className="px-2 py-0.5 bg-gray-700 text-gray-400 text-xs rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => handleSubscribe(strategy.strategy_id)}
                  className="w-full py-2.5 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  Subscribe
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StrategyMarketplace;
