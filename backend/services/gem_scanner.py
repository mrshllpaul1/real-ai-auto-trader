import asyncio
import httpx
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class GemScanner:
    """
    Real-time scanner that monitors market conditions and alerts
    when coins match the AI's learned 10x-100x hidden gem patterns
    """
    
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.scan_interval = 300  # 5 minutes
        self.coinmarketcap_key = os.getenv('COINMARKETCAP_API_KEY')
        self.coingecko_url = 'https://api.coingecko.com/api/v3'
        
        # Coins to monitor
        self.monitored_coins = [
            'bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot',
            'avalanche-2', 'chainlink', 'matic-network', 'uniswap', 'litecoin',
            'dogecoin', 'shiba-inu', 'ripple', 'tron', 'cosmos',
            'near', 'aptos', 'sui', 'arbitrum', 'optimism'
        ]
        
        # Learned patterns from training (loaded from DB)
        self.learned_signals = None
        self.optimal_conditions = None
    
    async def load_learned_patterns(self):
        """Load the AI's learned patterns from training"""
        patterns = await self.db.gem_success_patterns.find_one({}, {'_id': 0})
        if patterns:
            self.learned_signals = patterns.get('best_entry_signals', [])
            self.optimal_conditions = patterns.get('optimal_conditions', {})
            return True
        return False
    
    async def fetch_market_data(self) -> Dict[str, Any]:
        """Fetch current market data for all monitored coins"""
        market_data = {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Fetch from CoinGecko
                response = await client.get(
                    f"{self.coingecko_url}/coins/markets",
                    params={
                        'vs_currency': 'usd',
                        'ids': ','.join(self.monitored_coins),
                        'order': 'market_cap_desc',
                        'sparkline': 'false',
                        'price_change_percentage': '1h,24h,7d,30d'
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    coins = response.json()
                    for coin in coins:
                        market_data[coin['id']] = {
                            'name': coin.get('name'),
                            'symbol': coin.get('symbol', '').upper(),
                            'price_usd': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'price_change_1h': coin.get('price_change_percentage_1h_in_currency', 0) or 0,
                            'price_change_24h': coin.get('price_change_percentage_24h', 0) or 0,
                            'price_change_7d': coin.get('price_change_percentage_7d_in_currency', 0) or 0,
                            'price_change_30d': coin.get('price_change_percentage_30d_in_currency', 0) or 0,
                            'ath': coin.get('ath', 0),
                            'ath_change_percentage': coin.get('ath_change_percentage', 0),
                            'market_cap_rank': coin.get('market_cap_rank', 999)
                        }
                
                # Fetch additional data for RSI calculation (historical prices)
                for coin_id in list(market_data.keys())[:10]:  # Limit to avoid rate limits
                    try:
                        hist_response = await client.get(
                            f"{self.coingecko_url}/coins/{coin_id}/market_chart",
                            params={'vs_currency': 'usd', 'days': '14'},
                            timeout=15.0
                        )
                        if hist_response.status_code == 200:
                            hist_data = hist_response.json()
                            prices = [p[1] for p in hist_data.get('prices', [])]
                            volumes = [v[1] for v in hist_data.get('total_volumes', [])]
                            
                            if len(prices) > 14:
                                # Calculate RSI
                                rsi = self._calculate_rsi(prices)
                                market_data[coin_id]['rsi'] = rsi
                                
                                # Calculate volume ratio
                                if volumes:
                                    avg_volume = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[0]
                                    current_volume = volumes[-1] if volumes else 0
                                    market_data[coin_id]['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1
                                
                                # Calculate price vs recent average (proxy for SMA position)
                                avg_price = sum(prices) / len(prices)
                                market_data[coin_id]['price_vs_avg'] = (prices[-1] - avg_price) / avg_price if avg_price > 0 else 0
                                
                        await asyncio.sleep(0.5)  # Rate limit protection
                    except Exception as e:
                        print(f"Error fetching historical data for {coin_id}: {e}")
                        
        except Exception as e:
            print(f"Error fetching market data: {e}")
        
        return market_data
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI from price list"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze_coin_for_gems(self, coin_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single coin against learned 10x-100x patterns
        Returns match score and signals
        """
        match_score = 0
        matching_signals = []
        alert_level = 'NONE'
        
        rsi = data.get('rsi', 50)
        volume_ratio = data.get('volume_ratio', 1.0)
        price_change_24h = data.get('price_change_24h', 0)
        price_change_7d = data.get('price_change_7d', 0)
        price_change_30d = data.get('price_change_30d', 0)
        ath_change = data.get('ath_change_percentage', 0)
        price_vs_avg = data.get('price_vs_avg', 0)
        
        # Signal 1: MACD BULLISH proxy (price momentum + volume)
        # Learned: RSI ~77, Volume 3.6x
        if price_change_24h > 5 and volume_ratio > 2.0:
            match_score += 25
            matching_signals.append({
                'signal': 'MACD_BULLISH',
                'description': 'Strong upward momentum with high volume',
                'strength': min(100, int(volume_ratio * 20 + price_change_24h))
            })
        
        # Signal 2: BOLLINGER SQUEEZE proxy (low recent volatility + volume building)
        # Learned: RSI ~71, Volume 3.4x
        if abs(price_change_7d) < 5 and volume_ratio > 1.5 and price_change_24h > 0:
            match_score += 20
            matching_signals.append({
                'signal': 'BOLLINGER_SQUEEZE',
                'description': 'Low volatility with volume accumulation - potential breakout',
                'strength': int(volume_ratio * 25)
            })
        
        # Signal 3: OVERSOLD ACCUMULATION
        # Learned: RSI ~6, Volume 3.5x
        if rsi < 30 and volume_ratio > 1.5:
            match_score += 30
            matching_signals.append({
                'signal': 'OVERSOLD_ACCUMULATION',
                'description': f'Oversold (RSI: {rsi:.1f}) with accumulation volume',
                'strength': int((30 - rsi) * 2 + volume_ratio * 10)
            })
        
        # Signal 4: DEEP VALUE
        # Learned: RSI ~5.5, Volume 3.5x, price well below averages
        if ath_change < -70 and volume_ratio > 1.2:
            match_score += 25
            matching_signals.append({
                'signal': 'DEEP_VALUE',
                'description': f'{abs(ath_change):.0f}% below ATH with volume interest',
                'strength': min(100, int(abs(ath_change) * 0.8))
            })
        
        # Signal 5: TREND REVERSAL
        # Learned: RSI ~11, Volume 3.6x, recovering from downtrend
        if price_change_30d < -20 and price_change_7d > 0 and price_change_24h > 0:
            match_score += 20
            matching_signals.append({
                'signal': 'TREND_REVERSAL',
                'description': 'Recovering from downtrend with positive momentum',
                'strength': int(abs(price_change_30d) * 0.5 + price_change_24h * 2)
            })
        
        # Additional: EXTREME VOLUME (98% of 10x gems had 2x+ volume)
        if volume_ratio > 3.0:
            match_score += 15
            matching_signals.append({
                'signal': 'EXTREME_VOLUME',
                'description': f'Volume {volume_ratio:.1f}x above average - major interest',
                'strength': min(100, int(volume_ratio * 20))
            })
        
        # Calculate alert level
        if match_score >= 60:
            alert_level = 'HIGH'
        elif match_score >= 40:
            alert_level = 'MEDIUM'
        elif match_score >= 20:
            alert_level = 'LOW'
        
        # Calculate potential based on signals
        potential_multiplier = "1x"
        if match_score >= 70:
            potential_multiplier = "10x-50x"
        elif match_score >= 50:
            potential_multiplier = "5x-10x"
        elif match_score >= 30:
            potential_multiplier = "2x-5x"
        
        return {
            'coin_id': coin_id,
            'symbol': data.get('symbol', coin_id.upper()),
            'name': data.get('name', coin_id),
            'current_price': data.get('price_usd', 0),
            'market_cap_rank': data.get('market_cap_rank', 999),
            'match_score': match_score,
            'alert_level': alert_level,
            'potential_multiplier': potential_multiplier,
            'matching_signals': matching_signals,
            'indicators': {
                'rsi': round(rsi, 1),
                'volume_ratio': round(volume_ratio, 2),
                'price_change_24h': round(price_change_24h, 2),
                'price_change_7d': round(price_change_7d, 2),
                'ath_change': round(ath_change, 1)
            },
            'scanned_at': datetime.now().isoformat()
        }
    
    async def scan_market(self) -> List[Dict[str, Any]]:
        """Perform a full market scan and return alerts"""
        print(f"\n🔍 Scanning market for hidden gems... ({datetime.now().strftime('%H:%M:%S')})")
        
        # Load learned patterns if not loaded
        if not self.learned_signals:
            await self.load_learned_patterns()
        
        # Fetch current market data
        market_data = await self.fetch_market_data()
        
        if not market_data:
            print("  ⚠️ No market data available")
            return []
        
        # Analyze each coin
        alerts = []
        for coin_id, data in market_data.items():
            analysis = self.analyze_coin_for_gems(coin_id, data)
            
            if analysis['match_score'] > 0:
                alerts.append(analysis)
        
        # Sort by match score
        alerts.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Store alerts in database
        if alerts:
            await self.db.gem_alerts.delete_many({})  # Clear old alerts
            await self.db.gem_alerts.insert_many(alerts)
            
            # Store in alert history (keep last 100)
            for alert in alerts[:10]:  # Top 10 only
                alert['timestamp'] = datetime.now()
                await self.db.gem_alert_history.insert_one(alert)
            
            # Cleanup old history
            count = await self.db.gem_alert_history.count_documents({})
            if count > 500:
                oldest = await self.db.gem_alert_history.find().sort('timestamp', 1).limit(count - 500).to_list(count - 500)
                if oldest:
                    ids = [doc['_id'] for doc in oldest]
                    await self.db.gem_alert_history.delete_many({'_id': {'$in': ids}})
        
        # Print summary
        high_alerts = [a for a in alerts if a['alert_level'] == 'HIGH']
        medium_alerts = [a for a in alerts if a['alert_level'] == 'MEDIUM']
        
        print(f"  ✅ Scan complete: {len(alerts)} coins analyzed")
        print(f"  🔴 HIGH alerts: {len(high_alerts)}")
        print(f"  🟡 MEDIUM alerts: {len(medium_alerts)}")
        
        if high_alerts:
            print("\n  🚨 HIGH ALERT GEMS:")
            for alert in high_alerts[:3]:
                print(f"     {alert['symbol']}: Score {alert['match_score']} - {alert['potential_multiplier']} potential")
        
        return alerts
    
    async def start_scanner(self, interval_seconds: int = 300):
        """Start the continuous scanner"""
        self.is_running = True
        self.scan_interval = interval_seconds
        
        print("="*60)
        print("🚀 HIDDEN GEM SCANNER STARTED")
        print("="*60)
        print(f"Scan interval: {interval_seconds} seconds")
        print(f"Monitoring: {len(self.monitored_coins)} coins")
        print("="*60)
        
        while self.is_running:
            try:
                await self.scan_market()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                print(f"Scanner error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    def stop_scanner(self):
        """Stop the scanner"""
        self.is_running = False
        print("\n🛑 Hidden gem scanner stopped")
    
    async def get_current_alerts(self, min_score: int = 0) -> List[Dict[str, Any]]:
        """Get current alerts from last scan"""
        query = {}
        if min_score > 0:
            query['match_score'] = {'$gte': min_score}
        
        alerts = await self.db.gem_alerts.find(
            query, {'_id': 0}
        ).sort('match_score', -1).to_list(50)
        
        return alerts
    
    async def get_alert_history(self, coin_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical alerts"""
        query = {}
        if coin_id:
            query['coin_id'] = coin_id
        
        alerts = await self.db.gem_alert_history.find(
            query, {'_id': 0}
        ).sort('timestamp', -1).to_list(limit)
        
        return alerts
    
    async def get_scanner_status(self) -> Dict[str, Any]:
        """Get scanner status"""
        last_scan = await self.db.gem_alerts.find_one({}, {'_id': 0, 'scanned_at': 1})
        alert_count = await self.db.gem_alerts.count_documents({})
        high_count = await self.db.gem_alerts.count_documents({'alert_level': 'HIGH'})
        
        return {
            'running': self.is_running,
            'scan_interval_seconds': self.scan_interval,
            'monitored_coins': len(self.monitored_coins),
            'last_scan': last_scan.get('scanned_at') if last_scan else None,
            'current_alerts': alert_count,
            'high_alerts': high_count,
            'coins_list': self.monitored_coins
        }
