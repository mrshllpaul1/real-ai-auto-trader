import asyncio
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class PortfolioRebalancer:
    """
    Automatic portfolio rebalancing to maintain target allocations
    """
    
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.rebalance_interval = 86400  # Daily
    
    async def get_target_allocation(self, user_id: str) -> Dict[str, float]:
        """Get user's target portfolio allocation"""
        allocation = await self.db.target_allocations.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not allocation:
            # Default allocation
            return {
                'BTC': 40,
                'ETH': 30,
                'SOL': 15,
                'USD': 15
            }
        
        return allocation.get('allocations', {})
    
    async def set_target_allocation(
        self,
        user_id: str,
        allocations: Dict[str, float]
    ) -> Dict[str, Any]:
        """Set target allocation percentages"""
        # Validate total equals 100%
        total = sum(allocations.values())
        if abs(total - 100) > 0.01:
            raise ValueError(f"Allocations must sum to 100%, got {total}%")
        
        await self.db.target_allocations.update_one(
            {'user_id': user_id},
            {'$set': {
                'user_id': user_id,
                'allocations': allocations,
                'updated_at': datetime.now().isoformat()
            }},
            upsert=True
        )
        
        return {'allocations': allocations, 'status': 'saved'}
    
    async def get_current_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get current portfolio holdings and values"""
        portfolio = await self.db.portfolios.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not portfolio:
            # Demo portfolio
            portfolio = {
                'user_id': user_id,
                'holdings': {
                    'BTC': {'amount': 0.1, 'value_usd': 4500},
                    'ETH': {'amount': 1.5, 'value_usd': 3750},
                    'SOL': {'amount': 20, 'value_usd': 2000},
                    'USD': {'amount': 1000, 'value_usd': 1000}
                },
                'total_value': 11250
            }
        
        return portfolio
    
    async def calculate_rebalance(
        self,
        user_id: str,
        prices: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Calculate rebalancing trades needed"""
        target = await self.get_target_allocation(user_id)
        portfolio = await self.get_current_portfolio(user_id)
        
        # Default prices if not provided
        if prices is None:
            prices = {'BTC': 45000, 'ETH': 2500, 'SOL': 100, 'USD': 1}
        
        holdings = portfolio.get('holdings', {})
        total_value = sum(h.get('value_usd', 0) for h in holdings.values())
        
        if total_value == 0:
            return {'message': 'No portfolio value', 'trades': []}
        
        # Calculate current vs target
        current_allocation = {}
        for asset, data in holdings.items():
            current_allocation[asset] = (data.get('value_usd', 0) / total_value) * 100
        
        # Calculate needed trades
        trades = []
        for asset, target_pct in target.items():
            current_pct = current_allocation.get(asset, 0)
            diff_pct = target_pct - current_pct
            diff_value = (diff_pct / 100) * total_value
            
            # Only rebalance if difference > 2%
            if abs(diff_pct) > 2:
                price = prices.get(asset, 1)
                amount = abs(diff_value) / price if price > 0 else 0
                
                trades.append({
                    'asset': asset,
                    'action': 'BUY' if diff_pct > 0 else 'SELL',
                    'current_pct': round(current_pct, 2),
                    'target_pct': round(target_pct, 2),
                    'diff_pct': round(diff_pct, 2),
                    'value_usd': round(abs(diff_value), 2),
                    'amount': round(amount, 6),
                    'price': price
                })
        
        # Sort by absolute value (largest trades first)
        trades.sort(key=lambda x: abs(x['value_usd']), reverse=True)
        
        return {
            'user_id': user_id,
            'total_value': total_value,
            'current_allocation': current_allocation,
            'target_allocation': target,
            'trades_needed': trades,
            'rebalance_value': sum(t['value_usd'] for t in trades),
            'calculated_at': datetime.now().isoformat()
        }
    
    async def execute_rebalance(
        self,
        user_id: str,
        mode: str = 'paper'
    ) -> Dict[str, Any]:
        """Execute rebalancing trades"""
        rebalance = await self.calculate_rebalance(user_id)
        trades = rebalance.get('trades_needed', [])
        
        if not trades:
            return {'message': 'Portfolio already balanced', 'trades_executed': 0}
        
        executed = []
        for trade in trades:
            trade_record = {
                'user_id': user_id,
                'asset': trade['asset'],
                'action': trade['action'],
                'amount': trade['amount'],
                'price': trade['price'],
                'value_usd': trade['value_usd'],
                'mode': mode,
                'type': 'REBALANCE',
                'executed_at': datetime.now().isoformat()
            }
            
            # In paper mode, just record. In live mode, would call exchange API
            if mode == 'live':
                # TODO: Integrate with Kraken for real execution
                trade_record['status'] = 'SIMULATED'
            else:
                trade_record['status'] = 'PAPER'
            
            await self.db.rebalance_trades.insert_one(dict(trade_record))
            executed.append(trade_record)
        
        # Update portfolio (simulation)
        await self.db.portfolios.update_one(
            {'user_id': user_id},
            {'$set': {'last_rebalance': datetime.now().isoformat()}},
            upsert=True
        )
        
        return {
            'trades_executed': len(executed),
            'trades': executed,
            'mode': mode,
            'total_rebalanced': sum(t['value_usd'] for t in executed)
        }
    
    async def get_rebalance_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get rebalancing history"""
        history = await self.db.rebalance_trades.find(
            {'user_id': user_id},
            {'_id': 0}
        ).sort('executed_at', -1).limit(limit).to_list(limit)
        return history
    
    async def set_auto_rebalance(
        self,
        user_id: str,
        enabled: bool,
        frequency: str = 'daily',
        threshold_pct: float = 5.0
    ) -> Dict[str, Any]:
        """Configure automatic rebalancing"""
        config = {
            'user_id': user_id,
            'enabled': enabled,
            'frequency': frequency,  # 'daily', 'weekly', 'monthly'
            'threshold_pct': threshold_pct,  # Minimum drift to trigger
            'updated_at': datetime.now().isoformat()
        }
        
        await self.db.auto_rebalance_config.update_one(
            {'user_id': user_id},
            {'$set': config},
            upsert=True
        )
        
        return config
    
    async def get_auto_rebalance_config(self, user_id: str) -> Dict[str, Any]:
        """Get auto-rebalance configuration"""
        config = await self.db.auto_rebalance_config.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not config:
            return {
                'enabled': False,
                'frequency': 'weekly',
                'threshold_pct': 5.0
            }
        
        return config
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'enabled': True,
            'target_allocations': {},
            'available_templates': ['conservative', 'balanced', 'aggressive', 'altcoin_heavy']
        }


# Singleton
_rebalancer = None

def get_rebalancer(db=None, kraken=None, market=None):
    """Get or create the rebalancer service"""
    global _rebalancer
    if _rebalancer is None and db is not None:
        _rebalancer = PortfolioRebalancer(db)
    return _rebalancer

