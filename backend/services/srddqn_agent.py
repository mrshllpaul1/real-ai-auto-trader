"""
Self-Rewarding Double Deep Q-Network (SRDDQN)
=============================================
Advanced DRL agent that combines Double DQN with self-rewarding mechanism.
Based on Huang et al. (2024) "A Self-Rewarding Mechanism in Deep Reinforcement Learning"

Features:
- Self-reward predictor network for intrinsic motivation
- Expert knowledge integration
- Curiosity-driven exploration
- Adaptive reward shaping for sparse reward environments

Reference: https://www.mdpi.com/2227-7390/12/24/4020
"""

import logging
import numpy as np
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import deque
import json

logger = logging.getLogger(__name__)

# TensorFlow/Keras for neural networks
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model, optimizers
    from tensorflow.keras.layers import Dense, Input, BatchNormalization, Dropout, concatenate
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available for SRDDQN")


# =============================================================================
# NOISY LINEAR LAYER (MDPI Recommendation: Parameter-Space Exploration)
# =============================================================================

class NoisyDense(layers.Layer):
    """
    Noisy Linear Layer for parameter-space exploration.
    
    Instead of ε-greedy random actions (which are costly in financial trading),
    we add learnable noise to network weights. The network learns when to explore.
    
    Reference: "Noisy Networks for Exploration" (Fortunato et al., 2018)
    """
    
    def __init__(self, units, sigma_init=0.5, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.sigma_init = sigma_init
        
    def build(self, input_shape):
        self.input_dim = input_shape[-1]
        
        # Factorized Gaussian noise (more efficient)
        mu_range = 1.0 / np.sqrt(float(self.input_dim))
        
        # Mean weights
        self.w_mu = self.add_weight(
            name='w_mu',
            shape=(self.input_dim, self.units),
            initializer=tf.keras.initializers.RandomUniform(-mu_range, mu_range),
            trainable=True
        )
        
        # Noise weights (sigma)
        self.w_sigma = self.add_weight(
            name='w_sigma',
            shape=(self.input_dim, self.units),
            initializer=tf.keras.initializers.Constant(self.sigma_init / np.sqrt(float(self.input_dim))),
            trainable=True
        )
        
        # Mean bias
        self.b_mu = self.add_weight(
            name='b_mu',
            shape=(self.units,),
            initializer=tf.keras.initializers.RandomUniform(-mu_range, mu_range),
            trainable=True
        )
        
        # Noise bias (sigma)
        self.b_sigma = self.add_weight(
            name='b_sigma',
            shape=(self.units,),
            initializer=tf.keras.initializers.Constant(self.sigma_init / np.sqrt(float(self.units))),
            trainable=True
        )
        
    def _scale_noise(self, size):
        """Factorized Gaussian noise"""
        x = tf.random.normal([size])
        return tf.sign(x) * tf.sqrt(tf.abs(x))
    
    def call(self, inputs, training=None):
        if training:
            # Generate factorized noise
            epsilon_in = self._scale_noise(self.input_dim)
            epsilon_out = self._scale_noise(self.units)
            
            # Outer product for weight noise
            w_epsilon = tf.tensordot(epsilon_in, epsilon_out, axes=0)
            b_epsilon = epsilon_out
            
            # Add noise to weights
            w = self.w_mu + self.w_sigma * w_epsilon
            b = self.b_mu + self.b_sigma * b_epsilon
        else:
            # No noise during inference
            w = self.w_mu
            b = self.b_mu
        
        return tf.matmul(inputs, w) + b
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'units': self.units,
            'sigma_init': self.sigma_init
        })
        return config


class SelfRewardPredictor:
    """
    Self-Reward Predictor Network
    Generates intrinsic rewards based on state-action pairs to guide exploration.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dims: List[int] = [128, 64, 32],
        learning_rate: float = 1e-4
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        
        self.model = self._build_network()
        self.optimizer = optimizers.Adam(learning_rate=learning_rate)
        
        # History for tracking predictions
        self.prediction_history = deque(maxlen=1000)
        self.reward_scale = 1.0
        
    def _build_network(self) -> Model:
        """Build self-reward predictor network"""
        # State input
        state_input = Input(shape=(self.state_dim,), name='state_input')
        
        # Action input (one-hot encoded)
        action_input = Input(shape=(self.action_dim,), name='action_input')
        
        # Combine state and action
        combined = concatenate([state_input, action_input])
        
        # Hidden layers with batch normalization
        x = combined
        for i, dim in enumerate(self.hidden_dims):
            x = Dense(dim, activation='relu', name=f'hidden_{i}')(x)
            x = BatchNormalization()(x)
            x = Dropout(0.1)(x)
        
        # Output: predicted intrinsic reward
        reward_output = Dense(1, activation='tanh', name='reward_output')(x)
        
        # Confidence output (how certain the predictor is)
        confidence_output = Dense(1, activation='sigmoid', name='confidence_output')(x)
        
        model = Model(
            inputs=[state_input, action_input],
            outputs=[reward_output, confidence_output],
            name='self_reward_predictor'
        )
        
        return model
    
    def predict_reward(self, state: np.ndarray, action: int) -> Tuple[float, float]:
        """Predict intrinsic reward for state-action pair"""
        state = np.array(state).reshape(1, -1)
        action_onehot = np.zeros((1, self.action_dim))
        action_onehot[0, action] = 1.0
        
        reward, confidence = self.model.predict([state, action_onehot], verbose=0)
        
        intrinsic_reward = float(reward[0, 0]) * self.reward_scale
        conf = float(confidence[0, 0])
        
        self.prediction_history.append({
            'reward': intrinsic_reward,
            'confidence': conf
        })
        
        return intrinsic_reward, conf
    
    def train_step(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        target_rewards: np.ndarray
    ) -> float:
        """Train the self-reward predictor"""
        # Convert actions to one-hot
        actions_onehot = np.zeros((len(actions), self.action_dim))
        for i, a in enumerate(actions):
            actions_onehot[i, int(a)] = 1.0
        
        with tf.GradientTape() as tape:
            pred_rewards, confidence = self.model([states, actions_onehot], training=True)
            
            # MSE loss for reward prediction
            reward_loss = tf.reduce_mean(tf.square(pred_rewards - target_rewards))
            
            # Encourage high confidence on accurate predictions
            accuracy = 1.0 - tf.abs(pred_rewards - target_rewards)
            confidence_loss = tf.reduce_mean(tf.square(confidence - accuracy))
            
            total_loss = reward_loss + 0.1 * confidence_loss
        
        gradients = tape.gradient(total_loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.model.trainable_variables))
        
        return float(total_loss)
    
    def update_reward_scale(self, scale: float):
        """Dynamically adjust reward scaling"""
        self.reward_scale = np.clip(scale, 0.1, 2.0)
    
    def get_stats(self) -> Dict[str, float]:
        """Get predictor statistics"""
        if not self.prediction_history:
            return {'mean_reward': 0, 'mean_confidence': 0}
        
        rewards = [p['reward'] for p in self.prediction_history]
        confidences = [p['confidence'] for p in self.prediction_history]
        
        return {
            'mean_reward': float(np.mean(rewards)),
            'std_reward': float(np.std(rewards)),
            'mean_confidence': float(np.mean(confidences)),
            'reward_scale': self.reward_scale
        }


class CuriosityModule:
    """
    Intrinsic Curiosity Module (ICM) for exploration bonus.
    Predicts next state given current state and action.
    Prediction error = curiosity = intrinsic reward.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        feature_dim: int = 64,
        learning_rate: float = 1e-4
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.feature_dim = feature_dim
        
        # Feature encoder
        self.encoder = self._build_encoder()
        
        # Forward model: predicts next state features
        self.forward_model = self._build_forward_model()
        
        # Inverse model: predicts action from state pair
        self.inverse_model = self._build_inverse_model()
        
        self.optimizer = optimizers.Adam(learning_rate=learning_rate)
        self.curiosity_scale = 0.1
        
    def _build_encoder(self) -> Model:
        """State feature encoder"""
        state_input = Input(shape=(self.state_dim,))
        x = Dense(128, activation='relu')(state_input)
        x = Dense(self.feature_dim, activation='relu')(x)
        return Model(state_input, x, name='encoder')
    
    def _build_forward_model(self) -> Model:
        """Predicts next state features from current features + action"""
        feature_input = Input(shape=(self.feature_dim,))
        action_input = Input(shape=(self.action_dim,))
        
        x = concatenate([feature_input, action_input])
        x = Dense(128, activation='relu')(x)
        x = Dense(self.feature_dim, activation='relu')(x)
        
        return Model([feature_input, action_input], x, name='forward_model')
    
    def _build_inverse_model(self) -> Model:
        """Predicts action from current and next state features"""
        current_feature = Input(shape=(self.feature_dim,))
        next_feature = Input(shape=(self.feature_dim,))
        
        x = concatenate([current_feature, next_feature])
        x = Dense(128, activation='relu')(x)
        action_pred = Dense(self.action_dim, activation='softmax')(x)
        
        return Model([current_feature, next_feature], action_pred, name='inverse_model')
    
    def compute_curiosity(
        self,
        state: np.ndarray,
        action: int,
        next_state: np.ndarray
    ) -> float:
        """Compute curiosity-based intrinsic reward"""
        state = np.array(state).reshape(1, -1)
        next_state = np.array(next_state).reshape(1, -1)
        action_onehot = np.zeros((1, self.action_dim))
        action_onehot[0, action] = 1.0
        
        # Encode states
        current_features = self.encoder.predict(state, verbose=0)
        next_features = self.encoder.predict(next_state, verbose=0)
        
        # Predict next features
        predicted_next = self.forward_model.predict(
            [current_features, action_onehot], verbose=0
        )
        
        # Prediction error = curiosity
        prediction_error = np.mean(np.square(predicted_next - next_features))
        curiosity_reward = float(prediction_error) * self.curiosity_scale
        
        return curiosity_reward
    
    def train_step(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        next_states: np.ndarray
    ) -> Dict[str, float]:
        """Train curiosity module"""
        actions_onehot = np.zeros((len(actions), self.action_dim))
        for i, a in enumerate(actions):
            actions_onehot[i, int(a)] = 1.0
        
        with tf.GradientTape() as tape:
            # Encode states
            current_features = self.encoder(states, training=True)
            next_features = self.encoder(next_states, training=True)
            
            # Forward model loss
            predicted_next = self.forward_model(
                [current_features, actions_onehot], training=True
            )
            forward_loss = tf.reduce_mean(tf.square(predicted_next - next_features))
            
            # Inverse model loss
            predicted_actions = self.inverse_model(
                [current_features, next_features], training=True
            )
            inverse_loss = tf.reduce_mean(
                tf.keras.losses.categorical_crossentropy(actions_onehot, predicted_actions)
            )
            
            total_loss = forward_loss + 0.2 * inverse_loss
        
        # Get all trainable variables
        trainable_vars = (
            self.encoder.trainable_variables +
            self.forward_model.trainable_variables +
            self.inverse_model.trainable_variables
        )
        
        gradients = tape.gradient(total_loss, trainable_vars)
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        
        return {
            'forward_loss': float(forward_loss),
            'inverse_loss': float(inverse_loss),
            'total_loss': float(total_loss)
        }


class SRDDQNAgent:
    """
    Self-Rewarding Double Deep Q-Network (SRDDQN)
    
    Combines:
    1. Double DQN for stable Q-learning
    2. Self-reward predictor for intrinsic motivation
    3. Curiosity module for exploration
    4. Sharpe ratio-based extrinsic rewards
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 5,  # strong_sell, sell, hold, buy, strong_buy
        hidden_dims: List[int] = [256, 256, 128],
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        tau: float = 0.005,
        buffer_size: int = 100000,
        batch_size: int = 64,
        exploration_initial: float = 1.0,
        exploration_final: float = 0.02,
        exploration_fraction: float = 0.2,
        self_reward_weight: float = 0.3,
        curiosity_weight: float = 0.2,
        sharpe_weight: float = 0.5,
        model_dir: str = "/app/backend/models/srddqn"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.tau = tau
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.model_dir = model_dir
        
        # Exploration parameters
        self.exploration_initial = exploration_initial
        self.exploration_final = exploration_final
        self.exploration_fraction = exploration_fraction
        self.epsilon = exploration_initial
        
        # Reward weights (must sum to 1)
        total_weight = self_reward_weight + curiosity_weight + sharpe_weight
        self.self_reward_weight = self_reward_weight / total_weight
        self.curiosity_weight = curiosity_weight / total_weight
        self.sharpe_weight = sharpe_weight / total_weight
        
        os.makedirs(model_dir, exist_ok=True)
        
        # Build networks
        self.q_network = self._build_q_network()
        self.target_network = self._build_q_network()
        self.target_network.set_weights(self.q_network.get_weights())
        
        # Self-reward predictor
        self.self_reward_predictor = SelfRewardPredictor(
            state_dim=state_dim,
            action_dim=action_dim,
            hidden_dims=[128, 64, 32],
            learning_rate=learning_rate
        )
        
        # Curiosity module
        self.curiosity_module = CuriosityModule(
            state_dim=state_dim,
            action_dim=action_dim,
            feature_dim=64,
            learning_rate=learning_rate
        )
        
        # Experience replay buffer
        self.replay_buffer = deque(maxlen=buffer_size)
        
        # Optimizer
        self.optimizer = optimizers.Adam(learning_rate=learning_rate)
        
        # Training statistics
        self.training_steps = 0
        self.episode_count = 0
        self.total_timesteps = 0
        self.training_history = []
        
        # Performance tracking
        self.sharpe_history = deque(maxlen=100)
        self.reward_components = {
            'extrinsic': deque(maxlen=1000),
            'self_reward': deque(maxlen=1000),
            'curiosity': deque(maxlen=1000)
        }
        
        # Noisy Networks flag (MDPI: parameter-space exploration)
        self.use_noisy_networks = True
        
        logger.info(f"SRDDQN Agent initialized: state_dim={state_dim}, action_dim={action_dim}, noisy_nets={self.use_noisy_networks}")
    
    def _build_q_network(self, noisy: bool = True) -> Model:
        """
        Build Q-network with dueling architecture and optional Noisy Networks.
        
        MDPI Best Practice: Use parameter-space exploration (NoisyNet) instead of
        ε-greedy which results in costly random trades in financial markets.
        """
        state_input = Input(shape=(self.state_dim,), name='state_input')
        
        # Shared feature extraction (standard Dense layers)
        x = state_input
        for i, dim in enumerate(self.hidden_dims):
            x = Dense(dim, activation='relu', name=f'shared_{i}')(x)
            x = BatchNormalization()(x)
        
        # Dueling architecture with Noisy layers for exploration
        if noisy and self.use_noisy_networks:
            # Value stream with noisy output
            value = NoisyDense(64, name='value_noisy_1')(x)
            value = tf.nn.relu(value)
            value = NoisyDense(1, name='value_output')(value)
            
            # Advantage stream with noisy output  
            advantage = NoisyDense(64, name='advantage_noisy_1')(x)
            advantage = tf.nn.relu(advantage)
            advantage = NoisyDense(self.action_dim, name='advantage_output')(advantage)
        else:
            # Standard Dense layers (for target network or inference)
            value = Dense(64, activation='relu', name='value_hidden')(x)
            value = Dense(1, name='value_output')(value)
            
            advantage = Dense(64, activation='relu', name='advantage_hidden')(x)
            advantage = Dense(self.action_dim, name='advantage_output')(advantage)
        
        # Combine: Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = value + (advantage - tf.reduce_mean(advantage, axis=1, keepdims=True))
        
        model = Model(state_input, q_values, name='dueling_dqn')
        return model
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using Noisy Networks + self-reward guidance.
        
        MDPI Best Practice: With NoisyNets, the network learns when to explore.
        We remove costly ε-greedy random actions and rely on:
        1. Parameter noise in NoisyDense layers (learned exploration)
        2. Self-reward predictor guidance (informed exploration)
        """
        state = np.array(state).reshape(1, -1)
        
        if training and self.use_noisy_networks:
            # NoisyNet exploration: forward pass with noise in weights
            # The network naturally explores via its noisy parameters
            q_values = self.q_network(state, training=True).numpy()[0]
            
            # Optional: Add self-reward guidance for smarter exploration
            # This biases exploration toward predicted valuable actions
            if np.random.random() < 0.1:  # 10% self-reward guided (much less than before)
                rewards = []
                for a in range(self.action_dim):
                    r, conf = self.self_reward_predictor.predict_reward(state[0], a)
                    rewards.append(r * conf)  # Weight by confidence
                
                # Combine Q-values with self-reward predictions
                rewards = np.array(rewards)
                combined = q_values + rewards * 0.5
                return int(np.argmax(combined))
            
            return int(np.argmax(q_values))
        
        elif training:
            # Fallback epsilon-greedy if noisy networks disabled
            if np.random.random() < self.epsilon:
            q_values = self.q_network.predict(state, verbose=0)[0]
            return int(np.argmax(q_values))
    
    def compute_combined_reward(
        self,
        state: np.ndarray,
        action: int,
        next_state: np.ndarray,
        extrinsic_reward: float
    ) -> Tuple[float, Dict[str, float]]:
        """Compute combined reward from all sources"""
        # Self-reward
        self_reward, confidence = self.self_reward_predictor.predict_reward(state, action)
        
        # Curiosity reward
        curiosity_reward = self.curiosity_module.compute_curiosity(state, action, next_state)
        
        # Combined reward
        combined = (
            self.sharpe_weight * extrinsic_reward +
            self.self_reward_weight * self_reward * confidence +
            self.curiosity_weight * curiosity_reward
        )
        
        # Track components
        self.reward_components['extrinsic'].append(extrinsic_reward)
        self.reward_components['self_reward'].append(self_reward)
        self.reward_components['curiosity'].append(curiosity_reward)
        
        components = {
            'extrinsic': extrinsic_reward,
            'self_reward': self_reward,
            'curiosity': curiosity_reward,
            'confidence': confidence,
            'combined': combined
        }
        
        return combined, components
    
    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        extrinsic_reward: float
    ):
        """Store transition in replay buffer"""
        self.replay_buffer.append({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'extrinsic_reward': extrinsic_reward
        })
    
    def train_step(self) -> Dict[str, float]:
        """Perform one training step"""
        if len(self.replay_buffer) < self.batch_size:
            return {}
        
        # Sample batch
        indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in indices]
        
        states = np.array([t['state'] for t in batch])
        actions = np.array([t['action'] for t in batch])
        rewards = np.array([t['reward'] for t in batch])
        next_states = np.array([t['next_state'] for t in batch])
        dones = np.array([t['done'] for t in batch])
        extrinsic_rewards = np.array([t['extrinsic_reward'] for t in batch])
        
        # Double DQN update
        with tf.GradientTape() as tape:
            # Current Q-values
            q_values = self.q_network(states, training=True)
            q_values_selected = tf.reduce_sum(
                q_values * tf.one_hot(actions, self.action_dim), axis=1
            )
            
            # Target Q-values using Double DQN
            # Use online network to select action
            next_q_values = self.q_network(next_states, training=False)
            next_actions = tf.argmax(next_q_values, axis=1)
            
            # Use target network to evaluate
            target_next_q = self.target_network(next_states, training=False)
            next_q_selected = tf.reduce_sum(
                target_next_q * tf.one_hot(next_actions, self.action_dim), axis=1
            )
            
            # Compute targets
            targets = rewards + self.gamma * next_q_selected * (1 - dones)
            
            # Huber loss for stability
            q_loss = tf.reduce_mean(tf.keras.losses.huber(targets, q_values_selected))
        
        # Update Q-network
        gradients = tape.gradient(q_loss, self.q_network.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.q_network.trainable_variables))
        
        # Soft update target network
        for target_var, var in zip(self.target_network.weights, self.q_network.weights):
            target_var.assign(self.tau * var + (1 - self.tau) * target_var)
        
        # Train self-reward predictor
        target_rewards = extrinsic_rewards.reshape(-1, 1)
        sr_loss = self.self_reward_predictor.train_step(states, actions, target_rewards)
        
        # Train curiosity module
        curiosity_losses = self.curiosity_module.train_step(states, actions, next_states)
        
        self.training_steps += 1
        
        # Update exploration rate
        progress = min(1.0, self.total_timesteps / (self.exploration_fraction * self.buffer_size))
        self.epsilon = self.exploration_initial + progress * (
            self.exploration_final - self.exploration_initial
        )
        
        return {
            'q_loss': float(q_loss),
            'sr_loss': float(sr_loss),
            'curiosity_loss': curiosity_losses['total_loss'],
            'epsilon': self.epsilon
        }
    
    def train_episode(self, env, max_steps: int = 1000) -> Dict[str, Any]:
        """Train for one episode"""
        state, _ = env.reset()
        total_reward = 0
        total_extrinsic = 0
        episode_losses = []
        
        for step in range(max_steps):
            # Select action
            action = self.select_action(state, training=True)
            
            # Execute action
            next_state, extrinsic_reward, terminated, truncated, info = env.step(
                np.array([self._action_to_continuous(action)])
            )
            done = terminated or truncated
            
            # Compute combined reward
            combined_reward, _ = self.compute_combined_reward(
                state, action, next_state, extrinsic_reward
            )
            
            # Store transition
            self.store_transition(
                state, action, combined_reward, next_state, done, extrinsic_reward
            )
            
            # Train
            losses = self.train_step()
            if losses:
                episode_losses.append(losses)
            
            total_reward += combined_reward
            total_extrinsic += extrinsic_reward
            self.total_timesteps += 1
            
            state = next_state
            
            if done:
                break
        
        self.episode_count += 1
        
        # Compute average losses
        avg_losses = {}
        if episode_losses:
            for key in episode_losses[0].keys():
                avg_losses[key] = np.mean([l[key] for l in episode_losses])
        
        episode_result = {
            'episode': self.episode_count,
            'total_reward': total_reward,
            'extrinsic_reward': total_extrinsic,
            'steps': step + 1,
            'epsilon': self.epsilon,
            **avg_losses
        }
        
        self.training_history.append(episode_result)
        
        return episode_result
    
    def _action_to_continuous(self, action: int) -> float:
        """Convert discrete action to continuous value"""
        action_map = {0: -1.0, 1: -0.5, 2: 0.0, 3: 0.5, 4: 1.0}
        return action_map.get(action, 0.0)
    
    def save(self, path: str = None):
        """Save all models"""
        path = path or self.model_dir
        
        self.q_network.save(os.path.join(path, 'q_network.keras'))
        self.target_network.save(os.path.join(path, 'target_network.keras'))
        self.self_reward_predictor.model.save(os.path.join(path, 'sr_predictor.keras'))
        self.curiosity_module.encoder.save(os.path.join(path, 'curiosity_encoder.keras'))
        self.curiosity_module.forward_model.save(os.path.join(path, 'curiosity_forward.keras'))
        self.curiosity_module.inverse_model.save(os.path.join(path, 'curiosity_inverse.keras'))
        
        # Save config
        config = {
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'hidden_dims': self.hidden_dims,
            'total_timesteps': self.total_timesteps,
            'episode_count': self.episode_count,
            'epsilon': self.epsilon,
            'reward_weights': {
                'sharpe': self.sharpe_weight,
                'self_reward': self.self_reward_weight,
                'curiosity': self.curiosity_weight
            }
        }
        with open(os.path.join(path, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"SRDDQN models saved to {path}")
    
    def load(self, path: str = None):
        """Load all models"""
        path = path or self.model_dir
        
        self.q_network = keras.models.load_model(os.path.join(path, 'q_network.keras'))
        self.target_network = keras.models.load_model(os.path.join(path, 'target_network.keras'))
        
        # Load config
        with open(os.path.join(path, 'config.json'), 'r') as f:
            config = json.load(f)
            self.total_timesteps = config['total_timesteps']
            self.episode_count = config['episode_count']
            self.epsilon = config['epsilon']
        
        logger.info(f"SRDDQN models loaded from {path}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        sr_stats = self.self_reward_predictor.get_stats()
        
        reward_stats = {}
        for key, values in self.reward_components.items():
            if values:
                reward_stats[f'{key}_mean'] = float(np.mean(values))
                reward_stats[f'{key}_std'] = float(np.std(values))
        
        return {
            'type': 'SRDDQN',
            'description': 'Self-Rewarding Double Deep Q-Network',
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'total_timesteps': self.total_timesteps,
            'episode_count': self.episode_count,
            'epsilon': self.epsilon,
            'buffer_size': len(self.replay_buffer),
            'training_steps': self.training_steps,
            'reward_weights': {
                'sharpe': self.sharpe_weight,
                'self_reward': self.self_reward_weight,
                'curiosity': self.curiosity_weight
            },
            'self_reward_stats': sr_stats,
            'reward_component_stats': reward_stats,
            'features': [
                'Double DQN with target network',
                'Dueling architecture (V + A streams)',
                'Self-reward predictor for intrinsic motivation',
                'Curiosity module (ICM) for exploration',
                'Sharpe ratio-based extrinsic rewards',
                'Adaptive exploration via epsilon decay'
            ]
        }


# =============================================================================
# SRDDQN MANAGER
# =============================================================================

class SRDDQNManager:
    """Manager for SRDDQN agents"""
    
    def __init__(self, db, model_dir: str = "/app/backend/models/srddqn"):
        self.db = db
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.agents: Dict[str, SRDDQNAgent] = {}
        self.training_tasks = {}
        
    def create_agent(
        self,
        agent_name: str,
        state_dim: int,
        config: Dict = None
    ) -> SRDDQNAgent:
        """Create a new SRDDQN agent"""
        config = config or {}
        
        agent = SRDDQNAgent(
            state_dim=state_dim,
            action_dim=config.get('action_dim', 5),
            hidden_dims=config.get('hidden_dims', [256, 256, 128]),
            learning_rate=config.get('learning_rate', 1e-4),
            gamma=config.get('gamma', 0.99),
            self_reward_weight=config.get('self_reward_weight', 0.3),
            curiosity_weight=config.get('curiosity_weight', 0.2),
            sharpe_weight=config.get('sharpe_weight', 0.5),
            model_dir=os.path.join(self.model_dir, agent_name)
        )
        
        self.agents[agent_name] = agent
        logger.info(f"Created SRDDQN agent: {agent_name}")
        
        return agent
    
    def get_agent(self, agent_name: str) -> Optional[SRDDQNAgent]:
        """Get agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict]:
        """List all agents"""
        return [
            {
                'name': name,
                'status': agent.get_status()
            }
            for name, agent in self.agents.items()
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            'tensorflow_available': TF_AVAILABLE,
            'agents': list(self.agents.keys()),
            'model_directory': self.model_dir,
            'type': 'SRDDQN',
            'features': {
                'self_reward': 'Intrinsic reward predictor for dense rewards',
                'curiosity': 'ICM-based exploration bonus',
                'double_dqn': 'Reduced Q-value overestimation',
                'dueling': 'Separate value and advantage streams',
                'sharpe_reward': 'Risk-adjusted extrinsic rewards'
            }
        }


# Singleton
_srddqn_manager = None

def get_srddqn_manager(db=None) -> SRDDQNManager:
    """Get or create SRDDQN manager"""
    global _srddqn_manager
    if _srddqn_manager is None and db is not None:
        _srddqn_manager = SRDDQNManager(db)
    return _srddqn_manager

async def initialize_srddqn_manager(db) -> SRDDQNManager:
    """Initialize SRDDQN manager"""
    manager = get_srddqn_manager(db)
    logger.info("SRDDQN Manager initialized")
    return manager
