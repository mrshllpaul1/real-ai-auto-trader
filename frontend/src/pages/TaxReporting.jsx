import React, { useState, useEffect } from 'react';
import { Receipt, Download, Calendar, DollarSign, TrendingUp, TrendingDown, AlertTriangle, FileText, ChevronDown, PieChart } from 'lucide-react';

const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '';

const TaxReporting = () => {
  const [summary, setSummary] = useState(null);
  const [gainsByAsset, setGainsByAsset] = useState([]);
  const [washSales, setWashSales] = useState([]);
  const [taxLossHarvest, setTaxLossHarvest] = useState(null);
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    fetchData();
  }, [year]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, assetsRes, washRes, harvestRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/tax/summary?year=${year}`),
        fetch(`${BACKEND_URL}/api/tax/gains-by-asset?year=${year}`),
        fetch(`${BACKEND_URL}/api/tax/wash-sale-alerts?year=${year}`),
        fetch(`${BACKEND_URL}/api/tax/tax-loss-harvesting`)
      ]);

      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (assetsRes.ok) {
        const data = await assetsRes.json();
        setGainsByAsset(data.assets || []);
      }
      if (washRes.ok) {
        const data = await washRes.json();
        setWashSales(data.wash_sale_alerts || []);
      }
      if (harvestRes.ok) setTaxLossHarvest(await harvestRes.json());
    } catch (error) {
      console.error('Error fetching tax data:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (format) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/tax/report/${format}?year=${year}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tax_report_${year}.${format}`;
        a.click();
      }
    } catch (error) {
      console.error('Error downloading report:', error);
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
          <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20">
            <Receipt className="w-8 h-8 text-green-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Tax Reporting</h1>
            <p className="text-gray-400">Track gains, losses, and generate tax reports</p>
          </div>
        </div>

        {/* Year Selector */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <select
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {[2025, 2024, 2023, 2022, 2021].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          <button
            onClick={() => downloadReport('csv')}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Warning Banner */}
      <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-yellow-400 font-medium">Disclaimer</p>
          <p className="text-sm text-gray-400">This is an estimate for informational purposes only. Consult a tax professional for accurate filing. Tax laws vary by jurisdiction.</p>
        </div>
      </div>

      {/* Summary Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-800/50 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <DollarSign className="w-4 h-4" />
              Total Proceeds
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.summary?.total_proceeds || 0)}
            </p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <FileText className="w-4 h-4" />
              Cost Basis
            </div>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.summary?.total_cost_basis || 0)}
            </p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              {(summary.summary?.net_gain_loss || 0) >= 0 ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              Net Gain/Loss
            </div>
            <p className={`text-2xl font-bold ${
              (summary.summary?.net_gain_loss || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {formatCurrency(summary.summary?.net_gain_loss || 0)}
            </p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <Receipt className="w-4 h-4" />
              Est. Tax Liability
            </div>
            <p className="text-2xl font-bold text-orange-400">
              {formatCurrency(summary.summary?.estimated_tax || 0)}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {['summary', 'by-asset', 'wash-sales', 'tax-loss'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-green-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {tab === 'summary' && 'Summary'}
            {tab === 'by-asset' && 'By Asset'}
            {tab === 'wash-sales' && `Wash Sales (${washSales.length})`}
            {tab === 'tax-loss' && 'Tax-Loss Harvesting'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden">
        {activeTab === 'summary' && summary && (
          <div className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Tax Year {year} Summary</h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm text-gray-400 mb-3">Short-Term Capital Gains</h4>
                <p className={`text-3xl font-bold ${
                  (summary.summary?.short_term_gains || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(summary.summary?.short_term_gains || 0)}
                </p>
                <p className="text-sm text-gray-500 mt-1">Taxed as ordinary income</p>
              </div>
              <div>
                <h4 className="text-sm text-gray-400 mb-3">Long-Term Capital Gains</h4>
                <p className={`text-3xl font-bold ${
                  (summary.summary?.long_term_gains || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(summary.summary?.long_term_gains || 0)}
                </p>
                <p className="text-sm text-gray-500 mt-1">Preferential tax rates (0-20%)</p>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Total Transactions</span>
                <span className="text-white font-medium">{summary.stats?.total_trades || 0}</span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-gray-400">Total Fees Paid</span>
                <span className="text-white font-medium">{formatCurrency(summary.summary?.total_fees || 0)}</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'by-asset' && (
          <div className="divide-y divide-gray-700">
            <div className="grid grid-cols-5 gap-4 p-4 text-sm font-medium text-gray-400">
              <div>Asset</div>
              <div className="text-right">Proceeds</div>
              <div className="text-right">Cost Basis</div>
              <div className="text-right">Gain/Loss</div>
              <div className="text-right">Trades</div>
            </div>
            {gainsByAsset.map((asset, i) => (
              <div key={i} className="grid grid-cols-5 gap-4 p-4 text-sm hover:bg-gray-700/30">
                <div className="font-medium text-white">{asset.asset}</div>
                <div className="text-right text-gray-300">{formatCurrency(asset.proceeds)}</div>
                <div className="text-right text-gray-300">{formatCurrency(asset.cost_basis)}</div>
                <div className={`text-right font-medium ${
                  asset.gain_loss >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(asset.gain_loss)}
                </div>
                <div className="text-right text-gray-400">{asset.trades}</div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'wash-sales' && (
          <div className="p-6">
            {washSales.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <TrendingUp className="w-6 h-6 text-green-400" />
                </div>
                <p className="text-white font-medium">No Wash Sale Alerts</p>
                <p className="text-sm text-gray-400 mt-1">Great job! No potential wash sale violations detected.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {washSales.map((alert, i) => (
                  <div key={i} className={`p-4 rounded-lg border ${
                    alert.severity === 'high' 
                      ? 'bg-red-500/10 border-red-500/30'
                      : 'bg-yellow-500/10 border-yellow-500/30'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-white">{alert.symbol}</p>
                        <p className="text-sm text-gray-400 mt-1">
                          Sold on {alert.sell_date}, bought on {alert.buy_date} ({alert.days_between} days apart)
                        </p>
                      </div>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        alert.severity === 'high'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-red-400 mt-2">Potential disallowed loss: {formatCurrency(Math.abs(alert.loss_amount))}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'tax-loss' && taxLossHarvest && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white">Tax-Loss Harvesting Opportunities</h3>
                <p className="text-sm text-gray-400">Sell losing positions to offset gains</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Potential Tax Savings</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatCurrency(taxLossHarvest.potential_tax_savings || 0)}
                </p>
              </div>
            </div>

            {(taxLossHarvest.opportunities || []).length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">No tax-loss harvesting opportunities found.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {(taxLossHarvest.opportunities || []).map((opp, i) => (
                  <div key={i} className="p-4 bg-gray-700/30 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-medium text-white">{opp.asset}</p>
                      <p className="text-sm text-gray-400">Current value: {formatCurrency(opp.current_value)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-red-400 font-medium">{formatCurrency(opp.unrealized_loss)}</p>
                      <p className="text-xs text-gray-500">{opp.loss_percent.toFixed(1)}% loss</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TaxReporting;
