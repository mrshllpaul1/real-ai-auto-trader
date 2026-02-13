"""
Full RLHF Training Loop with PPO
=================================
Implements Proximal Policy Optimization (PPO) for training
trading agents using human feedback.

Components:
1. Reward Model - Trained from human ratings
2. PPO Agent - Policy optimization with learned reward
3. Training Loop - Iterative improvement from feedback
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical, Normal
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import deque
import asyncio

logger = logging.getLogger(__name__)

# Check for GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RewardModelNetwork(nn.Module):
    """
    Neural network that learns to predict human ratings from trade features.
    """
    
    def __init__(self, input_dim: int = 10, hidden_dim: int = 128):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)  # Output: predicted rating
        )
    
    def forward(self, x):
        return self.network(x)


class PPOActorCritic(nn.Module):
    """
    Actor-Critic network for PPO.
    Actor: Policy network that outputs action probabilities
    Critic: Value network that estimates state value
    """
    
    def __init__(
        self,
        state_dim: int = 20,
        action_dim: int = 3,  # BUY, HOLD, SELL
        hidden_dim: int = 256
    ):
        super().__init__()
        
        # Shared feature extractor
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim)
        )
        
        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
    
    def forward(self, state):
        shared_features = self.shared(state)
        action_probs = self.actor(shared_features)
        value = self.critic(shared_features)
        return action_probs, value
    
    def get_action(self, state):
        """Sample action from policy"""
        action_probs, value = self.forward(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action, log_prob, value
    
    def evaluate_actions(self, states, actions):
        """Evaluate actions for PPO update"""
        action_probs, values = self.forward(states)
        dist = Categorical(action_probs)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, values, entropy


class RLHFPPOTrainer:
    """
    Full RLHF training loop using PPO.
    
    Training process:
    1. Collect human feedback on trades
    2. Train reward model to predict human ratings
    3. Use reward model to provide rewards for PPO
    4. Train PPO agent with learned rewards
    5. Iterate and improve
    """
    
    def __init__(
        self,
        db=None,
        state_dim: int = 20,
        action_dim: int = 3,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01
    ):
        self.db = db
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # PPO hyperparameters
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        
        # Initialize networks
        self.reward_model = RewardModelNetwork(input_dim=10).to(device)
        self.actor_critic = PPOActorCritic(state_dim, action_dim).to(device)
        
        # Optimizers
        self.reward_optimizer = optim.Adam(self.reward_model.parameters(), lr=learning_rate)
        self.ppo_optimizer = optim.Adam(self.actor_critic.parameters(), lr=learning_rate)
        
        # Experience buffer
        self.buffer = {
            "states": [],
            "actions": [],
            "log_probs": [],
            "rewards": [],
            "values": [],
            "dones": []
        }
        
        # Training data
        self.feedback_data: List[Dict] = []
        self.training_history = []
        
        # Stats
        self.stats = {
            "reward_model_loss": 0,
            "policy_loss": 0,
            "value_loss": 0,
            "entropy": 0,
            "total_feedback": 0,
            "training_iterations": 0
        }
        
        self.is_training = False
        
        logger.info("🎓 RLHF PPO Trainer initialized")
    
    def add_feedback(self, trade_features: Dict, human_rating: float):
        """Add human feedback to training data"""
        self.feedback_data.append({
            "features": trade_features,
            "rating": human_rating,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.stats["total_feedback"] += 1
    
    def _prepare_reward_features(self, trade_features: Dict) -> torch.Tensor:
        """Convert trade features to tensor for reward model"""
        feature_order = [
            "profit_pct", "hold_time_hours", "entry_timing_score",
            "exit_timing_score", "risk_reward_ratio", "position_size_score",
            "volatility", "trend_strength", "volume_ratio", "sentiment_score"
        ]
        
        features = []
        for key in feature_order:
            features.append(float(trade_features.get(key, 0)))
        
        return torch.FloatTensor(features).to(device)
    
    async def train_reward_model(self, epochs: int = 10, batch_size: int = 32) -> Dict:
        """
        Train the reward model on collected human feedback.
        """
        if len(self.feedback_data) < batch_size:
            return {"error": "Not enough feedback data", "required": batch_size, "current": len(self.feedback_data)}
        
        logger.info(f"Training reward model on {len(self.feedback_data)} samples")
        
        # Prepare training data
        X = torch.stack([
            self._prepare_reward_features(d["features"]) 
            for d in self.feedback_data
        ])
        y = torch.FloatTensor([d["rating"] for d in self.feedback_data]).unsqueeze(1).to(device)
        
        # Normalize ratings to 0-1
        y = (y - 1) / 4  # Rating 1-5 -> 0-1
        
        total_loss = 0
        
        for epoch in range(epochs):
            # Shuffle data
            perm = torch.randperm(len(X))
            X_shuffled = X[perm]
            y_shuffled = y[perm]
            
            epoch_loss = 0
            
            for i in range(0, len(X), batch_size):
                batch_X = X_shuffled[i:i+batch_size]
                batch_y = y_shuffled[i:i+batch_size]
                
                # Forward pass
                predictions = self.reward_model(batch_X)
                loss = nn.MSELoss()(predictions, batch_y)
                
                # Backward pass
                self.reward_optimizer.zero_grad()
                loss.backward()
                self.reward_optimizer.step()
                
                epoch_loss += loss.item()
            
            total_loss += epoch_loss
            
            await asyncio.sleep(0.01)
        
        avg_loss = total_loss / epochs
        self.stats["reward_model_loss"] = avg_loss
        
        return {
            "status": "trained",
            "epochs": epochs,
            "samples": len(self.feedback_data),
            "avg_loss": avg_loss
        }
    
    def get_learned_reward(self, trade_features: Dict) -> float:
        """Get reward from trained reward model"""
        with torch.no_grad():
            features = self._prepare_reward_features(trade_features)
            reward = self.reward_model(features.unsqueeze(0))
            return reward.item() * 4 + 1  # Scale back to 1-5
    
    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        log_prob: float,
        reward: float,
        value: float,
        done: bool
    ):
        """Store a transition in the buffer"""
        self.buffer["states"].append(state)
        self.buffer["actions"].append(action)
        self.buffer["log_probs"].append(log_prob)
        self.buffer["rewards"].append(reward)
        self.buffer["values"].append(value)
        self.buffer["dones"].append(done)
    
    def compute_gae(self, rewards: List, values: List, dones: List) -> Tuple[List, List]:
        """Compute Generalized Advantage Estimation"""
        advantages = []
        returns = []
        gae = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
            
            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[t])
        
        return advantages, returns
    
    async def train_ppo(
        self,
        num_updates: int = 10,
        mini_batch_size: int = 64
    ) -> Dict:
        """
        Perform PPO update on collected experience.
        """
        if len(self.buffer["states"]) < mini_batch_size:
            return {"error": "Not enough experience", "required": mini_batch_size}
        
        self.is_training = True
        
        # Convert buffer to tensors
        states = torch.FloatTensor(np.array(self.buffer["states"])).to(device)
        actions = torch.LongTensor(self.buffer["actions"]).to(device)
        old_log_probs = torch.FloatTensor(self.buffer["log_probs"]).to(device)
        rewards = self.buffer["rewards"]
        values = self.buffer["values"]
        dones = self.buffer["dones"]
        
        # Compute advantages
        advantages, returns = self.compute_gae(rewards, values, dones)
        advantages = torch.FloatTensor(advantages).to(device)
        returns = torch.FloatTensor(returns).to(device)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0
        
        for _ in range(num_updates):
            # Mini-batch training
            perm = torch.randperm(len(states))
            
            for start in range(0, len(states), mini_batch_size):
                end = start + mini_batch_size
                batch_indices = perm[start:end]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Get current policy evaluation
                log_probs, values, entropy = self.actor_critic.evaluate_actions(
                    batch_states, batch_actions
                )
                
                # PPO clipped objective
                ratio = torch.exp(log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss
                value_loss = nn.MSELoss()(values.squeeze(), batch_returns)
                
                # Total loss
                loss = (
                    policy_loss + 
                    self.value_coef * value_loss - 
                    self.entropy_coef * entropy.mean()
                )
                
                # Update
                self.ppo_optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), 0.5)
                self.ppo_optimizer.step()
                
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
            
            await asyncio.sleep(0.01)
        
        # Update stats
        n_batches = (len(states) // mini_batch_size) * num_updates
        self.stats["policy_loss"] = total_policy_loss / max(n_batches, 1)
        self.stats["value_loss"] = total_value_loss / max(n_batches, 1)
        self.stats["entropy"] = total_entropy / max(n_batches, 1)
        self.stats["training_iterations"] += 1
        
        # Clear buffer
        self.buffer = {k: [] for k in self.buffer}
        
        self.is_training = False
        
        # Record history
        self.training_history.append({
            "iteration": self.stats["training_iterations"],
            "policy_loss": self.stats["policy_loss"],
            "value_loss": self.stats["value_loss"],
            "entropy": self.stats["entropy"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "status": "trained",
            "updates": num_updates,
            "policy_loss": self.stats["policy_loss"],
            "value_loss": self.stats["value_loss"],
            "entropy": self.stats["entropy"]
        }
    
    def get_action(self, state: np.ndarray) -> Tuple[int, Dict]:
        """Get action from trained policy"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            action, log_prob, value = self.actor_critic.get_action(state_tensor)
            
            action_map = {0: "BUY", 1: "HOLD", 2: "SELL"}
            
            return action.item(), {
                "action_name": action_map.get(action.item(), "HOLD"),
                "log_prob": log_prob.item(),
                "value": value.item()
            }
    
    async def full_training_loop(
        self,
        reward_epochs: int = 10,
        ppo_updates: int = 10,
        iterations: int = 5
    ) -> Dict:
        """
        Run full RLHF training loop:
        1. Train reward model on feedback
        2. Collect experience with current policy
        3. Update policy with PPO
        4. Repeat
        """
        results = {
            "iterations": [],
            "final_stats": None
        }
        
        for i in range(iterations):
            logger.info(f"RLHF Iteration {i + 1}/{iterations}")
            
            # Train reward model
            reward_result = await self.train_reward_model(epochs=reward_epochs)
            
            # Train PPO (if we have experience)
            ppo_result = await self.train_ppo(num_updates=ppo_updates)
            
            results["iterations"].append({
                "iteration": i + 1,
                "reward_training": reward_result,
                "ppo_training": ppo_result
            })
            
            await asyncio.sleep(0.1)
        
        results["final_stats"] = self.get_stats()
        
        # Save to database
        if self.db is not None:
            try:
                await self.db.rlhf_training_runs.insert_one({
                    **results,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to save training results: {e}")
        
        return results
    
    def get_stats(self) -> Dict:
        """Get current training statistics"""
        return {
            **self.stats,
            "training_history_length": len(self.training_history),
            "feedback_data_count": len(self.feedback_data),
            "buffer_size": len(self.buffer["states"]),
            "is_training": self.is_training,
            "device": str(device)
        }
    
    def save_models(self, path: str = "/app/backend/models"):
        """Save trained models"""
        import os
        os.makedirs(path, exist_ok=True)
        
        torch.save(self.reward_model.state_dict(), f"{path}/reward_model.pt")
        torch.save(self.actor_critic.state_dict(), f"{path}/ppo_actor_critic.pt")
        logger.info(f"✅ Models saved to {path}")
    
    def load_models(self, path: str = "/app/backend/models"):
        """Load trained models"""
        import os
        
        reward_path = f"{path}/reward_model.pt"
        ppo_path = f"{path}/ppo_actor_critic.pt"
        
        if os.path.exists(reward_path):
            self.reward_model.load_state_dict(torch.load(reward_path, map_location=device))
            logger.info("✅ Reward model loaded")
        
        if os.path.exists(ppo_path):
            self.actor_critic.load_state_dict(torch.load(ppo_path, map_location=device))
            logger.info("✅ PPO model loaded")


# Singleton
_rlhf_ppo_trainer: Optional[RLHFPPOTrainer] = None


def get_rlhf_ppo_trainer(db=None) -> RLHFPPOTrainer:
    """Get or create RLHF PPO trainer singleton"""
    global _rlhf_ppo_trainer
    if _rlhf_ppo_trainer is None:
        _rlhf_ppo_trainer = RLHFPPOTrainer(db)
    return _rlhf_ppo_trainer
