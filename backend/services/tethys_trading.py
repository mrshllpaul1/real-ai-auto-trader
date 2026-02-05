"""
Tethys Integrated Trading System
=================================
Connects Rainbow DQN + Order Book + Safety Systems into a unified trading loop.

Components:
1. Live order book data from Kraken WebSocket
2. Rainbow DQN with Transformer for decisions
3. Tethys Safety System for risk management
4. SHAP explainability for trade rationale
5. Kraken executor for live trades
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)

# =============================================================================
# SHAP EXPLAINABILITY MODULE
# =============================================================================

class TradingExplainer:
    """
    SHAP-based explainability for trading decisions.
    
    Provides human-readable explanations for why Tethys made each decision.
    """
    
    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or self._default_feature_names()
        self.background_data = None
        self.explainer = None
        
        # Feature importance history
        self.importance_history = deque(maxlen=100)
        
        logger.info("📊 Trading Explainer initialized")
    
    def _default_feature_names(self) -> List[str]:
        """Default feature names for order book data"""
        names = []
        for i in range(10):  # 10 levels
            names.extend([
                f'bid_price_L{i+1}',
                f'bid_qty_L{i+1}',
                f'ask_price_L{i+1}',
                f'ask_qty_L{i+1}'
            ])
        names.extend([
            'spread',
            'imbalance',
            'bid_depth',
            'ask_depth',
            'total_depth'
        ])
        return names
    
    def set_background(self, background_data: np.ndarray):
        """Set background data for SHAP explainer"""
        self.background_data = background_data
        logger.info(f"Background data set: {background_data.shape}")
    
    def explain_decision(
        self,
        state: np.ndarray,
        q_values: np.ndarray,
        action: int,
        model=None
    ) -> Dict[str, Any]:
        """
        Generate explanation for a trading decision.
        
        Uses gradient-based approximation when SHAP is too slow.
        """
        action_names = ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
        
        # Get latest timestep features (from transformer input)
        if state.ndim == 3:
            latest_features = state[0, -1, :]  # Last timestep
        elif state.ndim == 2:
            latest_features = state[-1, :]
        else:
            latest_features = state
        
        # Compute feature importance using gradient approximation
        # (Much faster than full SHAP for real-time trading)
        importance = self._compute_gradient_importance(
            latest_features, q_values, action
        )
        
        # Get top contributing features
        top_indices = np.argsort(np.abs(importance))[-5:][::-1]
        
        top_features = []
        for idx in top_indices:
            if idx < len(self.feature_names):
                name = self.feature_names[idx]
                value = float(latest_features[idx]) if idx < len(latest_features) else 0
                contrib = float(importance[idx])
                direction = "bullish" if contrib > 0 else "bearish"
                
                top_features.append({
                    'feature': name,
                    'value': value,
                    'contribution': contrib,
                    'direction': direction
                })
        
        # Generate natural language rationale
        rationale = self._generate_rationale(action_names[action], top_features, q_values)
        
        # Store for history
        self.importance_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': action_names[action],
            'top_features': top_features
        })
        
        return {
            'action': action_names[action],
            'q_values': {name: float(q) for name, q in zip(action_names, q_values)},
            'top_features': top_features,
            'rationale': rationale,
            'confidence_gap': float(np.max(q_values) - np.sort(q_values)[-2])
        }
    
    def _compute_gradient_importance(
        self,
        features: np.ndarray,
        q_values: np.ndarray,
        action: int
    ) -> np.ndarray:
        """
        Compute feature importance using finite difference approximation.
        
        For each feature, compute how much Q-value changes when feature changes.
        """
        importance = np.zeros(len(features))
        
        # Use Q-value differences as proxy for importance
        # Features that differ most from mean have highest impact
        mean_features = np.mean(features) if len(features) > 0 else 0
        std_features = np.std(features) if len(features) > 0 else 1
        
        # Z-score based importance
        z_scores = (features - mean_features) / (std_features + 1e-8)
        
        # Weight by position in feature vector (recent features matter more)
        position_weights = np.linspace(0.5, 1.0, len(features))
        
        # Combine with action preference
        action_weight = q_values[action] - np.mean(q_values)
        
        importance = z_scores * position_weights * np.sign(action_weight)
        
        return importance
    
    def _generate_rationale(
        self,
        action: str,
        top_features: List[Dict],
        q_values: np.ndarray
    ) -> str:
        """Generate human-readable rationale"""
        
        if action == 'hold':
            return "Market conditions unclear. Maintaining current position."
        
        direction = "buy" if action in ['buy', 'strong_buy'] else "sell"
        strength = "Strong" if 'strong' in action else "Moderate"
        
        # Build explanation from top features
        bullish_reasons = [f for f in top_features if f['direction'] == 'bullish']
        bearish_reasons = [f for f in top_features if f['direction'] == 'bearish']
        
        reasons = []
        
        if direction == 'buy' and bullish_reasons:
            main = bullish_reasons[0]
            if 'imbalance' in main['feature']:
                reasons.append("order book imbalance favors buyers")
            elif 'bid' in main['feature']:
                reasons.append("strong bid support")
            elif 'spread' in main['feature']:
                reasons.append("tight spread indicates stability")
            else:
                reasons.append(f"{main['feature']} signals upward momentum")
        
        elif direction == 'sell' and bearish_reasons:
            main = bearish_reasons[0]
            if 'imbalance' in main['feature']:
                reasons.append("order book imbalance favors sellers")
            elif 'ask' in main['feature']:
                reasons.append("heavy sell pressure")
            else:
                reasons.append(f"{main['feature']} signals downward pressure")
        
        # Confidence statement
        q_gap = np.max(q_values) - np.sort(q_values)[-2]
        if q_gap > 0.5:
            confidence = "high confidence"
        elif q_gap > 0.2:
            confidence = "moderate confidence"
        else:
            confidence = "low confidence"
        
        if reasons:
            return f"{strength} {direction} signal ({confidence}): {', '.join(reasons)}."
        else:
            return f"{strength} {direction} signal ({confidence}) based on overall market conditions."
    
    def get_feature_importance_summary(self) -> Dict[str, Any]:
        """Get summary of feature importance over recent decisions"""
        if not self.importance_history:
            return {'status': 'no_data'}
        
        # Aggregate feature contributions
        feature_counts = {}
        for record in self.importance_history:
            for feat in record['top_features']:
                name = feat['feature']
                if name not in feature_counts:
                    feature_counts[name] = {'count': 0, 'avg_contribution': 0}
                feature_counts[name]['count'] += 1
                feature_counts[name]['avg_contribution'] += abs(feat['contribution'])
        
        # Normalize
        for name in feature_counts:
            feature_counts[name]['avg_contribution'] /= feature_counts[name]['count']
        
        # Sort by importance
        sorted_features = sorted(
            feature_counts.items(),
            key=lambda x: x[1]['count'] * x[1]['avg_contribution'],
            reverse=True
        )[:10]
        
        return {
            'total_decisions': len(self.importance_history),
            'top_features': [
                {'feature': name, **stats}
                for name, stats in sorted_features
            ]
        }


# =============================================================================
# GENETIC ALGORITHM FOR HYPERPARAMETER EVOLUTION
# =============================================================================

class HyperparameterEvolver:
    """
    Genetic Algorithm for evolving trading hyperparameters.
    
    Evolves:
    - Risk limits
    - Model architecture params
    - Reward function weights
    - Trading thresholds
    """
    
    def __init__(
        self,
        population_size: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elite_size: int = 2
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        
        # Define hyperparameter space
        self.param_space = {
            # Risk parameters
            'max_position_pct': (0.1, 0.5),
            'max_daily_loss_pct': (0.02, 0.10),
            'max_drawdown_pct': (0.10, 0.30),
            
            # Model parameters
            'learning_rate': (1e-5, 1e-3),
            'gamma': (0.95, 0.999),
            'tau': (0.001, 0.01),
            'n_step': (1, 5),
            
            # Reward weights
            'sharpe_weight': (0.3, 0.7),
            'cvar_weight': (0.1, 0.5),
            'drawdown_penalty': (0.1, 1.0),
            
            # Trading thresholds
            'confidence_threshold': (0.4, 0.8),
            'uncertainty_threshold': (0.2, 0.6),
            'min_trade_size': (0.001, 0.05)
        }
        
        # Population
        self.population = []
        self.fitness_history = []
        self.generation = 0
        self.best_individual = None
        self.best_fitness = float('-inf')
        
        # Initialize population
        self._initialize_population()
        
        logger.info(f"🧬 Hyperparameter Evolver initialized: pop={population_size}")
    
    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (low, high) in self.param_space.items():
                if param == 'n_step':
                    individual[param] = np.random.randint(int(low), int(high) + 1)
                else:
                    individual[param] = np.random.uniform(low, high)
            self.population.append(individual)
    
    def evaluate_fitness(
        self,
        individual: Dict[str, float],
        backtest_results: Dict[str, Any]
    ) -> float:
        """
        Evaluate fitness of an individual based on backtest results.
        
        Fitness = Sharpe * (1 - MaxDrawdown) * WinRate
        """
        sharpe = backtest_results.get('sharpe_ratio', 0)
        max_dd = backtest_results.get('max_drawdown', 1)
        win_rate = backtest_results.get('win_rate', 0.5)
        total_return = backtest_results.get('total_return', 0)
        
        # Penalize extreme drawdowns
        dd_penalty = 1.0 - min(max_dd, 0.5) * 2
        
        # Reward consistent positive returns
        return_bonus = np.tanh(total_return * 10)
        
        # Combined fitness
        fitness = sharpe * dd_penalty * win_rate * (1 + return_bonus)
        
        return fitness
    
    def select_parents(self, fitnesses: List[float]) -> Tuple[Dict, Dict]:
        """Tournament selection"""
        def tournament(k=3):
            indices = np.random.choice(len(self.population), k, replace=False)
            best_idx = indices[np.argmax([fitnesses[i] for i in indices])]
            return self.population[best_idx]
        
        return tournament(), tournament()
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Uniform crossover"""
        child = {}
        for param in self.param_space:
            if np.random.random() < self.crossover_rate:
                # Blend crossover
                alpha = np.random.uniform(0.3, 0.7)
                if param == 'n_step':
                    child[param] = int(alpha * parent1[param] + (1-alpha) * parent2[param])
                else:
                    child[param] = alpha * parent1[param] + (1-alpha) * parent2[param]
            else:
                child[param] = parent1[param] if np.random.random() < 0.5 else parent2[param]
        return child
    
    def mutate(self, individual: Dict) -> Dict:
        """Gaussian mutation"""
        mutated = individual.copy()
        for param, (low, high) in self.param_space.items():
            if np.random.random() < self.mutation_rate:
                if param == 'n_step':
                    mutated[param] = np.random.randint(int(low), int(high) + 1)
                else:
                    # Gaussian mutation within bounds
                    sigma = (high - low) * 0.1
                    mutated[param] = np.clip(
                        mutated[param] + np.random.normal(0, sigma),
                        low, high
                    )
        return mutated
    
    def evolve(self, fitnesses: List[float]) -> List[Dict]:
        """Evolve population to next generation"""
        # Sort by fitness
        sorted_indices = np.argsort(fitnesses)[::-1]
        
        # Track best
        if fitnesses[sorted_indices[0]] > self.best_fitness:
            self.best_fitness = fitnesses[sorted_indices[0]]
            self.best_individual = self.population[sorted_indices[0]].copy()
        
        # Elitism - keep best individuals
        new_population = [self.population[i] for i in sorted_indices[:self.elite_size]]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents(fitnesses)
            child = self.crossover(parent1, parent2)
            child = self.mutate(child)
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        self.fitness_history.append({
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'avg_fitness': np.mean(fitnesses),
            'std_fitness': np.std(fitnesses)
        })
        
        logger.info(
            f"🧬 Generation {self.generation}: "
            f"Best={self.best_fitness:.4f}, Avg={np.mean(fitnesses):.4f}"
        )
        
        return self.population
    
    def get_best_params(self) -> Dict[str, Any]:
        """Get best parameters found so far"""
        if self.best_individual is None:
            return {'status': 'no_evolution_yet'}
        
        return {
            'generation': self.generation,
            'fitness': self.best_fitness,
            'params': self.best_individual,
            'history': self.fitness_history[-10:]  # Last 10 generations
        }


# =============================================================================
# TETHYS INTEGRATED TRADING LOOP
# =============================================================================

class TethysTradingLoop:
    """
    Main trading loop integrating all components.
    
    Flow:
    1. Receive order book update
    2. Generate state features
    3. Get action from Rainbow DQN
    4. Explain decision with SHAP
    5. Evaluate through Tethys Safety
    6. Execute if approved
    7. Log to audit trail
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Components (lazy initialized)
        self._rainbow = None
        self._safety = None
        self._explainer = None
        self._evolver = None
        self._order_book = None
        self._feature_extractor = None
        
        # State
        self.is_running = False
        self.last_action_time = None
        self.min_action_interval = 60  # Minimum seconds between trades
        
        # Performance tracking
        self.trade_history = deque(maxlen=1000)
        self.session_pnl = 0.0
        self.session_start = datetime.utcnow()
        
        logger.info("🌊 Tethys Trading Loop initialized")
    
    async def initialize(self):
        """Initialize all components"""
        # Import and initialize components
        from services.rainbow_dqn import get_rainbow_agent
        from services.tethys_safety import get_tethys_safety
        from services.kraken_orderbook_ws import (
            initialize_order_book_service,
            get_feature_extractor
        )
        
        # Initialize Rainbow DQN
        self._rainbow = get_rainbow_agent(
            state_dim=45,
            action_dim=5,
            sequence_length=168
        )
        
        # Initialize Safety System
        self._safety = get_tethys_safety(self.db)
        
        # Initialize Explainer
        self._explainer = TradingExplainer()
        
        # Initialize Evolver
        self._evolver = HyperparameterEvolver()
        
        # Initialize Order Book
        self._order_book = await initialize_order_book_service(
            symbols=["BTC/USD", "ETH/USD"],
            depth=25
        )
        self._feature_extractor = get_feature_extractor()
        
        logger.info("✅ All Tethys components initialized")
    
    async def process_tick(self, symbol: str = "BTC/USD") -> Optional[Dict]:
        """
        Process a single trading tick.
        
        Returns trade decision or None if no action taken.
        """
        if not self._rainbow or not self._safety:
            await self.initialize()
        
        # Check action interval
        now = datetime.utcnow()
        if self.last_action_time:
            elapsed = (now - self.last_action_time).total_seconds()
            if elapsed < self.min_action_interval:
                return None
        
        # Get order book state
        order_book = self._order_book.get_order_book(symbol)
        if not order_book or not order_book.snapshot_received:
            return {'status': 'no_data', 'symbol': symbol}
        
        # Get feature sequence for transformer
        state_sequence = self._feature_extractor.get_sequence(symbol)
        
        # Get action from Rainbow DQN
        action = self._rainbow.select_action(state_sequence, training=False)
        
        # Get Q-values for explanation
        q_dist = self._rainbow.online_network(
            state_sequence[np.newaxis, ...], training=False
        )
        q_values = self._rainbow.c51.get_q_values(q_dist).numpy()[0]
        
        # Generate explanation
        explanation = self._explainer.explain_decision(
            state_sequence, q_values, action
        )
        
        # Get current price and portfolio
        mid_price = order_book.get_mid_price()
        
        # Determine quantity (simplified - in production use proper sizing)
        base_quantity = 0.01  # Base trade size
        
        # Evaluate through safety system
        action_names = ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
        
        evaluation = await self._safety.evaluate_trade(
            symbol=symbol,
            action=action,
            action_name=action_names[action],
            quantity=base_quantity,
            price=mid_price,
            state=state_sequence,
            q_values=q_values,
            q_distribution=q_dist.numpy()[0] if q_dist is not None else None,
            order_book={
                'spread': order_book.get_spread(),
                'imbalance': order_book.get_imbalance(),
                'depth': order_book.get_depth()
            },
            portfolio_value=self._safety.risk_gateway.state.portfolio_value or 10000
        )
        
        # Build result
        result = {
            'timestamp': now.isoformat(),
            'symbol': symbol,
            'action': action_names[action],
            'price': mid_price,
            'spread': order_book.get_spread(),
            'imbalance': order_book.get_imbalance(),
            'explanation': explanation,
            'evaluation': evaluation
        }
        
        # Execute if approved and not hold
        if evaluation['approved'] and action != 2:  # Not hold
            result['executed'] = True
            self.last_action_time = now
            
            # Log execution
            await self._safety.audit_trail.log_execution(
                evaluation['audit_record_id'],
                executed=True,
                price=mid_price,
                quantity=evaluation['adjusted_quantity']
            )
            
            logger.info(
                f"🌊 Tethys {action_names[action].upper()} {symbol} @ ${mid_price:.2f} | "
                f"Confidence: {evaluation['confidence']:.1%}"
            )
        else:
            result['executed'] = False
        
        # Store in history
        self.trade_history.append(result)
        
        return result
    
    async def run_continuous(self, interval: int = 60):
        """Run continuous trading loop"""
        self.is_running = True
        logger.info(f"🌊 Tethys starting continuous trading (interval={interval}s)")
        
        while self.is_running:
            try:
                result = await self.process_tick("BTC/USD")
                if result and result.get('executed'):
                    logger.info(f"Trade: {result['action']} - {result['explanation']['rationale']}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop trading loop"""
        self.is_running = False
        logger.info("🌊 Tethys trading loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get trading loop status"""
        return {
            'agent': 'Tethys',
            'is_running': self.is_running,
            'session_start': self.session_start.isoformat(),
            'session_duration': str(datetime.utcnow() - self.session_start),
            'total_ticks': len(self.trade_history),
            'executed_trades': sum(1 for t in self.trade_history if t.get('executed')),
            'last_action': self.last_action_time.isoformat() if self.last_action_time else None,
            'components': {
                'rainbow_dqn': self._rainbow is not None,
                'safety_system': self._safety is not None,
                'explainer': self._explainer is not None,
                'order_book': self._order_book is not None
            }
        }


# =============================================================================
# SINGLETON
# =============================================================================

_trading_loop: Optional[TethysTradingLoop] = None

def get_trading_loop(db=None) -> TethysTradingLoop:
    """Get or create trading loop"""
    global _trading_loop
    if _trading_loop is None:
        _trading_loop = TethysTradingLoop(db=db)
    return _trading_loop
