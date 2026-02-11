import React, { useState, useEffect, useCallback } from 'react';
import {
  Edit3, Save, X, DollarSign, RefreshCw, AlertCircle,
  Check, History, Plus, Trash2, Download, Upload
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import api from '../services/api';

const EntryPriceManager = ({ embedded = false }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [editingSymbol, setEditingSymbol] = useState(null);
  const [editForm, setEditForm] = useState({ entry_price: '', quantity: '', notes: '' });
  const [showAddNew, setShowAddNew] = useState(false);
  const [newEntry, setNewEntry] = useState({ symbol: '', entry_price: '', quantity: '', notes: '' });

  const loadEntries = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/entry-prices/');
      setEntries(res.data.entries || []);
    } catch (error) {
      console.error('Failed to load entries:', error);
      toast.error('Failed to load entry prices');
    } finally {
      setLoading(false);
    }
  }, []);

  const syncFromKraken = async () => {
    try {
      setSyncing(true);
      toast.info('Syncing positions from Kraken...');
      
      const res = await api.post('/entry-prices/sync-from-kraken');
      
      if (res.data.created > 0) {
        toast.success(`Created ${res.data.created} entries. Please correct the entry prices.`);
      } else {
        toast.info('No new positions to sync');
      }
      
      await loadEntries();
    } catch (error) {
      console.error('Sync failed:', error);
      toast.error('Failed to sync from Kraken');
    } finally {
      setSyncing(false);
    }
  };

  const startEdit = (entry) => {
    setEditingSymbol(entry.symbol);
    setEditForm({
      entry_price: entry.entry_price?.toString() || '',
      quantity: entry.quantity?.toString() || '',
      notes: entry.manual_notes || ''
    });
  };

  const cancelEdit = () => {
    setEditingSymbol(null);
    setEditForm({ entry_price: '', quantity: '', notes: '' });
  };

  const saveEntry = async (symbol) => {
    try {
      const res = await api.post('/entry-prices/correct', {
        symbol,
        entry_price: parseFloat(editForm.entry_price),
        quantity: editForm.quantity ? parseFloat(editForm.quantity) : null,
        notes: editForm.notes || null
      });
      
      toast.success(`Entry price for ${symbol} updated`);
      cancelEdit();
      await loadEntries();
    } catch (error) {
      console.error('Save failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to save');
    }
  };

  const addNewEntry = async () => {
    try {
      if (!newEntry.symbol || !newEntry.entry_price || !newEntry.quantity) {
        toast.error('Symbol, entry price, and quantity are required');
        return;
      }
      
      const res = await api.post('/entry-prices/correct', {
        symbol: newEntry.symbol.toUpperCase(),
        entry_price: parseFloat(newEntry.entry_price),
        quantity: parseFloat(newEntry.quantity),
        notes: newEntry.notes || null
      });
      
      toast.success(`Entry for ${newEntry.symbol.toUpperCase()} created`);
      setShowAddNew(false);
      setNewEntry({ symbol: '', entry_price: '', quantity: '', notes: '' });
      await loadEntries();
    } catch (error) {
      console.error('Add failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to add entry');
    }
  };

  const deleteEntry = async (symbol) => {
    if (!window.confirm(`Delete entry for ${symbol}? This cannot be undone.`)) {
      return;
    }
    
    try {
      await api.delete(`/entry-prices/${symbol}`);
      toast.success(`Entry for ${symbol} deleted`);
      await loadEntries();
    } catch (error) {
      console.error('Delete failed:', error);
      toast.error('Failed to delete entry');
    }
  };

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${embedded ? '' : 'p-6'}`} data-testid="entry-price-manager">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-green-400" />
            Entry Price Manager
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Manually correct entry prices for accurate P&L tracking
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadEntries}
            disabled={loading}
            className="border-slate-700 hover:bg-slate-800"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={syncFromKraken}
            disabled={syncing}
            className="border-slate-700 hover:bg-slate-800"
          >
            <Download className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync from Kraken'}
          </Button>
          <Button
            size="sm"
            onClick={() => setShowAddNew(true)}
            className="bg-gradient-to-r from-green-500 to-emerald-500"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Entry
          </Button>
        </div>
      </div>

      {/* Add New Entry Form */}
      <AnimatePresence>
        {showAddNew && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-4 bg-slate-800/50 border border-green-500/30 rounded-xl"
          >
            <h3 className="font-medium text-white mb-4 flex items-center gap-2">
              <Plus className="w-4 h-4 text-green-400" />
              Add New Entry
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Symbol</label>
                <Input
                  placeholder="BTC"
                  value={newEntry.symbol}
                  onChange={(e) => setNewEntry({ ...newEntry, symbol: e.target.value })}
                  className="bg-slate-900 border-slate-700"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Entry Price ($)</label>
                <Input
                  type="number"
                  step="0.00000001"
                  placeholder="45000.00"
                  value={newEntry.entry_price}
                  onChange={(e) => setNewEntry({ ...newEntry, entry_price: e.target.value })}
                  className="bg-slate-900 border-slate-700"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Quantity</label>
                <Input
                  type="number"
                  step="0.00000001"
                  placeholder="0.5"
                  value={newEntry.quantity}
                  onChange={(e) => setNewEntry({ ...newEntry, quantity: e.target.value })}
                  className="bg-slate-900 border-slate-700"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Notes (optional)</label>
                <Input
                  placeholder="Transferred from Coinbase"
                  value={newEntry.notes}
                  onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
                  className="bg-slate-900 border-slate-700"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button size="sm" onClick={addNewEntry} className="bg-green-600 hover:bg-green-700">
                <Check className="w-4 h-4 mr-2" />
                Save Entry
              </Button>
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => setShowAddNew(false)}
                className="border-slate-700"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Entries Table */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-900/50">
            <tr>
              <th className="text-left p-4 text-xs font-medium text-slate-400 uppercase">Symbol</th>
              <th className="text-right p-4 text-xs font-medium text-slate-400 uppercase">Entry Price</th>
              <th className="text-right p-4 text-xs font-medium text-slate-400 uppercase">Quantity</th>
              <th className="text-right p-4 text-xs font-medium text-slate-400 uppercase">Cost Basis</th>
              <th className="text-center p-4 text-xs font-medium text-slate-400 uppercase">Source</th>
              <th className="text-right p-4 text-xs font-medium text-slate-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No entry prices recorded</p>
                  <p className="text-sm mt-1">Click "Sync from Kraken" to import positions</p>
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.symbol} className="hover:bg-slate-700/30 transition-colors">
                  {editingSymbol === entry.symbol ? (
                    // Edit Mode
                    <>
                      <td className="p-4">
                        <span className="font-medium text-white">{entry.symbol}</span>
                      </td>
                      <td className="p-4">
                        <Input
                          type="number"
                          step="0.00000001"
                          value={editForm.entry_price}
                          onChange={(e) => setEditForm({ ...editForm, entry_price: e.target.value })}
                          className="w-32 bg-slate-900 border-slate-600 text-right"
                        />
                      </td>
                      <td className="p-4">
                        <Input
                          type="number"
                          step="0.00000001"
                          value={editForm.quantity}
                          onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                          className="w-28 bg-slate-900 border-slate-600 text-right"
                        />
                      </td>
                      <td className="p-4 text-right text-slate-400">
                        ${((parseFloat(editForm.entry_price) || 0) * (parseFloat(editForm.quantity) || 0)).toFixed(2)}
                      </td>
                      <td className="p-4">
                        <Input
                          placeholder="Notes"
                          value={editForm.notes}
                          onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                          className="w-full bg-slate-900 border-slate-600 text-sm"
                        />
                      </td>
                      <td className="p-4">
                        <div className="flex justify-end gap-2">
                          <Button size="sm" onClick={() => saveEntry(entry.symbol)} className="bg-green-600 hover:bg-green-700 h-8 px-2">
                            <Save className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="outline" onClick={cancelEdit} className="border-slate-600 h-8 px-2">
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </>
                  ) : (
                    // View Mode
                    <>
                      <td className="p-4">
                        <span className="font-medium text-white">{entry.symbol}</span>
                      </td>
                      <td className="p-4 text-right">
                        <span className={`font-mono ${entry.entry_price < 0.02 ? 'text-amber-400' : 'text-white'}`}>
                          ${entry.entry_price?.toFixed(entry.entry_price < 1 ? 6 : 2)}
                        </span>
                        {entry.entry_price < 0.02 && (
                          <Badge className="ml-2 bg-amber-500/20 text-amber-400 text-xs">
                            Needs correction
                          </Badge>
                        )}
                      </td>
                      <td className="p-4 text-right font-mono text-slate-300">
                        {entry.quantity?.toFixed(entry.quantity < 1 ? 6 : 4)}
                      </td>
                      <td className="p-4 text-right font-mono text-slate-300">
                        ${entry.total_cost?.toFixed(2)}
                      </td>
                      <td className="p-4 text-center">
                        {entry.is_manual ? (
                          <Badge className="bg-purple-500/20 text-purple-400">
                            <Edit3 className="w-3 h-3 mr-1" />
                            Manual
                          </Badge>
                        ) : (
                          <Badge className="bg-blue-500/20 text-blue-400">
                            Auto
                          </Badge>
                        )}
                        {entry.correction_count > 0 && (
                          <Badge className="ml-1 bg-slate-700 text-slate-400">
                            <History className="w-3 h-3 mr-1" />
                            {entry.correction_count}
                          </Badge>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex justify-end gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => startEdit(entry)}
                            className="border-slate-600 h-8 px-2 hover:bg-slate-700"
                          >
                            <Edit3 className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => deleteEntry(entry.symbol)}
                            className="border-red-500/50 text-red-400 h-8 px-2 hover:bg-red-500/10"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Help Text */}
      <div className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg">
        <h4 className="text-sm font-medium text-white mb-2 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-cyan-400" />
          How Entry Prices Work
        </h4>
        <ul className="text-xs text-slate-400 space-y-1">
          <li>• <strong>Auto:</strong> Entry prices calculated from trade history</li>
          <li>• <strong>Manual:</strong> Entry prices you've manually set or corrected</li>
          <li>• <strong>Needs correction:</strong> Placeholder entries that require your input</li>
          <li>• Entry prices are used to calculate unrealized P&L on the Performance Dashboard</li>
        </ul>
      </div>
    </div>
  );
};

export default EntryPriceManager;
