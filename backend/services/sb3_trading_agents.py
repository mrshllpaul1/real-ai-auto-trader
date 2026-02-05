"""
Stable-Baselines3 Trading Agents
================================
Professional-grade DRL agents using Stable-Baselines3 library.
Implements DQN, PPO, A2C, and SAC algorithms for crypto trading.

GitHub References:
- https://github.com/AI4Finance-Foundation/FinRL
- https://github.com/DLR-RM/stable-baselines3
- https://github.com/theanh97/Deep-Reinforcement-Learning-with-Stock-Trading
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import json
from collections import deque

logger = logging.getLogger(__name__)

# Gymnasium for custom environments
try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    logger.warning("Gymnasium not available")

# Stable-Baselines3 for DRL algorithms
try:
    from stable_baselines3 import DQN, PPO, A2C, SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
    from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, BaseCallback
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.evaluation import evaluate_policy
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    logger.warning("Stable-Baselines3 not available")

# TensorFlow for custom networks
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


# =============================================================================
# CUSTOM TRADING ENVIRONMENT (Gymnasium-compatible)
# =============================================================================

class CryptoTradingEnv(gym.Env):
    """
    Custom Gymnasium environment for crypto trading.
    Compatible with Stable-Baselines3 algorithms.
    
    Features:
    - Realistic transaction costs and slippage
    - Multi-feature observation space
    - Continuous action space for position sizing
    - Sharpe ratio-based reward function
    - Drawdown penalty for risk management
    """
    
    metadata = {'render_modes': ['human', 'ansi']}
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10000,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        max_position_pct: float = 0.25,
        window_size: int = 60,
        reward_scaling: float = 1e-4,
        sharpe_window: int = 24,  # Window for Sharpe ratio calculation
        reward_type: str = 'sharpe'  # 'sharpe', 'simple', 'sortino'
    ):
        super().__init__()
        
        self.df = df.reset_index(drop=True) if df is not None else pd.DataFrame()
        self.initial_balance = initial_balance
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_pct = max_position_pct
        self.window_size = window_size
        self.reward_scaling = reward_scaling
        self.sharpe_window = sharpe_window
        self.reward_type = reward_type
        
        # State variables
        self.balance = initial_balance
        self.position = 0.0  # Current position in base asset
        self.position_value = 0.0
        self.current_step = window_size
        self.total_pnl = 0.0
        self.trades = []
        self.portfolio_history = []
        
        # Sharpe ratio tracking
        self.returns_history = deque(maxlen=sharpe_window * 2)
        self.peak_value = initial_balance
        
        # Feature columns
        self.feature_cols = self._get_feature_columns()
        n_features = len(self.feature_cols) if self.feature_cols else 20
        
        # Observation space: [features, position_info, portfolio_info]
        # Features + position + balance_ratio + unrealized_pnl
        obs_dim = n_features + 4
        
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(obs_dim,), 
            dtype=np.float32
        )
        
        # Action space: continuous [-1, 1]
        # -1 = full short/sell, 0 = hold, 1 = full long/buy
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(1,), 
            dtype=np.float32
        )
    
    def _get_feature_columns(self) -> List[str]:
        """Get available feature columns from dataframe"""
        if self.df.empty:
            return []
        
        potential_features = [
            'close', 'open', 'high', 'low', 'volume',
            'returns', 'volatility', 'rsi', 'macd', 'macd_signal',
            'sma_10', 'sma_20', 'sma_50', 'ema_10', 'ema_20',
            'bb_upper', 'bb_lower', 'bb_middle', 'bb_width',
            'momentum_1', 'momentum_5', 'momentum_10',
            'atr', 'adx', 'obv', 'vwap'
        ]
        
        return [col for col in potential_features if col in self.df.columns]
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation"""
        if self.df.empty or self.current_step >= len(self.df):
            return np.zeros(self.observation_space.shape[0], dtype=np.float32)
        
        # Get features
        if self.feature_cols:
            features = self.df.loc[self.current_step, self.feature_cols].values.astype(np.float32)
        else:
            features = np.zeros(20, dtype=np.float32)
        
        # Normalize features
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Current price
        current_price = self.df.loc[self.current_step, 'close'] if 'close' in self.df.columns else 1.0
        
        # Portfolio info
        position_value = self.position * current_price
        total_value = self.balance + position_value
        
        portfolio_info = np.array([
            self.position / (self.initial_balance / current_price + 1e-8),  # Normalized position
            self.balance / self.initial_balance,  # Balance ratio
            position_value / (total_value + 1e-8),  # Position ratio
            (total_value - self.initial_balance) / self.initial_balance  # Total return
        ], dtype=np.float32)
        
        observation = np.concatenate([features, portfolio_info])
        return observation
    
    def _calculate_reward(self, prev_value: float, current_value: float, action: float) -> float:
        """Calculate reward using Sharpe ratio methodology"""
        # Base return
        pnl = current_value - prev_value
        ret = pnl / (prev_value + 1e-8)
        
        # Track returns for Sharpe calculation
        self.returns_history.append(ret)
        
        # Calculate rolling Sharpe ratio reward
        if len(self.returns_history) >= self.sharpe_window:
            recent_returns = np.array(list(self.returns_history)[-self.sharpe_window:])
            mean_return = np.mean(recent_returns)
            std_return = np.std(recent_returns) + 1e-8
            
            # Annualized Sharpe ratio (assuming hourly data)
            sharpe_ratio = np.sqrt(24 * 365) * mean_return / std_return
            
            # Sharpe-based reward component
            sharpe_reward = sharpe_ratio * 0.1  # Scale factor
        else:
            sharpe_reward = ret * 10  # Use simple return until enough data
        
        # Risk penalty for large positions
        position_ratio = abs(self.position * self._get_current_price()) / (current_value + 1e-8)
        risk_penalty = -0.1 * max(0, position_ratio - self.max_position_pct)
        
        # Transaction cost penalty
        action_penalty = -abs(action) * self.transaction_cost_pct * 0.5
        
        # Drawdown penalty
        if current_value > self.peak_value:
            self.peak_value = current_value
        drawdown = (self.peak_value - current_value) / (self.peak_value + 1e-8)
        drawdown_penalty = -drawdown * 0.5 if drawdown > 0.1 else 0  # Penalize >10% drawdown
        
        # Combined Sharpe-based reward
        reward = (sharpe_reward + risk_penalty + action_penalty + drawdown_penalty) * self.reward_scaling
        
        return float(reward)
    
    def _get_current_price(self) -> float:
        """Get current price"""
        if self.df.empty or self.current_step >= len(self.df):
            return 1.0
        return float(self.df.loc[self.current_step, 'close']) if 'close' in self.df.columns else 1.0
    
    def reset(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)
        
        self.balance = self.initial_balance
        self.position = 0.0
        self.position_value = 0.0
        self.current_step = self.window_size
        self.total_pnl = 0.0
        self.trades = []
        self.portfolio_history = []
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action: np.ndarray):
        """Execute one step in the environment"""
        action_value = float(action[0])
        current_price = self._get_current_price()
        
        # Calculate previous portfolio value
        prev_value = self.balance + self.position * current_price
        
        # Execute action
        target_position_value = action_value * self.max_position_pct * prev_value
        target_position = target_position_value / (current_price + 1e-8)
        
        position_change = target_position - self.position
        
        if abs(position_change) > 1e-8:
            # Apply transaction costs and slippage
            trade_value = abs(position_change) * current_price
            costs = trade_value * (self.transaction_cost_pct + self.slippage_pct)
            
            if position_change > 0:  # Buying
                # Apply slippage (worse price)
                effective_price = current_price * (1 + self.slippage_pct)
                actual_cost = position_change * effective_price + costs
                
                if actual_cost <= self.balance:
                    self.balance -= actual_cost
                    self.position += position_change
                    self.trades.append({
                        'step': self.current_step,
                        'action': 'buy',
                        'amount': position_change,
                        'price': effective_price,
                        'cost': costs
                    })
            else:  # Selling
                effective_price = current_price * (1 - self.slippage_pct)
                proceeds = abs(position_change) * effective_price - costs
                
                if self.position >= abs(position_change):
                    self.balance += proceeds
                    self.position += position_change  # Negative change
                    self.trades.append({
                        'step': self.current_step,
                        'action': 'sell',
                        'amount': abs(position_change),
                        'price': effective_price,
                        'cost': costs
                    })
        
        # Move to next step
        self.current_step += 1
        
        # Calculate new portfolio value
        new_price = self._get_current_price()
        current_value = self.balance + self.position * new_price
        
        # Calculate reward
        reward = self._calculate_reward(prev_value, current_value, action_value)
        
        # Track portfolio history
        self.portfolio_history.append({
            'step': self.current_step,
            'value': current_value,
            'balance': self.balance,
            'position': self.position,
            'price': new_price
        })
        
        # Check if done
        terminated = self.current_step >= len(self.df) - 1
        truncated = current_value <= self.initial_balance * 0.5  # Stop if 50% loss
        
        observation = self._get_observation()
        info = {
            'portfolio_value': current_value,
            'balance': self.balance,
            'position': self.position,
            'total_trades': len(self.trades),
            'return': (current_value - self.initial_balance) / self.initial_balance
        }
        
        return observation, reward, terminated, truncated, info
    
    def render(self, mode='human'):
        """Render current state"""
        current_price = self._get_current_price()
        value = self.balance + self.position * current_price
        ret = (value - self.initial_balance) / self.initial_balance * 100
        
        print(f"Step: {self.current_step} | Balance: ${self.balance:.2f} | "
              f"Position: {self.position:.6f} | Value: ${value:.2f} | Return: {ret:.2f}%")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.portfolio_history:
            return {}
        
        values = [h['value'] for h in self.portfolio_history]
        returns = np.diff(values) / (np.array(values[:-1]) + 1e-8)
        
        final_value = values[-1] if values else self.initial_balance
        total_return = (final_value - self.initial_balance) / self.initial_balance
        
        # Sharpe ratio (annualized, assuming hourly data)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = np.sqrt(365 * 24) * np.mean(returns) / np.std(returns)
        else:
            sharpe = 0
        
        # Max drawdown
        peak = np.maximum.accumulate(values)
        drawdown = (peak - values) / (peak + 1e-8)
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Win rate
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / max(len(self.trades), 1)
        
        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_drawdown),
            'total_trades': len(self.trades),
            'win_rate': float(win_rate),
            'final_value': float(final_value)
        }


# =============================================================================
# TRAINING CALLBACK
# =============================================================================

class TradingCallback(BaseCallback):
    """Custom callback for tracking training progress"""
    
    def __init__(self, check_freq: int = 1000, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.episode_rewards = []
        self.episode_lengths = []
        self.best_mean_reward = -np.inf
        
    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # Get recent rewards
            if len(self.episode_rewards) > 0:
                mean_reward = np.mean(self.episode_rewards[-100:])
                if self.verbose > 0:
                    logger.info(f"Step {self.n_calls}: Mean reward = {mean_reward:.4f}")
                
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
        return True
    
    def _on_rollout_end(self) -> None:
        if hasattr(self.model, 'ep_info_buffer') and len(self.model.ep_info_buffer) > 0:
            ep_info = self.model.ep_info_buffer[-1]
            if 'r' in ep_info:
                self.episode_rewards.append(ep_info['r'])
            if 'l' in ep_info:
                self.episode_lengths.append(ep_info['l'])


# =============================================================================
# SB3 TRADING AGENT MANAGER
# =============================================================================

class SB3TradingAgentManager:
    """
    Manager for Stable-Baselines3 trading agents.
    Supports DQN, PPO, A2C, and SAC algorithms.
    """
    
    def __init__(self, db, model_dir: str = "/app/backend/models/sb3"):
        self.db = db
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.agents: Dict[str, Any] = {}
        self.envs: Dict[str, Any] = {}
        self.training_history: Dict[str, List] = {}
        
        # Default hyperparameters for each algorithm
        self.default_params = {
            'dqn': {
                'learning_rate': 1e-4,
                'buffer_size': 100000,
                'learning_starts': 1000,
                'batch_size': 64,
                'tau': 0.005,
                'gamma': 0.99,
                'train_freq': 4,
                'target_update_interval': 1000,
                'exploration_fraction': 0.3,
                'exploration_initial_eps': 1.0,
                'exploration_final_eps': 0.05
            },
            'ppo': {
                'learning_rate': 3e-4,
                'n_steps': 2048,
                'batch_size': 64,
                'n_epochs': 10,
                'gamma': 0.99,
                'gae_lambda': 0.95,
                'clip_range': 0.2,
                'ent_coef': 0.01,
                'vf_coef': 0.5,
                'max_grad_norm': 0.5
            },
            'a2c': {
                'learning_rate': 7e-4,
                'n_steps': 5,
                'gamma': 0.99,
                'gae_lambda': 1.0,
                'ent_coef': 0.01,
                'vf_coef': 0.5,
                'max_grad_norm': 0.5
            },
            'sac': {
                'learning_rate': 3e-4,
                'buffer_size': 100000,
                'learning_starts': 1000,
                'batch_size': 256,
                'tau': 0.005,
                'gamma': 0.99,
                'ent_coef': 'auto',
                'target_entropy': 'auto'
            }
        }
    
    def create_env(self, df: pd.DataFrame, env_name: str = "default") -> gym.Env:
        """Create and register trading environment"""
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Gymnasium is required for SB3 agents")
        
        env = CryptoTradingEnv(df)
        env = Monitor(env)  # Wrap with Monitor for logging
        self.envs[env_name] = env
        
        return env
    
    def create_vectorized_env(
        self, 
        df: pd.DataFrame, 
        n_envs: int = 4,
        use_subproc: bool = False
    ) -> DummyVecEnv:
        """Create vectorized environment for parallel training"""
        if not SB3_AVAILABLE:
            raise ImportError("Stable-Baselines3 is required")
        
        def make_env():
            env = CryptoTradingEnv(df.copy())
            return Monitor(env)
        
        if use_subproc and n_envs > 1:
            vec_env = SubprocVecEnv([make_env for _ in range(n_envs)])
        else:
            vec_env = DummyVecEnv([make_env for _ in range(n_envs)])
        
        return vec_env
    
    def create_agent(
        self,
        algorithm: str,
        env: gym.Env,
        agent_name: str = None,
        custom_params: Dict = None
    ) -> Any:
        """Create a new SB3 agent"""
        if not SB3_AVAILABLE:
            raise ImportError("Stable-Baselines3 is required")
        
        algorithm = algorithm.lower()
        params = self.default_params.get(algorithm, {}).copy()
        
        if custom_params:
            params.update(custom_params)
        
        agent_name = agent_name or f"{algorithm}_agent"
        
        # Select algorithm
        if algorithm == 'dqn':
            # DQN requires discrete action space, create wrapper
            from gymnasium.spaces import Discrete
            
            class DiscreteActionWrapper(gym.ActionWrapper):
                def __init__(self, env):
                    super().__init__(env)
                    self.action_space = Discrete(5)  # sell_strong, sell, hold, buy, buy_strong
                    self._action_map = {
                        0: np.array([-1.0]),   # Strong sell
                        1: np.array([-0.5]),   # Sell
                        2: np.array([0.0]),    # Hold
                        3: np.array([0.5]),    # Buy
                        4: np.array([1.0])     # Strong buy
                    }
                
                def action(self, action):
                    return self._action_map[action]
            
            wrapped_env = DiscreteActionWrapper(env)
            agent = DQN("MlpPolicy", wrapped_env, verbose=1, **params)
            
        elif algorithm == 'ppo':
            agent = PPO("MlpPolicy", env, verbose=1, **params)
            
        elif algorithm == 'a2c':
            agent = A2C("MlpPolicy", env, verbose=1, **params)
            
        elif algorithm == 'sac':
            agent = SAC("MlpPolicy", env, verbose=1, **params)
            
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}. Use dqn, ppo, a2c, or sac")
        
        self.agents[agent_name] = {
            'model': agent,
            'algorithm': algorithm,
            'created_at': datetime.utcnow().isoformat(),
            'trained': False,
            'total_timesteps': 0
        }
        
        logger.info(f"Created {algorithm.upper()} agent: {agent_name}")
        return agent
    
    async def train_agent(
        self,
        agent_name: str,
        total_timesteps: int = 100000,
        eval_freq: int = 10000,
        save_freq: int = 25000
    ) -> Dict[str, Any]:
        """Train an agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent_info = self.agents[agent_name]
        model = agent_info['model']
        
        # Callbacks
        callbacks = []
        
        # Checkpoint callback
        checkpoint_callback = CheckpointCallback(
            save_freq=save_freq,
            save_path=os.path.join(self.model_dir, agent_name),
            name_prefix=agent_name
        )
        callbacks.append(checkpoint_callback)
        
        # Custom trading callback
        trading_callback = TradingCallback(check_freq=eval_freq)
        callbacks.append(trading_callback)
        
        # Train
        logger.info(f"Starting training for {agent_name} ({total_timesteps} timesteps)...")
        start_time = datetime.utcnow()
        
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True
        )
        
        end_time = datetime.utcnow()
        training_duration = (end_time - start_time).total_seconds()
        
        # Update agent info
        agent_info['trained'] = True
        agent_info['total_timesteps'] += total_timesteps
        agent_info['last_trained'] = end_time.isoformat()
        
        # Save final model
        model_path = os.path.join(self.model_dir, f"{agent_name}_final")
        model.save(model_path)
        agent_info['model_path'] = model_path
        
        # Record training history
        if agent_name not in self.training_history:
            self.training_history[agent_name] = []
        
        training_record = {
            'timestamp': end_time.isoformat(),
            'timesteps': total_timesteps,
            'duration_seconds': training_duration,
            'mean_reward': np.mean(trading_callback.episode_rewards[-100:]) if trading_callback.episode_rewards else 0,
            'best_reward': trading_callback.best_mean_reward
        }
        self.training_history[agent_name].append(training_record)
        
        logger.info(f"Training complete for {agent_name}. Duration: {training_duration:.1f}s")
        
        return training_record
    
    def predict(
        self,
        agent_name: str,
        observation: np.ndarray,
        deterministic: bool = True
    ) -> Tuple[int, np.ndarray]:
        """Get action from agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        model = self.agents[agent_name]['model']
        action, _ = model.predict(observation, deterministic=deterministic)
        
        return action
    
    def evaluate_agent(
        self,
        agent_name: str,
        env: gym.Env,
        n_eval_episodes: int = 10
    ) -> Dict[str, float]:
        """Evaluate agent performance"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        model = self.agents[agent_name]['model']
        
        mean_reward, std_reward = evaluate_policy(
            model, 
            env, 
            n_eval_episodes=n_eval_episodes,
            deterministic=True
        )
        
        return {
            'mean_reward': float(mean_reward),
            'std_reward': float(std_reward),
            'n_episodes': n_eval_episodes
        }
    
    def load_agent(self, agent_name: str, algorithm: str) -> Any:
        """Load a saved agent"""
        model_path = os.path.join(self.model_dir, f"{agent_name}_final.zip")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        algorithm = algorithm.lower()
        
        if algorithm == 'dqn':
            model = DQN.load(model_path)
        elif algorithm == 'ppo':
            model = PPO.load(model_path)
        elif algorithm == 'a2c':
            model = A2C.load(model_path)
        elif algorithm == 'sac':
            model = SAC.load(model_path)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.agents[agent_name] = {
            'model': model,
            'algorithm': algorithm,
            'loaded_from': model_path,
            'trained': True
        }
        
        logger.info(f"Loaded {algorithm.upper()} agent from {model_path}")
        return model
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        agent_statuses = {}
        for name, info in self.agents.items():
            agent_statuses[name] = {
                'algorithm': info.get('algorithm'),
                'trained': info.get('trained', False),
                'total_timesteps': info.get('total_timesteps', 0),
                'created_at': info.get('created_at'),
                'last_trained': info.get('last_trained')
            }
        
        return {
            'sb3_available': SB3_AVAILABLE,
            'gymnasium_available': GYMNASIUM_AVAILABLE,
            'agents': agent_statuses,
            'environments': list(self.envs.keys()),
            'model_directory': self.model_dir,
            'supported_algorithms': ['dqn', 'ppo', 'a2c', 'sac']
        }


# =============================================================================
# FEATURE ENGINEERING FOR SB3 ENVIRONMENTS
# =============================================================================

def prepare_training_data(price_data: List[Dict]) -> pd.DataFrame:
    """Prepare price data for SB3 environment"""
    df = pd.DataFrame(price_data)
    
    # Ensure required columns
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in df.columns:
            if col == 'close' and 'price' in df.columns:
                df['close'] = df['price']
            else:
                df[col] = df.get('close', 0)
    
    # Calculate returns
    df['returns'] = df['close'].pct_change().fillna(0)
    
    # Volatility
    df['volatility'] = df['returns'].rolling(20).std().fillna(0)
    
    # Moving averages
    for window in [10, 20, 50]:
        df[f'sma_{window}'] = df['close'].rolling(window).mean()
        df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-8)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12).mean()
    ema_26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    
    # Bollinger Bands
    bb_window = 20
    df['bb_middle'] = df['close'].rolling(bb_window).mean()
    bb_std = df['close'].rolling(bb_window).std()
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / (df['bb_middle'] + 1e-8)
    
    # Momentum
    for period in [1, 5, 10]:
        df[f'momentum_{period}'] = df['close'].pct_change(period)
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    
    # Fill NaN
    df = df.fillna(method='ffill').fillna(0)
    
    return df


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_manager_instance = None

def get_sb3_manager(db=None) -> SB3TradingAgentManager:
    """Get or create SB3 manager singleton"""
    global _manager_instance
    if _manager_instance is None and db is not None:
        _manager_instance = SB3TradingAgentManager(db)
    return _manager_instance


async def initialize_sb3_manager(db) -> SB3TradingAgentManager:
    """Initialize SB3 manager"""
    manager = get_sb3_manager(db)
    logger.info("SB3 Trading Agent Manager initialized")
    return manager
