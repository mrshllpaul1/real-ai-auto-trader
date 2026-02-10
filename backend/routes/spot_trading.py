"""
Spot Trading API Routes
Direct spot trading interface for manual and AI-assisted trades.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/spot", tags=["Spot Trading"])

# Global references
_db = None
_kraken_service = None
_isolated_portfolio = None
_automated_trader = None
_prediction_services = None
_entry_tracker = None


def set_dependencies(database, kraken_service, isolated_portfolio=None, automated_trader=None, prediction_services=None, entry_tracker=None):
    """Set dependencies from main app"""
    global _db, _kraken_service, _isolated_portfolio, _automated_trader, _prediction_services, _entry_tracker
    _db = database
    _kraken_service = kraken_service
    _isolated_portfolio = isolated_portfolio
    _automated_trader = automated_trader
    _prediction_services = prediction_services
    _entry_tracker = entry_tracker


# Trading Pairs commonly used on Kraken
TRADING_PAIRS = {
    'BTC': {'pair': 'XXBTZUSD', 'name': 'Bitcoin', 'decimals': 8, 'min_order': 0.0001},
    'ETH': {'pair': 'XETHZUSD', 'name': 'Ethereum', 'decimals': 8, 'min_order': 0.001},
    'SOL': {'pair': 'SOLUSD', 'name': 'Solana', 'decimals': 8, 'min_order': 0.01},
    'XRP': {'pair': 'XXRPZUSD', 'name': 'Ripple', 'decimals': 8, 'min_order': 1},
    'ADA': {'pair': 'ADAUSD', 'name': 'Cardano', 'decimals': 8, 'min_order': 1},
    'DOGE': {'pair': 'XDGUSD', 'name': 'Dogecoin', 'decimals': 8, 'min_order': 10},
    'DOT': {'pair': 'DOTUSD', 'name': 'Polkadot', 'decimals': 8, 'min_order': 0.1},
    'LINK': {'pair': 'LINKUSD', 'name': 'Chainlink', 'decimals': 8, 'min_order': 0.1},
    'AVAX': {'pair': 'AVAXUSD', 'name': 'Avalanche', 'decimals': 8, 'min_order': 0.01},
    'MATIC': {'pair': 'POLUSD', 'name': 'Polygon', 'decimals': 8, 'min_order': 1},
    'ATOM': {'pair': 'ATOMUSD', 'name': 'Cosmos', 'decimals': 8, 'min_order': 0.1},
    'UNI': {'pair': 'UNIUSD', 'name': 'Uniswap', 'decimals': 8, 'min_order': 0.1},
    'SHIB': {'pair': 'SHIBUSD', 'name': 'Shiba Inu', 'decimals': 8, 'min_order': 100000},
    'LTC': {'pair': 'XLTCZUSD', 'name': 'Litecoin', 'decimals': 8, 'min_order': 0.01},
    'BCH': {'pair': 'BCHUSD', 'name': 'Bitcoin Cash', 'decimals': 8, 'min_order': 0.01},
    'NEAR': {'pair': 'NEARUSD', 'name': 'NEAR Protocol', 'decimals': 8, 'min_order': 0.1},
    'APT': {'pair': 'APTUSD', 'name': 'Aptos', 'decimals': 8, 'min_order': 0.1},
    'ARB': {'pair': 'ARBUSD', 'name': 'Arbitrum', 'decimals': 8, 'min_order': 1},
    'OP': {'pair': 'OPUSD', 'name': 'Optimism', 'decimals': 8, 'min_order': 1},
}


class SpotOrderRequest(BaseModel):
    symbol: str  # e.g., "BTC", "ETH"
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    amount: Optional[float] = None  # Amount of crypto to buy/sell
    usd_amount: Optional[float] = None  # USD amount for buy orders
    price: Optional[float] = None  # Required for limit orders
    use_ai_timing: bool = False  # Whether to use AI signals for timing


class QuickBuyRequest(BaseModel):
    symbol: str
    usd_amount: float
    use_ai_signal: bool = False


class QuickSellRequest(BaseModel):
    symbol: str
    percent_to_sell: float = 100  # Percentage of holdings to sell
    use_ai_signal: bool = False


@router.get("/status")
async def get_spot_trading_status():
    """Get spot trading status and available features"""
    if _kraken_service is None:
        return {
            "available": False,
            "error": "Kraken service not initialized",
            "features": []
        }
    
    features = []
    budget_info = None
    
    # Check trading permissions
    try:
        if _isolated_portfolio:
            budget = await _isolated_portfolio.get_budget_status()
            budget_info = {
                "available_usd": budget.get("available_cash", 0),
                "total_value": budget.get("current_value", 0),
                "real_trading_enabled": budget.get("real_trading_enabled", False),
                "allocated_budget": budget.get("allocated_budget", 500)
            }
            features.append("budget_isolation")
            if budget.get("real_trading_enabled"):
                features.append("real_trading")
    except Exception as e:
        logger.error(f"Budget check error: {e}")
    
    # Check AI features
    if _prediction_services:
        features.append("ai_signals")
        if _prediction_services.get('transformer'):
            features.append("transformer_predictions")
        if _prediction_services.get('rl_agent'):
            features.append("rl_recommendations")
    
    # Check Kraken connection
    try:
        balance = await _kraken_service.get_balance()
        features.append("kraken_connected")
    except:
        pass
    
    return {
        "available": True,
        "features": features,
        "budget": budget_info,
        "supported_pairs": len(TRADING_PAIRS),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/pairs")
async def get_trading_pairs():
    """Get all available trading pairs with current prices"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    # Fetch all tickers in a single batch request
    all_pairs = [info['pair'] for info in TRADING_PAIRS.values()]
    
    try:
        tickers = await _kraken_service.get_tickers_batch(all_pairs)
    except Exception as e:
        logger.error(f"Batch ticker fetch error: {e}")
        tickers = {}
    
    pairs_with_prices = []
    
    for symbol, info in TRADING_PAIRS.items():
        pair_name = info['pair']
        
        # Kraken returns exact pair names
        ticker = tickers.get(pair_name)
        
        if ticker:
            last_price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
            volume_24h = float(ticker.get("v", [0, 0])[1]) if ticker.get("v") else 0
            low_24h = float(ticker.get("l", [0, 0])[1]) if ticker.get("l") else 0
            high_24h = float(ticker.get("h", [0, 0])[1]) if ticker.get("h") else 0
            open_24h = float(ticker.get("o", 0)) if ticker.get("o") else last_price
            
            change_24h = ((last_price - open_24h) / open_24h * 100) if open_24h else 0
            
            pairs_with_prices.append({
                "symbol": symbol,
                "pair": pair_name,
                "name": info['name'],
                "price": last_price,
                "change_24h": round(change_24h, 2),
                "volume_24h": volume_24h,
                "low_24h": low_24h,
                "high_24h": high_24h,
                "min_order": info['min_order'],
                "decimals": info['decimals']
            })
        else:
            pairs_with_prices.append({
                "symbol": symbol,
                "pair": pair_name,
                "name": info['name'],
                "price": 0,
                "error": "Price unavailable",
                "min_order": info['min_order'],
                "decimals": info['decimals']
            })
    
    # Sort by 24h volume
    pairs_with_prices.sort(key=lambda x: x.get('volume_24h', 0) or 0, reverse=True)
    
    return {
        "pairs": pairs_with_prices,
        "count": len(pairs_with_prices),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/pairs/all")
async def get_all_kraken_pairs():
    """
    Get ALL available USD trading pairs from Kraken.
    This fetches the complete list directly from Kraken's AssetPairs API.
    """
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.kraken.com/0/public/AssetPairs")
            data = response.json()
            
            if data.get("error") and len(data["error"]) > 0:
                raise HTTPException(status_code=503, detail=f"Kraken API error: {data['error']}")
            
            result = data.get("result", {})
            
            # Filter for USD pairs only
            usd_pairs = []
            seen_bases = set()
            
            for pair_name, pair_info in result.items():
                # Skip darkpool pairs
                if pair_name.endswith('.d'):
                    continue
                
                quote = pair_info.get("quote", "")
                base = pair_info.get("base", "")
                wsname = pair_info.get("wsname", pair_name)
                altname = pair_info.get("altname", pair_name)
                
                # Check if it's a USD pair
                is_usd = quote in ["ZUSD", "USD"] or pair_name.endswith("USD") or wsname.endswith("/USD")
                
                if is_usd:
                    # Normalize base symbol (remove X prefix and Z suffix)
                    base_clean = base.replace("X", "").replace("Z", "").upper()
                    if base_clean.startswith("X"):
                        base_clean = base_clean[1:]
                    
                    # Skip duplicates (prefer shorter pair names)
                    if base_clean in seen_bases:
                        continue
                    seen_bases.add(base_clean)
                    
                    usd_pairs.append({
                        "symbol": base_clean,
                        "pair": pair_name,
                        "wsname": wsname,
                        "altname": altname,
                        "base": base,
                        "quote": quote,
                        "lot_decimals": pair_info.get("lot_decimals", 8),
                        "pair_decimals": pair_info.get("pair_decimals", 5),
                        "ordermin": pair_info.get("ordermin", "0.0001"),
                        "display": f"{base_clean}/USD"
                    })
            
            # Sort alphabetically by symbol
            usd_pairs.sort(key=lambda x: x["symbol"])
            
            return {
                "pairs": usd_pairs,
                "count": len(usd_pairs),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "kraken_api"
            }
            
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch Kraken pairs: {e}")
        raise HTTPException(status_code=503, detail="Failed to connect to Kraken API")


@router.get("/pair/{symbol}")
async def get_pair_details(symbol: str):
    """Get detailed information for a specific trading pair"""
    symbol = symbol.upper()
    
    if symbol not in TRADING_PAIRS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    pair_info = TRADING_PAIRS[symbol]
    
    try:
        ticker = await _kraken_service.get_ticker(pair_info['pair'])
        
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Ticker not available for {symbol}")
        
        last_price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
        ask = float(ticker.get("a", [0])[0]) if ticker.get("a") else 0
        bid = float(ticker.get("b", [0])[0]) if ticker.get("b") else 0
        volume_24h = float(ticker.get("v", [0, 0])[1]) if ticker.get("v") else 0
        low_24h = float(ticker.get("l", [0, 0])[1]) if ticker.get("l") else 0
        high_24h = float(ticker.get("h", [0, 0])[1]) if ticker.get("h") else 0
        open_24h = float(ticker.get("o", 0)) if ticker.get("o") else last_price
        
        change_24h = ((last_price - open_24h) / open_24h * 100) if open_24h else 0
        spread = ((ask - bid) / last_price * 100) if last_price else 0
        
        # Get AI signal if available
        ai_signal = None
        if _automated_trader and hasattr(_automated_trader, 'get_prediction_signals'):
            try:
                ai_signal = await _automated_trader.get_prediction_signals(symbol)
            except Exception as e:
                logger.warning(f"AI signal error for {symbol}: {e}")
        
        # Get user balance for this coin
        user_balance = None
        if _kraken_service:
            try:
                balance = await _kraken_service.get_balance()
                # Kraken uses different naming for coins
                kraken_symbols = {
                    'BTC': ['XXBT', 'XBT'],
                    'ETH': ['XETH', 'ETH'],
                    'SOL': ['SOL'],
                    'XRP': ['XXRP', 'XRP'],
                }
                for ks in kraken_symbols.get(symbol, [symbol]):
                    if ks in balance:
                        user_balance = float(balance[ks])
                        break
            except Exception as e:
                logger.warning(f"Balance check error: {e}")
        
        return {
            "symbol": symbol,
            "name": pair_info['name'],
            "pair": pair_info['pair'],
            "price": {
                "last": last_price,
                "ask": ask,
                "bid": bid,
                "spread": round(spread, 4),
                "open_24h": open_24h,
                "low_24h": low_24h,
                "high_24h": high_24h,
                "change_24h": round(change_24h, 2)
            },
            "volume_24h": volume_24h,
            "volume_usd_24h": volume_24h * last_price,
            "min_order": pair_info['min_order'],
            "min_order_usd": pair_info['min_order'] * last_price,
            "user_balance": user_balance,
            "user_balance_usd": user_balance * last_price if user_balance else None,
            "ai_signal": ai_signal,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pair details: {str(e)}")


@router.get("/balance")
async def get_spot_balance():
    """Get user's spot balance across all supported coins with entry price tracking"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        balance = await _kraken_service.get_balance()
        
        # Map Kraken currency names to standard symbols
        kraken_to_symbol = {
            'XXBT': 'BTC', 'XBT': 'BTC',
            'XETH': 'ETH', 'ETH': 'ETH',
            'ZUSD': 'USD', 'USD': 'USD',
            'XXRP': 'XRP', 'XRP': 'XRP',
            'XXLM': 'XLM', 'XLM': 'XLM',
            'XXDG': 'DOGE', 'DOGE': 'DOGE',
            'SOL': 'SOL',
            'ADA': 'ADA',
            'DOT': 'DOT',
            'LINK': 'LINK',
            'AVAX': 'AVAX',
            'MATIC': 'MATIC',
            'ATOM': 'ATOM',
            'UNI': 'UNI',
            'SHIB': 'SHIB',
            'XLTC': 'LTC', 'LTC': 'LTC',
            'BCH': 'BCH',
            'NEAR': 'NEAR',
            'APT': 'APT',
            'ARB': 'ARB',
            'OP': 'OP',
        }
        
        # Get entry prices if tracker is available
        entry_prices = {}
        if _entry_tracker:
            try:
                all_entries = await _entry_tracker.get_all_entries()
                entry_prices = {e['symbol']: e for e in all_entries}
            except Exception as e:
                logger.warning(f"Could not load entry prices: {e}")
        
        holdings = []
        total_usd_value = 0
        total_cost_basis = 0
        total_unrealized_pnl = 0
        usd_balance = 0
        
        for currency, amount in balance.items():
            amount = float(amount)
            if amount <= 0:
                continue
            
            symbol = kraken_to_symbol.get(currency, currency)
            
            if symbol == 'USD':
                usd_balance = amount
                continue
            
            # Get current price
            usd_value = 0
            price = 0
            if symbol in TRADING_PAIRS:
                try:
                    ticker = await _kraken_service.get_ticker(TRADING_PAIRS[symbol]['pair'])
                    if ticker:
                        price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
                        usd_value = amount * price
                except:
                    pass
            
            if amount > 0:
                # Get entry price data if available
                entry_data = entry_prices.get(symbol, {})
                entry_price = entry_data.get('entry_price')
                has_entry_price = entry_price is not None
                
                # Calculate P&L
                if has_entry_price and price > 0:
                    cost_basis = entry_price * amount
                    unrealized_pnl = usd_value - cost_basis
                    pnl_percent = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    total_cost_basis += cost_basis
                    total_unrealized_pnl += unrealized_pnl
                else:
                    cost_basis = None
                    unrealized_pnl = None
                    pnl_percent = None
                
                holdings.append({
                    "symbol": symbol,
                    "name": TRADING_PAIRS.get(symbol, {}).get('name', symbol),
                    "amount": amount,
                    "price": price,
                    "usd_value": round(usd_value, 2),
                    "kraken_currency": currency,
                    # Entry price tracking fields
                    "entry_price": entry_price,
                    "has_entry_price": has_entry_price,
                    "cost_basis": round(cost_basis, 2) if cost_basis else None,
                    "unrealized_pnl": round(unrealized_pnl, 2) if unrealized_pnl is not None else None,
                    "pnl_percent": round(pnl_percent, 2) if pnl_percent is not None else None,
                    "realized_pnl": entry_data.get('realized_pnl', 0),
                    "total_buys": entry_data.get('total_buys', 0),
                    "total_sells": entry_data.get('total_sells', 0)
                })
                total_usd_value += usd_value
        
        # Sort by USD value
        holdings.sort(key=lambda x: x['usd_value'], reverse=True)
        
        # Calculate portfolio P&L metrics
        portfolio_pnl_percent = ((total_usd_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else None
        
        return {
            "holdings": holdings,
            "usd_balance": round(usd_balance, 2),
            "total_crypto_value": round(total_usd_value, 2),
            "total_portfolio_value": round(usd_balance + total_usd_value, 2),
            "holdings_count": len(holdings),
            # P&L metrics
            "total_cost_basis": round(total_cost_basis, 2) if total_cost_basis > 0 else None,
            "total_unrealized_pnl": round(total_unrealized_pnl, 2) if total_cost_basis > 0 else None,
            "portfolio_pnl_percent": round(portfolio_pnl_percent, 2) if portfolio_pnl_percent is not None else None,
            "has_entry_data": len(entry_prices) > 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Balance error: {str(e)}")


@router.post("/order")
async def place_spot_order(request: SpotOrderRequest):
    """
    Place a spot order.
    
    For buy orders, specify either:
    - amount: Amount of crypto to buy
    - usd_amount: USD amount to spend
    
    For sell orders, specify amount to sell.
    """
    symbol = request.symbol.upper()
    
    if symbol not in TRADING_PAIRS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    # Check trading permissions
    if _isolated_portfolio:
        budget = await _isolated_portfolio.get_budget_status()
        if not budget.get("real_trading_enabled"):
            raise HTTPException(
                status_code=403,
                detail="Real trading not enabled. Enable it in Trading Budget settings."
            )
    
    pair_info = TRADING_PAIRS[symbol]
    
    try:
        # Get current price
        ticker = await _kraken_service.get_ticker(pair_info['pair'])
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Cannot get price for {symbol}")
        
        current_price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
        
        # Calculate volume
        volume = request.amount
        
        if request.side.lower() == 'buy' and request.usd_amount:
            # Convert USD amount to crypto amount
            volume = request.usd_amount / current_price
        
        if not volume:
            raise HTTPException(status_code=400, detail="Amount or usd_amount required")
        
        # Check minimum order
        if volume < pair_info['min_order']:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order for {symbol} is {pair_info['min_order']} ({pair_info['min_order'] * current_price:.2f} USD)"
            )
        
        # AI timing recommendation
        ai_recommendation = None
        if request.use_ai_timing and _automated_trader:
            try:
                signals = await _automated_trader.get_prediction_signals(symbol)
                if signals:
                    ai_recommendation = {
                        "signal": signals.get('composite_signal', 'neutral'),
                        "score": signals.get('composite_score', 0),
                        "recommendation": signals.get('recommendation', 'Hold position')
                    }
                    
                    # Warn if AI disagrees with order
                    composite_score = signals.get('composite_score', 0)
                    if request.side.lower() == 'buy' and composite_score < -0.3:
                        logger.warning(f"AI signals suggest against buying {symbol} (score: {composite_score})")
                    elif request.side.lower() == 'sell' and composite_score > 0.3:
                        logger.warning(f"AI signals suggest against selling {symbol} (score: {composite_score})")
            except Exception as e:
                logger.warning(f"AI timing error: {e}")
        
        # Place order
        order_params = {
            "pair": pair_info['pair'],
            "side": request.side.lower(),
            "ordertype": request.order_type.lower(),
            "volume": str(round(volume, pair_info['decimals']))
        }
        
        if request.order_type.lower() == 'limit':
            if not request.price:
                raise HTTPException(status_code=400, detail="Price required for limit orders")
            order_params["price"] = str(request.price)
        else:
            order_params["price"] = "0"
        
        result = await _kraken_service.place_order(**order_params)
        
        # Record entry price for tracking
        executed_price = current_price if request.order_type.lower() == 'market' else request.price
        if _entry_tracker:
            try:
                order_id = result.get('txid', [None])[0] if isinstance(result.get('txid'), list) else result.get('txid')
                
                if request.side.lower() == 'buy':
                    entry_result = await _entry_tracker.record_buy(
                        symbol=symbol,
                        quantity=volume,
                        price=executed_price,
                        order_id=order_id,
                        source="manual_trade"
                    )
                    logger.info(f"📈 Entry price recorded for {symbol}: {entry_result}")
                else:  # sell
                    entry_result = await _entry_tracker.record_sell(
                        symbol=symbol,
                        quantity=volume,
                        price=executed_price,
                        order_id=order_id,
                        source="manual_trade"
                    )
                    logger.info(f"📉 Sell recorded for {symbol}: {entry_result}")
            except Exception as e:
                logger.warning(f"Entry price tracking error: {e}")
        
        # Log trade to DB
        if _db:
            await _db.spot_trades.insert_one({
                "symbol": symbol,
                "pair": pair_info['pair'],
                "side": request.side.lower(),
                "order_type": request.order_type.lower(),
                "volume": volume,
                "price": current_price if request.order_type.lower() == 'market' else request.price,
                "usd_value": volume * current_price,
                "result": result,
                "ai_recommendation": ai_recommendation,
                "timestamp": datetime.now(timezone.utc)
            })
        
        return {
            "success": True,
            "order": result,
            "details": {
                "symbol": symbol,
                "side": request.side,
                "type": request.order_type,
                "volume": volume,
                "price": current_price if request.order_type.lower() == 'market' else request.price,
                "usd_value": round(volume * current_price, 2)
            },
            "ai_recommendation": ai_recommendation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order failed: {str(e)}")


@router.post("/quick-buy")
async def quick_buy(request: QuickBuyRequest):
    """Quick market buy with USD amount"""
    symbol = request.symbol.upper()
    
    if symbol not in TRADING_PAIRS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    
    # Use the main order endpoint
    order_request = SpotOrderRequest(
        symbol=symbol,
        side="buy",
        order_type="market",
        usd_amount=request.usd_amount,
        use_ai_timing=request.use_ai_signal
    )
    
    return await place_spot_order(order_request)


@router.post("/quick-sell")
async def quick_sell(request: QuickSellRequest):
    """Quick market sell of holdings"""
    symbol = request.symbol.upper()
    
    if symbol not in TRADING_PAIRS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    # Get current balance
    balance = await _kraken_service.get_balance()
    
    # Find balance for symbol
    kraken_symbols = {
        'BTC': ['XXBT', 'XBT'],
        'ETH': ['XETH', 'ETH'],
        'XRP': ['XXRP', 'XRP'],
        'DOGE': ['XXDG', 'DOGE'],
        'LTC': ['XLTC', 'LTC'],
    }
    
    user_balance = 0
    for ks in kraken_symbols.get(symbol, [symbol]):
        if ks in balance:
            user_balance = float(balance[ks])
            break
    
    if user_balance <= 0:
        raise HTTPException(status_code=400, detail=f"No {symbol} balance to sell")
    
    # Calculate amount to sell
    amount_to_sell = user_balance * (request.percent_to_sell / 100)
    
    # Use the main order endpoint
    order_request = SpotOrderRequest(
        symbol=symbol,
        side="sell",
        order_type="market",
        amount=amount_to_sell,
        use_ai_timing=request.use_ai_signal
    )
    
    return await place_spot_order(order_request)


@router.get("/ai-recommendations")
async def get_ai_recommendations():
    """Get AI trading recommendations for all supported pairs"""
    if _automated_trader is None:
        raise HTTPException(status_code=503, detail="Auto trader not initialized")
    
    recommendations = []
    
    for symbol in list(TRADING_PAIRS.keys())[:10]:  # Top 10 pairs
        try:
            signals = await _automated_trader.get_prediction_signals(symbol)
            
            if signals:
                pair_info = TRADING_PAIRS[symbol]
                
                # Get current price
                price = 0
                if _kraken_service:
                    try:
                        ticker = await _kraken_service.get_ticker(pair_info['pair'])
                        if ticker:
                            price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
                    except:
                        pass
                
                recommendations.append({
                    "symbol": symbol,
                    "name": pair_info['name'],
                    "price": price,
                    "signal": signals.get('composite_signal', 'neutral'),
                    "score": round(signals.get('composite_score', 0), 3),
                    "confidence": signals.get('confidence', 0),
                    "recommendation": signals.get('recommendation', 'Hold'),
                    "components": {
                        k: v for k, v in signals.items() 
                        if k in ['order_book', 'on_chain', 'social', 'transformer', 'rl_agent', 'technical']
                    }
                })
        except Exception as e:
            logger.warning(f"AI recommendation error for {symbol}: {e}")
    
    # Sort by absolute score (strongest signals first)
    recommendations.sort(key=lambda x: abs(x['score']), reverse=True)
    
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/recent-trades")
async def get_recent_spot_trades(limit: int = Query(20, ge=1, le=100)):
    """Get recent spot trades from DB"""
    if _db is None:
        return {"trades": [], "count": 0}
    
    try:
        trades = await _db.spot_trades.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {
            "trades": trades,
            "count": len(trades),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        return {"trades": [], "count": 0, "error": str(e)}


@router.get("/trade-history/kraken")
async def get_kraken_trade_history(limit: int = Query(50, ge=1, le=500)):
    """Get actual trade history from Kraken exchange"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        history = await _kraken_service.get_trades_history()
        trades = history.get("trades", {})
        
        formatted_trades = []
        for trade_id, trade in list(trades.items())[:limit]:
            # Map Kraken pair to symbol
            pair = trade.get("pair", "")
            symbol = pair.replace("USD", "").replace("Z", "").replace("X", "")[:4]
            
            formatted_trades.append({
                "id": trade_id,
                "symbol": symbol,
                "pair": pair,
                "side": trade.get("type"),
                "price": float(trade.get("price", 0)),
                "volume": float(trade.get("vol", 0)),
                "cost": float(trade.get("cost", 0)),
                "fee": float(trade.get("fee", 0)),
                "time": datetime.fromtimestamp(trade.get("time", 0)).isoformat()
            })
        
        # Sort by time descending
        formatted_trades.sort(key=lambda x: x['time'], reverse=True)
        
        return {
            "trades": formatted_trades,
            "count": len(formatted_trades),
            "source": "kraken_exchange",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade history error: {str(e)}")


@router.get("/open-orders")
async def get_open_orders():
    """Get all open orders"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        result = await _kraken_service.get_open_orders()
        orders = result.get("open", {})
        
        formatted_orders = []
        for order_id, order in orders.items():
            formatted_orders.append({
                "id": order_id,
                "pair": order.get("descr", {}).get("pair"),
                "type": order.get("descr", {}).get("type"),
                "order_type": order.get("descr", {}).get("ordertype"),
                "price": order.get("descr", {}).get("price"),
                "volume": float(order.get("vol", 0)),
                "volume_exec": float(order.get("vol_exec", 0)),
                "status": order.get("status"),
                "open_time": datetime.fromtimestamp(order.get("opentm", 0)).isoformat()
            })
        
        return {
            "orders": formatted_orders,
            "count": len(formatted_orders),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Open orders error: {str(e)}")


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an open order"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        result = await _kraken_service.cancel_order(order_id)
        
        return {
            "success": True,
            "order_id": order_id,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel order error: {str(e)}")


# ============= Entry Price Tracking Endpoints =============

@router.get("/entry-prices")
async def get_all_entry_prices():
    """Get all recorded entry prices for positions"""
    if _entry_tracker is None:
        return {
            "entries": [],
            "message": "Entry tracking not initialized",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    try:
        entries = await _entry_tracker.get_all_entries()
        return {
            "entries": entries,
            "count": len(entries),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching entry prices: {e}")
        return {"entries": [], "error": str(e)}


@router.get("/entry-prices/{symbol}")
async def get_entry_price(symbol: str):
    """Get entry price for a specific symbol"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracking not initialized")
    
    symbol = symbol.upper()
    entry = await _entry_tracker.get_entry_price(symbol)
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"No entry price found for {symbol}")
    
    # Get current price for P&L calculation
    current_price = 0
    if _kraken_service and symbol in TRADING_PAIRS:
        try:
            ticker = await _kraken_service.get_ticker(TRADING_PAIRS[symbol]['pair'])
            if ticker:
                current_price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
        except:
            pass
    
    # Calculate unrealized P&L
    pnl_data = await _entry_tracker.calculate_unrealized_pnl(symbol, current_price)
    
    return {
        "entry": entry,
        "current_price": current_price,
        "pnl": pnl_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/entry-prices/{symbol}")
async def manually_set_entry_price(
    symbol: str,
    entry_price: float = Query(..., gt=0, description="Entry price per unit"),
    quantity: float = Query(..., gt=0, description="Quantity held")
):
    """
    Manually set entry price for a position.
    Useful for recording positions acquired before tracking was enabled.
    """
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracking not initialized")
    
    symbol = symbol.upper()
    
    result = await _entry_tracker.record_buy(
        symbol=symbol,
        quantity=quantity,
        price=entry_price,
        source="manual_entry"
    )
    
    return {
        "success": True,
        "symbol": symbol,
        "entry_price": entry_price,
        "quantity": quantity,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.delete("/entry-prices/{symbol}")
async def delete_entry_price(symbol: str):
    """Delete entry price record for a symbol"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracking not initialized")
    
    symbol = symbol.upper()
    
    if _entry_tracker.collection:
        result = await _entry_tracker.collection.delete_one({"symbol": symbol})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"No entry found for {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "message": f"Entry price record for {symbol} deleted",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    raise HTTPException(status_code=503, detail="Database not available")


@router.get("/portfolio-pnl")
async def get_portfolio_pnl():
    """Get comprehensive P&L summary for entire portfolio"""
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracking not initialized")
    
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    # Get current prices for all held assets
    current_prices = {}
    for symbol in TRADING_PAIRS:
        try:
            ticker = await _kraken_service.get_ticker(TRADING_PAIRS[symbol]['pair'])
            if ticker:
                current_prices[symbol] = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
        except:
            pass
    
    pnl_summary = await _entry_tracker.get_portfolio_pnl_summary(current_prices)
    
    return pnl_summary


@router.get("/cache-stats")
async def get_cache_stats():
    """Get Kraken API cache statistics"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    if hasattr(_kraken_service, 'get_stats'):
        stats = _kraken_service.get_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return {
        "message": "Cache stats not available",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/cache-invalidate")
async def invalidate_cache(key: str = None):
    """Invalidate Kraken API cache (admin use)"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    if hasattr(_kraken_service, 'invalidate'):
        _kraken_service.invalidate(key)
        return {
            "success": True,
            "invalidated": key or "all",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return {"message": "Cache invalidation not available"}


# ============= Trade History Sync =============

@router.post("/sync-trade-history")
async def sync_trade_history(
    days_back: int = Query(365, ge=1, le=1825, description="Number of days of history to sync"),
    force_resync: bool = Query(False, description="Clear existing entries and resync")
):
    """
    Sync historical trades from Kraken to populate entry prices.
    
    This will:
    1. Fetch all trades from Kraken for the specified period
    2. Process buys and sells in chronological order
    3. Update entry prices based on actual trade data
    
    Args:
        days_back: Number of days of history to fetch (default 365, max 1825/5 years)
        force_resync: If true, clears existing entry data before syncing
    """
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    import time
    
    # Calculate time range
    end_time = int(time.time())
    start_time = end_time - (days_back * 24 * 60 * 60)
    
    # Clear existing if force resync
    if force_resync and _entry_tracker.collection:
        await _entry_tracker.collection.delete_many({})
        logger.info("🗑️ Cleared existing entry prices for resync")
    
    # Fetch all trades with pagination
    all_trades = []
    offset = 0
    
    while True:
        try:
            # Get raw kraken service if using cache wrapper
            kraken = _kraken_service._kraken if hasattr(_kraken_service, '_kraken') else _kraken_service
            
            result = await kraken.get_trades_history(start=start_time, end=end_time, ofs=offset)
            trades = result.get("trades", {})
            
            if not trades:
                break
            
            all_trades.extend(list(trades.values()))
            
            # Check if we have more trades
            total_count = result.get("count", 0)
            offset += len(trades)
            
            if offset >= total_count or len(trades) < 50:
                break
                
            # Rate limit protection
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            break
    
    if not all_trades:
        return {
            "success": True,
            "message": "No trades found in the specified period",
            "trades_processed": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Sort trades by time (oldest first)
    all_trades.sort(key=lambda t: t.get("time", 0))
    
    # Map Kraken pair names to symbols
    pair_to_symbol = {}
    for symbol, info in TRADING_PAIRS.items():
        pair_to_symbol[info['pair']] = symbol
        # Also map without X/Z prefixes
        alt_pair = info['pair'].replace('X', '').replace('Z', '')
        pair_to_symbol[alt_pair] = symbol
    
    # Process trades
    processed = 0
    buys = 0
    sells = 0
    errors = 0
    symbols_updated = set()
    
    for trade in all_trades:
        try:
            pair = trade.get("pair", "")
            trade_type = trade.get("type", "").lower()
            volume = float(trade.get("vol", 0))
            price = float(trade.get("price", 0))
            order_id = trade.get("ordertxid", "")
            
            # Find symbol from pair
            symbol = pair_to_symbol.get(pair)
            if not symbol:
                # Try alternate formats
                for s, info in TRADING_PAIRS.items():
                    if pair in info['pair'] or info['pair'] in pair:
                        symbol = s
                        break
            
            if not symbol or volume <= 0 or price <= 0:
                continue
            
            if trade_type == "buy":
                await _entry_tracker.record_buy(
                    symbol=symbol,
                    quantity=volume,
                    price=price,
                    order_id=order_id,
                    source="kraken_sync"
                )
                buys += 1
                symbols_updated.add(symbol)
            elif trade_type == "sell":
                await _entry_tracker.record_sell(
                    symbol=symbol,
                    quantity=volume,
                    price=price,
                    order_id=order_id,
                    source="kraken_sync"
                )
                sells += 1
                symbols_updated.add(symbol)
            
            processed += 1
            
        except Exception as e:
            logger.warning(f"Error processing trade: {e}")
            errors += 1
    
    # Get updated entry prices summary
    entries = await _entry_tracker.get_all_entries()
    
    return {
        "success": True,
        "message": f"Synced {processed} trades ({buys} buys, {sells} sells)",
        "summary": {
            "trades_found": len(all_trades),
            "trades_processed": processed,
            "buys": buys,
            "sells": sells,
            "errors": errors,
            "symbols_updated": list(symbols_updated),
            "positions_with_entry_prices": len(entries)
        },
        "entries": [
            {
                "symbol": e.get("symbol"),
                "entry_price": e.get("entry_price"),
                "quantity": e.get("quantity"),
                "total_buys": e.get("total_buys", 0),
                "total_sells": e.get("total_sells", 0),
                "realized_pnl": e.get("realized_pnl", 0)
            }
            for e in entries
        ],
        "period": {
            "start": datetime.fromtimestamp(start_time, timezone.utc).isoformat(),
            "end": datetime.fromtimestamp(end_time, timezone.utc).isoformat(),
            "days": days_back
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/trade-history/summary")
async def get_trade_history_summary():
    """Get summary of synced trade history and entry prices"""
    if _entry_tracker is None:
        return {
            "has_data": False,
            "message": "Entry tracker not initialized",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    entries = await _entry_tracker.get_all_entries()
    
    total_cost_basis = 0
    total_realized_pnl = 0
    total_buys = 0
    total_sells = 0
    
    positions = []
    for entry in entries:
        cost_basis = (entry.get("entry_price", 0) or 0) * (entry.get("quantity", 0) or 0)
        total_cost_basis += cost_basis
        total_realized_pnl += entry.get("realized_pnl", 0) or 0
        total_buys += entry.get("total_buys", 0) or 0
        total_sells += entry.get("total_sells", 0) or 0
        
        positions.append({
            "symbol": entry.get("symbol"),
            "entry_price": entry.get("entry_price"),
            "quantity": entry.get("quantity"),
            "cost_basis": cost_basis,
            "total_buys": entry.get("total_buys", 0),
            "total_sells": entry.get("total_sells", 0),
            "realized_pnl": entry.get("realized_pnl", 0),
            "first_buy": entry.get("created_at"),
            "last_updated": entry.get("updated_at")
        })
    
    return {
        "has_data": len(entries) > 0,
        "summary": {
            "positions_tracked": len(entries),
            "total_cost_basis": round(total_cost_basis, 2),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "total_trade_count": total_buys + total_sells,
            "total_buys": total_buys,
            "total_sells": total_sells
        },
        "positions": positions,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

