from typing import Dict, Any, List
from datetime import datetime
import uuid
import random

class TradingEngine:
    def __init__(self, db, kraken_service=None):
        self.db = db
        self.kraken_service = kraken_service
        self.paper_portfolio = {}
    
    async def execute_trade(
        self,
        user_id: str,
        strategy_id: str,
        coin_pair: str,
        action: str,
        amount: float,
        price: float,
        mode: str = "paper"  # paper or real
    ) -> Dict[str, Any]:
        """Execute a trade in paper or real mode"""
        trade_id = str(uuid.uuid4())
        
        try:
            if mode == "real" and self.kraken_service:
                # Execute real trade on Kraken
                result = await self.kraken_service.place_order(
                    pair=coin_pair,
                    side=action.lower(),
                    ordertype="market",
                    price="0",
                    volume=str(amount)
                )
                
                trade_record = {
                    "trade_id": trade_id,
                    "user_id": user_id,
                    "strategy_id": strategy_id,
                    "coin_pair": coin_pair,
                    "action": action,
                    "amount": amount,
                    "price": price,
                    "mode": "real",
                    "status": "executed",
                    "kraken_order_id": result.get('txid', [None])[0],
                    "created_at": datetime.now().isoformat(),
                    "result": result
                }
            else:
                # Execute paper trade (simulation)
                trade_record = {
                    "trade_id": trade_id,
                    "user_id": user_id,
                    "strategy_id": strategy_id,
                    "coin_pair": coin_pair,
                    "action": action,
                    "amount": amount,
                    "price": price,
                    "mode": "paper",
                    "status": "executed",
                    "created_at": datetime.now().isoformat(),
                    "paper_simulation": True
                }
                
                # Update paper portfolio
                portfolio_key = f"{user_id}_{coin_pair}"
                if portfolio_key not in self.paper_portfolio:
                    self.paper_portfolio[portfolio_key] = {
                        "balance": 0,
                        "average_price": 0,
                        "total_trades": 0
                    }
                
                if action == "BUY":
                    current_balance = self.paper_portfolio[portfolio_key]["balance"]
                    current_avg = self.paper_portfolio[portfolio_key]["average_price"]
                    
                    new_balance = current_balance + amount
                    new_avg = ((current_balance * current_avg) + (amount * price)) / new_balance if new_balance > 0 else price
                    
                    self.paper_portfolio[portfolio_key]["balance"] = new_balance
                    self.paper_portfolio[portfolio_key]["average_price"] = new_avg
                else:  # SELL
                    self.paper_portfolio[portfolio_key]["balance"] -= amount
                
                self.paper_portfolio[portfolio_key]["total_trades"] += 1
            
            # Store trade in database
            await self.db.trades.insert_one(trade_record)
            
            return trade_record
        
        except Exception as e:
            return {
                "error": str(e),
                "trade_id": trade_id,
                "status": "failed"
            }
    
    async def get_trade_history(
        self,
        user_id: str,
        mode: str = "all",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trade history for a user"""
        query = {"user_id": user_id}
        if mode in ["paper", "real"]:
            query["mode"] = mode
        
        trades = await self.db.trades.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return trades
    
    async def calculate_portfolio_performance(
        self,
        user_id: str,
        current_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate portfolio performance"""
        trades = await self.get_trade_history(user_id)
        
        total_invested = 0
        current_value = 0
        trades_count = len(trades)
        winning_trades = 0
        
        for trade in trades:
            if trade.get('action') == 'BUY':
                total_invested += trade.get('amount', 0) * trade.get('price', 0)
            
            coin_pair = trade.get('coin_pair', '')
            if coin_pair in current_prices:
                current_price = current_prices[coin_pair]
                current_value += trade.get('amount', 0) * current_price
                
                if trade.get('action') == 'BUY' and current_price > trade.get('price', 0):
                    winning_trades += 1
        
        profit_loss = current_value - total_invested
        profit_loss_percentage = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0
        
        return {
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percentage": round(profit_loss_percentage, 2),
            "total_trades": trades_count,
            "winning_trades": winning_trades,
            "win_rate": round(win_rate, 2)
        }