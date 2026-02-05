"""
Tethys Production Safety Systems
=================================
Critical production infrastructure for the Tethys trading agent.

Components:
1. Pre-Trade Risk Gateway - Hard limits enforced OUTSIDE the RL agent
2. Audit Trail - Full logging of every decision to MongoDB
3. Uncertainty Quantification - Reduces position when uncertain

Named after Tethys, the Greek Titan of fresh water and nourishment,
symbolizing the flow of capital and sustenance of wealth.
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
import json
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# AGENT IDENTITY
# =============================================================================

AGENT_NAME = "Tethys"
AGENT_VERSION = "1.0.0"
AGENT_DESCRIPTION = "Rainbow DQN with Transformer - Production Trading Agent"


# =============================================================================
# 1. PRE-TRADE RISK GATEWAY
# =============================================================================

class RiskViolationType(Enum):
    """Types of risk violations"""
    MAX_POSITION_SIZE = "max_position_size"
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_LEVERAGE = "max_leverage"
    MAX_SECTOR_EXPOSURE = "max_sector_exposure"
    MAX_SINGLE_TRADE = "max_single_trade"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    VOLATILITY_LIMIT = "volatility_limit"
    CIRCUIT_BREAKER = "circuit_breaker"
    PRICE_SANITY = "price_sanity"


@dataclass
class RiskLimits:
    """Hard-coded risk limits - NOT modifiable by RL agent"""
    # Position limits
    max_position_pct: float = 0.25  # Max 25% of portfolio in single asset
    max_total_exposure_pct: float = 1.0  # Max 100% exposure (no leverage by default)
    max_single_trade_pct: float = 0.10  # Max 10% per trade
    
    # Loss limits
    max_daily_loss_pct: float = 0.05  # Max 5% daily loss
    max_drawdown_pct: float = 0.15  # Max 15% drawdown from peak
    max_consecutive_losses: int = 5  # Max 5 consecutive losing trades
    
    # Volatility limits
    max_volatility_multiplier: float = 3.0  # Reduce size if vol > 3x normal
    volatility_lookback: int = 24  # Hours for volatility calculation
    
    # Circuit breaker
    circuit_breaker_loss_pct: float = 0.10  # Halt trading if 10% loss in session
    circuit_breaker_duration_hours: int = 24  # How long to halt
    
    # Price sanity
    max_price_change_pct: float = 0.20  # Reject if price moved >20% in 1 hour
    min_liquidity_usd: float = 1000  # Minimum order book depth required


@dataclass
class RiskState:
    """Current risk state - updated in real-time"""
    portfolio_value: float = 0.0
    peak_value: float = 0.0
    daily_start_value: float = 0.0
    daily_pnl: float = 0.0
    current_drawdown: float = 0.0
    consecutive_losses: int = 0
    positions: Dict[str, float] = field(default_factory=dict)
    recent_returns: deque = field(default_factory=lambda: deque(maxlen=168))
    circuit_breaker_active: bool = False
    circuit_breaker_until: Optional[datetime] = None
    last_update: datetime = field(default_factory=datetime.utcnow)


class PreTradeRiskGateway:
    """
    Pre-Trade Risk Gateway
    ======================
    Enforces hard risk limits OUTSIDE the RL agent.
    
    This is the LAST LINE OF DEFENSE before order execution.
    The RL agent cannot bypass or modify these limits.
    """
    
    def __init__(self, limits: RiskLimits = None, db=None):
        self.limits = limits or RiskLimits()
        self.state = RiskState()
        self.db = db
        self.violations_log: List[Dict] = []
        
        logger.info(f"🛡️ {AGENT_NAME} Risk Gateway initialized")
        logger.info(f"   Max position: {self.limits.max_position_pct*100}%")
        logger.info(f"   Max daily loss: {self.limits.max_daily_loss_pct*100}%")
        logger.info(f"   Circuit breaker: {self.limits.circuit_breaker_loss_pct*100}%")
    
    def update_state(
        self,
        portfolio_value: float,
        positions: Dict[str, float],
        last_trade_pnl: Optional[float] = None
    ):
        """Update risk state with latest portfolio data"""
        now = datetime.utcnow()
        
        # Update portfolio value
        self.state.portfolio_value = portfolio_value
        self.state.positions = positions
        self.state.last_update = now
        
        # Update peak (for drawdown)
        if portfolio_value > self.state.peak_value:
            self.state.peak_value = portfolio_value
        
        # Calculate drawdown
        if self.state.peak_value > 0:
            self.state.current_drawdown = (
                self.state.peak_value - portfolio_value
            ) / self.state.peak_value
        
        # Reset daily PnL at midnight UTC
        if now.date() > self.state.last_update.date():
            self.state.daily_start_value = portfolio_value
            self.state.daily_pnl = 0.0
        else:
            self.state.daily_pnl = (
                portfolio_value - self.state.daily_start_value
            ) / self.state.daily_start_value if self.state.daily_start_value > 0 else 0
        
        # Track consecutive losses
        if last_trade_pnl is not None:
            if last_trade_pnl < 0:
                self.state.consecutive_losses += 1
            else:
                self.state.consecutive_losses = 0
        
        # Check circuit breaker
        if self.state.circuit_breaker_active:
            if now >= self.state.circuit_breaker_until:
                self.state.circuit_breaker_active = False
                self.state.circuit_breaker_until = None
                logger.info(f"🟢 {AGENT_NAME} Circuit breaker deactivated")
    
    def check_trade(
        self,
        symbol: str,
        action: str,  # 'buy', 'sell', 'hold'
        quantity: float,
        price: float,
        order_book_depth: float = 0.0
    ) -> Tuple[bool, List[RiskViolationType], Dict[str, Any]]:
        """
        Check if a proposed trade passes all risk limits.
        
        Returns:
            (approved, violations, details)
        """
        violations = []
        details = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        trade_value = quantity * price
        
        # 1. Circuit Breaker Check
        if self.state.circuit_breaker_active:
            violations.append(RiskViolationType.CIRCUIT_BREAKER)
            details['checks']['circuit_breaker'] = {
                'passed': False,
                'active_until': self.state.circuit_breaker_until.isoformat()
            }
        else:
            details['checks']['circuit_breaker'] = {'passed': True}
        
        # 2. Daily Loss Check
        if self.state.daily_pnl <= -self.limits.max_daily_loss_pct:
            violations.append(RiskViolationType.MAX_DAILY_LOSS)
            details['checks']['daily_loss'] = {
                'passed': False,
                'current': self.state.daily_pnl,
                'limit': -self.limits.max_daily_loss_pct
            }
            
            # Activate circuit breaker if loss exceeds threshold
            if self.state.daily_pnl <= -self.limits.circuit_breaker_loss_pct:
                self._activate_circuit_breaker()
        else:
            details['checks']['daily_loss'] = {'passed': True}
        
        # 3. Drawdown Check
        if self.state.current_drawdown >= self.limits.max_drawdown_pct:
            violations.append(RiskViolationType.MAX_DRAWDOWN)
            details['checks']['drawdown'] = {
                'passed': False,
                'current': self.state.current_drawdown,
                'limit': self.limits.max_drawdown_pct
            }
        else:
            details['checks']['drawdown'] = {'passed': True}
        
        # 4. Single Trade Size Check
        if self.state.portfolio_value > 0:
            trade_pct = trade_value / self.state.portfolio_value
            if trade_pct > self.limits.max_single_trade_pct:
                violations.append(RiskViolationType.MAX_SINGLE_TRADE)
                details['checks']['single_trade'] = {
                    'passed': False,
                    'trade_pct': trade_pct,
                    'limit': self.limits.max_single_trade_pct
                }
            else:
                details['checks']['single_trade'] = {'passed': True, 'trade_pct': trade_pct}
        
        # 5. Position Size Check (after trade)
        if action == 'buy':
            new_position = self.state.positions.get(symbol, 0) + quantity
        elif action == 'sell':
            new_position = self.state.positions.get(symbol, 0) - quantity
        else:
            new_position = self.state.positions.get(symbol, 0)
        
        if self.state.portfolio_value > 0:
            position_pct = abs(new_position * price) / self.state.portfolio_value
            if position_pct > self.limits.max_position_pct:
                violations.append(RiskViolationType.MAX_POSITION_SIZE)
                details['checks']['position_size'] = {
                    'passed': False,
                    'position_pct': position_pct,
                    'limit': self.limits.max_position_pct
                }
            else:
                details['checks']['position_size'] = {'passed': True, 'position_pct': position_pct}
        
        # 6. Consecutive Losses Check
        if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
            violations.append(RiskViolationType.CONSECUTIVE_LOSSES)
            details['checks']['consecutive_losses'] = {
                'passed': False,
                'count': self.state.consecutive_losses,
                'limit': self.limits.max_consecutive_losses
            }
        else:
            details['checks']['consecutive_losses'] = {'passed': True}
        
        # 7. Liquidity Check
        if order_book_depth < self.limits.min_liquidity_usd:
            violations.append(RiskViolationType.PRICE_SANITY)
            details['checks']['liquidity'] = {
                'passed': False,
                'depth': order_book_depth,
                'min_required': self.limits.min_liquidity_usd
            }
        else:
            details['checks']['liquidity'] = {'passed': True}
        
        # Log violations
        approved = len(violations) == 0
        details['approved'] = approved
        details['violations'] = [v.value for v in violations]
        
        if not approved:
            self.violations_log.append(details)
            logger.warning(
                f"⚠️ {AGENT_NAME} TRADE BLOCKED: {symbol} {action} - "
                f"Violations: {[v.value for v in violations]}"
            )
        
        return approved, violations, details
    
    def _activate_circuit_breaker(self):
        """Activate circuit breaker - halt all trading"""
        self.state.circuit_breaker_active = True
        self.state.circuit_breaker_until = (
            datetime.utcnow() + timedelta(hours=self.limits.circuit_breaker_duration_hours)
        )
        logger.critical(
            f"🔴 {AGENT_NAME} CIRCUIT BREAKER ACTIVATED! "
            f"Trading halted until {self.state.circuit_breaker_until}"
        )
    
    def get_adjusted_size(
        self,
        symbol: str,
        base_quantity: float,
        price: float,
        volatility: float = None
    ) -> float:
        """
        Adjust trade size based on current risk state.
        
        Reduces size when:
        - Approaching position limits
        - High volatility
        - Consecutive losses
        """
        adjusted = base_quantity
        
        # Reduce for volatility
        if volatility is not None and len(self.state.recent_returns) > 0:
            normal_vol = np.std(list(self.state.recent_returns)) or 0.01
            vol_ratio = volatility / normal_vol
            if vol_ratio > self.limits.max_volatility_multiplier:
                vol_reduction = 1.0 / vol_ratio
                adjusted *= vol_reduction
                logger.info(f"📉 Size reduced {vol_reduction:.1%} due to high volatility")
        
        # Reduce for consecutive losses
        if self.state.consecutive_losses > 2:
            loss_reduction = 1.0 / (1 + self.state.consecutive_losses * 0.2)
            adjusted *= loss_reduction
            logger.info(f"📉 Size reduced {loss_reduction:.1%} due to {self.state.consecutive_losses} losses")
        
        # Cap at position limit
        if self.state.portfolio_value > 0:
            max_value = self.state.portfolio_value * self.limits.max_single_trade_pct
            max_quantity = max_value / price
            adjusted = min(adjusted, max_quantity)
        
        return adjusted
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk gateway status"""
        return {
            'agent': AGENT_NAME,
            'version': AGENT_VERSION,
            'limits': asdict(self.limits),
            'state': {
                'portfolio_value': self.state.portfolio_value,
                'peak_value': self.state.peak_value,
                'daily_pnl_pct': self.state.daily_pnl,
                'current_drawdown_pct': self.state.current_drawdown,
                'consecutive_losses': self.state.consecutive_losses,
                'circuit_breaker_active': self.state.circuit_breaker_active,
                'positions': self.state.positions
            },
            'recent_violations': self.violations_log[-10:]
        }


# =============================================================================
# 2. AUDIT TRAIL SYSTEM
# =============================================================================

@dataclass
class AuditRecord:
    """Complete audit record for a single decision"""
    # Identity
    record_id: str
    agent_name: str = AGENT_NAME
    agent_version: str = AGENT_VERSION
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # State
    state_features: List[float] = field(default_factory=list)
    state_hash: str = ""
    portfolio_value: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    
    # Order Book Snapshot
    order_book_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Model Output
    action: int = 0
    action_name: str = ""
    q_values: List[float] = field(default_factory=list)
    q_distribution: List[List[float]] = field(default_factory=list)
    confidence: float = 0.0
    uncertainty: float = 0.0
    
    # Risk Check
    risk_approved: bool = False
    risk_violations: List[str] = field(default_factory=list)
    risk_details: Dict[str, Any] = field(default_factory=dict)
    
    # Execution
    executed: bool = False
    execution_price: float = 0.0
    execution_quantity: float = 0.0
    execution_id: str = ""
    
    # Reward (filled after outcome known)
    reward: Optional[float] = None
    pnl: Optional[float] = None
    
    # Explainability
    feature_attributions: Dict[str, float] = field(default_factory=dict)
    decision_rationale: str = ""


class AuditTrail:
    """
    Complete Audit Trail System
    ===========================
    Logs every decision for regulatory compliance and analysis.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.session_records: List[AuditRecord] = []
        self.session_id = self._generate_session_id()
        
        logger.info(f"📋 {AGENT_NAME} Audit Trail initialized - Session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        now = datetime.utcnow()
        return f"{AGENT_NAME}_{now.strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_record_id(self) -> str:
        """Generate unique record ID"""
        import uuid
        return f"{self.session_id}_{uuid.uuid4().hex[:8]}"
    
    def _hash_state(self, state: np.ndarray) -> str:
        """Create deterministic hash of state"""
        state_bytes = state.tobytes()
        return hashlib.sha256(state_bytes).hexdigest()[:16]
    
    async def log_decision(
        self,
        state: np.ndarray,
        action: int,
        action_name: str,
        q_values: np.ndarray,
        q_distribution: np.ndarray = None,
        confidence: float = 0.0,
        uncertainty: float = 0.0,
        portfolio_value: float = 0.0,
        positions: Dict[str, float] = None,
        order_book: Dict[str, Any] = None,
        risk_approved: bool = True,
        risk_violations: List[str] = None,
        risk_details: Dict[str, Any] = None,
        feature_attributions: Dict[str, float] = None,
        rationale: str = ""
    ) -> AuditRecord:
        """Log a decision to the audit trail"""
        
        record = AuditRecord(
            record_id=self._generate_record_id(),
            timestamp=datetime.utcnow(),
            state_features=state.flatten().tolist()[:100],  # Truncate for storage
            state_hash=self._hash_state(state),
            portfolio_value=portfolio_value,
            positions=positions or {},
            order_book_snapshot=order_book or {},
            action=action,
            action_name=action_name,
            q_values=q_values.tolist() if isinstance(q_values, np.ndarray) else q_values,
            q_distribution=q_distribution.tolist() if q_distribution is not None else [],
            confidence=confidence,
            uncertainty=uncertainty,
            risk_approved=risk_approved,
            risk_violations=risk_violations or [],
            risk_details=risk_details or {},
            feature_attributions=feature_attributions or {},
            decision_rationale=rationale
        )
        
        self.session_records.append(record)
        
        # Persist to MongoDB
        if self.db is not None:
            try:
                await self.db.tethys_audit_trail.insert_one({
                    **asdict(record),
                    'timestamp': record.timestamp,
                    'session_id': self.session_id
                })
            except Exception as e:
                logger.error(f"Failed to persist audit record: {e}")
        
        return record
    
    async def log_execution(
        self,
        record_id: str,
        executed: bool,
        price: float = 0.0,
        quantity: float = 0.0,
        execution_id: str = ""
    ):
        """Log execution details for a decision"""
        # Find record in session
        for record in self.session_records:
            if record.record_id == record_id:
                record.executed = executed
                record.execution_price = price
                record.execution_quantity = quantity
                record.execution_id = execution_id
                break
        
        # Update in MongoDB
        if self.db is not None:
            try:
                await self.db.tethys_audit_trail.update_one(
                    {'record_id': record_id},
                    {'$set': {
                        'executed': executed,
                        'execution_price': price,
                        'execution_quantity': quantity,
                        'execution_id': execution_id
                    }}
                )
            except Exception as e:
                logger.error(f"Failed to update audit record: {e}")
    
    async def log_outcome(
        self,
        record_id: str,
        reward: float,
        pnl: float
    ):
        """Log outcome after trade settled"""
        for record in self.session_records:
            if record.record_id == record_id:
                record.reward = reward
                record.pnl = pnl
                break
        
        if self.db is not None:
            try:
                await self.db.tethys_audit_trail.update_one(
                    {'record_id': record_id},
                    {'$set': {'reward': reward, 'pnl': pnl}}
                )
            except Exception as e:
                logger.error(f"Failed to update outcome: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        total = len(self.session_records)
        executed = sum(1 for r in self.session_records if r.executed)
        blocked = sum(1 for r in self.session_records if not r.risk_approved)
        
        return {
            'session_id': self.session_id,
            'agent': AGENT_NAME,
            'total_decisions': total,
            'executed_trades': executed,
            'blocked_by_risk': blocked,
            'avg_confidence': np.mean([r.confidence for r in self.session_records]) if total > 0 else 0,
            'avg_uncertainty': np.mean([r.uncertainty for r in self.session_records]) if total > 0 else 0
        }


# =============================================================================
# 3. UNCERTAINTY QUANTIFICATION
# =============================================================================

class UncertaintyQuantifier:
    """
    Uncertainty Quantification System
    ==================================
    Measures model uncertainty and adjusts behavior accordingly.
    
    Methods:
    1. Ensemble disagreement (variance across models)
    2. Distributional variance (from C51 distribution)
    3. Temporal consistency (agreement with recent decisions)
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        uncertainty_threshold: float = 0.4,
        lookback: int = 10
    ):
        self.confidence_threshold = confidence_threshold
        self.uncertainty_threshold = uncertainty_threshold
        self.recent_decisions = deque(maxlen=lookback)
        
        logger.info(f"🎯 {AGENT_NAME} Uncertainty Quantifier initialized")
    
    def compute_distributional_uncertainty(
        self,
        q_distribution: np.ndarray,
        support: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute uncertainty from C51 value distribution.
        
        Args:
            q_distribution: Shape (num_actions, num_atoms) - probability over atoms
            support: Shape (num_atoms,) - atom values
        
        Returns:
            (confidence, uncertainty)
        """
        # Get best action's distribution
        q_values = np.sum(q_distribution * support, axis=-1)
        best_action = np.argmax(q_values)
        best_dist = q_distribution[best_action]
        
        # Compute variance of the distribution
        mean = np.sum(best_dist * support)
        variance = np.sum(best_dist * (support - mean) ** 2)
        std = np.sqrt(variance)
        
        # High variance = high uncertainty
        # Normalize by range of support
        support_range = support[-1] - support[0]
        normalized_std = std / support_range
        
        uncertainty = min(1.0, normalized_std * 2)  # Scale to [0, 1]
        confidence = 1.0 - uncertainty
        
        # Also check if distribution is concentrated
        entropy = -np.sum(best_dist * np.log(best_dist + 1e-8))
        max_entropy = np.log(len(support))
        entropy_ratio = entropy / max_entropy
        
        # High entropy = uniform distribution = uncertain
        confidence *= (1.0 - entropy_ratio * 0.5)
        
        return confidence, uncertainty
    
    def compute_action_confidence(
        self,
        q_values: np.ndarray
    ) -> Tuple[float, int]:
        """
        Compute confidence in action selection from Q-values.
        
        High confidence = large gap between best and second-best action
        """
        sorted_q = np.sort(q_values)[::-1]
        best_action = np.argmax(q_values)
        
        # Gap between best and second-best
        q_gap = sorted_q[0] - sorted_q[1] if len(sorted_q) > 1 else 0
        
        # Normalize by range
        q_range = sorted_q[0] - sorted_q[-1] if len(sorted_q) > 1 else 1
        normalized_gap = q_gap / (q_range + 1e-8)
        
        confidence = min(1.0, normalized_gap * 2)
        
        return confidence, best_action
    
    def compute_temporal_consistency(
        self,
        current_action: int,
        current_state_hash: str
    ) -> float:
        """
        Check if current decision is consistent with recent history.
        
        Rapid flip-flopping indicates uncertainty.
        """
        if len(self.recent_decisions) < 3:
            return 1.0  # Not enough history
        
        # Count action changes
        recent_actions = [d['action'] for d in self.recent_decisions]
        changes = sum(1 for i in range(1, len(recent_actions)) if recent_actions[i] != recent_actions[i-1])
        
        # High changes = low consistency
        consistency = 1.0 - (changes / len(recent_actions))
        
        return consistency
    
    def should_reduce_exposure(
        self,
        confidence: float,
        uncertainty: float
    ) -> Tuple[bool, float]:
        """
        Determine if agent should reduce position size due to uncertainty.
        
        Returns:
            (should_reduce, reduction_factor)
        """
        # Reduce if low confidence OR high uncertainty
        if confidence < self.confidence_threshold:
            reduction = confidence / self.confidence_threshold
            return True, reduction
        
        if uncertainty > self.uncertainty_threshold:
            reduction = 1.0 - (uncertainty - self.uncertainty_threshold) / (1.0 - self.uncertainty_threshold)
            return True, max(0.2, reduction)
        
        return False, 1.0
    
    def record_decision(
        self,
        action: int,
        state_hash: str,
        confidence: float,
        uncertainty: float
    ):
        """Record decision for temporal tracking"""
        self.recent_decisions.append({
            'action': action,
            'state_hash': state_hash,
            'confidence': confidence,
            'uncertainty': uncertainty,
            'timestamp': datetime.utcnow()
        })
    
    def get_uncertainty_report(self) -> Dict[str, Any]:
        """Get uncertainty analysis report"""
        if not self.recent_decisions:
            return {'status': 'no_data'}
        
        confidences = [d['confidence'] for d in self.recent_decisions]
        uncertainties = [d['uncertainty'] for d in self.recent_decisions]
        
        return {
            'agent': AGENT_NAME,
            'recent_decisions': len(self.recent_decisions),
            'avg_confidence': np.mean(confidences),
            'min_confidence': np.min(confidences),
            'avg_uncertainty': np.mean(uncertainties),
            'max_uncertainty': np.max(uncertainties),
            'temporal_consistency': self.compute_temporal_consistency(
                self.recent_decisions[-1]['action'],
                self.recent_decisions[-1]['state_hash']
            )
        }


# =============================================================================
# TETHYS INTEGRATED SAFETY SYSTEM
# =============================================================================

class TethysSafetySystem:
    """
    Integrated Safety System for Tethys Trading Agent
    ==================================================
    Combines all safety components into a unified interface.
    """
    
    def __init__(self, db=None, limits: RiskLimits = None):
        self.risk_gateway = PreTradeRiskGateway(limits=limits, db=db)
        self.audit_trail = AuditTrail(db=db)
        self.uncertainty = UncertaintyQuantifier()
        self.db = db
        
        logger.info(f"🏛️ {AGENT_NAME} Safety System initialized")
    
    async def evaluate_trade(
        self,
        symbol: str,
        action: int,
        action_name: str,
        quantity: float,
        price: float,
        state: np.ndarray,
        q_values: np.ndarray,
        q_distribution: np.ndarray = None,
        order_book: Dict = None,
        portfolio_value: float = 0.0,
        positions: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Complete trade evaluation through all safety systems.
        
        Returns:
            Decision dict with approval status and all checks
        """
        # 1. Compute uncertainty
        if q_distribution is not None:
            support = np.linspace(-10, 10, 51)  # C51 support
            confidence, uncertainty = self.uncertainty.compute_distributional_uncertainty(
                q_distribution, support
            )
        else:
            confidence, _ = self.uncertainty.compute_action_confidence(q_values)
            uncertainty = 1.0 - confidence
        
        # 2. Check if should reduce due to uncertainty
        should_reduce, reduction_factor = self.uncertainty.should_reduce_exposure(
            confidence, uncertainty
        )
        
        adjusted_quantity = quantity * reduction_factor if should_reduce else quantity
        
        # 3. Risk gateway check
        order_book_depth = order_book.get('depth', {}).get('total_depth_usd', 0) if order_book else 0
        
        risk_approved, violations, risk_details = self.risk_gateway.check_trade(
            symbol=symbol,
            action=action_name,
            quantity=adjusted_quantity,
            price=price,
            order_book_depth=order_book_depth
        )
        
        # 4. Final decision
        final_approved = risk_approved and confidence >= 0.3  # Min confidence threshold
        
        # Generate rationale
        if final_approved:
            rationale = f"Trade approved: {action_name} {adjusted_quantity:.4f} {symbol} @ ${price:.2f}"
            if should_reduce:
                rationale += f" (reduced {reduction_factor:.1%} due to uncertainty)"
        else:
            reasons = violations + (['low_confidence'] if confidence < 0.3 else [])
            rationale = f"Trade BLOCKED: {reasons}"
        
        # 5. Log to audit trail
        audit_record = await self.audit_trail.log_decision(
            state=state,
            action=action,
            action_name=action_name,
            q_values=q_values,
            q_distribution=q_distribution,
            confidence=confidence,
            uncertainty=uncertainty,
            portfolio_value=portfolio_value,
            positions=positions,
            order_book=order_book,
            risk_approved=risk_approved,
            risk_violations=[v.value if hasattr(v, 'value') else str(v) for v in violations],
            risk_details=risk_details,
            rationale=rationale
        )
        
        # 6. Record for temporal tracking
        state_hash = self.audit_trail._hash_state(state)
        self.uncertainty.record_decision(action, state_hash, confidence, uncertainty)
        
        # Convert numpy types to native Python for JSON serialization
        return {
            'approved': bool(final_approved),
            'action': int(action),
            'action_name': str(action_name),
            'original_quantity': float(quantity),
            'adjusted_quantity': float(adjusted_quantity),
            'reduction_factor': float(reduction_factor),
            'confidence': float(confidence),
            'uncertainty': float(uncertainty),
            'risk_approved': bool(risk_approved),
            'violations': [v.value if hasattr(v, 'value') else str(v) for v in violations],
            'audit_record_id': str(audit_record.record_id),
            'rationale': str(rationale)
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get complete safety system status"""
        return {
            'agent': AGENT_NAME,
            'version': AGENT_VERSION,
            'risk_gateway': self.risk_gateway.get_status(),
            'audit_summary': self.audit_trail.get_session_summary(),
            'uncertainty': self.uncertainty.get_uncertainty_report()
        }


# =============================================================================
# SINGLETON
# =============================================================================

_safety_system: Optional[TethysSafetySystem] = None

def get_tethys_safety(db=None) -> TethysSafetySystem:
    """Get or create Tethys safety system"""
    global _safety_system
    if _safety_system is None:
        _safety_system = TethysSafetySystem(db=db)
    return _safety_system
