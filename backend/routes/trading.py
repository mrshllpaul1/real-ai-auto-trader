from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class OrderRequest(BaseModel):
    user_id: str
    strategy_id: str
    coin_pair: str
    action: str  # BUY or SELL
    amount: float
    mode: str = "paper"  # paper or real

class TradeResponse(BaseModel):
    trade_id: str
    status: str
    message: Optional[str] = None

async def get_database():
    from server import db
    return db

async def get_trading_engine():
    from services.trading_engine import TradingEngine
    from server import db
    return TradingEngine(db)

async def get_risk_manager():
    from services.risk_manager import RiskManager
    from server import db
    return RiskManager(db)

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    order: OrderRequest,
    db = Depends(get_database),
    trading_engine = Depends(get_trading_engine),
    risk_manager = Depends(get_risk_manager)
):
    """Execute a trade order and record outcome for learning"""
    try:
        # Validate trade against risk management rules
        validation = await risk_manager.validate_trade(
            order.user_id,
            order.amount,
            order.coin_pair
        )
        
        if not validation.get('valid'):
            raise HTTPException(status_code=400, detail=validation.get('reason'))
        
        # Get current market price (simplified - should fetch real price)
        market_service = await get_market_service()
        coin_id = order.coin_pair.split('/')[0].lower()
        price_data = await market_service.get_coin_price([coin_id])
        current_price = price_data.get(coin_id, {}).get('price_usd', 0)
        
        # Execute trade
        result = await trading_engine.execute_trade(
            user_id=order.user_id,
            strategy_id=order.strategy_id,
            coin_pair=order.coin_pair,
            action=order.action,
            amount=order.amount,
            price=current_price,
            mode=order.mode
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Record for learning (asynchronously, don't wait)
        try:
            # Store entry price for later P/L calculation
            await db.trade_entries.insert_one({
                "trade_id": result['trade_id'],
                "strategy_id": order.strategy_id,
                "entry_price": current_price,
                "action": order.action,
                "amount": order.amount,
                "timestamp": result['created_at']
            })
        except Exception as e:
            print(f"Warning: Could not record trade for learning: {str(e)}")
        
        return TradeResponse(
            trade_id=result['trade_id'],
            status=result['status'],
            message="Trade executed successfully. AI is learning from this trade."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_trade_history(
    user_id: str,
    mode: str = "all",
    limit: int = 100,
    trading_engine = Depends(get_trading_engine)
):
    """Get trade history for a user"""
    try:
        trades = await trading_engine.get_trade_history(user_id, mode, limit)
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/{user_id}")
async def get_portfolio_performance(
    user_id: str,
    trading_engine = Depends(get_trading_engine)
):
    """Get portfolio performance metrics"""
    try:
        # Get current prices for portfolio calculation
        market_service = await get_market_service()
        # Simplified - should fetch actual coin pairs from user's portfolio
        price_data = await market_service.get_coin_price(['bitcoin', 'ethereum'])
        
        current_prices = {
            'XBTUSD': price_data.get('bitcoin', {}).get('price_usd', 0),
            'ETHUSD': price_data.get('ethereum', {}).get('price_usd', 0)
        }
        
        performance = await trading_engine.calculate_portfolio_performance(
            user_id,
            current_prices
        )
        
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kraken/trades")
async def get_kraken_trades(limit: int = 50):
    """Get real trade history from Kraken exchange"""
    try:
        from server import kraken_service
        if not kraken_service:
            return {"trades": [], "count": 0, "error": "Kraken service not initialized"}
        
        # Get trades history from Kraken
        result = await kraken_service.get_trades_history()
        trades_dict = result.get("trades", {})
        
        # Convert to list format
        trades = []
        for trade_id, trade_data in trades_dict.items():
            trades.append({
                "id": trade_id,
                "pair": trade_data.get("pair", ""),
                "type": trade_data.get("type", ""),  # buy/sell
                "ordertype": trade_data.get("ordertype", ""),
                "price": float(trade_data.get("price", 0)),
                "volume": float(trade_data.get("vol", 0)),
                "cost": float(trade_data.get("cost", 0)),
                "fee": float(trade_data.get("fee", 0)),
                "time": trade_data.get("time", 0),
                "timestamp": datetime.fromtimestamp(trade_data.get("time", 0)).isoformat() if trade_data.get("time") else None
            })
        
        # Sort by time, most recent first
        trades.sort(key=lambda x: x.get("time", 0), reverse=True)
        
        return {
            "trades": trades[:limit],
            "count": len(trades),
            "total": result.get("count", len(trades))
        }
    except Exception as e:
        print(f"Error fetching Kraken trades: {e}")
        return {"trades": [], "count": 0, "error": str(e)}

@router.get("/kraken/orders")
async def get_kraken_closed_orders(limit: int = 50):
    """Get closed orders from Kraken exchange"""
    try:
        from server import kraken_service
        if not kraken_service:
            return {"orders": [], "count": 0, "error": "Kraken service not initialized"}
        
        # Get closed orders from Kraken
        result = await kraken_service.get_closed_orders()
        orders_dict = result.get("closed", {})
        
        # Convert to list format
        orders = []
        for order_id, order_data in orders_dict.items():
            descr = order_data.get("descr", {})
            orders.append({
                "id": order_id,
                "pair": descr.get("pair", ""),
                "type": descr.get("type", ""),  # buy/sell
                "ordertype": descr.get("ordertype", ""),
                "price": float(descr.get("price", 0)),
                "volume": float(order_data.get("vol", 0)),
                "vol_exec": float(order_data.get("vol_exec", 0)),
                "cost": float(order_data.get("cost", 0)),
                "fee": float(order_data.get("fee", 0)),
                "status": order_data.get("status", ""),
                "opentm": order_data.get("opentm", 0),
                "closetm": order_data.get("closetm", 0),
                "timestamp": datetime.fromtimestamp(order_data.get("closetm", 0)).isoformat() if order_data.get("closetm") else None
            })
        
        # Sort by close time, most recent first
        orders.sort(key=lambda x: x.get("closetm", 0), reverse=True)
        
        return {
            "orders": orders[:limit],
            "count": len(orders)
        }
    except Exception as e:
        print(f"Error fetching Kraken orders: {e}")
        return {"orders": [], "count": 0, "error": str(e)}

async def get_market_service():
    from services.market_data_service import MarketDataService
    return MarketDataService()


# Kraken asset to CoinGecko ID mapping
KRAKEN_TO_COINGECKO = {
    'XXBT': 'bitcoin',
    'XBT': 'bitcoin',
    'XETH': 'ethereum',
    'ETH': 'ethereum',
    'XXRP': 'ripple',
    'XRP': 'ripple',
    'SOL': 'solana',
    'DOT': 'polkadot',
    'AAVE': 'aave',
    'SUI': 'sui',
    'APT': 'aptos',
    'UNI': 'uniswap',
    'ZUSD': 'usd',
    'USD': 'usd',
    'USDT': 'tether',
    'USDC': 'usd-coin',
    'ADA': 'cardano',
    'LINK': 'chainlink',
    'MATIC': 'matic-network',
    'AVAX': 'avalanche-2',
    'ATOM': 'cosmos',
    'NEAR': 'near',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'FIL': 'filecoin',
    'LTC': 'litecoin',
    'BCH': 'bitcoin-cash',
    'DOGE': 'dogecoin',
    'SHIB': 'shiba-inu',
    'TRX': 'tron',
    'PEPE': 'pepe',
}


# Cache for Kraken portfolio
_kraken_portfolio_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 60  # Cache for 60 seconds
}


@router.get("/kraken/portfolio")
async def get_kraken_portfolio():
    """
    Get complete Kraken portfolio with real-time USD values.
    Returns all holdings with current prices and total portfolio value.
    Cached for 60 seconds to avoid rate limits.
    """
    import time
    global _kraken_portfolio_cache
    
    # Check cache
    if (_kraken_portfolio_cache["data"] is not None and 
        _kraken_portfolio_cache["timestamp"] is not None and
        time.time() - _kraken_portfolio_cache["timestamp"] < _kraken_portfolio_cache["ttl"]):
        return _kraken_portfolio_cache["data"]
    
    try:
        from server import kraken_service
        if not kraken_service:
            return {"error": "Kraken service not initialized", "holdings": [], "total_value_usd": 0}
        
        # Get raw balances from Kraken
        balances = await kraken_service.get_balance()
        
        if not balances:
            return {"holdings": [], "total_value_usd": 0, "message": "No balances found"}
        
        # Get market service for prices
        market_service = await get_market_service()
        
        # Build list of coin IDs to fetch prices for
        coin_ids_to_fetch = []
        for asset, amount in balances.items():
            amount_float = float(amount)
            if amount_float > 0:
                # Map Kraken asset to CoinGecko ID
                clean_asset = asset.replace('.S', '').replace('.M', '')  # Remove staking suffixes
                coingecko_id = KRAKEN_TO_COINGECKO.get(clean_asset, clean_asset.lower())
                if coingecko_id not in ['usd', 'zusd', 'usdt', 'usdc', 'usd-coin', 'tether']:
                    coin_ids_to_fetch.append(coingecko_id)
        
        # Fetch all prices at once
        prices = {}
        if coin_ids_to_fetch:
            try:
                price_data = await market_service.get_coin_price(list(set(coin_ids_to_fetch)))
                prices = price_data
            except Exception as e:
                print(f"Error fetching prices: {e}")
        
        # Build portfolio
        holdings = []
        total_value_usd = 0.0
        
        for asset, amount in balances.items():
            amount_float = float(amount)
            if amount_float <= 0.0001:  # Skip dust
                continue
            
            # Clean asset name
            clean_asset = asset.replace('.S', '').replace('.M', '')
            coingecko_id = KRAKEN_TO_COINGECKO.get(clean_asset, clean_asset.lower())
            
            # Get USD value
            if coingecko_id in ['usd', 'zusd']:
                usd_value = amount_float
                price_usd = 1.0
            elif coingecko_id in ['usdt', 'tether', 'usdc', 'usd-coin']:
                usd_value = amount_float
                price_usd = 1.0
            else:
                price_info = prices.get(coingecko_id, {})
                price_usd = price_info.get('price_usd', 0)
                usd_value = amount_float * price_usd
            
            if usd_value > 0.01:  # Only include if worth more than 1 cent
                holdings.append({
                    "asset": clean_asset,
                    "symbol": clean_asset.replace('X', '').replace('XX', ''),
                    "coingecko_id": coingecko_id,
                    "amount": amount_float,
                    "price_usd": price_usd,
                    "value_usd": round(usd_value, 2),
                    "price_change_24h": prices.get(coingecko_id, {}).get('price_change_24h', 0)
                })
                total_value_usd += usd_value
        
        # Sort by USD value (highest first)
        holdings.sort(key=lambda x: x['value_usd'], reverse=True)
        
        return {
            "holdings": holdings,
            "total_value_usd": round(total_value_usd, 2),
            "holdings_count": len(holdings),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        print(f"Error fetching Kraken portfolio: {e}")
        return {"error": str(e), "holdings": [], "total_value_usd": 0}