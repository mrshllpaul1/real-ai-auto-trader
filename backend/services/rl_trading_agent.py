"""
Reinforcement Learning Trading Agent
Enhancement #5: RL agent to maximize portfolio returns with optimal entry/exit
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from collections import deque
import random
from motor.motor_asyncio import AsyncIOMotorDatabase
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound TensorFlow operations
_training_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rl_train")

# TensorFlow imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Dense, Input, Concatenate
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available for RL agent")


class TradingEnvironment:
    """
    Trading environment for RL agent:
    - State: price features, portfolio state, market indicators
    - Actions: buy, sell, hold
    - Rewards: based on PnL and risk-adjusted returns
    """
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0  # Coin amount held
        self.position_price = 0  # Average entry price
        self.current_price = 0
        self.step_count = 0
        self.trades = []
        self.history = []
        
        # Action space: 0=hold, 1=buy, 2=sell
        self.action_space = 3
        
        # State space dimensions
        self.state_dim = 15
        
    def reset(self, initial_price: float = 100) -> np.ndarray:
        """Reset environment to initial state"""
        self.balance = self.initial_balance
        self.position = 0
        self.position_price = 0
        self.current_price = initial_price
        self.step_count = 0
        self.trades = []
        self.history = []
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        # Portfolio state
        portfolio_value = self.balance + self.position * self.current_price
        position_pct = (self.position * self.current_price) / portfolio_value if portfolio_value > 0 else 0
        unrealized_pnl = (self.current_price - self.position_price) / self.position_price if self.position_price > 0 else 0
        
        # Normalize balance and position
        normalized_balance = self.balance / self.initial_balance
        
        state = np.array([
            normalized_balance,
            position_pct,
            unrealized_pnl,
            self.current_price / 100,  # Normalized price (assuming ~100 base)
            1 if self.position > 0 else 0,  # Has position
            len(self.trades) / 100,  # Trade count normalized
            min(self.step_count / 1000, 1),  # Step progress
            # Placeholder for market features (filled by step)
            0, 0, 0, 0, 0, 0, 0, 0
        ])
        
        return state
    
    def step(self, action: int, new_price: float, market_features: np.ndarray = None) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return new state, reward, done, info
        
        Args:
            action: 0=hold, 1=buy, 2=sell
            new_price: New market price
            market_features: Additional market indicators
            
        Returns:
            state, reward, done, info
        """
        self.step_count += 1
        old_portfolio_value = self.balance + self.position * self.current_price
        
        # Update price
        price_change = (new_price - self.current_price) / self.current_price if self.current_price > 0 else 0
        self.current_price = new_price
        
        reward = 0
        trade_info = None
        
        # Execute action
        if action == 1:  # Buy
            if self.balance > 0:
                # Use 50% of balance
                buy_amount = self.balance * 0.5
                coins = buy_amount / self.current_price
                
                # Update position (average price)
                total_coins = self.position + coins
                if total_coins > 0:
                    self.position_price = (
                        (self.position * self.position_price + coins * self.current_price) / total_coins
                    )
                
                self.position += coins
                self.balance -= buy_amount
                
                self.trades.append({
                    'action': 'buy',
                    'price': self.current_price,
                    'amount': coins,
                    'step': self.step_count
                })
                
                reward -= 0.001  # Small transaction cost
                trade_info = {'action': 'buy', 'amount': coins}
                
        elif action == 2:  # Sell
            if self.position > 0:
                # Sell all position
                sell_value = self.position * self.current_price
                pnl = sell_value - (self.position * self.position_price)
                pnl_pct = pnl / (self.position * self.position_price) if self.position_price > 0 else 0
                
                self.balance += sell_value
                
                self.trades.append({
                    'action': 'sell',
                    'price': self.current_price,
                    'amount': self.position,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'step': self.step_count
                })
                
                # Reward based on trade PnL
                reward += pnl_pct * 10  # Scale reward
                
                self.position = 0
                self.position_price = 0
                
                trade_info = {'action': 'sell', 'pnl_pct': pnl_pct}
        
        # Calculate new portfolio value
        new_portfolio_value = self.balance + self.position * self.current_price
        portfolio_return = (new_portfolio_value - old_portfolio_value) / old_portfolio_value if old_portfolio_value > 0 else 0
        
        # Add position holding reward/penalty
        if self.position > 0:
            # Reward for holding during price increase
            reward += price_change * 5
        
        # Penalize for missed opportunities (holding cash during price increase)
        if self.position == 0 and price_change > 0.01:
            reward -= price_change * 2
        
        # Store history
        self.history.append({
            'step': self.step_count,
            'action': action,
            'price': self.current_price,
            'portfolio_value': new_portfolio_value,
            'reward': reward
        })
        
        # Update state with market features
        state = self._get_state()
        if market_features is not None and len(market_features) >= 8:
            state[7:15] = market_features[:8]
        
        # Episode done conditions
        done = False
        if new_portfolio_value < self.initial_balance * 0.5:  # Lost 50%
            done = True
            reward -= 10  # Large penalty for blowing up
        elif self.step_count >= 1000:  # Max steps
            done = True
        
        info = {
            'portfolio_value': new_portfolio_value,
            'total_return': (new_portfolio_value - self.initial_balance) / self.initial_balance,
            'trade_info': trade_info,
            'num_trades': len(self.trades)
        }
        
        return state, reward, done, info
    
    def get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        return self.balance + self.position * self.current_price


class DQNAgent:
    """
    Deep Q-Network agent for trading:
    - Experience replay for stable learning
    - Target network for reduced variance
    - Epsilon-greedy exploration
    """
    
    def __init__(self, state_dim: int = 15, action_dim: int = 3):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Hyperparameters
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.batch_size = 64
        
        # Experience replay
        self.memory = deque(maxlen=10000)
        
        # Build networks
        if TF_AVAILABLE:
            self.model = self._build_model()
            self.target_model = self._build_model()
            self.update_target_model()
        else:
            self.model = None
            self.target_model = None
    
    def _build_model(self) -> Model:
        """Build DQN model"""
        model = Sequential([
            Dense(128, activation='relu', input_dim=self.state_dim),
            Dense(128, activation='relu'),
            Dense(64, activation='relu'),
            Dense(self.action_dim, activation='linear')
        ])
        model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='mse')
        return model
    
    def update_target_model(self):
        """Copy weights to target model"""
        if self.model and self.target_model:
            self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """Choose action using epsilon-greedy policy"""
        if not TF_AVAILABLE or self.model is None:
            return random.randint(0, self.action_dim - 1)
        
        if training and np.random.rand() <= self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        q_values = self.model.predict(state.reshape(1, -1), verbose=0)[0]
        return int(np.argmax(q_values))
    
    def replay(self) -> float:
        """Train on batch from replay buffer"""
        if not TF_AVAILABLE or len(self.memory) < self.batch_size:
            return 0.0
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.array([exp[0] for exp in minibatch])
        actions = np.array([exp[1] for exp in minibatch])
        rewards = np.array([exp[2] for exp in minibatch])
        next_states = np.array([exp[3] for exp in minibatch])
        dones = np.array([exp[4] for exp in minibatch])
        
        # Predict Q values
        current_q = self.model.predict(states, verbose=0)
        next_q = self.target_model.predict(next_states, verbose=0)
        
        # Update Q values
        for i in range(self.batch_size):
            if dones[i]:
                current_q[i][actions[i]] = rewards[i]
            else:
                current_q[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])
        
        # Train model
        history = self.model.fit(states, current_q, epochs=1, verbose=0)
        loss = history.history['loss'][0]
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss
    
    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """Get Q values for state"""
        if not TF_AVAILABLE or self.model is None:
            return np.zeros(self.action_dim)
        return self.model.predict(state.reshape(1, -1), verbose=0)[0]


class RLTradingAgent:
    """
    High-level RL Trading Agent:
    - Manages training and inference
    - Provides trading signals
    - Tracks performance
    - Supports background task execution for long-running training
    - Supports model persistence (save/load to disk)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.env = TradingEnvironment()
        self.agent = DQNAgent()
        self.is_trained = False
        self.training_history = []
        self.task_manager = None  # Set via set_task_manager()
        self.current_training_task_id = None
        self.history_service = None  # Training history tracking
        
        # Try to load saved model on initialization
        self._load_saved_model()
    
    def _load_saved_model(self):
        """Attempt to load a previously saved model"""
        try:
            from services.model_persistence import get_rl_persistence
            persistence = get_rl_persistence()
            
            if persistence.model_exists():
                model = persistence.load_keras_model()
                if model is not None:
                    self.agent.model = model
                    self.agent.target_model = model
                    self.is_trained = True
                    meta = persistence.get_metadata() or {}
                    # Restore epsilon from metadata
                    if 'epsilon' in meta:
                        self.agent.epsilon = meta['epsilon']
                    logger.info(f"✅ RL Agent loaded saved model (trained: {meta.get('saved_at', 'unknown')})")
        except Exception as e:
            logger.warning(f"Could not load saved RL model: {e}")
    
    def save_model(self) -> bool:
        """Save the current model to disk"""
        try:
            from services.model_persistence import get_rl_persistence
            persistence = get_rl_persistence()
            
            if self.agent.model is not None:
                return persistence.save_keras_model(
                    self.agent.model,
                    metadata={
                        "is_trained": self.is_trained,
                        "epsilon": self.agent.epsilon,
                        "memory_size": len(self.agent.memory)
                    }
                )
            return False
        except Exception as e:
            logger.error(f"Failed to save RL model: {e}")
            return False
    
    def set_task_manager(self, task_manager):
        """Set background task manager for async training"""
        self.task_manager = task_manager
    
    def set_history_service(self, history_service):
        """Set training history service for tracking"""
        self.history_service = history_service
        
    async def train(self, episodes: int = 100, symbols: List[str] = None) -> Dict[str, Any]:
        """Train RL agent on historical data"""
        if not TF_AVAILABLE:
            return {'error': 'TensorFlow not available'}
        
        try:
            logger.info(f"🤖 Training RL Agent for {episodes} episodes...")
            
            if not symbols:
                symbols = ['BTC', 'ETH']
            
            # Collect price data
            all_prices = []
            for symbol in symbols:
                ohlcv = await self.db.ohlcv_data.find(
                    {'symbol': {'$regex': symbol, '$options': 'i'}}
                ).sort('timestamp', 1).limit(500).to_list(length=500)
                
                prices = [float(d['close']) for d in ohlcv if 'close' in d]
                if prices:
                    all_prices.extend(prices)
            
            if len(all_prices) < 100:
                return {'error': 'Insufficient price data'}
            
            # Normalize prices for training
            base_price = np.mean(all_prices[:50])
            normalized_prices = [p / base_price * 100 for p in all_prices]
            
            episode_rewards = []
            episode_returns = []
            
            for episode in range(episodes):
                # Random starting point
                start_idx = random.randint(0, len(normalized_prices) - 200)
                episode_prices = normalized_prices[start_idx:start_idx + 200]
                
                state = self.env.reset(episode_prices[0])
                total_reward = 0
                
                for i in range(1, len(episode_prices)):
                    # Generate market features
                    market_features = self._generate_market_features(episode_prices, i)
                    
                    # Choose action
                    action = self.agent.act(state)
                    
                    # Step environment
                    next_state, reward, done, info = self.env.step(
                        action, episode_prices[i], market_features
                    )
                    
                    # Store experience
                    self.agent.remember(state, action, reward, next_state, done)
                    
                    # Train
                    if len(self.agent.memory) >= self.agent.batch_size:
                        self.agent.replay()
                    
                    state = next_state
                    total_reward += reward
                    
                    if done:
                        break
                
                # Update target network periodically
                if episode % 10 == 0:
                    self.agent.update_target_model()
                
                episode_rewards.append(total_reward)
                final_return = (self.env.get_portfolio_value() - 10000) / 10000
                episode_returns.append(final_return)
                
                if episode % 20 == 0:
                    avg_reward = np.mean(episode_rewards[-20:])
                    avg_return = np.mean(episode_returns[-20:]) * 100
                    logger.info(f"  Episode {episode}: Avg Reward={avg_reward:.2f}, Avg Return={avg_return:.1f}%")
            
            self.is_trained = True
            self.training_history = {
                'rewards': episode_rewards,
                'returns': episode_returns
            }
            
            final_avg_return = np.mean(episode_returns[-20:]) * 100
            logger.info(f"✅ RL Agent trained: Final avg return = {final_avg_return:.1f}%")
            
            return {
                'status': 'success',
                'episodes': episodes,
                'final_epsilon': round(self.agent.epsilon, 4),
                'avg_reward_last_20': round(np.mean(episode_rewards[-20:]), 2),
                'avg_return_last_20_pct': round(final_avg_return, 2),
                'total_experiences': len(self.agent.memory)
            }
            
        except Exception as e:
            logger.error(f"RL training failed: {e}")
            return {'error': str(e)}
    
    async def train_background(self, episodes: int = 100, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Train RL agent in background using BackgroundTaskManager.
        This prevents API timeouts for long-running training.
        Uses thread pool to prevent blocking the event loop.
        
        Args:
            episodes: Number of training episodes (default 100)
            symbols: List of symbols to train on (default ['BTC', 'ETH'])
            
        Returns:
            task_id for tracking progress, or direct result if no task manager
        """
        if not self.task_manager:
            # Fallback to synchronous training if no task manager
            logger.warning("No task manager available, running synchronous training")
            return await self.train(episodes=episodes, symbols=symbols)
        
        # Check if already training
        if self.current_training_task_id:
            status = await self.task_manager.get_task_status(self.current_training_task_id)
            if status and status.get('status') in ['pending', 'running']:
                return {
                    'status': 'already_training',
                    'task_id': self.current_training_task_id,
                    'message': 'Training already in progress'
                }
        
        from services.background_tasks import TaskType
        
        # Pre-fetch data before starting background task
        train_symbols = symbols or ['BTC', 'ETH']
        all_prices = []
        
        for symbol in train_symbols:
            ohlcv = await self.db.ohlcv_data.find(
                {'symbol': {'$regex': symbol, '$options': 'i'}}
            ).sort('timestamp', 1).limit(500).to_list(length=500)
            
            prices = [float(d['close']) for d in ohlcv if 'close' in d]
            if prices:
                all_prices.extend(prices)
        
        if len(all_prices) < 100:
            return {'error': 'Insufficient price data', 'data_points': len(all_prices)}
        
        # Normalize prices for training
        base_price = np.mean(all_prices[:50])
        normalized_prices = [p / base_price * 100 for p in all_prices]
        
        logger.info(f"📊 Loaded {len(normalized_prices)} price points for RL training")
        
        # Define the sync training function to run in thread pool
        def sync_training_loop(train_episodes: int, prices: list) -> Dict[str, Any]:
            """Synchronous training loop to run in thread pool"""
            if not TF_AVAILABLE:
                return {'error': 'TensorFlow not available'}
            
            try:
                logger.info(f"🤖 Starting RL training: {train_episodes} episodes in thread")
                
                episode_rewards = []
                episode_returns = []
                
                for episode in range(train_episodes):
                    # Random starting point
                    start_idx = random.randint(0, len(prices) - 200)
                    episode_prices = prices[start_idx:start_idx + 200]
                    
                    state = self.env.reset(episode_prices[0])
                    total_reward = 0
                    
                    for i in range(1, len(episode_prices)):
                        # Generate market features
                        market_features = self._generate_market_features(episode_prices, i)
                        
                        # Choose action
                        action = self.agent.act(state)
                        
                        # Step environment
                        next_state, reward, done, info = self.env.step(
                            action, episode_prices[i], market_features
                        )
                        
                        # Store experience
                        self.agent.remember(state, action, reward, next_state, done)
                        
                        # Train
                        if len(self.agent.memory) >= self.agent.batch_size:
                            self.agent.replay()
                        
                        state = next_state
                        total_reward += reward
                        
                        if done:
                            break
                    
                    # Update target network periodically
                    if episode % 10 == 0:
                        self.agent.update_target_model()
                    
                    episode_rewards.append(total_reward)
                    final_return = (self.env.get_portfolio_value() - 10000) / 10000
                    episode_returns.append(final_return)
                    
                    if episode % 20 == 0:
                        avg_reward = np.mean(episode_rewards[-20:]) if len(episode_rewards) >= 20 else np.mean(episode_rewards)
                        avg_return = np.mean(episode_returns[-20:]) * 100 if len(episode_returns) >= 20 else np.mean(episode_returns) * 100
                        logger.info(f"  Episode {episode}/{train_episodes}: Avg Reward={avg_reward:.2f}, Avg Return={avg_return:.1f}%")
                
                self.is_trained = True
                self.training_history = {
                    'rewards': episode_rewards,
                    'returns': episode_returns
                }
                
                final_avg_return = np.mean(episode_returns[-20:]) * 100 if len(episode_returns) >= 20 else np.mean(episode_returns) * 100
                logger.info(f"✅ RL Agent trained: Final avg return = {final_avg_return:.1f}%")
                
                # Auto-save model after training
                self.save_model()
                
                return {
                    'status': 'success',
                    'episodes': train_episodes,
                    'final_epsilon': round(self.agent.epsilon, 4),
                    'avg_reward_last_20': round(np.mean(episode_rewards[-20:]) if len(episode_rewards) >= 20 else np.mean(episode_rewards), 2),
                    'avg_return_last_20_pct': round(final_avg_return, 2),
                    'total_experiences': len(self.agent.memory),
                    'model_saved': True
                }
                
            except Exception as e:
                logger.error(f"RL training failed in thread: {e}")
                return {'error': str(e)}
        
        # Define the async wrapper that runs training in thread pool
        async def rl_training_task(progress_callback=None, **kwargs):
            train_episodes = kwargs.get('episodes', 100)
            prices = kwargs.get('prices', [])
            history_svc = kwargs.get('history_service')
            session_id = None
            
            # Start training history record
            if history_svc:
                try:
                    session_id = await history_svc.start_training(
                        model_type="rl_agent",
                        config={"episodes": train_episodes, "data_points": len(prices)},
                        task_id=self.current_training_task_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to start training history: {e}")
            
            if progress_callback:
                progress_callback(5, f"Starting RL training: {train_episodes} episodes")
            
            if progress_callback:
                progress_callback(10, f"Running training in background thread...")
            
            # Run the CPU-bound training in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _training_executor,
                sync_training_loop,
                train_episodes,
                prices
            )
            
            if progress_callback:
                progress_callback(100, "Training complete")
            
            # Record training history
            if history_svc and session_id:
                try:
                    if result.get('status') == 'success':
                        await history_svc.complete_training(
                            session_id=session_id,
                            result=result,
                            metrics={
                                "final_epsilon": result.get("final_epsilon"),
                                "avg_return_pct": result.get("avg_return_last_20_pct"),
                                "total_experiences": result.get("total_experiences")
                            }
                        )
                    else:
                        await history_svc.fail_training(
                            session_id=session_id,
                            error=result.get('error', 'Unknown error')
                        )
                except Exception as e:
                    logger.warning(f"Failed to record training history: {e}")
            
            return result
        
        # Submit to background task manager
        task_id = await self.task_manager.submit_task(
            task_type=TaskType.RL_AGENT_TRAINING,
            task_func=rl_training_task,
            task_name=f"rl_agent_training_{episodes}_episodes",
            timeout=900,  # 15 minutes
            episodes=episodes,
            prices=normalized_prices,
            history_service=self.history_service
        )
        
        self.current_training_task_id = task_id
        
        logger.info(f"🤖 RL Agent training submitted as background task: {task_id}")
        
        return {
            'status': 'submitted',
            'task_id': task_id,
            'message': f'RL training started in background ({episodes} episodes)',
            'check_status': f'/api/predictions/rl-agent/training-status/{task_id}'
        }
    
    async def get_training_status(self, task_id: str = None) -> Dict[str, Any]:
        """Get status of background training task"""
        check_task_id = task_id or self.current_training_task_id
        
        if not check_task_id:
            return {
                'status': 'no_training',
                'is_trained': self.is_trained,
                'message': 'No training task found'
            }
        
        if not self.task_manager:
            return {
                'status': 'error',
                'message': 'Task manager not available'
            }
        
        status = await self.task_manager.get_task_status(check_task_id)
        
        if not status:
            return {
                'status': 'not_found',
                'task_id': check_task_id,
                'message': 'Task not found (may have expired)'
            }
        
        return {
            'task_id': check_task_id,
            'is_trained': self.is_trained,
            **status
        }
    
    def _generate_market_features(self, prices: List[float], current_idx: int) -> np.ndarray:
        """Generate market features for state"""
        if current_idx < 20:
            return np.zeros(8)
        
        recent_prices = prices[max(0, current_idx-20):current_idx+1]
        
        # Calculate features
        returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                   for i in range(1, len(recent_prices))]
        
        features = [
            np.mean(returns[-5:]) if len(returns) >= 5 else 0,  # 5-period momentum
            np.mean(returns[-10:]) if len(returns) >= 10 else 0,  # 10-period momentum
            np.std(returns[-10:]) if len(returns) >= 10 else 0,  # Volatility
            (prices[current_idx] - np.mean(recent_prices)) / np.std(recent_prices) if np.std(recent_prices) > 0 else 0,  # Z-score
            1 if returns[-1] > 0 else -1 if returns[-1] < 0 else 0,  # Last direction
            sum(1 for r in returns[-5:] if r > 0) / 5 if len(returns) >= 5 else 0.5,  # Win rate
            max(recent_prices) / prices[current_idx] - 1,  # Distance from high
            prices[current_idx] / min(recent_prices) - 1,  # Distance from low
        ]
        
        return np.array(features)
    
    async def get_signal(self, symbol: str) -> Dict[str, Any]:
        """Get trading signal for symbol"""
        if not self.is_trained:
            return {'signal': 'hold', 'confidence': 0, 'error': 'Agent not trained'}
        
        try:
            # Get recent prices
            ohlcv = await self.db.ohlcv_data.find(
                {'symbol': {'$regex': symbol, '$options': 'i'}}
            ).sort('timestamp', -1).limit(50).to_list(length=50)
            
            if len(ohlcv) < 20:
                return {'signal': 'hold', 'confidence': 0, 'error': 'Insufficient data'}
            
            prices = [float(d['close']) for d in reversed(ohlcv)]
            
            # Create state
            market_features = self._generate_market_features(prices, len(prices) - 1)
            
            # Simplified state for prediction
            state = np.concatenate([
                [1.0, 0.0, 0.0, prices[-1] / 100, 0, 0, 0],
                market_features
            ])
            
            # Get Q values
            q_values = self.agent.get_q_values(state)
            action = int(np.argmax(q_values))
            
            # Calculate confidence
            q_range = np.max(q_values) - np.min(q_values)
            confidence = min(100, max(0, q_range * 50))
            
            action_names = ['hold', 'buy', 'sell']
            
            return {
                'symbol': symbol,
                'signal': action_names[action],
                'confidence': round(confidence, 1),
                'q_values': {
                    'hold': round(float(q_values[0]), 3),
                    'buy': round(float(q_values[1]), 3),
                    'sell': round(float(q_values[2]), 3)
                },
                'model': 'rl_dqn',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"RL signal failed: {e}")
            return {'signal': 'hold', 'confidence': 0, 'error': str(e)}
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get training summary"""
        # If model is trained (loaded from disk), return trained status even without history
        if self.is_trained and not self.training_history:
            return {
                'trained': True,
                'total_episodes': 0,
                'best_return_pct': 0,
                'worst_return_pct': 0,
                'avg_return_pct': 0,
                'final_epsilon': round(self.agent.epsilon, 4),
                'memory_size': len(self.agent.memory),
                'note': 'Model loaded from disk'
            }
        
        if not self.training_history:
            return {'trained': False}
        
        returns = self.training_history.get('returns', [])
        
        return {
            'trained': self.is_trained,
            'total_episodes': len(returns),
            'best_return_pct': round(max(returns) * 100, 2) if returns else 0,
            'worst_return_pct': round(min(returns) * 100, 2) if returns else 0,
            'avg_return_pct': round(np.mean(returns) * 100, 2) if returns else 0,
            'final_epsilon': round(self.agent.epsilon, 4),
            'memory_size': len(self.agent.memory)
        }


# Singleton instance
_rl_agent = None

def get_rl_agent(db: AsyncIOMotorDatabase = None) -> RLTradingAgent:
    global _rl_agent
    if _rl_agent is None and db is not None:
        _rl_agent = RLTradingAgent(db)
    return _rl_agent
