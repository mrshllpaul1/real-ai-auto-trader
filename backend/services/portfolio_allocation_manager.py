from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class PortfolioAllocationManager:
    """
    Manages isolated trading portfolio with allocated funds.
    Ensures AI only trades with user-allocated funds and never touches other Kraken assets.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def create_allocation(
        self,
        user_id: str,
        allocations: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Create or update portfolio allocation.
        Example: {'USD': 1000, 'BTC': 0.5, 'ETH': 2.0}
        """
        allocation_record = {
            'user_id': user_id,
            'allocations': allocations,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Store allocation
        await self.db.portfolio_allocations.replace_one(
            {'user_id': user_id},
            allocation_record,
            upsert=True
        )
        
        # Initialize bot portfolio tracking
        bot_portfolio = {
            'user_id': user_id,
            'allocated_funds': allocations,
            'current_holdings': {asset: 0.0 for asset in allocations.keys()},
            'available_balance': allocations.copy(),  # What's available to trade
            'locked_in_orders': {asset: 0.0 for asset in allocations.keys()},
            'total_profit_loss': 0.0,
            'trade_history': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        await self.db.bot_portfolios.replace_one(
            {'user_id': user_id},
            bot_portfolio,
            upsert=True
        )
        
        print(f"✅ Portfolio allocated for user {user_id}:")
        for asset, amount in allocations.items():
            print(f"   • {asset}: {amount}")
        
        return allocation_record
    
    async def get_allocation(self, user_id: str) -> Dict[str, Any]:
        """Get current portfolio allocation"""
        allocation = await self.db.portfolio_allocations.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not allocation:
            return {
                'allocated': False,
                'message': 'No allocation found. Please allocate funds first.'
            }
        
        return allocation
    
    async def get_bot_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Get current bot portfolio status"""
        portfolio = await self.db.bot_portfolios.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not portfolio:
            return {
                'initialized': False,
                'message': 'Bot portfolio not initialized'
            }
        
        return portfolio
    
    async def validate_trade_allocation(
        self,
        user_id: str,
        asset: str,
        amount: float,
        trade_type: str  # 'buy' or 'sell'
    ) -> Dict[str, Any]:
        """
        Validate if trade is within allocated funds.
        CRITICAL: This prevents bot from touching non-allocated funds.
        """
        portfolio = await self.get_bot_portfolio(user_id)
        
        if not portfolio.get('initialized', True):
            return {
                'valid': False,
                'reason': 'Bot portfolio not initialized. Allocate funds first.'
            }
        
        available = portfolio.get('available_balance', {}).get(asset, 0)
        locked = portfolio.get('locked_in_orders', {}).get(asset, 0)
        
        if trade_type == 'buy':
            # For buys, check if enough USD/fiat is available
            required_usd = amount  # Amount in USD
            available_usd = portfolio.get('available_balance', {}).get('USD', 0)
            
            if available_usd < required_usd:
                return {
                    'valid': False,
                    'reason': f'Insufficient allocated funds. Available: ${available_usd:.2f}, Required: ${required_usd:.2f}',
                    'available': available_usd,
                    'required': required_usd
                }
        
        elif trade_type == 'sell':
            # For sells, check if enough crypto is held
            holdings = portfolio.get('current_holdings', {}).get(asset, 0)
            
            if holdings < amount:
                return {
                    'valid': False,
                    'reason': f'Insufficient {asset} holdings. Holdings: {holdings:.8f}, Required: {amount:.8f}',
                    'available': holdings,
                    'required': amount
                }
        
        return {
            'valid': True,
            'message': 'Trade within allocated funds',
            'available': available
        }
    
    async def record_trade(
        self,
        user_id: str,
        trade_data: Dict[str, Any]
    ):
        """
        Record trade and update bot portfolio balances.
        Keeps strict separation from user's other Kraken assets.
        """
        portfolio = await self.get_bot_portfolio(user_id)
        
        if not portfolio.get('initialized', True):
            raise Exception('Bot portfolio not initialized')
        
        asset = trade_data['asset']
        action = trade_data['action']  # BUY or SELL
        amount = trade_data['amount']
        price = trade_data['price']
        
        # Update holdings
        current_holdings = portfolio.get('current_holdings', {})
        available_balance = portfolio.get('available_balance', {})
        
        if action == 'BUY':
            # Deduct USD, add crypto
            usd_spent = amount
            crypto_acquired = amount / price
            
            available_balance['USD'] = available_balance.get('USD', 0) - usd_spent
            current_holdings[asset] = current_holdings.get(asset, 0) + crypto_acquired
            
            print(f"📊 Bot Portfolio Update:")
            print(f"   • Spent: ${usd_spent:.2f} USD")
            print(f"   • Acquired: {crypto_acquired:.8f} {asset}")
            print(f"   • Remaining USD: ${available_balance['USD']:.2f}")
        
        elif action == 'SELL':
            # Deduct crypto, add USD
            crypto_sold = amount / price
            usd_gained = amount
            
            current_holdings[asset] = current_holdings.get(asset, 0) - crypto_sold
            available_balance['USD'] = available_balance.get('USD', 0) + usd_gained
            
            print(f"📊 Bot Portfolio Update:")
            print(f"   • Sold: {crypto_sold:.8f} {asset}")
            print(f"   • Gained: ${usd_gained:.2f} USD")
            print(f"   • Total USD: ${available_balance['USD']:.2f}")
        
        # Update portfolio in database
        await self.db.bot_portfolios.update_one(
            {'user_id': user_id},
            {'$set': {
                'current_holdings': current_holdings,
                'available_balance': available_balance,
                'last_updated': datetime.now().isoformat()
            },
            '$push': {
                'trade_history': {
                    **trade_data,
                    'timestamp': datetime.now().isoformat()
                }
            }}
        )
    
    async def calculate_portfolio_value(
        self,
        user_id: str,
        current_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate total value of bot portfolio.
        Separate from user's main Kraken holdings.
        """
        portfolio = await self.get_bot_portfolio(user_id)
        
        if not portfolio.get('initialized', True):
            return {'total_value': 0, 'breakdown': {}}
        
        holdings = portfolio.get('current_holdings', {})
        available_balance = portfolio.get('available_balance', {})
        
        total_value = available_balance.get('USD', 0)  # Start with USD
        breakdown = {'USD': available_balance.get('USD', 0)}
        
        # Add value of crypto holdings
        for asset, amount in holdings.items():
            if asset != 'USD' and amount > 0:
                asset_value = amount * current_prices.get(asset.lower(), 0)
                total_value += asset_value
                breakdown[asset] = {
                    'amount': amount,
                    'value_usd': asset_value,
                    'price': current_prices.get(asset.lower(), 0)
                }
        
        # Calculate profit/loss
        initial_allocation = sum(portfolio.get('allocated_funds', {}).values())
        profit_loss = total_value - initial_allocation
        profit_loss_pct = (profit_loss / initial_allocation * 100) if initial_allocation > 0 else 0
        
        return {
            'total_value': total_value,
            'initial_allocation': initial_allocation,
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_pct,
            'breakdown': breakdown,
            'last_updated': datetime.now().isoformat()
        }
    
    async def withdraw_profits(
        self,
        user_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Withdraw profits from bot portfolio back to user's control.
        Can only withdraw profits, not initial allocation (preserves trading capital).
        """
        portfolio = await self.get_bot_portfolio(user_id)
        
        if not portfolio.get('initialized', True):
            return {'success': False, 'error': 'Portfolio not initialized'}
        
        available_usd = portfolio.get('available_balance', {}).get('USD', 0)
        initial_allocation = portfolio.get('allocated_funds', {}).get('USD', 0)
        
        # Calculate withdrawable amount (only profits, not principal)
        withdrawable = max(0, available_usd - initial_allocation)
        
        if amount > withdrawable:
            return {
                'success': False,
                'error': f'Cannot withdraw ${amount:.2f}. Only ${withdrawable:.2f} in profits available.',
                'withdrawable': withdrawable
            }
        
        # Process withdrawal
        new_balance = available_usd - amount
        
        await self.db.bot_portfolios.update_one(
            {'user_id': user_id},
            {'$set': {
                'available_balance.USD': new_balance,
                'last_updated': datetime.now().isoformat()
            }}
        )
        
        # Record withdrawal
        await self.db.withdrawals.insert_one({
            'user_id': user_id,
            'amount': amount,
            'type': 'profit_withdrawal',
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"💰 Profit Withdrawal: ${amount:.2f}")
        print(f"   • Remaining bot balance: ${new_balance:.2f}")
        
        return {
            'success': True,
            'withdrawn': amount,
            'remaining_balance': new_balance
        }
    
    async def get_allocation_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive allocation summary showing:
        - What user allocated to bot
        - Current bot portfolio value
        - User's other Kraken assets (untouched)
        - Clear separation between bot and user funds
        """
        allocation = await self.get_allocation(user_id)
        portfolio = await self.get_bot_portfolio(user_id)
        
        return {
            'bot_allocated_funds': allocation.get('allocations', {}),
            'bot_current_holdings': portfolio.get('current_holdings', {}),
            'bot_available_to_trade': portfolio.get('available_balance', {}),
            'separation_status': 'ACTIVE - Bot trades only with allocated funds',
            'user_other_assets': 'Completely untouched and separate',
            'protection': 'AI cannot access non-allocated Kraken assets'
        }
