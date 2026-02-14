from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

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
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

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
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# Cache for portfolio performance
_portfolio_cache = {
    "data": {},
    "timestamp": {},
    "ttl": 30  # Cache for 30 seconds
}


@router.get("/portfolio/{user_id}")
async def get_portfolio_performance(
    user_id: str,
    trading_engine = Depends(get_trading_engine)
):
    """Get portfolio performance metrics (cached for 30s)"""
    global _portfolio_cache
    
    # Check cache
    current_time = time.time()
    if (user_id in _portfolio_cache["data"] and 
        user_id in _portfolio_cache["timestamp"] and
        current_time - _portfolio_cache["timestamp"][user_id] < _portfolio_cache["ttl"]):
        return _portfolio_cache["data"][user_id]
    
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
        
        # Update cache
        _portfolio_cache["data"][user_id] = performance
        _portfolio_cache["timestamp"][user_id] = current_time
        
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/kraken/trades")
async def get_kraken_trades(limit: int = 50):
    """Get real trade history from Kraken exchange"""
    try:
        from server import get_service
        kraken_service = get_service('kraken')
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
        from server import get_service
        kraken_service = get_service('kraken')
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
    """Get the initialized market service from services"""
    try:
        from server import get_service
        market = get_service('market')
        if market:
            return market
        else:
            import logging
            logging.getLogger(__name__).warning("Market service not found in global services")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error getting market service: {e}")
    # Fallback to creating new instance
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
    global _kraken_portfolio_cache
    
    # Check cache
    if (_kraken_portfolio_cache["data"] is not None and 
        _kraken_portfolio_cache["timestamp"] is not None and
        time.time() - _kraken_portfolio_cache["timestamp"] < _kraken_portfolio_cache["ttl"]):
        return _kraken_portfolio_cache["data"]
    
    try:
        from server import get_service
        kraken_service = get_service('kraken')
        if not kraken_service:
            return {"error": "Kraken service not initialized", "holdings": [], "total_value_usd": 0}
        
        # Get raw balances from Kraken
        balances = await kraken_service.get_balance()
        
        if not balances:
            return {"holdings": [], "total_value_usd": 0, "message": "No balances found"}
        
        # Kraken asset to pair mapping (verified working pairs)
        ASSET_TO_PAIR = {
            'XXBT': 'XXBTZUSD',
            'XBT': 'XXBTZUSD',
            'XETH': 'XETHZUSD',
            'ETH': 'XETHZUSD',
            'SOL': 'SOLUSD',
            'DOT': 'DOTUSD',
            'ADA': 'ADAUSD',
            'ATOM': 'ATOMUSD',
            'LINK': 'LINKUSD',
            'AAVE': 'AAVEUSD',
            'UNI': 'UNIUSD',
            'APT': 'APTUSD',
            'NEAR': 'NEARUSD',
            'MATIC': 'MATICUSD',
            'AVAX': 'AVAXUSD',
            'FTM': 'FTMUSD',
            'ALGO': 'ALGOUSD',
            'XXRP': 'XRPUSD',
            'XRP': 'XRPUSD',
            'XLTC': 'XLTCZUSD',
            'LTC': 'XLTCZUSD',
            'XXDG': 'XDGUSD',
            'DOGE': 'XDGUSD',
            'SHIB': 'SHIBUSD',
            'TRX': 'TRXUSD',
            'SUI': 'SUIUSD',
            'XXLM': 'XLMUSD',
            'XLM': 'XLMUSD',
            'PEPE': 'PEPEUSD',
            'BNB': 'BNBUSD',
            'KAS': 'KASUSD',
            'EIGEN': 'EIGENUSD',
            'SCRT': 'SCRTUSD',
        }
        
        # Build list of Kraken pairs for price lookup
        kraken_pairs = []
        asset_to_pair = {}
        
        for asset, amount in balances.items():
            amount_float = float(amount)
            if amount_float > 0.0001:
                clean_asset = asset.replace('.S', '').replace('.M', '')
                if clean_asset not in ['ZUSD', 'USD', 'USDT', 'USDC', 'USD.HOLD', 'USDG', 'WLFI', 'BABY', 'TRUMP']:
                    # Use predefined mapping only
                    if clean_asset in ASSET_TO_PAIR:
                        pair = ASSET_TO_PAIR[clean_asset]
                        kraken_pairs.append(pair)
                        asset_to_pair[clean_asset] = pair
        
        # Fetch prices from Kraken directly
        kraken_prices = {}
        kraken_ticker_data = {}  # Store full ticker data for 24h change
        if kraken_pairs:
            try:
                ticker_data = await kraken_service.get_tickers_batch(list(set(kraken_pairs)))
                if ticker_data:
                    for pair, data in ticker_data.items():
                        if isinstance(data, dict) and 'c' in data:
                            price = float(data['c'][0]) if data['c'] else 0
                            kraken_prices[pair] = price
                            kraken_ticker_data[pair] = data  # Store full data
                logger.info(f"Fetched {len(kraken_prices)} Kraken prices")
            except Exception as e:
                logger.error(f"Error fetching Kraken prices: {e}")
        
        # Build portfolio
        holdings = []
        total_value_usd = 0.0
        total_value_24h_ago = 0.0  # For calculating portfolio 24h change
        
        for asset, amount in balances.items():
            try:
                amount_float = float(amount)
                if amount_float <= 0.0001:  # Skip dust
                    continue
                
                # Clean asset name
                clean_asset = asset.replace('.S', '').replace('.M', '')
                
                # Get USD value
                if clean_asset in ['ZUSD', 'USD']:
                    usd_value = amount_float
                    price_usd = 1.0
                    price_change = 0
                    value_24h_ago = amount_float
                elif clean_asset in ['USDT', 'USDC']:
                    usd_value = amount_float
                    price_usd = 1.0
                    price_change = 0
                    value_24h_ago = amount_float
                else:
                    # Get price from Kraken ticker
                    pair = asset_to_pair.get(clean_asset)
                    price_usd = 0
                    price_change = 0
                    ticker_info = None
                    
                    # Try different pair formats
                    for possible_pair in [pair, f"{clean_asset}USD", f"X{clean_asset}ZUSD", f"{clean_asset}ZUSD"]:
                        if possible_pair and possible_pair in kraken_prices:
                            price_usd = kraken_prices[possible_pair]
                            ticker_info = kraken_ticker_data.get(possible_pair)
                            break
                    
                    # Also try without X prefix
                    if price_usd == 0:
                        for p, v in kraken_prices.items():
                            if clean_asset.replace('X', '') in p or clean_asset in p:
                                price_usd = v
                                ticker_info = kraken_ticker_data.get(p)
                                break
                    
                    # Calculate 24h change from ticker data
                    if ticker_info and price_usd > 0:
                        open_24h = float(ticker_info.get('o', price_usd)) if ticker_info.get('o') else price_usd
                        if open_24h > 0:
                            price_change = ((price_usd - open_24h) / open_24h) * 100
                    
                    usd_value = amount_float * price_usd
                    # Calculate value 24h ago
                    if price_change != 0:
                        value_24h_ago = usd_value / (1 + price_change / 100)
                    else:
                        value_24h_ago = usd_value
                
                total_value_24h_ago += value_24h_ago
                
                # Include holding
                symbol = clean_asset.replace('XX', '').replace('X', '')
                if symbol.startswith('Z'):
                    symbol = symbol[1:]
                
                holdings.append({
                    "asset": clean_asset,
                    "symbol": symbol,
                    "amount": amount_float,
                    "price_usd": price_usd,
                    "value_usd": round(usd_value, 2),
                    "change_24h": round(price_change, 2)
                })
                total_value_usd += usd_value
            except Exception as e:
                logger.error(f"Error processing asset {asset}: {e}")
                continue
        
        # Calculate portfolio 24h change percentage
        portfolio_change_24h = 0
        if total_value_24h_ago > 0:
            portfolio_change_24h = ((total_value_usd - total_value_24h_ago) / total_value_24h_ago) * 100
        
        # Sort by USD value (highest first)
        holdings.sort(key=lambda x: x['value_usd'], reverse=True)
        
        result = {
            "holdings": holdings,
            "total_value_usd": round(total_value_usd, 2),
            "change_24h": round(portfolio_change_24h, 2),
            "holdings_count": len(holdings),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        _kraken_portfolio_cache["data"] = result
        _kraken_portfolio_cache["timestamp"] = time.time()
        
        return result
    
    except Exception as e:
        print(f"Error fetching Kraken portfolio: {e}")
        return {"error": str(e), "holdings": [], "total_value_usd": 0}