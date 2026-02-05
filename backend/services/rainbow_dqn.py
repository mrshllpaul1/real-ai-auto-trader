"""
Rainbow DQN with Transformer Encoder
=====================================
State-of-the-art DRL combining:
1. C51 Distributional RL (51 atoms)
2. Double DQN
3. Dueling Architecture
4. Noisy Networks
5. Prioritized Experience Replay
6. Multi-step Learning (n-step returns)
7. Causal Transformer State Encoder (168 timesteps)

References:
- Rainbow: https://arxiv.org/abs/1710.02298
- C51: https://arxiv.org/abs/1707.06887
- Transformers: https://arxiv.org/abs/1706.03762
"""

import logging
import numpy as np
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model, optimizers
    from tensorflow.keras.layers import (
        Dense, Input, LayerNormalization, Dropout,
        MultiHeadAttention, Add, Embedding
    )
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available")


# =============================================================================
# NOISY LINEAR LAYER (From previous implementation)
# =============================================================================

class NoisyDense(layers.Layer):
    """Factorized Gaussian Noisy Layer for exploration"""
    
    def __init__(self, units, sigma_init=0.5, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.sigma_init = sigma_init
        
    def build(self, input_shape):
        self.input_dim = input_shape[-1]
        mu_range = 1.0 / np.sqrt(float(self.input_dim))
        
        self.w_mu = self.add_weight(
            name='w_mu',
            shape=(self.input_dim, self.units),
            initializer=tf.keras.initializers.RandomUniform(-mu_range, mu_range),
            trainable=True
        )
        self.w_sigma = self.add_weight(
            name='w_sigma',
            shape=(self.input_dim, self.units),
            initializer=tf.keras.initializers.Constant(self.sigma_init / np.sqrt(float(self.input_dim))),
            trainable=True
        )
        self.b_mu = self.add_weight(
            name='b_mu',
            shape=(self.units,),
            initializer=tf.keras.initializers.RandomUniform(-mu_range, mu_range),
            trainable=True
        )
        self.b_sigma = self.add_weight(
            name='b_sigma',
            shape=(self.units,),
            initializer=tf.keras.initializers.Constant(self.sigma_init / np.sqrt(float(self.units))),
            trainable=True
        )
        
    def _scale_noise(self, size):
        x = tf.random.normal([size])
        return tf.sign(x) * tf.sqrt(tf.abs(x))
    
    def call(self, inputs, training=None):
        if training:
            epsilon_in = self._scale_noise(self.input_dim)
            epsilon_out = self._scale_noise(self.units)
            w_epsilon = tf.tensordot(epsilon_in, epsilon_out, axes=0)
            b_epsilon = epsilon_out
            w = self.w_mu + self.w_sigma * w_epsilon
            b = self.b_mu + self.b_sigma * b_epsilon
        else:
            w = self.w_mu
            b = self.b_mu
        return tf.matmul(inputs, w) + b


# =============================================================================
# CAUSAL TRANSFORMER ENCODER (168 timesteps)
# =============================================================================

class PositionalEncoding(layers.Layer):
    """Sinusoidal positional encoding for transformer"""
    
    def __init__(self, max_len: int = 168, d_model: int = 128, **kwargs):
        super().__init__(**kwargs)
        self.max_len = max_len
        self.d_model = d_model
        
    def build(self, input_shape):
        position = np.arange(self.max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, self.d_model, 2) * (-np.log(10000.0) / self.d_model))
        
        pe = np.zeros((self.max_len, self.d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        self.pe = tf.constant(pe, dtype=tf.float32)
        
    def call(self, x):
        seq_len = tf.shape(x)[1]
        return x + self.pe[:seq_len, :]


class CausalTransformerBlock(layers.Layer):
    """Single causal transformer block with masked self-attention"""
    
    def __init__(
        self,
        d_model: int = 128,
        num_heads: int = 8,
        ff_dim: int = 256,
        dropout: float = 0.1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout
        
    def build(self, input_shape):
        self.attention = MultiHeadAttention(
            num_heads=self.num_heads,
            key_dim=self.d_model // self.num_heads,
            dropout=self.dropout_rate
        )
        self.ffn = keras.Sequential([
            Dense(self.ff_dim, activation='gelu'),
            Dropout(self.dropout_rate),
            Dense(self.d_model),
            Dropout(self.dropout_rate)
        ])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(self.dropout_rate)
        self.dropout2 = Dropout(self.dropout_rate)
        
    def call(self, x, training=None):
        # Create causal mask
        seq_len = tf.shape(x)[1]
        causal_mask = tf.linalg.band_part(
            tf.ones((seq_len, seq_len)), -1, 0
        )
        
        # Multi-head self-attention with causal mask
        attn_output = self.attention(
            query=x, value=x, key=x,
            attention_mask=causal_mask,
            training=training
        )
        attn_output = self.dropout1(attn_output, training=training)
        x = self.layernorm1(x + attn_output)
        
        # Feed-forward
        ffn_output = self.ffn(x, training=training)
        x = self.layernorm2(x + ffn_output)
        
        return x


class CausalTransformerEncoder(layers.Layer):
    """
    Causal Transformer Encoder for time-series state encoding.
    
    Processes 168 timesteps (1 week) of market data including
    order book features and OHLCV.
    """
    
    def __init__(
        self,
        sequence_length: int = 168,
        input_dim: int = 45,  # Order book features
        d_model: int = 128,
        num_heads: int = 8,
        num_layers: int = 4,
        ff_dim: int = 256,
        dropout: float = 0.1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.sequence_length = sequence_length
        self.input_dim = input_dim
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.ff_dim = ff_dim
        self.dropout_rate = dropout
        
    def build(self, input_shape):
        # Input projection
        self.input_projection = Dense(self.d_model, name='input_proj')
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(
            max_len=self.sequence_length,
            d_model=self.d_model
        )
        
        # Transformer blocks
        self.transformer_blocks = [
            CausalTransformerBlock(
                d_model=self.d_model,
                num_heads=self.num_heads,
                ff_dim=self.ff_dim,
                dropout=self.dropout_rate,
                name=f'transformer_block_{i}'
            )
            for i in range(self.num_layers)
        ]
        
        # Output projection
        self.output_norm = LayerNormalization(epsilon=1e-6)
        self.output_projection = Dense(self.d_model, name='output_proj')
        
    def call(self, x, training=None):
        """
        Args:
            x: Input tensor of shape (batch, sequence_length, input_dim)
        Returns:
            Encoded representation of shape (batch, d_model)
        """
        # Project input to d_model dimensions
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Pass through transformer blocks
        for block in self.transformer_blocks:
            x = block(x, training=training)
        
        # Take the last timestep output (causal - can only see past)
        x = x[:, -1, :]
        
        # Final normalization and projection
        x = self.output_norm(x)
        x = self.output_projection(x)
        
        return x


# =============================================================================
# C51 DISTRIBUTIONAL DQN
# =============================================================================

class C51Distribution:
    """
    C51 Categorical Distribution for Distributional RL.
    
    Instead of predicting E[Q(s,a)], we predict a distribution over returns.
    Uses 51 atoms to approximate the value distribution.
    """
    
    def __init__(
        self,
        v_min: float = -10.0,
        v_max: float = 10.0,
        n_atoms: int = 51
    ):
        self.v_min = v_min
        self.v_max = v_max
        self.n_atoms = n_atoms
        
        # Atom values (support)
        self.delta_z = (v_max - v_min) / (n_atoms - 1)
        self.support = np.linspace(v_min, v_max, n_atoms).astype(np.float32)
        self.support_tf = tf.constant(self.support)
    
    def project_distribution(
        self,
        next_dist: tf.Tensor,
        rewards: tf.Tensor,
        dones: tf.Tensor,
        gamma: float
    ) -> tf.Tensor:
        """
        Project target distribution onto support.
        
        Args:
            next_dist: Next state distribution (batch, n_atoms)
            rewards: Rewards (batch,)
            dones: Done flags (batch,)
            gamma: Discount factor
        
        Returns:
            Projected distribution (batch, n_atoms)
        """
        batch_size = tf.shape(rewards)[0]
        
        # Compute Tz (Bellman projection)
        rewards = tf.cast(rewards, tf.float32)
        dones = tf.cast(dones, tf.float32)
        
        Tz = rewards[:, None] + gamma * (1 - dones[:, None]) * self.support_tf[None, :]
        Tz = tf.clip_by_value(Tz, self.v_min, self.v_max)
        
        # Compute projection
        b = (Tz - self.v_min) / self.delta_z
        lower = tf.floor(b)
        upper = tf.math.ceil(b)
        
        # Handle edge cases
        lower = tf.clip_by_value(lower, 0, self.n_atoms - 1)
        upper = tf.clip_by_value(upper, 0, self.n_atoms - 1)
        
        # Distribute probability
        l_idx = tf.cast(lower, tf.int32)
        u_idx = tf.cast(upper, tf.int32)
        
        # Create projected distribution
        m = tf.zeros((batch_size, self.n_atoms))
        
        # Lower bound contribution
        l_offset = (u - b) * next_dist
        u_offset = (b - l) * next_dist
        
        # Use scatter_nd for projection
        batch_indices = tf.repeat(
            tf.range(batch_size)[:, None], self.n_atoms, axis=1
        )
        
        l_indices = tf.stack([batch_indices, l_idx], axis=-1)
        u_indices = tf.stack([batch_indices, u_idx], axis=-1)
        
        m = tf.tensor_scatter_nd_add(m, l_indices, l_offset)
        m = tf.tensor_scatter_nd_add(m, u_indices, u_offset)
        
        return m
    
    def get_q_values(self, distribution: tf.Tensor) -> tf.Tensor:
        """
        Get Q-values from distribution.
        Q(s,a) = sum(p_i * z_i) = expected value
        """
        return tf.reduce_sum(distribution * self.support_tf, axis=-1)


# =============================================================================
# RAINBOW DQN AGENT
# =============================================================================

class RainbowDQN:
    """
    Rainbow DQN with all components:
    1. C51 Distributional RL (51 atoms)
    2. Double DQN
    3. Dueling Architecture
    4. Noisy Networks
    5. Prioritized Experience Replay
    6. Multi-step Learning
    7. Causal Transformer Encoder
    """
    
    def __init__(
        self,
        state_dim: int = 45,  # Order book features per timestep
        action_dim: int = 5,
        sequence_length: int = 168,  # 1 week
        # C51 parameters
        v_min: float = -10.0,
        v_max: float = 10.0,
        n_atoms: int = 51,
        # Training parameters
        gamma: float = 0.99,
        n_step: int = 3,
        learning_rate: float = 1e-4,
        tau: float = 0.005,
        buffer_size: int = 100000,
        batch_size: int = 32,
        # Transformer parameters
        d_model: int = 128,
        num_heads: int = 8,
        num_transformer_layers: int = 4,
        ff_dim: int = 256,
        dropout: float = 0.1,
        model_dir: str = "/app/backend/models/rainbow"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.sequence_length = sequence_length
        self.gamma = gamma
        self.n_step = n_step
        self.tau = tau
        self.batch_size = batch_size
        self.model_dir = model_dir
        
        os.makedirs(model_dir, exist_ok=True)
        
        # C51 Distribution
        self.c51 = C51Distribution(v_min, v_max, n_atoms)
        self.n_atoms = n_atoms
        
        # Build networks
        self.online_network = self._build_network(
            state_dim, action_dim, sequence_length,
            d_model, num_heads, num_transformer_layers, ff_dim, dropout,
            n_atoms
        )
        self.target_network = self._build_network(
            state_dim, action_dim, sequence_length,
            d_model, num_heads, num_transformer_layers, ff_dim, dropout,
            n_atoms,
            noisy=False  # Target network doesn't need noise
        )
        self.target_network.set_weights(self.online_network.get_weights())
        
        # Optimizer
        self.optimizer = optimizers.Adam(learning_rate=learning_rate)
        
        # Prioritized Replay Buffer
        self.replay_buffer = PrioritizedNStepBuffer(
            capacity=buffer_size,
            n_step=n_step,
            gamma=gamma
        )
        
        # Training stats
        self.training_steps = 0
        self.total_timesteps = 0
        
        logger.info(f"Rainbow DQN initialized: seq_len={sequence_length}, atoms={n_atoms}")
    
    def _build_network(
        self,
        state_dim: int,
        action_dim: int,
        sequence_length: int,
        d_model: int,
        num_heads: int,
        num_layers: int,
        ff_dim: int,
        dropout: float,
        n_atoms: int,
        noisy: bool = True
    ) -> Model:
        """Build Rainbow network with Transformer encoder"""
        
        # Input: sequence of order book features
        state_input = Input(
            shape=(sequence_length, state_dim),
            name='state_sequence'
        )
        
        # Transformer encoder
        encoder = CausalTransformerEncoder(
            sequence_length=sequence_length,
            input_dim=state_dim,
            d_model=d_model,
            num_heads=num_heads,
            num_layers=num_layers,
            ff_dim=ff_dim,
            dropout=dropout
        )
        
        encoded = encoder(state_input)
        
        # Dueling streams with distributional output
        if noisy:
            # Value stream
            value = NoisyDense(d_model, name='value_noisy_1')(encoded)
            value = tf.nn.relu(value)
            value = NoisyDense(n_atoms, name='value_dist')(value)  # (batch, n_atoms)
            
            # Advantage stream
            advantage = NoisyDense(d_model, name='advantage_noisy_1')(encoded)
            advantage = tf.nn.relu(advantage)
            advantage = NoisyDense(action_dim * n_atoms, name='advantage_dist')(advantage)
            advantage = tf.reshape(advantage, (-1, action_dim, n_atoms))  # (batch, actions, atoms)
        else:
            value = Dense(d_model, activation='relu', name='value_1')(encoded)
            value = Dense(n_atoms, name='value_dist')(value)
            
            advantage = Dense(d_model, activation='relu', name='advantage_1')(encoded)
            advantage = Dense(action_dim * n_atoms, name='advantage_dist')(advantage)
            advantage = tf.reshape(advantage, (-1, action_dim, n_atoms))
        
        # Expand value for broadcasting
        value = tf.expand_dims(value, axis=1)  # (batch, 1, atoms)
        
        # Dueling combination: Q(s,a) = V(s) + A(s,a) - mean(A(s,:))
        q_dist = value + (advantage - tf.reduce_mean(advantage, axis=1, keepdims=True))
        
        # Softmax over atoms for each action
        q_dist = tf.nn.softmax(q_dist, axis=-1)  # (batch, actions, atoms)
        
        return Model(state_input, q_dist, name='rainbow_dqn')
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using distributional Q-values"""
        # Ensure correct shape (1, seq_len, state_dim)
        if state.ndim == 2:
            state = state[np.newaxis, ...]
        
        # Get distribution for all actions
        q_dist = self.online_network(state, training=training)
        
        # Compute Q-values from distributions
        q_values = self.c51.get_q_values(q_dist)  # (1, action_dim)
        
        return int(tf.argmax(q_values[0]).numpy())
    
    def train_step(self) -> Dict[str, float]:
        """Perform one training step"""
        if len(self.replay_buffer) < self.batch_size:
            return {}
        
        # Sample from PER
        batch, indices, weights = self.replay_buffer.sample(self.batch_size)
        
        states = np.array([t['state'] for t in batch])
        actions = np.array([t['action'] for t in batch])
        rewards = np.array([t['n_step_reward'] for t in batch])
        next_states = np.array([t['next_state'] for t in batch])
        dones = np.array([t['done'] for t in batch])
        
        weights = tf.constant(weights, dtype=tf.float32)
        
        with tf.GradientTape() as tape:
            # Current distributions
            current_dist = self.online_network(states, training=True)
            
            # Select distributions for taken actions
            action_indices = tf.stack([
                tf.range(self.batch_size),
                tf.cast(actions, tf.int32)
            ], axis=1)
            current_action_dist = tf.gather_nd(current_dist, action_indices)
            
            # Double DQN: use online network for action selection
            next_dist_online = self.online_network(next_states, training=False)
            next_q_online = self.c51.get_q_values(next_dist_online)
            next_actions = tf.argmax(next_q_online, axis=1)
            
            # Use target network for evaluation
            next_dist_target = self.target_network(next_states, training=False)
            next_action_indices = tf.stack([
                tf.range(self.batch_size),
                tf.cast(next_actions, tf.int32)
            ], axis=1)
            next_action_dist = tf.gather_nd(next_dist_target, next_action_indices)
            
            # Project distribution (n-step with gamma^n)
            gamma_n = self.gamma ** self.n_step
            target_dist = self.c51.project_distribution(
                next_action_dist, rewards, dones, gamma_n
            )
            
            # Cross-entropy loss
            loss = -tf.reduce_sum(
                target_dist * tf.math.log(current_action_dist + 1e-8),
                axis=-1
            )
            
            # Weighted loss for PER
            weighted_loss = tf.reduce_mean(weights * loss)
        
        # Update priorities
        td_errors = loss.numpy()
        self.replay_buffer.update_priorities(indices, td_errors)
        
        # Gradient update
        gradients = tape.gradient(weighted_loss, self.online_network.trainable_variables)
        self.optimizer.apply_gradients(
            zip(gradients, self.online_network.trainable_variables)
        )
        
        # Soft update target network
        for target_var, var in zip(
            self.target_network.weights,
            self.online_network.weights
        ):
            target_var.assign(self.tau * var + (1 - self.tau) * target_var)
        
        self.training_steps += 1
        
        return {
            'loss': float(weighted_loss),
            'mean_q': float(tf.reduce_mean(self.c51.get_q_values(current_dist))),
            'mean_td_error': float(np.mean(td_errors))
        }
    
    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store transition in n-step buffer"""
        self.replay_buffer.push({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done
        })
        self.total_timesteps += 1
    
    def save(self, path: str = None):
        """Save model"""
        path = path or self.model_dir
        self.online_network.save(os.path.join(path, 'rainbow_online.keras'))
        self.target_network.save(os.path.join(path, 'rainbow_target.keras'))
        
        config = {
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'sequence_length': self.sequence_length,
            'n_atoms': self.n_atoms,
            'training_steps': self.training_steps,
            'total_timesteps': self.total_timesteps
        }
        with open(os.path.join(path, 'rainbow_config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Rainbow DQN saved to {path}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'type': 'Rainbow DQN',
            'components': [
                'C51 Distributional (51 atoms)',
                'Double DQN',
                'Dueling Architecture',
                'Noisy Networks',
                'Prioritized Experience Replay',
                f'Multi-step Learning (n={self.n_step})',
                f'Causal Transformer ({self.sequence_length} timesteps)'
            ],
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'sequence_length': self.sequence_length,
            'n_atoms': self.n_atoms,
            'training_steps': self.training_steps,
            'total_timesteps': self.total_timesteps,
            'buffer_size': len(self.replay_buffer)
        }


# =============================================================================
# N-STEP PRIORITIZED REPLAY BUFFER
# =============================================================================

class PrioritizedNStepBuffer:
    """
    Prioritized Experience Replay with N-step returns.
    """
    
    def __init__(
        self,
        capacity: int = 100000,
        n_step: int = 3,
        gamma: float = 0.99,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_frames: int = 100000
    ):
        self.capacity = capacity
        self.n_step = n_step
        self.gamma = gamma
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_frames = beta_frames
        self.frame = 1
        
        # N-step buffer
        self.n_step_buffer = deque(maxlen=n_step)
        
        # Main buffer with sum tree
        self.tree_capacity = 1
        while self.tree_capacity < capacity:
            self.tree_capacity *= 2
        
        self.sum_tree = np.zeros(2 * self.tree_capacity)
        self.data = [None] * self.tree_capacity
        
        self.size = 0
        self.position = 0
        self.max_priority = 1.0
    
    def _compute_n_step_return(self) -> Tuple[float, np.ndarray, bool]:
        """Compute n-step return from buffer"""
        n_step_return = 0.0
        
        for i, transition in enumerate(self.n_step_buffer):
            n_step_return += (self.gamma ** i) * transition['reward']
        
        # Next state is from the last transition
        last = self.n_step_buffer[-1]
        
        return n_step_return, last['next_state'], last['done']
    
    def push(self, transition: Dict):
        """Add transition with n-step processing"""
        self.n_step_buffer.append(transition)
        
        if len(self.n_step_buffer) < self.n_step:
            return
        
        # Compute n-step return
        n_step_reward, next_state, done = self._compute_n_step_return()
        
        # Store n-step transition
        n_step_transition = {
            'state': self.n_step_buffer[0]['state'],
            'action': self.n_step_buffer[0]['action'],
            'n_step_reward': n_step_reward,
            'next_state': next_state,
            'done': done
        }
        
        # Add to sum tree with max priority
        priority = self.max_priority ** self.alpha
        
        self.data[self.position] = n_step_transition
        self._update_tree(self.position, priority)
        
        self.position = (self.position + 1) % self.tree_capacity
        self.size = min(self.size + 1, self.capacity)
    
    def _update_tree(self, idx: int, priority: float):
        """Update sum tree"""
        tree_idx = idx + self.tree_capacity
        self.sum_tree[tree_idx] = priority
        
        while tree_idx > 1:
            tree_idx //= 2
            left = 2 * tree_idx
            right = left + 1
            self.sum_tree[tree_idx] = self.sum_tree[left] + self.sum_tree[right]
    
    def sample(self, batch_size: int):
        """Sample batch with priorities"""
        indices = []
        weights = []
        
        beta = min(1.0, self.beta_start + self.frame * (1.0 - self.beta_start) / self.beta_frames)
        self.frame += 1
        
        total_priority = self.sum_tree[1]
        segment = total_priority / batch_size
        
        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            value = np.random.uniform(a, b)
            
            idx = self._sample_idx(value)
            if idx >= self.size:
                idx = np.random.randint(0, self.size)
            
            indices.append(idx)
            
            prob = self.sum_tree[idx + self.tree_capacity] / total_priority
            weight = (prob * self.size) ** (-beta)
            weights.append(weight)
        
        max_weight = max(weights)
        weights = [w / max_weight for w in weights]
        
        batch = [self.data[i] for i in indices]
        
        return batch, np.array(indices), np.array(weights)
    
    def _sample_idx(self, value: float) -> int:
        """Sample index from sum tree"""
        idx = 1
        while idx < self.tree_capacity:
            left = 2 * idx
            if value <= self.sum_tree[left]:
                idx = left
            else:
                value -= self.sum_tree[left]
                idx = left + 1
        return idx - self.tree_capacity
    
    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Update priorities based on TD-errors"""
        for idx, td_error in zip(indices, td_errors):
            priority = (abs(td_error) + 1e-6) ** self.alpha
            self.max_priority = max(self.max_priority, priority)
            self._update_tree(idx, priority)
    
    def __len__(self):
        return self.size


# =============================================================================
# SINGLETON
# =============================================================================

_rainbow_agent: Optional[RainbowDQN] = None

def get_rainbow_agent(
    state_dim: int = 45,
    action_dim: int = 5,
    sequence_length: int = 168
) -> RainbowDQN:
    """Get or create Rainbow DQN agent"""
    global _rainbow_agent
    if _rainbow_agent is None:
        _rainbow_agent = RainbowDQN(
            state_dim=state_dim,
            action_dim=action_dim,
            sequence_length=sequence_length
        )
    return _rainbow_agent
