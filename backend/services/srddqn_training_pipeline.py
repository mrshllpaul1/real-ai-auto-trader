"""
SRDDQN Advanced Training Pipeline
==================================
Comprehensive 6-phase training system based on MDPI research.

Phases:
1. Reward Modeling (Supervised Learning)
2. Reinforcement Learning (Double DQN + Hybrid Rewards)
3. Validation & Robustness Testing
4. Practical Deployment Considerations
5. Advanced Research Directions
6. Performance Attribution & Interpretability

Reference: Huang et al. (2024) - Self-Rewarding DRL for Trading
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import os
import json
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model, optimizers
    from tensorflow.keras.layers import Dense, Input, BatchNormalization, Dropout, LSTM, Attention
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class MarketRegime(Enum):
    """Market regime classification"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class RewardType(Enum):
    """Expert reward types for Phase 1"""
    MIN_MAX = "min_max"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"
    RETURN = "return"
    RISK_ADJUSTED = "risk_adjusted"


# =============================================================================
# PHASE 1: REWARD MODELING (Supervised Learning)
# =============================================================================

class RewardNetwork:
    """
    Phase 1: Supervised Reward Network
    Learns to predict expert-labeled rewards from state-action pairs.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 5,
        hidden_dims: List[int] = [256, 128, 64],
        learning_rate: float = 1e-4
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims
        
        # Build multi-head reward network (predicts multiple reward types)
        self.model = self._build_network()
        self.optimizer = optimizers.Adam(learning_rate=learning_rate)
        
        # Training history
        self.training_history = []
        self.expert_labels = []
        
    def _build_network(self) -> Model:
        """Build reward prediction network with multiple heads"""
        state_input = Input(shape=(self.state_dim,), name='state')
        action_input = Input(shape=(self.action_dim,), name='action')
        
        # Combine inputs
        combined = layers.concatenate([state_input, action_input])
        
        # Shared feature extraction
        x = combined
        for i, dim in enumerate(self.hidden_dims):
            x = Dense(dim, activation='relu', name=f'shared_{i}')(x)
            x = BatchNormalization()(x)
            x = Dropout(0.2)(x)
        
        # Multiple reward heads for different expert metrics
        sharpe_head = Dense(32, activation='relu')(x)
        sharpe_output = Dense(1, activation='tanh', name='sharpe_reward')(sharpe_head)
        
        return_head = Dense(32, activation='relu')(x)
        return_output = Dense(1, activation='tanh', name='return_reward')(return_head)
        
        risk_head = Dense(32, activation='relu')(x)
        risk_output = Dense(1, activation='tanh', name='risk_reward')(risk_head)
        
        # Confidence score
        confidence_head = Dense(32, activation='relu')(x)
        confidence_output = Dense(1, activation='sigmoid', name='confidence')(confidence_head)
        
        # Hybrid reward (weighted combination)
        hybrid_output = Dense(1, activation='tanh', name='hybrid_reward')(x)
        
        model = Model(
            inputs=[state_input, action_input],
            outputs=[sharpe_output, return_output, risk_output, confidence_output, hybrid_output],
            name='reward_network'
        )
        
        return model
    
    def compute_expert_rewards(
        self,
        returns: np.ndarray,
        window: int = 24
    ) -> Dict[str, float]:
        """Compute expert-labeled rewards"""
        if len(returns) < window:
            return {
                'sharpe': 0.0,
                'sortino': 0.0,
                'return': 0.0,
                'risk': 0.0
            }
        
        recent_returns = returns[-window:]
        mean_return = np.mean(recent_returns)
        std_return = np.std(recent_returns) + 1e-8
        
        # Sharpe Ratio (annualized)
        sharpe = np.sqrt(365 * 24) * mean_return / std_return
        
        # Sortino Ratio (downside deviation only)
        downside_returns = recent_returns[recent_returns < 0]
        downside_std = np.std(downside_returns) + 1e-8 if len(downside_returns) > 0 else 1e-8
        sortino = np.sqrt(365 * 24) * mean_return / downside_std
        
        # Total Return
        total_return = np.sum(recent_returns)
        
        # Risk metric (inverse of volatility)
        risk = -std_return * 10  # Negative because lower volatility is better
        
        return {
            'sharpe': np.clip(sharpe / 3, -1, 1),  # Normalize to [-1, 1]
            'sortino': np.clip(sortino / 3, -1, 1),
            'return': np.clip(total_return * 100, -1, 1),
            'risk': np.clip(risk, -1, 1)
        }
    
    def train_supervised(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        expert_rewards: Dict[str, np.ndarray],
        epochs: int = 10,
        batch_size: int = 64
    ) -> Dict[str, float]:
        """Phase 1: Train reward network with supervised learning"""
        # Convert actions to one-hot
        actions_onehot = np.zeros((len(actions), self.action_dim))
        for i, a in enumerate(actions):
            actions_onehot[i, int(a)] = 1.0
        
        # Prepare targets
        sharpe_targets = expert_rewards.get('sharpe', np.zeros(len(states))).reshape(-1, 1)
        return_targets = expert_rewards.get('return', np.zeros(len(states))).reshape(-1, 1)
        risk_targets = expert_rewards.get('risk', np.zeros(len(states))).reshape(-1, 1)
        
        # Confidence targets (higher for consistent rewards)
        confidence_targets = np.ones((len(states), 1)) * 0.8
        
        # Hybrid targets (weighted average)
        hybrid_targets = (0.5 * sharpe_targets + 0.3 * return_targets + 0.2 * risk_targets)
        
        losses = []
        for epoch in range(epochs):
            # Shuffle data
            indices = np.random.permutation(len(states))
            
            epoch_loss = 0
            n_batches = 0
            
            for i in range(0, len(states), batch_size):
                batch_idx = indices[i:i+batch_size]
                
                with tf.GradientTape() as tape:
                    outputs = self.model(
                        [states[batch_idx], actions_onehot[batch_idx]],
                        training=True
                    )
                    
                    # Multi-task loss
                    sharpe_loss = tf.reduce_mean(tf.square(outputs[0] - sharpe_targets[batch_idx]))
                    return_loss = tf.reduce_mean(tf.square(outputs[1] - return_targets[batch_idx]))
                    risk_loss = tf.reduce_mean(tf.square(outputs[2] - risk_targets[batch_idx]))
                    confidence_loss = tf.reduce_mean(tf.square(outputs[3] - confidence_targets[batch_idx]))
                    hybrid_loss = tf.reduce_mean(tf.square(outputs[4] - hybrid_targets[batch_idx]))
                    
                    total_loss = sharpe_loss + return_loss + risk_loss + 0.5 * confidence_loss + hybrid_loss
                
                gradients = tape.gradient(total_loss, self.model.trainable_variables)
                self.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))
                
                epoch_loss += float(total_loss)
                n_batches += 1
            
            avg_loss = epoch_loss / max(n_batches, 1)
            losses.append(avg_loss)
            
            if epoch % 5 == 0:
                logger.info(f"Reward Network - Epoch {epoch}: Loss = {avg_loss:.6f}")
        
        self.training_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'epochs': epochs,
            'final_loss': losses[-1] if losses else 0,
            'loss_history': losses
        })
        
        return {
            'final_loss': losses[-1] if losses else 0,
            'epochs_trained': epochs,
            'samples': len(states)
        }
    
    def predict_hybrid_reward(
        self,
        state: np.ndarray,
        action: int
    ) -> Tuple[float, float]:
        """Predict hybrid reward and confidence"""
        state = np.array(state).reshape(1, -1)
        action_onehot = np.zeros((1, self.action_dim))
        action_onehot[0, action] = 1.0
        
        outputs = self.model.predict([state, action_onehot], verbose=0)
        
        hybrid_reward = float(outputs[4][0, 0])
        confidence = float(outputs[3][0, 0])
        
        return hybrid_reward, confidence


# =============================================================================
# PHASE 2: REINFORCEMENT LEARNING (Double DQN + Hybrid Rewards)
# =============================================================================

class ReplayBuffer:
    """Experience Replay Buffer with prioritized sampling option"""
    
    def __init__(self, capacity: int = 100000, prioritized: bool = False):
        self.capacity = capacity
        self.prioritized = prioritized
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
        
    def push(self, experience: Dict, priority: float = 1.0):
        """Add experience to buffer"""
        self.buffer.append(experience)
        if self.prioritized:
            self.priorities.append(priority)
    
    def sample(self, batch_size: int) -> List[Dict]:
        """Sample batch from buffer"""
        if self.prioritized and len(self.priorities) > 0:
            # Prioritized sampling
            probs = np.array(self.priorities) / np.sum(self.priorities)
            indices = np.random.choice(len(self.buffer), batch_size, p=probs, replace=False)
        else:
            indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        
        return [self.buffer[i] for i in indices]
    
    def __len__(self):
        return len(self.buffer)


class Phase2Agent:
    """
    Phase 2: RL Agent with trained Reward Network
    Uses Double DQN with hybrid reward signal.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 5,
        reward_network: RewardNetwork = None,
        gamma: float = 0.99,
        tau: float = 0.005,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.02,
        epsilon_decay: float = 0.995
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.reward_network = reward_network
        self.gamma = gamma
        self.tau = tau
        
        # Epsilon-greedy parameters
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # Build Q-networks
        self.q_network = self._build_q_network()
        self.target_network = self._build_q_network()
        self.target_network.set_weights(self.q_network.get_weights())
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(capacity=100000, prioritized=True)
        
        # Optimizer
        self.optimizer = optimizers.Adam(learning_rate=1e-4)
        
        # Training stats
        self.training_steps = 0
        self.episode_rewards = []
        
    def _build_q_network(self) -> Model:
        """Build Dueling DQN architecture"""
        state_input = Input(shape=(self.state_dim,))
        
        # Feature extraction
        x = Dense(256, activation='relu')(state_input)
        x = BatchNormalization()(x)
        x = Dense(256, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dense(128, activation='relu')(x)
        
        # Dueling streams
        value = Dense(64, activation='relu')(x)
        value = Dense(1, name='value')(value)
        
        advantage = Dense(64, activation='relu')(x)
        advantage = Dense(self.action_dim, name='advantage')(advantage)
        
        # Q = V + (A - mean(A)) using Lambda layer for Keras compatibility
        def combine_streams(inputs):
            value_stream, advantage_stream = inputs
            return value_stream + (advantage_stream - keras.ops.mean(advantage_stream, axis=1, keepdims=True))
        
        q_values = layers.Lambda(combine_streams, name='q_values')([value, advantage])
        
        return Model(state_input, q_values, name='dueling_dqn')
    
    def select_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy action selection"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        state = np.array(state).reshape(1, -1)
        q_values = self.q_network.predict(state, verbose=0)[0]
        return int(np.argmax(q_values))
    
    def compute_hybrid_reward(
        self,
        state: np.ndarray,
        action: int,
        extrinsic_reward: float
    ) -> float:
        """Compute hybrid reward from reward network + extrinsic"""
        if self.reward_network is not None:
            intrinsic_reward, confidence = self.reward_network.predict_hybrid_reward(state, action)
            # Weighted combination
            hybrid = 0.6 * extrinsic_reward + 0.4 * intrinsic_reward * confidence
        else:
            hybrid = extrinsic_reward
        
        return hybrid
    
    def train_step(self, batch_size: int = 64) -> Dict[str, float]:
        """Single training step with Double DQN"""
        if len(self.replay_buffer) < batch_size:
            return {}
        
        batch = self.replay_buffer.sample(batch_size)
        
        states = np.array([e['state'] for e in batch])
        actions = np.array([e['action'] for e in batch])
        rewards = np.array([e['reward'] for e in batch])
        next_states = np.array([e['next_state'] for e in batch])
        dones = np.array([e['done'] for e in batch])
        
        with tf.GradientTape() as tape:
            # Current Q-values
            q_values = self.q_network(states, training=True)
            q_selected = tf.reduce_sum(
                q_values * tf.one_hot(actions, self.action_dim), axis=1
            )
            
            # Double DQN: use online network to select action
            next_q = self.q_network(next_states, training=False)
            next_actions = tf.argmax(next_q, axis=1)
            
            # Use target network to evaluate
            target_next_q = self.target_network(next_states, training=False)
            next_q_selected = tf.reduce_sum(
                target_next_q * tf.one_hot(next_actions, self.action_dim), axis=1
            )
            
            # Compute targets
            targets = rewards + self.gamma * next_q_selected * (1 - dones)
            
            # Huber loss
            loss = tf.reduce_mean(tf.keras.losses.huber(targets, q_selected))
        
        gradients = tape.gradient(loss, self.q_network.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.q_network.trainable_variables))
        
        # Soft update target network
        for target_var, var in zip(self.target_network.weights, self.q_network.weights):
            target_var.assign(self.tau * var + (1 - self.tau) * target_var)
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        self.training_steps += 1
        
        return {'loss': float(loss), 'epsilon': self.epsilon}


# =============================================================================
# PHASE 3: VALIDATION & ROBUSTNESS TESTING
# =============================================================================

class ValidationEngine:
    """
    Phase 3: Out-of-sample testing and robustness analysis
    """
    
    def __init__(self, agent: Phase2Agent):
        self.agent = agent
        self.test_results = []
        self.regime_performance = {}
        
    def classify_market_regime(self, returns: np.ndarray, window: int = 24) -> MarketRegime:
        """Classify current market regime"""
        if len(returns) < window:
            return MarketRegime.SIDEWAYS
        
        recent = returns[-window:]
        mean_return = np.mean(recent)
        volatility = np.std(recent)
        
        # Volatility thresholds
        if volatility > 0.03:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < 0.01:
            return MarketRegime.LOW_VOLATILITY
        
        # Trend thresholds
        if mean_return > 0.001:
            return MarketRegime.BULL
        elif mean_return < -0.001:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS
    
    def run_out_of_sample_test(
        self,
        test_env,
        n_episodes: int = 10
    ) -> Dict[str, Any]:
        """Run agent on unseen test data"""
        results = []
        
        for ep in range(n_episodes):
            state, _ = test_env.reset()
            episode_reward = 0
            episode_returns = []
            actions_taken = []
            
            done = False
            while not done:
                action = self.agent.select_action(state)
                actions_taken.append(action)
                
                next_state, reward, terminated, truncated, info = test_env.step(
                    np.array([self._action_to_continuous(action)])
                )
                done = terminated or truncated
                
                episode_reward += reward
                if 'return' in info:
                    episode_returns.append(info['return'])
                
                state = next_state
            
            results.append({
                'episode': ep,
                'total_reward': episode_reward,
                'final_return': info.get('return', 0),
                'n_trades': sum(1 for a in actions_taken if a != 2),  # Non-hold actions
                'action_distribution': {
                    'sell': actions_taken.count(0) + actions_taken.count(1),
                    'hold': actions_taken.count(2),
                    'buy': actions_taken.count(3) + actions_taken.count(4)
                }
            })
        
        # Aggregate results
        returns = [r['final_return'] for r in results]
        rewards = [r['total_reward'] for r in results]
        
        return {
            'n_episodes': n_episodes,
            'mean_return': float(np.mean(returns)),
            'std_return': float(np.std(returns)),
            'mean_reward': float(np.mean(rewards)),
            'sharpe_ratio': float(np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)),
            'max_drawdown': self._compute_max_drawdown(returns),
            'win_rate': sum(1 for r in returns if r > 0) / len(returns),
            'episodes': results
        }
    
    def test_market_regimes(
        self,
        env_factory,
        regime_data: Dict[MarketRegime, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Test performance across different market regimes"""
        regime_results = {}
        
        for regime, data in regime_data.items():
            env = env_factory(data)
            result = self.run_out_of_sample_test(env, n_episodes=5)
            regime_results[regime.value] = {
                'mean_return': result['mean_return'],
                'sharpe_ratio': result['sharpe_ratio'],
                'win_rate': result['win_rate']
            }
        
        self.regime_performance = regime_results
        return regime_results
    
    def sensitivity_analysis(
        self,
        test_env,
        param_ranges: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Analyze sensitivity to hyperparameters"""
        results = {}
        
        original_epsilon = self.agent.epsilon
        
        for param, values in param_ranges.items():
            param_results = []
            
            for value in values:
                # Temporarily modify parameter
                if param == 'epsilon':
                    self.agent.epsilon = value
                elif param == 'gamma':
                    self.agent.gamma = value
                
                # Run test
                result = self.run_out_of_sample_test(test_env, n_episodes=3)
                param_results.append({
                    'value': value,
                    'mean_return': result['mean_return'],
                    'sharpe': result['sharpe_ratio']
                })
            
            results[param] = param_results
        
        # Restore original
        self.agent.epsilon = original_epsilon
        
        return results
    
    def benchmark_comparison(
        self,
        test_env,
        price_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compare against baseline strategies"""
        # Agent performance
        agent_result = self.run_out_of_sample_test(test_env, n_episodes=5)
        
        # Buy and Hold
        if 'close' in price_data.columns:
            prices = price_data['close'].values
            buy_hold_return = (prices[-1] - prices[0]) / prices[0]
        else:
            buy_hold_return = 0
        
        # Simple Moving Average Crossover
        sma_return = self._simulate_sma_crossover(price_data)
        
        return {
            'srddqn': {
                'return': agent_result['mean_return'],
                'sharpe': agent_result['sharpe_ratio'],
                'win_rate': agent_result['win_rate']
            },
            'buy_hold': {
                'return': buy_hold_return,
                'sharpe': 0,  # N/A for buy-hold
                'win_rate': 1.0 if buy_hold_return > 0 else 0.0
            },
            'sma_crossover': {
                'return': sma_return,
                'sharpe': 0,
                'win_rate': 0.5  # Placeholder
            }
        }
    
    def _action_to_continuous(self, action: int) -> float:
        return {0: -1.0, 1: -0.5, 2: 0.0, 3: 0.5, 4: 1.0}.get(action, 0.0)
    
    def _compute_max_drawdown(self, returns: List[float]) -> float:
        if not returns:
            return 0
        cumulative = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / (peak + 1e-8)
        return float(np.max(drawdown))
    
    def _simulate_sma_crossover(self, data: pd.DataFrame) -> float:
        if 'close' not in data.columns or len(data) < 50:
            return 0
        
        prices = data['close'].values
        sma_10 = pd.Series(prices).rolling(10).mean().values
        sma_50 = pd.Series(prices).rolling(50).mean().values
        
        position = 0
        returns = []
        
        for i in range(50, len(prices) - 1):
            if sma_10[i] > sma_50[i] and position <= 0:
                position = 1
            elif sma_10[i] < sma_50[i] and position >= 0:
                position = -1
            
            ret = position * (prices[i+1] - prices[i]) / prices[i]
            returns.append(ret)
        
        return float(np.sum(returns)) if returns else 0


# =============================================================================
# PHASE 4: DEPLOYMENT CONSIDERATIONS
# =============================================================================

class DeploymentConfig:
    """
    Phase 4: Practical deployment settings and safety guards
    """
    
    def __init__(self):
        # Transaction costs
        self.maker_fee = 0.001  # 0.1%
        self.taker_fee = 0.002  # 0.2%
        self.slippage = 0.0005  # 0.05%
        
        # Risk limits
        self.max_position_size = 0.25  # 25% of portfolio
        self.max_daily_loss = 0.05  # 5% daily stop
        self.max_drawdown = 0.15  # 15% max drawdown
        
        # Position limits
        self.max_trades_per_hour = 10
        self.min_trade_interval_seconds = 60
        
        # Circuit breakers
        self.volatility_threshold = 0.05  # 5% hourly volatility
        self.consecutive_loss_limit = 5
        
    def to_dict(self) -> Dict:
        return {
            'transaction_costs': {
                'maker_fee': self.maker_fee,
                'taker_fee': self.taker_fee,
                'slippage': self.slippage
            },
            'risk_limits': {
                'max_position_size': self.max_position_size,
                'max_daily_loss': self.max_daily_loss,
                'max_drawdown': self.max_drawdown
            },
            'position_limits': {
                'max_trades_per_hour': self.max_trades_per_hour,
                'min_trade_interval_seconds': self.min_trade_interval_seconds
            },
            'circuit_breakers': {
                'volatility_threshold': self.volatility_threshold,
                'consecutive_loss_limit': self.consecutive_loss_limit
            }
        }


class SafetyGuard:
    """Runtime safety checks for live trading"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.trades_this_hour = 0
        self.last_trade_time = None
        self.peak_value = 0
        self.current_value = 0
        
    def check_trade_allowed(
        self,
        action: int,
        current_position: float,
        portfolio_value: float,
        current_volatility: float
    ) -> Tuple[bool, str]:
        """Check if trade is allowed based on safety rules"""
        
        # Update tracking
        self.current_value = portfolio_value
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        
        # Check circuit breakers
        if current_volatility > self.config.volatility_threshold:
            return False, "High volatility circuit breaker triggered"
        
        if self.consecutive_losses >= self.config.consecutive_loss_limit:
            return False, "Consecutive loss limit reached"
        
        # Check daily loss limit
        if self.daily_pnl < -self.config.max_daily_loss * self.peak_value:
            return False, "Daily loss limit reached"
        
        # Check drawdown
        drawdown = (self.peak_value - self.current_value) / self.peak_value
        if drawdown > self.config.max_drawdown:
            return False, "Maximum drawdown exceeded"
        
        # Check trade frequency
        if self.trades_this_hour >= self.config.max_trades_per_hour:
            return False, "Hourly trade limit reached"
        
        if self.last_trade_time:
            elapsed = (datetime.utcnow() - self.last_trade_time).total_seconds()
            if elapsed < self.config.min_trade_interval_seconds:
                return False, f"Min trade interval not met ({elapsed:.0f}s < {self.config.min_trade_interval_seconds}s)"
        
        # Check position size
        if action != 2:  # Not hold
            if abs(current_position) > self.config.max_position_size:
                return False, "Position size limit reached"
        
        return True, "Trade allowed"
    
    def record_trade(self, pnl: float):
        """Record trade result"""
        self.daily_pnl += pnl
        self.last_trade_time = datetime.utcnow()
        self.trades_this_hour += 1
        
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def reset_daily(self):
        """Reset daily counters"""
        self.daily_pnl = 0
        self.trades_this_hour = 0


# =============================================================================
# PHASE 5: ADVANCED RESEARCH DIRECTIONS
# =============================================================================

class AttentionQNetwork(Model):
    """
    Advanced: Transformer-style attention for Q-network
    Captures long-range dependencies in market series
    """
    
    def __init__(self, state_dim: int, action_dim: int, seq_length: int = 24):
        super().__init__()
        
        self.seq_length = seq_length
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Embedding
        self.embedding = Dense(64, activation='relu')
        
        # Multi-head attention
        self.attention = layers.MultiHeadAttention(
            num_heads=4,
            key_dim=64,
            dropout=0.1
        )
        
        # Feed-forward
        self.ffn = keras.Sequential([
            Dense(128, activation='relu'),
            Dropout(0.1),
            Dense(64)
        ])
        
        # Layer normalization
        self.norm1 = layers.LayerNormalization()
        self.norm2 = layers.LayerNormalization()
        
        # Output layers
        self.value_head = Dense(1)
        self.advantage_head = Dense(action_dim)
    
    def call(self, x, training=False):
        # Reshape for sequence processing
        batch_size = tf.shape(x)[0]
        x = tf.reshape(x, [batch_size, self.seq_length, -1])
        
        # Embedding
        x = self.embedding(x)
        
        # Self-attention
        attn_output = self.attention(x, x, training=training)
        x = self.norm1(x + attn_output)
        
        # Feed-forward
        ffn_output = self.ffn(x, training=training)
        x = self.norm2(x + ffn_output)
        
        # Flatten
        x = tf.reshape(x, [batch_size, -1])
        
        # Dueling architecture
        value = self.value_head(x)
        advantage = self.advantage_head(x)
        
        q_values = value + (advantage - tf.reduce_mean(advantage, axis=1, keepdims=True))
        return q_values


class HierarchicalRewardShaper:
    """
    Advanced: Combine dense and sparse rewards
    """
    
    def __init__(self):
        self.milestones = [0.01, 0.05, 0.10, 0.20, 0.50]  # Return milestones
        self.milestone_rewards = [0.1, 0.2, 0.3, 0.5, 1.0]
        self.achieved_milestones = set()
        
    def compute_reward(
        self,
        dense_reward: float,  # Sharpe-based
        total_return: float,
        step: int
    ) -> float:
        """Combine dense and sparse milestone rewards"""
        # Dense component
        reward = dense_reward
        
        # Sparse milestone bonuses
        for i, milestone in enumerate(self.milestones):
            if total_return >= milestone and i not in self.achieved_milestones:
                reward += self.milestone_rewards[i]
                self.achieved_milestones.add(i)
        
        return reward
    
    def reset(self):
        self.achieved_milestones = set()


# =============================================================================
# PHASE 6: PERFORMANCE ATTRIBUTION & INTERPRETABILITY
# =============================================================================

class PerformanceAttributor:
    """
    Phase 6: Strategy analysis and explainability
    """
    
    def __init__(self, agent: Phase2Agent):
        self.agent = agent
        self.decision_log = []
        self.feature_importance = {}
        
    def log_decision(
        self,
        state: np.ndarray,
        action: int,
        q_values: np.ndarray,
        market_conditions: Dict
    ):
        """Log trading decision for later analysis"""
        self.decision_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'state': state.tolist() if isinstance(state, np.ndarray) else state,
            'action': action,
            'action_name': ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy'][action],
            'q_values': q_values.tolist() if isinstance(q_values, np.ndarray) else q_values,
            'market_conditions': market_conditions
        })
    
    def analyze_strategy(self) -> Dict[str, Any]:
        """Analyze what conditions the agent exploits"""
        if not self.decision_log:
            return {}
        
        # Action distribution
        actions = [d['action'] for d in self.decision_log]
        action_dist = {
            'sell': (actions.count(0) + actions.count(1)) / len(actions),
            'hold': actions.count(2) / len(actions),
            'buy': (actions.count(3) + actions.count(4)) / len(actions)
        }
        
        # Analyze conditions for each action type
        buy_conditions = [d for d in self.decision_log if d['action'] in [3, 4]]
        sell_conditions = [d for d in self.decision_log if d['action'] in [0, 1]]
        
        return {
            'action_distribution': action_dist,
            'total_decisions': len(self.decision_log),
            'buy_signal_count': len(buy_conditions),
            'sell_signal_count': len(sell_conditions),
            'strategy_type': self._classify_strategy(action_dist)
        }
    
    def _classify_strategy(self, action_dist: Dict) -> str:
        """Classify the agent's strategy style"""
        if action_dist['buy'] > 0.6:
            return "Aggressive Long"
        elif action_dist['sell'] > 0.6:
            return "Aggressive Short"
        elif action_dist['hold'] > 0.5:
            return "Conservative/Passive"
        elif action_dist['buy'] > action_dist['sell']:
            return "Momentum/Trend Following"
        else:
            return "Mean Reversion"
    
    def compute_feature_importance(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Compute simple feature importance via permutation"""
        base_q_values = self.agent.q_network.predict(states, verbose=0)
        base_selected = np.array([q[a] for q, a in zip(base_q_values, actions)])
        
        importance = {}
        
        for i, name in enumerate(feature_names):
            # Permute feature
            permuted_states = states.copy()
            np.random.shuffle(permuted_states[:, i])
            
            # Compute Q-values with permuted feature
            permuted_q = self.agent.q_network.predict(permuted_states, verbose=0)
            permuted_selected = np.array([q[a] for q, a in zip(permuted_q, actions)])
            
            # Importance = drop in Q-value
            importance[name] = float(np.mean(base_selected - permuted_selected))
        
        # Normalize
        max_imp = max(abs(v) for v in importance.values()) + 1e-8
        importance = {k: v / max_imp for k, v in importance.items()}
        
        self.feature_importance = importance
        return importance
    
    def failure_analysis(self, loss_threshold: float = -0.02) -> List[Dict]:
        """Identify and analyze failure cases"""
        failures = []
        
        for i, decision in enumerate(self.decision_log):
            # Check if this decision led to a loss
            if i < len(self.decision_log) - 1:
                # Simplified: check if next state shows loss
                market = decision.get('market_conditions', {})
                if market.get('pnl', 0) < loss_threshold:
                    failures.append({
                        'decision': decision,
                        'loss': market.get('pnl', 0),
                        'market_regime': market.get('regime', 'unknown'),
                        'possible_cause': self._diagnose_failure(decision, market)
                    })
        
        return failures[:10]  # Return top 10 failures
    
    def _diagnose_failure(self, decision: Dict, market: Dict) -> str:
        """Diagnose potential cause of failure"""
        action = decision['action']
        
        if action in [3, 4] and market.get('trend', 'neutral') == 'bearish':
            return "Bought in bearish market"
        elif action in [0, 1] and market.get('trend', 'neutral') == 'bullish':
            return "Sold in bullish market"
        elif market.get('volatility', 0) > 0.03:
            return "High volatility environment"
        else:
            return "Unknown - requires further analysis"
    
    def get_interpretability_report(self) -> Dict[str, Any]:
        """Generate full interpretability report"""
        strategy_analysis = self.analyze_strategy()
        
        return {
            'strategy_analysis': strategy_analysis,
            'feature_importance': self.feature_importance,
            'total_logged_decisions': len(self.decision_log),
            'model_type': 'SRDDQN (Self-Rewarding Double DQN)',
            'interpretability_methods': [
                'Action distribution analysis',
                'Market condition correlation',
                'Permutation feature importance',
                'Failure case analysis'
            ]
        }


# =============================================================================
# MASTER TRAINING PIPELINE
# =============================================================================

class SRDDQNTrainingPipeline:
    """
    Master pipeline orchestrating all 6 phases
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 5,
        model_dir: str = "/app/backend/models/srddqn_pipeline"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize components
        self.reward_network = RewardNetwork(state_dim, action_dim)
        self.agent = None
        self.validation_engine = None
        self.deployment_config = DeploymentConfig()
        self.safety_guard = None
        self.performance_attributor = None
        self.hierarchical_shaper = HierarchicalRewardShaper()
        
        # Training state
        self.current_phase = 0
        self.phase_results = {}
        self.training_complete = False
        
    async def run_phase_1(
        self,
        training_data: pd.DataFrame,
        epochs: int = 20
    ) -> Dict[str, Any]:
        """Phase 1: Reward Modeling"""
        logger.info("=== PHASE 1: Reward Modeling ===")
        
        # Prepare expert labels
        states, actions, expert_rewards = self._prepare_expert_data(training_data)
        
        # Train reward network
        result = self.reward_network.train_supervised(
            states, actions, expert_rewards, epochs=epochs
        )
        
        self.phase_results['phase_1'] = result
        self.current_phase = 1
        
        logger.info(f"Phase 1 complete: Loss = {result['final_loss']:.6f}")
        return result
    
    async def run_phase_2(
        self,
        env,
        episodes: int = 100
    ) -> Dict[str, Any]:
        """Phase 2: Reinforcement Learning"""
        logger.info("=== PHASE 2: Reinforcement Learning ===")
        
        # Initialize agent with trained reward network
        self.agent = Phase2Agent(
            self.state_dim,
            self.action_dim,
            reward_network=self.reward_network
        )
        
        episode_results = []
        
        for ep in range(episodes):
            state, _ = env.reset()
            episode_reward = 0
            
            done = False
            while not done:
                action = self.agent.select_action(state)
                
                next_state, extrinsic_reward, terminated, truncated, info = env.step(
                    np.array([self._action_to_continuous(action)])
                )
                done = terminated or truncated
                
                # Compute hybrid reward
                hybrid_reward = self.agent.compute_hybrid_reward(
                    state, action, extrinsic_reward
                )
                
                # Store in replay buffer
                self.agent.replay_buffer.push({
                    'state': state,
                    'action': action,
                    'reward': hybrid_reward,
                    'next_state': next_state,
                    'done': done
                })
                
                # Train
                self.agent.train_step()
                
                episode_reward += hybrid_reward
                state = next_state
            
            episode_results.append({
                'episode': ep,
                'reward': episode_reward,
                'epsilon': self.agent.epsilon
            })
            
            if ep % 10 == 0:
                logger.info(f"Episode {ep}: Reward = {episode_reward:.4f}, Epsilon = {self.agent.epsilon:.4f}")
        
        result = {
            'episodes': episodes,
            'final_epsilon': self.agent.epsilon,
            'mean_reward': float(np.mean([r['reward'] for r in episode_results[-20:]])),
            'episode_history': episode_results[-20:]
        }
        
        self.phase_results['phase_2'] = result
        self.current_phase = 2
        
        return result
    
    async def run_phase_3(
        self,
        test_env,
        regime_data: Dict = None
    ) -> Dict[str, Any]:
        """Phase 3: Validation & Robustness Testing"""
        logger.info("=== PHASE 3: Validation & Robustness ===")
        
        self.validation_engine = ValidationEngine(self.agent)
        
        # Out-of-sample testing
        oos_results = self.validation_engine.run_out_of_sample_test(test_env)
        
        # Sensitivity analysis
        sensitivity = self.validation_engine.sensitivity_analysis(
            test_env,
            {'epsilon': [0.01, 0.05, 0.1, 0.2]}
        )
        
        result = {
            'out_of_sample': oos_results,
            'sensitivity_analysis': sensitivity,
            'passed_validation': oos_results['sharpe_ratio'] > 0.5
        }
        
        self.phase_results['phase_3'] = result
        self.current_phase = 3
        
        return result
    
    def run_phase_4(self) -> Dict[str, Any]:
        """Phase 4: Deployment Configuration"""
        logger.info("=== PHASE 4: Deployment Configuration ===")
        
        self.safety_guard = SafetyGuard(self.deployment_config)
        
        result = {
            'deployment_config': self.deployment_config.to_dict(),
            'safety_guards_enabled': True,
            'ready_for_deployment': self.current_phase >= 3
        }
        
        self.phase_results['phase_4'] = result
        self.current_phase = 4
        
        return result
    
    def run_phase_5(self) -> Dict[str, Any]:
        """Phase 5: Advanced Features (research directions)"""
        logger.info("=== PHASE 5: Advanced Features ===")
        
        result = {
            'hierarchical_reward_shaping': True,
            'attention_network_available': True,
            'features': [
                'Hierarchical reward (dense + sparse)',
                'Attention-based Q-network option',
                'Human-in-the-loop capability'
            ]
        }
        
        self.phase_results['phase_5'] = result
        self.current_phase = 5
        
        return result
    
    def run_phase_6(self) -> Dict[str, Any]:
        """Phase 6: Performance Attribution & Interpretability"""
        logger.info("=== PHASE 6: Interpretability ===")
        
        self.performance_attributor = PerformanceAttributor(self.agent)
        
        result = {
            'interpretability_enabled': True,
            'available_analyses': [
                'Strategy deconstruction',
                'Feature importance (permutation)',
                'Failure case analysis',
                'Market condition correlation'
            ]
        }
        
        self.phase_results['phase_6'] = result
        self.current_phase = 6
        self.training_complete = True
        
        return result
    
    def _action_to_continuous(self, action: int) -> float:
        return {0: -1.0, 1: -0.5, 2: 0.0, 3: 0.5, 4: 1.0}.get(action, 0.0)
    
    def _prepare_expert_data(
        self,
        data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """Prepare data with expert labels for Phase 1"""
        # Extract features as states
        feature_cols = [c for c in data.columns if c not in ['timestamp', 'date']][:self.state_dim]
        
        if len(feature_cols) < self.state_dim:
            # Pad with zeros
            states = np.zeros((len(data), self.state_dim))
            states[:, :len(feature_cols)] = data[feature_cols].fillna(0).values
        else:
            states = data[feature_cols[:self.state_dim]].fillna(0).values
        
        # Generate pseudo-actions (based on price movement)
        if 'close' in data.columns:
            returns = data['close'].pct_change().fillna(0).values
            actions = np.digitize(returns, [-0.02, -0.005, 0.005, 0.02])  # Map to 0-4
        else:
            actions = np.random.randint(0, 5, len(data))
        
        # Compute expert rewards
        expert_rewards = {
            'sharpe': np.zeros(len(data)),
            'return': np.zeros(len(data)),
            'risk': np.zeros(len(data))
        }
        
        if 'close' in data.columns:
            returns_series = data['close'].pct_change().fillna(0).values
            
            for i in range(24, len(data)):
                recent = returns_series[i-24:i]
                mean_r = np.mean(recent)
                std_r = np.std(recent) + 1e-8
                
                expert_rewards['sharpe'][i] = np.clip(mean_r / std_r * 10, -1, 1)
                expert_rewards['return'][i] = np.clip(np.sum(recent) * 50, -1, 1)
                expert_rewards['risk'][i] = np.clip(-std_r * 100, -1, 1)
        
        return states, actions, expert_rewards
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            'current_phase': self.current_phase,
            'training_complete': self.training_complete,
            'phases': {
                1: 'Reward Modeling (Supervised)',
                2: 'Reinforcement Learning (Double DQN)',
                3: 'Validation & Robustness',
                4: 'Deployment Configuration',
                5: 'Advanced Features',
                6: 'Interpretability'
            },
            'phase_results': self.phase_results,
            'model_directory': self.model_dir
        }
    
    def save(self):
        """Save all models and state"""
        # Save reward network
        self.reward_network.model.save(os.path.join(self.model_dir, 'reward_network.keras'))
        
        # Save Q-networks
        if self.agent:
            self.agent.q_network.save(os.path.join(self.model_dir, 'q_network.keras'))
            self.agent.target_network.save(os.path.join(self.model_dir, 'target_network.keras'))
        
        # Save state
        state = {
            'current_phase': self.current_phase,
            'training_complete': self.training_complete,
            'phase_results': self.phase_results,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim
        }
        
        with open(os.path.join(self.model_dir, 'pipeline_state.json'), 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Pipeline saved to {self.model_dir}")


# Singleton
_pipeline = None

def get_training_pipeline(state_dim: int = 24) -> SRDDQNTrainingPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = SRDDQNTrainingPipeline(state_dim)
    return _pipeline
