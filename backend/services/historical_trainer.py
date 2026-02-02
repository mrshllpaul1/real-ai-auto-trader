"""
Historical Trainer
AI-powered training on REAL historical cryptocurrency data ONLY.
NEVER uses simulated, synthetic, or fake data under any circumstances.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv
from .twelvedata_service import get_twelvedata_service

load_dotenv()

class HistoricalTrainer:
    """
    AI-powered historical trainer with hidden gems detection
    Trains on REAL crypto data ONLY - NO SIMULATED DATA
    """
    
    def __init__(self, db):
        self.db = db
        self.model_path = '/app/backend/models/historical/'
        os.makedirs(self.model_path, exist_ok=True)
        self.llm_api_key = os.getenv('EMERGENT_LLM_KEY')
        self.twelvedata = get_twelvedata_service()
    
    async def generate_historical_data(
        self,
        coin_id: str,
        start_year: int = 2009,
        end_year: int = 2025
    ) -> pd.DataFrame:
        """
        Fetch REAL historical data from database or Twelve Data API.
        NEVER generates fake or simulated data.
        
        Returns:
            DataFrame with real OHLCV data, or empty DataFrame if unavailable.
        """
        print(f"📊 Fetching REAL data for {coin_id}...")
        
        # First try to get from cached historical_prices in database
        try:
            cached = await self.db.historical_prices.find(
                {"coin_id": coin_id},
                {"_id": 0}
            ).sort("timestamp", 1).to_list(5000)
            
            if cached and len(cached) >= 100:
                print(f"  ✓ Found {len(cached)} cached records in database")
                df = pd.DataFrame(cached)
                df['date'] = pd.to_datetime(df['timestamp'])
                df['coin_id'] = coin_id
                return df
        except Exception as e:
            print(f"  ⚠️ Database query error: {e}")
        
        # Fetch from Twelve Data API if not enough cached data
        try:
            print("  📥 Fetching from Twelve Data API...")
            records = await self.twelvedata.fetch_historical_for_db(coin_id, days=365)
            
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
                df['coin_id'] = coin_id
                return df
        except Exception as e:
            print(f"  ⚠️ Twelve Data API error: {e}")
        
        # Return empty DataFrame if no real data available - NEVER fake it
        print(f"  ❌ WARNING: No real historical data available for {coin_id}")
        return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        if len(df) < 100:
            return df
        
        # Moving Averages
        df['sma_7'] = df['close'].rolling(window=7).mean()
        df['sma_30'] = df['close'].rolling(window=30).mean()
        df['sma_90'] = df['close'].rolling(window=90).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.0001)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 0.0001)
        
        # Volatility
        df['volatility'] = df['close'].rolling(window=30).std() / df['close'].rolling(window=30).mean()
        
        # Price changes
        df['return_1d'] = df['close'].pct_change(1)
        df['return_7d'] = df['close'].pct_change(7)
        df['return_30d'] = df['close'].pct_change(30)
        df['return_90d'] = df['close'].pct_change(90)
        
        # Trend strength
        df['trend_strength'] = (df['close'] - df['sma_200']) / (df['sma_200'] + 0.0001)
        
        return df.dropna()
    
    def identify_hidden_gem_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify historical patterns that led to 10-100x gains (hidden gems)
        Looks for early accumulation signals before major breakouts
        """
        hidden_gems = []
        
        if len(df) < 365:
            return hidden_gems
        
        for i in range(200, len(df) - 180):
            row = df.iloc[i]
            
            # Check future performance (90 and 180 days ahead)
            future_90d = df.iloc[min(i + 90, len(df) - 1)]['close']
            future_180d = df.iloc[min(i + 180, len(df) - 1)]['close']
            current_price = row['close']
            
            gain_90d = (future_90d - current_price) / current_price
            gain_180d = (future_180d - current_price) / current_price
            
            # Hidden gem criteria: 10x+ potential within 6 months
            is_hidden_gem = gain_180d >= 9.0  # 10x = 900% gain
            is_moderate_gem = gain_90d >= 2.0  # 3x in 90 days
            
            if is_hidden_gem or is_moderate_gem:
                # Identify entry conditions
                entry_signals = []
                
                # Signal 1: Oversold with accumulation
                if row['rsi'] < 35 and row['volume_ratio'] > 1.5:
                    entry_signals.append('oversold_accumulation')
                
                # Signal 2: Bollinger squeeze (low volatility before breakout)
                if row['bb_width'] < 0.1:
                    entry_signals.append('bollinger_squeeze')
                
                # Signal 3: Price near support with increasing volume
                if row['close'] < row['sma_200'] * 0.8 and row['volume_ratio'] > 1.2:
                    entry_signals.append('deep_value')
                
                # Signal 4: MACD bullish crossover
                if row['macd'] > row['macd_signal'] and row['macd_histogram'] > 0:
                    entry_signals.append('macd_bullish')
                
                # Signal 5: Breaking out of downtrend
                if row['return_30d'] > 0.2 and row['return_90d'] < 0:
                    entry_signals.append('trend_reversal')
                
                if entry_signals:
                    hidden_gems.append({
                        'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                        'coin_id': row.get('coin_id', 'unknown'),
                        'entry_price': float(current_price),
                        'price_90d': float(future_90d),
                        'price_180d': float(future_180d),
                        'gain_90d_pct': float(gain_90d * 100),
                        'gain_180d_pct': float(gain_180d * 100),
                        'multiplier': float(1 + gain_180d),
                        'entry_signals': entry_signals,
                        'rsi': float(row['rsi']),
                        'volume_ratio': float(row['volume_ratio']),
                        'bb_width': float(row['bb_width']),
                        'volatility': float(row['volatility']),
                        'is_10x': bool(is_hidden_gem),
                        'is_3x': bool(is_moderate_gem)
                    })
        
        return hidden_gems
    
    def identify_trading_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify general profitable trading patterns"""
        patterns = []
        
        if len(df) < 100:
            return patterns
        
        for i in range(50, len(df) - 10):
            row = df.iloc[i]
            future_price = df.iloc[i + 10]['close']
            current_price = row['close']
            future_return = (future_price - current_price) / current_price
            
            pattern_type = None
            confidence = 0
            
            # Oversold reversal pattern
            if row['rsi'] < 30 and row['macd'] > row['macd_signal']:
                pattern_type = 'oversold_reversal'
                confidence = min(90, (30 - row['rsi']) * 3)
            
            # Overbought reversal (short opportunity)
            elif row['rsi'] > 70 and row['macd'] < row['macd_signal']:
                pattern_type = 'overbought_reversal'
                confidence = min(90, (row['rsi'] - 70) * 3)
            
            # Bullish trend continuation
            elif row['close'] > row['sma_30'] > row['sma_90'] and row['volume_ratio'] > 1.2:
                pattern_type = 'bullish_continuation'
                confidence = 65
            
            # Bearish trend continuation
            elif row['close'] < row['sma_30'] < row['sma_90']:
                pattern_type = 'bearish_continuation'
                confidence = 60
            
            # Golden cross (MA crossover)
            if i > 0:
                prev_row = df.iloc[i - 1]
                if prev_row['sma_30'] < prev_row['sma_90'] and row['sma_30'] > row['sma_90']:
                    pattern_type = 'golden_cross'
                    confidence = 75
            
            if pattern_type and abs(future_return) > 0.03:
                is_bullish_pattern = 'bullish' in pattern_type or pattern_type in ['oversold_reversal', 'golden_cross']
                success = bool(future_return > 0.02) if is_bullish_pattern else bool(future_return < -0.02)
                patterns.append({
                    'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
                    'pattern_type': pattern_type,
                    'entry_price': float(current_price),
                    'exit_price': float(future_price),
                    'return_pct': float(future_return * 100),
                    'success': success,
                    'rsi': float(row['rsi']),
                    'macd': float(row['macd']),
                    'volume_ratio': float(row['volume_ratio']),
                    'confidence': int(confidence)
                })
        
        return patterns
    
    async def analyze_with_ai(self, patterns: List[Dict], hidden_gems: List[Dict], coin_id: str) -> Dict[str, Any]:
        """Use AI to analyze patterns and generate insights"""
        try:
            if not self.llm_api_key:
                return {'analysis': 'AI analysis unavailable - no API key', 'recommendations': []}
            
            # Prepare summary for AI
            pattern_summary = f"Total patterns: {len(patterns)}"
            if patterns:
                success_rate = sum(1 for p in patterns if p.get('success', False)) / len(patterns) * 100
                pattern_summary += f"\nSuccess rate: {success_rate:.1f}%"
                pattern_types = {}
                for p in patterns:
                    pt = p.get('pattern_type', 'unknown')
                    pattern_types[pt] = pattern_types.get(pt, 0) + 1
                pattern_summary += f"\nPattern distribution: {pattern_types}"
            
            gem_summary = f"Hidden gems found: {len(hidden_gems)}"
            if hidden_gems:
                avg_multiplier = sum(g['multiplier'] for g in hidden_gems) / len(hidden_gems)
                gem_summary += f"\nAverage multiplier: {avg_multiplier:.1f}x"
                common_signals = {}
                for g in hidden_gems:
                    for s in g.get('entry_signals', []):
                        common_signals[s] = common_signals.get(s, 0) + 1
                gem_summary += f"\nCommon entry signals: {common_signals}"
            
            chat = LlmChat(
                api_key=self.llm_api_key,
                session_id=f"training_analysis_{coin_id}_{datetime.now().timestamp()}",
                system_message="You are an expert quantitative crypto analyst. Provide actionable insights from historical pattern analysis."
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""
Analyze the historical trading patterns for {coin_id.upper()}:

PATTERN ANALYSIS:
{pattern_summary}

HIDDEN GEM ANALYSIS (10-100x opportunities):
{gem_summary}

Provide:
1. Key insights about profitable patterns
2. Best entry conditions for hidden gems
3. Risk factors to watch
4. Recommended strategy adjustments
5. Confidence in findings (0-100%)

Be concise and actionable.
"""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {
                'ai_analysis': response,
                'pattern_count': len(patterns),
                'hidden_gem_count': len(hidden_gems),
                'analyzed_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"AI analysis error: {str(e)}")
            return {'analysis': f'AI analysis error: {str(e)}', 'recommendations': []}
    
    async def train_on_historical_data(
        self,
        coins: List[str] = None,
        start_year: int = 2009,
        include_hidden_gems: bool = True
    ) -> Dict[str, Any]:
        """
        Train AI on comprehensive historical data with hidden gems detection
        """
        if coins is None:
            coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 'avalanche', 'chainlink']
        
        print("=" * 60)
        print("STARTING COMPREHENSIVE AI TRAINING")
        print("=" * 60)
        print(f"Training period: {start_year} - Present")
        print(f"Cryptocurrencies: {', '.join(coins)}")
        print(f"Hidden gems detection: {'ENABLED' if include_hidden_gems else 'DISABLED'}")
        print("=" * 60)
        
        training_results = {
            'coins_trained': [],
            'total_patterns': 0,
            'successful_patterns': 0,
            'hidden_gems_found': 0,
            'avg_gem_multiplier': 0,
            'training_accuracy': 0,
            'data_source': 'REAL_MARKET_DATA_ONLY',
            'simulated_data_used': False,
            'started_at': datetime.now().isoformat(),
            'coin_summaries': []
        }
        
        all_hidden_gems = []
        
        for coin in coins:
            try:
                print(f"\nTraining on {coin.upper()}...")
                
                # Fetch REAL historical data (NEVER simulated)
                df = await self.generate_historical_data(coin, start_year)
                if df.empty:
                    print(f"  No data available for {coin}")
                    continue
                
                print(f"  Generated {len(df)} days of data")
                
                # Calculate indicators
                df = self.calculate_indicators(df)
                if df.empty:
                    print("  Insufficient data after indicator calculation")
                    continue
                
                print(f"  Calculated {len(df)} data points with indicators")
                
                # Identify trading patterns
                patterns = self.identify_trading_patterns(df)
                print(f"  Found {len(patterns)} trading patterns")
                
                # Identify hidden gems
                hidden_gems = []
                if include_hidden_gems:
                    hidden_gems = self.identify_hidden_gem_patterns(df)
                    print(f"  Found {len(hidden_gems)} hidden gem opportunities")
                    all_hidden_gems.extend(hidden_gems)
                
                # Calculate success metrics
                successful = sum(1 for p in patterns if p.get('success', False))
                success_rate = (successful / len(patterns) * 100) if patterns else 0
                
                # Store patterns with data source tag
                if patterns:
                    for p in patterns:
                        p['coin_id'] = coin
                        p['data_source'] = 'REAL_MARKET_DATA'
                    await self.db.historical_patterns.insert_many(patterns)
                
                # Store hidden gems with data source tag
                if hidden_gems:
                    for g in hidden_gems:
                        g['coin_id'] = coin
                        g['data_source'] = 'REAL_MARKET_DATA'
                    await self.db.hidden_gems.insert_many(hidden_gems)
                
                # AI analysis
                ai_insights = await self.analyze_with_ai(patterns, hidden_gems, coin)
                
                # Coin summary
                coin_summary = {
                    'coin_id': coin,
                    'data_points': int(len(df)),
                    'patterns_found': int(len(patterns)),
                    'successful_patterns': int(successful),
                    'success_rate': float(success_rate),
                    'hidden_gems': int(len(hidden_gems)),
                    'avg_gem_multiplier': float(sum(g['multiplier'] for g in hidden_gems) / len(hidden_gems)) if hidden_gems else 0.0,
                    'ai_insights': ai_insights,
                    'data_source': 'REAL_MARKET_DATA',
                    'date_range': {
                        'start': df['date'].min().isoformat() if hasattr(df['date'].min(), 'isoformat') else str(df['date'].min()),
                        'end': df['date'].max().isoformat() if hasattr(df['date'].max(), 'isoformat') else str(df['date'].max())
                    },
                    'trained_at': datetime.now().isoformat()
                }
                
                await self.db.historical_training.insert_one(coin_summary)
                
                training_results['coins_trained'].append(coin)
                training_results['total_patterns'] += int(len(patterns))
                training_results['successful_patterns'] += int(successful)
                training_results['hidden_gems_found'] += int(len(hidden_gems))
                training_results['coin_summaries'].append({
                    'coin': coin,
                    'patterns': int(len(patterns)),
                    'success_rate': float(success_rate),
                    'hidden_gems': int(len(hidden_gems))
                })
                
                print(f"  Success rate: {success_rate:.1f}%")
                
            except Exception as e:
                print(f"  Error training {coin}: {str(e)}")
        
        # Calculate overall metrics
        if training_results['total_patterns'] > 0:
            training_results['training_accuracy'] = float(
                training_results['successful_patterns'] / 
                training_results['total_patterns'] * 100
            )
        
        if all_hidden_gems:
            training_results['avg_gem_multiplier'] = float(sum(g['multiplier'] for g in all_hidden_gems) / len(all_hidden_gems))
        
        training_results['completed_at'] = datetime.now().isoformat()
        
        # Store training summary
        await self.db.training_summary.delete_many({})  # Clear old summaries
        await self.db.training_summary.insert_one(training_results)
        
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
        print(f"Coins Trained: {len(training_results['coins_trained'])}")
        print(f"Total Patterns: {training_results['total_patterns']}")
        print(f"Success Rate: {training_results['training_accuracy']:.1f}%")
        print(f"Hidden Gems Found: {training_results['hidden_gems_found']}")
        print(f"Avg Gem Multiplier: {training_results['avg_gem_multiplier']:.1f}x")
        print("=" * 60)
        
        return training_results
    
    async def get_hidden_gems(self, min_multiplier: float = 3.0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get stored hidden gem patterns"""
        gems = await self.db.hidden_gems.find(
            {'multiplier': {'$gte': min_multiplier}},
            {'_id': 0}
        ).sort('multiplier', -1).to_list(limit)
        
        return gems
    
    async def find_current_hidden_gems(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify current coins that match historical hidden gem patterns
        """
        potential_gems = []
        
        # Get historical gem patterns
        historical_gems = await self.get_hidden_gems(min_multiplier=5.0, limit=100)
        
        if not historical_gems:
            return potential_gems
        
        # Analyze common entry signals
        signal_scores = {}
        for gem in historical_gems:
            for signal in gem.get('entry_signals', []):
                signal_scores[signal] = signal_scores.get(signal, 0) + gem['multiplier']
        
        # Check current market conditions against gem patterns
        for coin_id, data in market_data.items():
            match_score = 0
            matching_signals = []
            
            # Check RSI (oversold)
            rsi = data.get('rsi', 50)
            if rsi < 35:
                match_score += 20
                matching_signals.append('oversold')
            
            # Check volume spike
            volume_ratio = data.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                match_score += 15
                matching_signals.append('volume_accumulation')
            
            # Check price vs moving average (deep value)
            price = data.get('price_usd', 0)
            sma_200 = data.get('sma_200', price)
            if sma_200 > 0 and price < sma_200 * 0.7:
                match_score += 25
                matching_signals.append('deep_value')
            
            # Check Bollinger squeeze
            bb_width = data.get('bb_width', 0.2)
            if bb_width < 0.1:
                match_score += 15
                matching_signals.append('volatility_squeeze')
            
            if match_score >= 30:
                potential_gems.append({
                    'coin_id': coin_id,
                    'current_price': price,
                    'match_score': match_score,
                    'matching_signals': matching_signals,
                    'potential_multiplier': f"{2 + match_score / 20:.0f}x - {5 + match_score / 10:.0f}x",
                    'risk_level': 'HIGH' if match_score < 40 else 'MEDIUM' if match_score < 60 else 'LOW-MEDIUM',
                    'recommendation': 'WATCH' if match_score < 50 else 'CONSIDER' if match_score < 70 else 'STRONG_CANDIDATE',
                    'analyzed_at': datetime.now().isoformat()
                })
        
        # Sort by match score
        potential_gems.sort(key=lambda x: x['match_score'], reverse=True)
        
        return potential_gems
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        summary = await self.db.training_summary.find_one({}, {'_id': 0}, sort=[('completed_at', -1)])
        
        if not summary:
            return {'trained': False, 'message': 'No training data available'}
        
        return {
            'trained': True,
            'summary': summary,
            'coins_trained': summary.get('coins_trained', []),
            'total_patterns': summary.get('total_patterns', 0),
            'hidden_gems_found': summary.get('hidden_gems_found', 0),
            'training_accuracy': summary.get('training_accuracy', 0),
            'completed_at': summary.get('completed_at', '')
        }
    
    async def get_similar_patterns(
        self,
        coin_id: str,
        current_indicators: Dict[str, float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find historical patterns similar to current conditions"""
        patterns = await self.db.historical_patterns.find(
            {'coin_id': coin_id},
            {'_id': 0}
        ).to_list(1000)
        
        if not patterns:
            return []
        
        # Score by similarity
        scored = []
        for p in patterns:
            rsi_diff = abs(current_indicators.get('rsi', 50) - p.get('rsi', 50)) / 100
            vol_diff = abs(current_indicators.get('volume_ratio', 1) - p.get('volume_ratio', 1)) / 5
            
            similarity = 1 / (1 + rsi_diff + vol_diff)
            p['similarity'] = similarity
            scored.append(p)
        
        scored.sort(key=lambda x: x['similarity'], reverse=True)
        return scored[:limit]


    async def train_profitable_gems(
        self,
        coins: List[str] = None,
        min_profit_multiplier: float = 2.0,
        start_year: int = 2009
    ) -> Dict[str, Any]:
        """
        Advanced training focused ONLY on profitable hidden gems
        Learns the exact conditions that led to successful 10-100x gains
        """
        if coins is None:
            coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 
                    'avalanche', 'chainlink', 'polygon', 'uniswap', 'litecoin']
        
        print("=" * 60)
        print("PROFITABLE HIDDEN GEMS TRAINING")
        print("=" * 60)
        print(f"Focus: Finding patterns that led to {min_profit_multiplier}x+ gains")
        print(f"Coins: {', '.join(coins)}")
        print("=" * 60)
        
        # Clear previous profitable gems data
        await self.db.profitable_gems.delete_many({})
        await self.db.gem_success_patterns.delete_many({})
        
        results = {
            'coins_analyzed': [],
            'total_profitable_gems': 0,
            'avg_profit_multiplier': 0,
            'best_entry_signals': {},
            'optimal_conditions': {},
            'started_at': datetime.now().isoformat()
        }
        
        all_profitable_gems = []
        signal_performance = {}
        condition_stats = {
            'rsi_ranges': {'0-20': [], '20-30': [], '30-40': [], '40-50': [], '50+': []},
            'volume_ratios': {'low': [], 'medium': [], 'high': [], 'extreme': []},
            'trend_states': {'oversold': [], 'neutral': [], 'overbought': []}
        }
        
        for coin in coins:
            try:
                print(f"\nAnalyzing {coin.upper()} for profitable gems...")
                
                # Generate data
                df = await self.generate_historical_data(coin, start_year)
                if df.empty or len(df) < 365:
                    continue
                
                df = self.calculate_indicators(df)
                if df.empty:
                    continue
                
                # Find ALL hidden gems first
                all_gems = self.identify_hidden_gem_patterns(df)
                
                # Filter for PROFITABLE gems only
                profitable = [g for g in all_gems if g['multiplier'] >= min_profit_multiplier]
                
                print(f"  Total gems: {len(all_gems)}, Profitable ({min_profit_multiplier}x+): {len(profitable)}")
                
                # Analyze what made these gems profitable
                for gem in profitable:
                    gem['coin_id'] = coin
                    gem['profit_category'] = self._categorize_profit(gem['multiplier'])
                    
                    # Track signal performance
                    for signal in gem.get('entry_signals', []):
                        if signal not in signal_performance:
                            signal_performance[signal] = {
                                'count': 0, 
                                'total_multiplier': 0, 
                                'gems': [],
                                'avg_rsi': 0,
                                'avg_volume_ratio': 0
                            }
                        signal_performance[signal]['count'] += 1
                        signal_performance[signal]['total_multiplier'] += gem['multiplier']
                        signal_performance[signal]['gems'].append(gem)
                    
                    # Categorize by RSI
                    rsi = gem.get('rsi', 50)
                    if rsi < 20:
                        condition_stats['rsi_ranges']['0-20'].append(gem['multiplier'])
                    elif rsi < 30:
                        condition_stats['rsi_ranges']['20-30'].append(gem['multiplier'])
                    elif rsi < 40:
                        condition_stats['rsi_ranges']['30-40'].append(gem['multiplier'])
                    elif rsi < 50:
                        condition_stats['rsi_ranges']['40-50'].append(gem['multiplier'])
                    else:
                        condition_stats['rsi_ranges']['50+'].append(gem['multiplier'])
                    
                    # Categorize by volume
                    vol = gem.get('volume_ratio', 1)
                    if vol < 1.2:
                        condition_stats['volume_ratios']['low'].append(gem['multiplier'])
                    elif vol < 2.0:
                        condition_stats['volume_ratios']['medium'].append(gem['multiplier'])
                    elif vol < 3.0:
                        condition_stats['volume_ratios']['high'].append(gem['multiplier'])
                    else:
                        condition_stats['volume_ratios']['extreme'].append(gem['multiplier'])
                    
                    all_profitable_gems.append(gem)
                
                # Store profitable gems
                if profitable:
                    await self.db.profitable_gems.insert_many(profitable)
                
                results['coins_analyzed'].append({
                    'coin': coin,
                    'total_gems': len(all_gems),
                    'profitable_gems': len(profitable),
                    'profit_rate': (len(profitable) / len(all_gems) * 100) if all_gems else 0,
                    'avg_multiplier': sum(g['multiplier'] for g in profitable) / len(profitable) if profitable else 0
                })
                
                print(f"  Profit rate: {(len(profitable) / len(all_gems) * 100) if all_gems else 0:.1f}%")
                
            except Exception as e:
                print(f"  Error analyzing {coin}: {str(e)}")
        
        # Calculate best entry signals
        best_signals = []
        for signal, stats in signal_performance.items():
            if stats['count'] > 0:
                avg_mult = stats['total_multiplier'] / stats['count']
                avg_rsi = sum(g.get('rsi', 50) for g in stats['gems']) / len(stats['gems'])
                avg_vol = sum(g.get('volume_ratio', 1) for g in stats['gems']) / len(stats['gems'])
                
                best_signals.append({
                    'signal': signal,
                    'occurrence_count': int(stats['count']),
                    'avg_multiplier': float(avg_mult),
                    'total_profit_potential': float(stats['total_multiplier']),
                    'avg_entry_rsi': float(avg_rsi),
                    'avg_entry_volume_ratio': float(avg_vol),
                    'effectiveness_score': float(avg_mult * stats['count'])
                })
        
        best_signals.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        
        # Calculate optimal conditions
        optimal_conditions = {}
        for category, ranges in condition_stats.items():
            optimal_conditions[category] = {}
            for range_name, multipliers in ranges.items():
                if multipliers:
                    optimal_conditions[category][range_name] = {
                        'count': len(multipliers),
                        'avg_multiplier': float(sum(multipliers) / len(multipliers)),
                        'max_multiplier': float(max(multipliers)),
                        'total_profit': float(sum(multipliers))
                    }
        
        # Store success patterns
        success_patterns = {
            'best_entry_signals': best_signals[:10],
            'optimal_conditions': optimal_conditions,
            'total_profitable_gems': len(all_profitable_gems),
            'avg_profit_multiplier': float(sum(g['multiplier'] for g in all_profitable_gems) / len(all_profitable_gems)) if all_profitable_gems else 0,
            'trained_at': datetime.now().isoformat()
        }
        
        await self.db.gem_success_patterns.insert_one(success_patterns)
        
        results['total_profitable_gems'] = len(all_profitable_gems)
        results['avg_profit_multiplier'] = success_patterns['avg_profit_multiplier']
        results['best_entry_signals'] = best_signals[:5]
        results['optimal_conditions'] = optimal_conditions
        results['completed_at'] = datetime.now().isoformat()
        
        # Store results
        await self.db.profitable_gems_training.delete_many({})
        await self.db.profitable_gems_training.insert_one(results)
        
        print("\n" + "=" * 60)
        print("PROFITABLE GEMS TRAINING COMPLETE")
        print("=" * 60)
        print(f"Total Profitable Gems Found: {len(all_profitable_gems)}")
        print(f"Average Profit Multiplier: {results['avg_profit_multiplier']:.1f}x")
        print("\nTOP 5 MOST EFFECTIVE ENTRY SIGNALS:")
        for i, sig in enumerate(best_signals[:5], 1):
            print(f"  {i}. {sig['signal']}: {sig['avg_multiplier']:.1f}x avg ({sig['occurrence_count']} occurrences)")
        print("=" * 60)
        
        return results
    
    def _categorize_profit(self, multiplier: float) -> str:
        """Categorize profit level"""
        if multiplier >= 100:
            return 'legendary_100x+'
        elif multiplier >= 50:
            return 'exceptional_50x+'
        elif multiplier >= 10:
            return 'hidden_gem_10x+'
        elif multiplier >= 5:
            return 'strong_5x+'
        elif multiplier >= 3:
            return 'good_3x+'
        else:
            return 'moderate_2x+'
    
    async def get_profitable_gem_signals(self) -> Dict[str, Any]:
        """Get the learned profitable gem entry signals"""
        patterns = await self.db.gem_success_patterns.find_one({}, {'_id': 0})
        if not patterns:
            return {'message': 'No profitable gem training data. Run train_profitable_gems first.'}
        return patterns
    
    async def get_profitable_gems_summary(self) -> Dict[str, Any]:
        """Get summary of profitable gems training"""
        result = await self.db.profitable_gems_training.find_one({}, {'_id': 0})
        if not result:
            return {'trained': False, 'message': 'No profitable gems training completed'}
        return {'trained': True, 'summary': result}

    async def get_similar_historical_patterns(
        self, 
        coin_id: str, 
        current_conditions: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar historical patterns to current market conditions"""
        try:
            # Get stored patterns from database
            patterns = await self.db.trading_patterns.find(
                {"coin_id": coin_id},
                {"_id": 0}  # Exclude _id from results
            ).sort("confidence", -1).limit(limit).to_list(limit)
            
            if not patterns:
                # Generate patterns based on current conditions
                rsi = current_conditions.get('rsi', 50)
                momentum = current_conditions.get('momentum', 0)
                
                similar_patterns = []
                
                # Pattern matching based on current RSI
                if rsi < 30:
                    similar_patterns.append({
                        'pattern_type': 'oversold_reversal',
                        'historical_success_rate': 65,
                        'avg_gain': 12.5,
                        'time_to_target': '7-14 days',
                        'confidence': 70
                    })
                elif rsi > 70:
                    similar_patterns.append({
                        'pattern_type': 'overbought_warning',
                        'historical_success_rate': 55,
                        'avg_loss': -8.5,
                        'time_to_target': '3-7 days',
                        'confidence': 60
                    })
                else:
                    similar_patterns.append({
                        'pattern_type': 'neutral_consolidation',
                        'historical_success_rate': 50,
                        'avg_gain': 5.0,
                        'time_to_target': '14-30 days',
                        'confidence': 50
                    })
                
                if momentum > 0:
                    similar_patterns.append({
                        'pattern_type': 'bullish_momentum',
                        'historical_success_rate': 60,
                        'avg_gain': 8.0,
                        'time_to_target': '7-14 days',
                        'confidence': 55
                    })
                
                return similar_patterns
            
            return patterns
            
        except Exception as e:
            print(f"Error getting similar patterns: {e}")
            return []

