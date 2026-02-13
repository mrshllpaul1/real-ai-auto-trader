import React, { useState, useEffect } from 'react';
import { 
  Brain, Sparkles, RefreshCw, Target, Zap, TrendingUp, TrendingDown,
  Eye, Info, ChevronRight, Play, Settings, BarChart3, GitBranch,
  Layers, AlertTriangle, Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, 
  AreaChart, Area, BarChart, Bar, CartesianGrid, Legend, ReferenceLine
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.REACT_APP_BACKEND_URL || '');

const MLAdvanced = () => {
  const [activeTab, setActiveTab] = useState('bayesian');
  const [bayesianModels, setBayesianModels] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [transferModels, setTransferModels] = useState([]);
  const [explainModels, setExplainModels] = useState([]);
  const [shapExplanation, setShapExplanation] = useState(null);
  const [limeExplanation, setLimeExplanation] = useState(null);
  const [tuningJob, setTuningJob] = useState(null);
  const [loading, setLoading] = useState(true);

  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USD');
  const [horizon, setHorizon] = useState(24);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bayesRes, transferRes, explainRes] = await Promise.all([
        fetch(`${API_URL}/api/ml-advanced/bayesian/models`),
        fetch(`${API_URL}/api/ml-advanced/transfer/available-models`),
        fetch(`${API_URL}/api/ml-advanced/explain/models`)
      ]);

      if (bayesRes.ok) {
        const data = await bayesRes.json();
        setBayesianModels(data.models || []);
      }
      if (transferRes.ok) {
        const data = await transferRes.json();
        setTransferModels(data.models || []);
      }
      if (explainRes.ok) {
        const data = await explainRes.json();
        setExplainModels(data.models || []);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getBayesianPrediction = async (modelId) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-advanced/bayesian/predict?model_id=${modelId}&symbol=${selectedSymbol}&horizon=${horizon}`, {
        method: 'POST'
      });
      if (res.ok) {
        setPredictions(await res.json());
        toast.success('Prediction generated with uncertainty bounds');
      }
    } catch (err) {
      toast.error('Failed to get prediction');
    }
  };

  const getShapExplanation = async (modelId) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-advanced/explain/shap?model_id=${modelId}&symbol=${selectedSymbol}`, {
        method: 'POST'
      });
      if (res.ok) {
        setShapExplanation(await res.json());
        toast.success('SHAP explanation generated');
      }
    } catch (err) {
      toast.error('Failed to get explanation');
    }
  };

  const getLimeExplanation = async (modelId) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-advanced/explain/lime?model_id=${modelId}&symbol=${selectedSymbol}`, {
        method: 'POST'
      });
      if (res.ok) {
        setLimeExplanation(await res.json());
        toast.success('LIME explanation generated');
      }
    } catch (err) {
      toast.error('Failed to get explanation');
    }
  };

  const startTuning = async (modelType) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-advanced/tuning/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_type: modelType,
          symbol: selectedSymbol,
          n_trials: 50,
          optimization_metric: 'sharpe_ratio'
        })
      });
      if (res.ok) {
        const data = await res.json();
        toast.success('Hyperparameter tuning started');
        // Poll for results
        setTimeout(() => getTuningResults(data.job_id), 3000);
      }
    } catch (err) {
      toast.error('Failed to start tuning');
    }
  };

  const getTuningResults = async (jobId) => {
    try {
      const res = await fetch(`${API_URL}/api/ml-advanced/tuning/status/${jobId}`);
      if (res.ok) {
        setTuningJob(await res.json());
      }
    } catch (err) {
      console.error('Error getting tuning results:', err);
    }
  };

  const symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'ARB/USD'];

  const tabs = [
    { id: 'bayesian', label: 'Bayesian Models', icon: Brain },
    { id: 'transfer', label: 'Transfer Learning', icon: GitBranch },
    { id: 'explain', label: 'Explainability', icon: Eye },
    { id: 'tuning', label: 'Hyperparameter Tuning', icon: Zap }
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 md:p-6" data-testid="ml-advanced-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
            <Sparkles className="text-[#00FF94]" />
            Advanced ML Features
          </h1>
          <p className="text-[#A1A1AA] mt-1">Bayesian networks, transfer learning, explainability</p>
        </div>
        <div className="flex gap-3">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-[#1F1F1F] border border-[#333] rounded-lg px-3 py-2 text-white"
          >
            {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button
            onClick={fetchData}
            className="p-2 bg-[#1F1F1F] border border-[#333] rounded-lg hover:bg-[#2a2a2a]"
          >
            <RefreshCw size={18} className={`text-[#A1A1AA] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition ${
              activeTab === tab.id
                ? 'bg-[#00FF94]/20 text-[#00FF94] border border-[#00FF94]/50'
                : 'bg-[#1F1F1F] text-[#A1A1AA] border border-transparent'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'bayesian' && (
          <motion.div
            key="bayesian"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Models */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {bayesianModels.map((model) => (
                <div
                  key={model.model_id}
                  className={`p-4 bg-[#1F1F1F]/50 border rounded-xl cursor-pointer transition ${
                    selectedModel === model.model_id ? 'border-[#00FF94]' : 'border-[#333] hover:border-[#555]'
                  }`}
                  onClick={() => setSelectedModel(model.model_id)}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Brain size={20} className="text-[#9D00FF]" />
                    <span className="text-white font-medium">{model.name}</span>
                  </div>
                  <p className="text-sm text-[#A1A1AA] mb-3">{model.description}</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-[#A1A1AA]">Calibration Error</p>
                      <p className="text-[#00FF94]">{model.metrics?.(mean_calibration_error ?? 0).toFixed(3)}</p>
                    </div>
                    <div>
                      <p className="text-[#A1A1AA]">90% Coverage</p>
                      <p className="text-white">{(model.metrics?.coverage_90 * 100)?.toFixed(1)}%</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      getBayesianPrediction(model.model_id);
                    }}
                    className="w-full mt-3 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30"
                  >
                    Get Prediction
                  </button>
                </div>
              ))}
            </div>

            {/* Predictions with Uncertainty */}
            {predictions && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <h3 className="text-white font-semibold mb-4">
                  Prediction with Uncertainty Bounds - {predictions.symbol}
                </h3>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={predictions.predictions}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis dataKey="hour" stroke="#A1A1AA" />
                      <YAxis stroke="#A1A1AA" domain={['auto', 'auto']} />
                      <Tooltip contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }} />
                      <Area
                        type="monotone"
                        dataKey="intervals.95%.upper"
                        stackId="1"
                        stroke="none"
                        fill="#9D00FF"
                        fillOpacity={0.1}
                      />
                      <Area
                        type="monotone"
                        dataKey="intervals.90%.upper"
                        stackId="2"
                        stroke="none"
                        fill="#9D00FF"
                        fillOpacity={0.15}
                      />
                      <Area
                        type="monotone"
                        dataKey="intervals.75%.upper"
                        stackId="3"
                        stroke="none"
                        fill="#9D00FF"
                        fillOpacity={0.2}
                      />
                      <Line
                        type="monotone"
                        dataKey="mean"
                        stroke="#00FF94"
                        strokeWidth={2}
                        dot={false}
                      />
                      <ReferenceLine y={predictions.current_price} stroke="#A1A1AA" strokeDasharray="5 5" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <p className="text-sm text-[#A1A1AA]">Expected Price</p>
                    <p className="text-xl font-bold text-white">${predictions.summary?.(expected_price ?? 0).toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <p className="text-sm text-[#A1A1AA]">Expected Return</p>
                    <p className={`text-xl font-bold ${predictions.summary?.expected_return >= 0 ? 'text-[#00FF94]' : 'text-red-400'}`}>
                      {predictions.summary?.expected_return >= 0 ? '+' : ''}{predictions.summary?.expected_return}%
                    </p>
                  </div>
                  <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <p className="text-sm text-[#A1A1AA]">Epistemic Uncertainty</p>
                    <p className="text-xl font-bold text-[#9D00FF]">${predictions.summary?.uncertainty_decomposition?.epistemic}</p>
                  </div>
                  <div className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                    <p className="text-sm text-[#A1A1AA]">Aleatoric Uncertainty</p>
                    <p className="text-xl font-bold text-yellow-400">${predictions.summary?.uncertainty_decomposition?.aleatoric}</p>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'transfer' && (
          <motion.div
            key="transfer"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {transferModels.map((model) => (
                <div key={model.model_id} className="p-4 bg-[#1F1F1F]/50 border border-[#333] rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <GitBranch size={20} className="text-[#00FF94]" />
                    <span className="text-white font-medium">{model.name}</span>
                  </div>
                  <p className="text-sm text-[#A1A1AA] mb-3">Architecture: {model.architecture}</p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {model.source_coins.map((coin) => (
                      <span key={coin} className="px-2 py-0.5 bg-[#333] text-white text-xs rounded">
                        {coin}
                      </span>
                    ))}
                  </div>
                  <div className="text-sm">
                    <p className="text-[#A1A1AA]">Transferable Layers: {model.transferable_layers}</p>
                    <p className="text-[#A1A1AA]">Embedding Dim: {model.embedding_dim}</p>
                  </div>
                  <button className="w-full mt-3 py-2 bg-[#00FF94]/20 text-[#00FF94] rounded-lg hover:bg-[#00FF94]/30">
                    Transfer to New Coin
                  </button>
                </div>
              ))}
            </div>

            {/* Transfer Learning Info */}
            <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4">About Transfer Learning</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="text-[#00FF94] font-medium mb-2">What it does</h4>
                  <p className="text-sm text-[#A1A1AA]">
                    Applies patterns learned from one cryptocurrency to another, 
                    reducing training time and improving performance on low-data coins.
                  </p>
                </div>
                <div>
                  <h4 className="text-[#00FF94] font-medium mb-2">Benefits</h4>
                  <ul className="text-sm text-[#A1A1AA] space-y-1">
                    <li>• 80% less training data needed</li>
                    <li>• 3x faster convergence</li>
                    <li>• Better generalization</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-[#00FF94] font-medium mb-2">Best for</h4>
                  <ul className="text-sm text-[#A1A1AA] space-y-1">
                    <li>• New coin listings</li>
                    <li>• Low-volume altcoins</li>
                    <li>• Cross-chain analysis</li>
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'explain' && (
          <motion.div
            key="explain"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Models */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {explainModels.map((model) => (
                <div key={model.model_id} className="p-4 bg-[#1F1F1F]/50 border border-[#333] rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <Eye size={20} className="text-[#9D00FF]" />
                    <span className="text-white font-medium">{model.name}</span>
                  </div>
                  <p className="text-sm text-[#A1A1AA] mb-2">{model.n_features} features</p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {model.explainability.map((method) => (
                      <span key={method} className="px-2 py-0.5 bg-[#9D00FF]/20 text-[#9D00FF] text-xs rounded">
                        {method.toUpperCase()}
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    {model.explainability.includes('shap') && (
                      <button
                        onClick={() => getShapExplanation(model.model_id)}
                        className="flex-1 py-2 bg-[#00FF94]/20 text-[#00FF94] text-sm rounded-lg hover:bg-[#00FF94]/30"
                      >
                        SHAP
                      </button>
                    )}
                    {model.explainability.includes('lime') && (
                      <button
                        onClick={() => getLimeExplanation(model.model_id)}
                        className="flex-1 py-2 bg-[#9D00FF]/20 text-[#9D00FF] text-sm rounded-lg hover:bg-[#9D00FF]/30"
                      >
                        LIME
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* SHAP Explanation */}
            {shapExplanation && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <h3 className="text-white font-semibold mb-4">SHAP Feature Importance</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={shapExplanation.top_features} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis type="number" stroke="#A1A1AA" />
                      <YAxis dataKey="feature" type="category" width={150} stroke="#A1A1AA" />
                      <Tooltip contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }} />
                      <Bar
                        dataKey="importance"
                        fill="#9D00FF"
                        radius={[0, 4, 4, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Interactions */}
                <div className="mt-4">
                  <h4 className="text-white font-medium mb-2">Feature Interactions</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {shapExplanation.feature_interactions?.map((int, i) => (
                      <div key={i} className="p-3 bg-[#0A0A0A] border border-[#333] rounded-lg">
                        <p className="text-sm text-white">{int.feature1} × {int.feature2}</p>
                        <p className="text-xs text-[#A1A1AA]">Interaction: {int.interaction_strength.toFixed(3)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* LIME Explanation */}
            {limeExplanation && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <h3 className="text-white font-semibold mb-4">LIME Local Explanation</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-[#A1A1AA] mb-2">Prediction</h4>
                    <div className="p-4 bg-[#0A0A0A] border border-[#333] rounded-lg">
                      <p className="text-3xl font-bold text-[#00FF94] capitalize">{limeExplanation.prediction?.class}</p>
                      <p className="text-[#A1A1AA]">Probability: {(limeExplanation.prediction?.probability * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-[#A1A1AA] mb-2">Summary</h4>
                    <p className="text-sm text-white">{limeExplanation.explanation_summary}</p>
                  </div>
                </div>
                
                <div className="mt-4">
                  <h4 className="text-white font-medium mb-2">Feature Contributions</h4>
                  <div className="space-y-2">
                    {limeExplanation.local_explanation?.map((contrib, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="w-40 text-sm text-[#A1A1AA] truncate">{contrib.feature}</span>
                        <div className="flex-1 h-4 bg-[#333] rounded-full overflow-hidden relative">
                          <div
                            className={`absolute top-0 h-full ${contrib.direction === 'positive' ? 'bg-[#00FF94] left-1/2' : 'bg-red-400 right-1/2'}`}
                            style={{ width: `${Math.abs(contrib.contribution) * 200}%` }}
                          />
                        </div>
                        <span className={`w-16 text-sm text-right ${contrib.direction === 'positive' ? 'text-[#00FF94]' : 'text-red-400'}`}>
                          {contrib.contribution >= 0 ? '+' : ''}{contrib.contribution.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'tuning' && (
          <motion.div
            key="tuning"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Start Tuning */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {['gradient_boosting', 'lstm', 'transformer'].map((modelType) => (
                <div key={modelType} className="p-4 bg-[#1F1F1F]/50 border border-[#333] rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap size={20} className="text-[#FF9500]" />
                    <span className="text-white font-medium capitalize">{modelType.replace('_', ' ')}</span>
                  </div>
                  <p className="text-sm text-[#A1A1AA] mb-3">
                    Automated hyperparameter optimization using Optuna
                  </p>
                  <button
                    onClick={() => startTuning(modelType)}
                    className="w-full py-2 bg-[#FF9500]/20 text-[#FF9500] rounded-lg hover:bg-[#FF9500]/30"
                  >
                    Start Tuning (50 trials)
                  </button>
                </div>
              ))}
            </div>

            {/* Tuning Results */}
            {tuningJob && (
              <div className="bg-[#1F1F1F]/50 border border-[#333] rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-semibold">Tuning Results</h3>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    tuningJob.status === 'completed' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {tuningJob.status}
                  </span>
                </div>

                {/* Optimization History */}
                <div className="h-64 mb-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={tuningJob.optimization_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis dataKey="trial" stroke="#A1A1AA" />
                      <YAxis stroke="#A1A1AA" />
                      <Tooltip contentStyle={{ backgroundColor: '#1F1F1F', border: '1px solid #333' }} />
                      <Line type="monotone" dataKey="score" stroke="#00FF94" dot={false} />
                      <ReferenceLine y={tuningJob.best_score} stroke="#9D00FF" strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Best Parameters */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-white font-medium mb-2">Best Parameters</h4>
                    <div className="space-y-2">
                      {tuningJob.best_params && Object.entries(tuningJob.best_params).map(([key, value]) => (
                        <div key={key} className="flex justify-between p-2 bg-[#0A0A0A] border border-[#333] rounded">
                          <span className="text-[#A1A1AA]">{key}</span>
                          <span className="text-white font-mono">{typeof value === 'number' ? value.toFixed(4) : value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-white font-medium mb-2">Parameter Importance</h4>
                    <div className="space-y-2">
                      {tuningJob.parameter_importance?.map((param) => (
                        <div key={param.param} className="flex items-center gap-2">
                          <span className="w-32 text-[#A1A1AA] text-sm">{param.param}</span>
                          <div className="flex-1 h-3 bg-[#333] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#FF9500]"
                              style={{ width: `${param.importance * 100}%` }}
                            />
                          </div>
                          <span className="text-white text-sm w-12">{(param.importance * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MLAdvanced;
