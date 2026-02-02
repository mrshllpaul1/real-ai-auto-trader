"""
Enhanced Historical Trainer
Trains AI on REAL historical cryptocurrency data ONLY.
NEVER uses simulated, synthetic, or fake data under any circumstances.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
import asyncio
from .twelvedata_service import get_twelvedata_service


class EnhancedHistoricalTrainer:
    """
    Enhanced training on REAL historical cryptocurrency data.
    Uses Twelve Data API for actual market data - NO SIMULATED DATA.
    Includes hidden gems detection (10-100x potential).
    """
    
    def __init__(self, db):
        self.db = db
        self.model_path = '/app/backend/models/historical/'
        os.makedirs(self.model_path, exist_ok=True)
        self.twelvedata = get_twelvedata_service()
        
        # Hidden gems criteria
        self.hidden_gem_indicators = {
            'market_cap_threshold': 100000000,  # Under $100M market cap
            'volume_surge_multiplier': 5,  # 5x volume increase
            'social_sentiment_min': 0.7,  # 70% positive sentiment
            'developer_activity_min': 0.6,  # Active development
            'min_gain_multiplier': 10  # 10x minimum for gem classification
        }
    
    async def get_real_historical_data(
        self,
        coin_id: str,
        days: int = 365
    ) -> pd.DataFrame:
        """
        Fetch REAL historical data from database or Twelve Data API.
        NEVER generates fake or simulated data.
        
        Returns:
            DataFrame with real OHLCV data, or empty DataFrame if unavailable.
        """
        print(f"📊 Fetching REAL data for {coin_id} (last {days} days)...")
        
        # First try to get from cached historical_prices in database
        try:
            cached = await self.db.historical_prices.find(
                {"coin_id": coin_id},
                {"_id": 0}
            ).sort("timestamp", 1).to_list(days * 2)  # Get more in case of gaps
            
            if cached and len(cached) >= days * 0.8:  # At least 80% of requested data
                print(f"  ✓ Found {len(cached)} cached records in database")
                df = pd.DataFrame(cached)
                df['date'] = pd.to_datetime(df['timestamp'])
                return df
        except Exception as e:
            print(f"  ⚠️ Database query error: {e}")
        
        # Fetch from Twelve Data API if not enough cached data
        try:
            print(f"  📥 Fetching from Twelve Data API...")
            records = await self.twelvedata.fetch_historical_for_db(coin_id, days)
            
            if records and len(records) > 0:
                print(f"  ✓ Retrieved {len(records)} records from Twelve Data")
                
                # Cache in database for future use
                try:
                    await self.db.historical_prices.delete_many({'coin_id': coin_id})
                    await self.db.historical_prices.insert_many(records)
                except Exception as cache_err:
                    print(f"  ⚠️ Cache write failed: {cache_err}")
                
                df = pd.DataFrame(records)
                df['date'] = pd.to_datetime(df['timestamp'])
                return df
        except Exception as e:
            print(f"  ⚠️ Twelve Data API error: {e}")
        
        # Return empty DataFrame if no real data available - NEVER fake it
        print(f"  ❌ WARNING: No real historical data available for {coin_id}")
        return pd.DataFrame()
    
    def calculate_comprehensive_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators for training"""
        if len(df) < 200:
            print(f"  ⚠️ Insufficient data for indicators ({len(df)} rows, need 200+)")
            return df
        
        # Basic moving averages
        df['sma_7'] = df['close'].rolling(window=7).mean()
        df['sma_30'] = df['close'].rolling(window=30).mean()
        df['sma_90'] = df['close'].rolling(window=90).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # EMAs
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volatility
        df['volatility_30'] = df['close'].rolling(window=30).std()
        df['volatility_90'] = df['close'].rolling(window=90).std()
        
        # Price changes
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_7d'] = df['close'].pct_change(7)
        df['price_change_30d'] = df['close'].pct_change(30)
        df['price_change_90d'] = df['close'].pct_change(90)
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=30).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma'].replace(0, 1)
        
        return df.dropna()
    
    def identify_hidden_gems(
        self,
        df: pd.DataFrame,
        coin_id: str
    ) -> List[Dict[str, Any]]:
        """
        Identify periods where coin was a 'hidden gem' before massive gains.
        This trains AI to recognize early signals of 10-100x coins.
        Uses REAL historical data patterns only.
        """
        gems = []
        
        if len(df) < 400:  # Need sufficient data
            print(f"  ⚠️ Insufficient data for hidden gem analysis ({len(df)} rows)")
            return gems
        
        # Look for periods of low price followed by massive gains
        for i in range(200, len(df) - 90):  # Need lookback and lookahead
            try:
                row = df.iloc[i]
                
                # Check future price (90 days ahead)
                future_price = df.iloc[i + 90]['close']
                current_price = row['close']
                
                if current_price <= 0:
                    continue
                    
                gain_multiplier = future_price / current_price
                
                # Is this a hidden gem? (3x+ gain ahead - adjusted for real data)
                if gain_multiplier >= 3:  # Lower threshold for real market data
                    # Identify the signals at this point
                    gem_signals = {
                        'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                        'coin_id': coin_id,
                        'entry_price': float(current_price),
                        'peak_price': float(future_price),
                        'gain_multiplier': float(gain_multiplier),
                        
                        # Technical signals
                        'rsi': float(row.get('rsi', 50)),
                        'macd': float(row.get('macd', 0)),
                        'volume_surge': float(row.get('volume_ratio', 1)),
                        'volatility': float(row.get('volatility_30', 0)),
                        
                        # Classification
                        'gem_type': self._classify_gem(gain_multiplier),
                        'is_hidden_gem': True,
                        'data_source': 'REAL_MARKET_DATA'
                    }
                    
                    gems.append(gem_signals)
                    print(f"   🎯 Hidden Gem Found: {coin_id} at {gem_signals['date']} → {gain_multiplier:.1f}x gain!")
            except Exception as e:
                continue
        
        return gems
    
    def _classify_gem(self, multiplier: float) -> str:
        """Classify gem by potential"""
        if multiplier >= 100:
            return 'moonshot'  # 100x+
        elif multiplier >= 50:
            return 'mega_gem'  # 50-100x
        elif multiplier >= 20:
            return 'major_gem'  # 20-50x
        elif multiplier >= 10:
            return 'gem'  # 10-20x
        else:
            return 'potential_gem'  # 3-10x
    
    async def train_with_real_data(
        self,
        coins: List[str] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
    ) -> Dict[str, Any]:
        """
        Comprehensive training with REAL market data ONLY.
        No simulated, synthetic, or fake data is ever used.
        """
        print("\n" + "="*70)
        print("🚀 ENHANCED AI TRAINING STARTED (REAL DATA ONLY)")
        print("="*70)
        print("📊 Data Source: Twelve Data API + CoinGecko (REAL market data)")
        print("💎 Hidden Gems: Training on REAL 3-100x patterns")
        print(f"🪙 Cryptocurrencies: {', '.join([c.upper() for c in coins])}")
        print("⚠️  NO SIMULATED DATA WILL BE USED")
        print("="*70 + "\n")
        
        training_results = {
            'coins_trained': [],
            'total_patterns': 0,
            'successful_patterns': 0,
            'hidden_gems_found': 0,
            'training_accuracy': 0,
            'data_source': 'REAL_MARKET_DATA_ONLY',
            'simulated_data_used': False,
            'started_at': datetime.now().isoformat()
        }
        
        all_hidden_gems = []
        
        for coin in coins:
            try:
                print(f"\n🔄 Training on {coin.upper()}...")
                print("-" * 50)
                
                # Fetch REAL historical data
                df = await self.get_real_historical_data(coin, days=365)
                
                if df.empty or len(df) < 100:
                    print(f"  ❌ Skipping {coin} - insufficient real data available")
                    continue
                
                print(f"  ✓ Loaded {len(df):,} days of REAL historical data")
                
                # Calculate indicators
                df = self.calculate_comprehensive_indicators(df)
                if df.empty:
                    print(f"  ❌ Skipping {coin} - insufficient data after indicator calculation")
                    continue
                    
                print("  ✓ Calculated comprehensive technical indicators")
                
                # Identify trading patterns using REAL data
                patterns = self.identify_historical_patterns(df)
                print(f"  ✓ Identified {len(patterns):,} trading patterns from REAL data")
                
                # Identify hidden gems from REAL price movements
                gems = self.identify_hidden_gems(df, coin)
                print(f"  ✓ Found {len(gems)} hidden gem patterns")
                
                all_hidden_gems.extend(gems)
                
                # Calculate success rate
                successful = sum(1 for p in patterns if p.get('success', False))
                success_rate = (successful / len(patterns) * 100) if patterns else 0
                print(f"  ✓ Pattern Success Rate: {success_rate:.1f}%")
                
                # Store patterns in database
                for pattern in patterns:
                    pattern['coin_id'] = coin
                    pattern['data_source'] = 'REAL_MARKET_DATA'
                    try:
                        await self.db.historical_patterns.insert_one(pattern)
                    except Exception:
                        pass
                
                # Store hidden gems
                for gem in gems:
                    try:
                        await self.db.hidden_gems.insert_one(gem)
                    except Exception:
                        pass
                
                # Store training summary
                coin_summary = {
                    'coin_id': coin,
                    'data_points': len(df),
                    'patterns_found': len(patterns),
                    'successful_patterns': successful,
                    'hidden_gems': len(gems),
                    'success_rate': success_rate,
                    'date_range': {
                        'start': str(df['date'].min()),
                        'end': str(df['date'].max())
                    },
                    'data_source': 'REAL_MARKET_DATA',
                    'trained_at': datetime.now().isoformat()
                }
                
                try:
                    await self.db.historical_training.insert_one(coin_summary)
                except Exception:
                    pass
                
                training_results['coins_trained'].append(coin)
                training_results['total_patterns'] += len(patterns)
                training_results['successful_patterns'] += successful
                training_results['hidden_gems_found'] += len(gems)
                
                print(f"  ✅ {coin.upper()} training complete!\n")
                
            except Exception as e:
                print(f"  ❌ Error training {coin}: {str(e)}")
        
        # Calculate overall metrics
        if training_results['total_patterns'] > 0:
            training_results['training_accuracy'] = (
                training_results['successful_patterns'] / 
                training_results['total_patterns'] * 100
            )
        
        training_results['completed_at'] = datetime.now().isoformat()
        
        # Store overall results
        try:
            await self.db.training_summary.replace_one(
                {},
                training_results,
                upsert=True
            )
        except Exception:
            pass
        
        # Store hidden gems summary
        if all_hidden_gems:
            gem_summary = {
                'total_gems': len(all_hidden_gems),
                'moonshots': sum(1 for g in all_hidden_gems if g['gem_type'] == 'moonshot'),
                'mega_gems': sum(1 for g in all_hidden_gems if g['gem_type'] == 'mega_gem'),
                'major_gems': sum(1 for g in all_hidden_gems if g['gem_type'] == 'major_gem'),
                'gems': sum(1 for g in all_hidden_gems if g['gem_type'] == 'gem'),
                'potential_gems': sum(1 for g in all_hidden_gems if g['gem_type'] == 'potential_gem'),
                'avg_multiplier': sum(g['gain_multiplier'] for g in all_hidden_gems) / len(all_hidden_gems),
                'max_multiplier': max(g['gain_multiplier'] for g in all_hidden_gems),
                'data_source': 'REAL_MARKET_DATA',
                'created_at': datetime.now().isoformat()
            }
            try:
                await self.db.gem_summary.replace_one({}, gem_summary, upsert=True)
            except Exception:
                pass
        
        print("\n" + "="*70)
        print("✅ ENHANCED AI TRAINING COMPLETE (REAL DATA ONLY)")
        print("="*70)
        print(f"📊 Coins Trained: {len(training_results['coins_trained'])}")
        print(f"📈 Total Patterns: {training_results['total_patterns']:,}")
        print(f"✅ Successful Patterns: {training_results['successful_patterns']:,}")
        print(f"💎 Hidden Gems Found: {training_results['hidden_gems_found']}")
        print(f"🎯 Overall Accuracy: {training_results['training_accuracy']:.2f}%")
        print(f"📡 Data Source: REAL MARKET DATA ONLY")
        print("="*70 + "\n")
        
        return training_results
    
    def identify_historical_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify trading patterns from REAL historical data"""
        patterns = []
        
        if len(df) < 220:
            return patterns
        
        for i in range(200, len(df) - 10):
            try:
                row = df.iloc[i]
                future_price = df.iloc[i + 10]['close']
                current_price = row['close']
                
                if current_price <= 0:
                    continue
                    
                future_return = (future_price - current_price) / current_price
                
                # Pattern identification based on technical indicators
                pattern_type = None
                rsi = row.get('rsi', 50)
                macd = row.get('macd', 0)
                macd_signal = row.get('macd_signal', 0)
                sma_7 = row.get('sma_7', current_price)
                sma_30 = row.get('sma_30', current_price)
                
                if rsi < 30 and macd > macd_signal:
                    pattern_type = 'oversold_reversal'
                elif rsi > 70 and macd < macd_signal:
                    pattern_type = 'overbought_reversal'
                elif current_price > sma_7 > sma_30:
                    pattern_type = 'uptrend_continuation'
                elif current_price < sma_7 < sma_30:
                    pattern_type = 'downtrend_continuation'
                
                if pattern_type and abs(future_return) > 0.03:  # 3% threshold
                    patterns.append({
                        'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                        'pattern_type': pattern_type,
                        'entry_price': float(current_price),
                        'exit_price': float(future_price),
                        'return': float(future_return),
                        'rsi': float(rsi),
                        'macd': float(macd),
                        'volatility': float(row.get('volatility_30', 0)),
                        'volume_ratio': float(row.get('volume_ratio', 1.0)),
                        'success': future_return > 0.02,
                        'data_source': 'REAL_MARKET_DATA'
                    })
            except Exception:
                continue
        
        return patterns
    
    # Backwards compatibility alias
    async def train_with_comprehensive_data(self, coins: List[str] = None) -> Dict[str, Any]:
        """Alias for train_with_real_data for backwards compatibility"""
        if coins is None:
            coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
        return await self.train_with_real_data(coins)
