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


def set_dependencies(database, kraken_service, isolated_portfolio=None, automated_trader=None, prediction_services=None):
    """Set dependencies from main app"""
    global _db, _kraken_service, _isolated_portfolio, _automated_trader, _prediction_services
    _db = database
    _kraken_service = kraken_service
    _isolated_portfolio = isolated_portfolio
    _automated_trader = automated_trader
    _prediction_services = prediction_services


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
    """Get user's spot balance across all supported coins"""
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
        
        holdings = []
        total_usd_value = 0
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
                holdings.append({
                    "symbol": symbol,
                    "name": TRADING_PAIRS.get(symbol, {}).get('name', symbol),
                    "amount": amount,
                    "price": price,
                    "usd_value": round(usd_value, 2),
                    "kraken_currency": currency
                })
                total_usd_value += usd_value
        
        # Sort by USD value
        holdings.sort(key=lambda x: x['usd_value'], reverse=True)
        
        return {
            "holdings": holdings,
            "usd_balance": round(usd_balance, 2),
            "total_crypto_value": round(total_usd_value, 2),
            "total_portfolio_value": round(usd_balance + total_usd_value, 2),
            "holdings_count": len(holdings),
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
async def get_ai_recommendations(
    min_confidence: float = Query(0.5, ge=0, le=1, description="Minimum confidence filter"),
    limit: int = Query(15, ge=1, le=50, description="Number of recommendations")
):
    """
    Get enhanced AI trading recommendations for all supported pairs.
    
    Returns comprehensive analysis including:
    - Multi-signal composite scoring
    - Confidence levels and accuracy tracking
    - Price targets and risk metrics
    - Trend analysis and momentum
    - Historical performance data
    """
    if _automated_trader is None:
        raise HTTPException(status_code=503, detail="Auto trader not initialized")
    
    recommendations = []
    
    for symbol in list(TRADING_PAIRS.keys())[:limit]:  # Top N pairs
        try:
            signals = await _automated_trader.get_prediction_signals(symbol)
            
            if not signals:
                continue
                
            # Filter by confidence
            confidence = signals.get('confidence', 0)
            if confidence < min_confidence:
                continue
            
            pair_info = TRADING_PAIRS[symbol]
            
            # Get current price and market data
            price = 0
            volume_24h = 0
            change_24h = 0
            high_24h = 0
            low_24h = 0
            
            if _kraken_service:
                try:
                    ticker = await _kraken_service.get_ticker(pair_info['pair'])
                    if ticker:
                        price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
                        volume_24h = float(ticker.get("v", [0, 0])[1]) if ticker.get("v") else 0
                        low_24h = float(ticker.get("l", [0, 0])[1]) if ticker.get("l") else 0
                        high_24h = float(ticker.get("h", [0, 0])[1]) if ticker.get("h") else 0
                        open_24h = float(ticker.get("o", 0)) if ticker.get("o") else price
                        change_24h = ((price - open_24h) / open_24h * 100) if open_24h else 0
                except:
                    pass
            
            # Calculate signal strength and action
            composite_score = signals.get('composite_score', 0)
            signal_type = signals.get('composite_signal', 'neutral')
            
            # Determine action recommendation
            if composite_score > 0.5:
                action = "Strong Buy"
                action_color = "success"
            elif composite_score > 0.2:
                action = "Buy"
                action_color = "success"
            elif composite_score < -0.5:
                action = "Strong Sell"
                action_color = "danger"
            elif composite_score < -0.2:
                action = "Sell"
                action_color = "danger"
            else:
                action = "Hold"
                action_color = "neutral"
            
            # Calculate price targets (basic estimate based on signal strength)
            if price > 0:
                target_percent = abs(composite_score) * 10  # Up to 10% move
                if composite_score > 0:
                    price_target = price * (1 + target_percent / 100)
                    stop_loss = price * 0.95  # 5% stop loss
                else:
                    price_target = price * (1 - target_percent / 100)
                    stop_loss = price * 1.05  # 5% stop loss above
            else:
                price_target = None
                stop_loss = None
            
            # Extract component scores
            components = {}
            for key in ['order_book', 'on_chain', 'social', 'transformer', 'rl_agent', 'technical']:
                if key in signals:
                    val = signals[key]
                    if isinstance(val, dict):
                        components[key] = {
                            'score': val.get('score', 0),
                            'signal': val.get('signal', 'neutral')
                        }
                    else:
                        components[key] = {'score': val, 'signal': 'neutral'}
            
            # Calculate trend strength (based on consistency of signals)
            if components:
                bullish_count = sum(1 for c in components.values() if isinstance(c, dict) and c.get('score', 0) > 0)
                bearish_count = sum(1 for c in components.values() if isinstance(c, dict) and c.get('score', 0) < 0)
                total = len(components)
                trend_strength = max(bullish_count, bearish_count) / total if total > 0 else 0
            else:
                trend_strength = 0
            
            # Get historical accuracy from DB if available
            historical_accuracy = None
            if _db:
                try:
                    # Query recent predictions for this symbol
                    recent_predictions = await _db.ai_predictions.find(
                        {"symbol": symbol},
                        {"_id": 0, "accuracy": 1}
                    ).sort("timestamp", -1).limit(10).to_list(10)
                    
                    if recent_predictions:
                        accuracies = [p.get('accuracy', 0) for p in recent_predictions if 'accuracy' in p]
                        if accuracies:
                            historical_accuracy = sum(accuracies) / len(accuracies)
                except:
                    pass
            
            recommendations.append({
                "symbol": symbol,
                "name": pair_info['name'],
                "price": price,
                "change_24h": round(change_24h, 2),
                "volume_24h": volume_24h,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "signal": signal_type,
                "score": round(composite_score, 3),
                "confidence": round(confidence, 2),
                "action": action,
                "action_color": action_color,
                "recommendation": signals.get('recommendation', 'Hold position'),
                "price_target": round(price_target, 2) if price_target else None,
                "stop_loss": round(stop_loss, 2) if stop_loss else None,
                "trend_strength": round(trend_strength, 2),
                "potential_return": round(target_percent, 1) if price > 0 else 0,
                "risk_reward_ratio": round(abs(target_percent) / 5, 2) if price > 0 else 0,  # vs 5% stop
                "components": components,
                "historical_accuracy": round(historical_accuracy, 2) if historical_accuracy else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.warning(f"AI recommendation error for {symbol}: {e}")
    
    # Sort by confidence-weighted score
    recommendations.sort(key=lambda x: abs(x['score']) * x['confidence'], reverse=True)
    
    # Add ranking
    for idx, rec in enumerate(recommendations):
        rec['rank'] = idx + 1
    
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "filters": {
            "min_confidence": min_confidence,
            "limit": limit
        },
        "summary": {
            "bullish_count": sum(1 for r in recommendations if r['score'] > 0.2),
            "bearish_count": sum(1 for r in recommendations if r['score'] < -0.2),
            "neutral_count": sum(1 for r in recommendations if -0.2 <= r['score'] <= 0.2),
            "avg_confidence": round(sum(r['confidence'] for r in recommendations) / len(recommendations), 2) if recommendations else 0,
            "high_confidence_count": sum(1 for r in recommendations if r['confidence'] > 0.7)
        },
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


# =============================================================================
# ENHANCED SPOT TRADING PREDICTIONS
# =============================================================================

class EnhancedSpotPredictionRequest(BaseModel):
    symbol: str
    target_hold_days: Optional[int] = 7  # How long planning to hold
    capital_pct: Optional[float] = 10.0  # What % of capital to deploy
    

@router.post("/ai-enhanced-prediction")
async def get_enhanced_spot_prediction(request: EnhancedSpotPredictionRequest):
    """
    Get enhanced AI prediction for spot trading with:
    - Entry timing optimization (DCA vs lump sum)
    - Multi-timeframe signal confluence
    - Volatility-adjusted position sizing
    - Dynamic stop-loss and take-profit zones
    - Hold duration recommendations
    - Market regime context
    """
    symbol = request.symbol
    
    if not _automated_trader:
        raise HTTPException(
            status_code=503,
            detail="Prediction services not available"
        )
    
    if symbol not in TRADING_PAIRS:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol {symbol} not supported"
        )
    
    try:
        # Get base predictions
        signals = await _automated_trader.get_prediction_signals(symbol)
        pair_info = TRADING_PAIRS[symbol]
        
        # Get current price
        price = 0
        volume_24h = 0
        change_24h = 0
        
        if _kraken_service:
            try:
                ticker = await _kraken_service.get_ticker(pair_info['pair'])
                if ticker:
                    price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
                    volume_24h = float(ticker.get("v", [0, 0])[1]) if ticker.get("v") else 0
                    open_24h = float(ticker.get("o", 0)) if ticker.get("o") else price
                    change_24h = ((price - open_24h) / open_24h * 100) if open_24h else 0
            except:
                pass
        
        if price == 0:
            raise HTTPException(status_code=500, detail="Unable to fetch current price")
        
        # Extract composite signal
        composite = signals.get('composite', {})
        score = composite.get('score', 50)
        confidence = composite.get('confidence', 0)
        signal = composite.get('signal', 'hold')
        
        # Normalize score to -1 to +1 range
        normalized_score = (score - 50) / 50
        signal_strength = abs(normalized_score)
        
        # === VOLATILITY ANALYSIS ===
        volatility_regime = "normal"
        volatility_factor = 1.0
        
        if 'advanced_ta' in signals.get('components', {}):
            volatility_regime = signals['components']['advanced_ta'].get('volatility_regime', 'normal')
            if volatility_regime == 'high':
                volatility_factor = 0.7  # Reduce size by 30%
            elif volatility_regime == 'extreme':
                volatility_factor = 0.5  # Reduce size by 50%
            elif volatility_regime == 'low':
                volatility_factor = 1.3  # Can size up 30%
        
        # === MULTI-TIMEFRAME CONFLUENCE ===
        # Check if signals align across different timeframes
        timeframe_scores = {}
        components = signals.get('components', {})
        
        # Map components to "timeframes" (different analysis types act as proxies)
        if 'transformer' in components:  # Long-term trend
            timeframe_scores['long_term'] = components['transformer'].get('score', 50)
        if 'rl_agent' in components:  # Medium-term
            timeframe_scores['medium_term'] = components['rl_agent'].get('score', 50)
        if 'advanced_ta' in components:  # Short-term
            timeframe_scores['short_term'] = components['advanced_ta'].get('score', 50)
        
        # Calculate confluence (agreement across timeframes)
        if timeframe_scores:
            bullish_tfs = sum(1 for s in timeframe_scores.values() if s > 60)
            bearish_tfs = sum(1 for s in timeframe_scores.values() if s < 40)
            total_tfs = len(timeframe_scores)
            
            if bullish_tfs == total_tfs:
                confluence = "strong_bullish"
                confluence_score = 100
            elif bearish_tfs == total_tfs:
                confluence = "strong_bearish"
                confluence_score = 100
            elif bullish_tfs > bearish_tfs:
                confluence = "bullish"
                confluence_score = bullish_tfs / total_tfs * 100
            elif bearish_tfs > bullish_tfs:
                confluence = "bearish"
                confluence_score = bearish_tfs / total_tfs * 100
            else:
                confluence = "mixed"
                confluence_score = 50
        else:
            confluence = "unknown"
            confluence_score = 0
        
        # === ENTRY TIMING OPTIMIZATION ===
        # DCA (Dollar Cost Averaging) vs Lump Sum recommendation
        
        if signal_strength > 0.6 and confidence > 75:
            entry_strategy = "LUMP_SUM"
            entry_detail = "Strong signal with high confidence - enter full position now"
            dca_splits = 1
        elif signal_strength > 0.3 and confidence > 60:
            entry_strategy = "SPLIT_2"
            entry_detail = "Moderate signal - split entry into 2 parts (60% now, 40% on dip)"
            dca_splits = 2
        elif volatility_regime in ['high', 'extreme']:
            entry_strategy = "DCA_4"
            entry_detail = "High volatility - use 4-part DCA over next 48 hours"
            dca_splits = 4
        else:
            entry_strategy = "DCA_3"
            entry_detail = "Conservative approach - use 3-part DCA over next 72 hours"
            dca_splits = 3
        
        # Calculate DCA entry prices
        if normalized_score > 0:  # Bullish
            dca_prices = [
                round(price * (1 - 0.01 * i), 2) 
                for i in range(dca_splits)
            ]
        else:  # Bearish or neutral
            dca_prices = [
                round(price * (1 + 0.01 * i), 2) 
                for i in range(dca_splits)
            ]
        
        # === POSITION SIZING ===
        recommended_position_pct = request.capital_pct * volatility_factor
        
        # Adjust based on confidence
        if confidence > 80:
            recommended_position_pct *= 1.3
        elif confidence < 50:
            recommended_position_pct *= 0.6
        
        recommended_position_pct = min(recommended_position_pct, 20.0)  # Cap at 20%
        
        # === DYNAMIC STOP-LOSS CALCULATION ===
        # Base stop-loss on volatility and timeframe
        
        if volatility_regime == 'extreme':
            stop_loss_pct = 15.0  # Wider stop for volatile markets
        elif volatility_regime == 'high':
            stop_loss_pct = 10.0
        elif volatility_regime == 'low':
            stop_loss_pct = 5.0  # Tighter stop for stable markets
        else:
            stop_loss_pct = 7.5  # Normal
        
        # Adjust for hold duration
        if request.target_hold_days <= 3:
            stop_loss_pct *= 0.7  # Tighter for short holds
        elif request.target_hold_days >= 14:
            stop_loss_pct *= 1.3  # Wider for long holds
        
        if normalized_score > 0:
            stop_loss = round(price * (1 - stop_loss_pct / 100), 2)
        else:
            stop_loss = round(price * (1 + stop_loss_pct / 100), 2)
        
        # === DYNAMIC TAKE-PROFIT ZONES ===
        # Calculate multiple TP levels based on signal strength and timeframe
        
        base_tp_pct = signal_strength * 20  # 0-20% based on signal
        
        if request.target_hold_days <= 3:
            # Short hold - conservative targets
            tp_multipliers = [0.5, 1.0, 1.5]
        elif request.target_hold_days <= 7:
            # Medium hold - moderate targets
            tp_multipliers = [0.7, 1.3, 2.0]
        else:
            # Long hold - aggressive targets
            tp_multipliers = [1.0, 2.0, 3.0]
        
        if normalized_score > 0:
            take_profit_zones = [
                {
                    "level": i + 1,
                    "price": round(price * (1 + base_tp_pct * mult / 100), 2),
                    "gain_pct": round(base_tp_pct * mult, 2),
                    "recommended_exit_pct": [30, 40, 30][i]  # Exit % at each level
                }
                for i, mult in enumerate(tp_multipliers)
            ]
        else:
            take_profit_zones = [
                {
                    "level": i + 1,
                    "price": round(price * (1 - base_tp_pct * mult / 100), 2),
                    "gain_pct": round(base_tp_pct * mult, 2),
                    "recommended_exit_pct": [30, 40, 30][i]
                }
                for i, mult in enumerate(tp_multipliers)
            ]
        
        # === HOLD DURATION RECOMMENDATION ===
        # Based on signal type and market regime
        
        if signal in ['strong_buy', 'strong_sell']:
            if request.target_hold_days < 7:
                hold_recommendation = "EXTEND"
                hold_detail = "Strong signal suggests holding for at least 7-14 days"
                optimal_hold_days = 14
            else:
                hold_recommendation = "GOOD"
                hold_detail = f"Your {request.target_hold_days}-day timeframe aligns with signal"
                optimal_hold_days = request.target_hold_days
        elif signal in ['buy', 'sell']:
            optimal_hold_days = max(request.target_hold_days, 5)
            hold_recommendation = "MODERATE"
            hold_detail = f"Moderate signal - recommend {optimal_hold_days}-day hold minimum"
        else:
            optimal_hold_days = request.target_hold_days
            hold_recommendation = "WAIT"
            hold_detail = "Weak signal - consider waiting for better setup"
        
        # === RISK/REWARD ANALYSIS ===
        main_target = take_profit_zones[1]['price']  # Use middle TP
        risk = abs(price - stop_loss)
        reward = abs(main_target - price)
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0
        
        # Expected value calculation
        win_probability = confidence / 100 * 0.8  # Discount confidence slightly
        expected_value = (win_probability * reward - (1 - win_probability) * risk) / price * 100
        
        # === MARKET REGIME CONTEXT ===
        market_regime = "unknown"
        regime_confidence = 0
        
        if 'cross_asset' in components:
            regime_data = components['cross_asset']
            if isinstance(regime_data, dict):
                market_regime = regime_data.get('risk_regime', 'unknown')
        
        # === TRADING RECOMMENDATION ===
        if signal in ['strong_buy', 'strong_sell']:
            if confidence > 75 and confluence_score > 75 and risk_reward_ratio > 2:
                action = "STRONG_ENTER"
                action_detail = f"Excellent setup - {signal.replace('_', ' ')} with {confluence} confluence"
            else:
                action = "ENTER"
                action_detail = f"Good setup - {signal.replace('_', ' ')}"
        elif signal in ['buy', 'sell']:
            if confluence_score > 60:
                action = "CONSIDER"
                action_detail = f"Consider {signal}ing with reduced size"
            else:
                action = "WAIT_CONFIRM"
                action_detail = "Wait for stronger confirmation"
        else:
            action = "WAIT"
            action_detail = "No clear edge - wait for better setup"
        
        # Adjust for poor risk/reward
        if risk_reward_ratio < 1.5 and action != "WAIT":
            action = "WAIT_BETTER_ENTRY"
            action_detail += " (Poor risk/reward - wait for better entry price)"
        
        # Compile response
        return {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            
            # Core Signal
            "signal": {
                "direction": signal,
                "score": score,
                "confidence": confidence,
                "strength": round(signal_strength, 2),
                "side": "long" if normalized_score > 0 else "short"
            },
            
            # Trading Recommendation
            "recommendation": {
                "action": action,
                "detail": action_detail
            },
            
            # Multi-Timeframe Analysis
            "timeframe_analysis": {
                "confluence": confluence,
                "confluence_score": round(confluence_score, 1),
                "timeframe_breakdown": timeframe_scores,
                "assessment": "Strong agreement" if confluence_score > 75 else 
                             "Moderate agreement" if confluence_score > 50 else 
                             "Mixed signals"
            },
            
            # Entry Strategy
            "entry_strategy": {
                "method": entry_strategy,
                "detail": entry_detail,
                "dca_splits": dca_splits,
                "dca_prices": dca_prices,
                "current_price": price
            },
            
            # Position Sizing
            "position_sizing": {
                "recommended_capital_pct": round(recommended_position_pct, 1),
                "original_capital_pct": request.capital_pct,
                "volatility_factor": round(volatility_factor, 2),
                "volatility_regime": volatility_regime,
                "explanation": f"Adjusted for {volatility_regime} volatility and {int(confidence)}% confidence"
            },
            
            # Risk Management
            "risk_management": {
                "stop_loss": {
                    "price": stop_loss,
                    "percent": round(stop_loss_pct, 2),
                    "distance_from_entry": round(abs(price - stop_loss) / price * 100, 2)
                },
                "take_profit_zones": take_profit_zones,
                "risk_reward_ratio": risk_reward_ratio,
                "expected_value_pct": round(expected_value, 2)
            },
            
            # Hold Duration
            "hold_duration": {
                "target_days": request.target_hold_days,
                "optimal_days": optimal_hold_days,
                "recommendation": hold_recommendation,
                "detail": hold_detail
            },
            
            # Market Context
            "market_context": {
                "current_price": price,
                "24h_change_pct": round(change_24h, 2),
                "volume_24h": volume_24h,
                "volatility_regime": volatility_regime,
                "market_regime": market_regime
            },
            
            # Component Signals
            "component_signals": components
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced spot prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
