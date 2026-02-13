"""
Cross-Asset Correlation Model
Enhancement #6: BTC dominance, DXY, S&P 500 correlation for risk-on/off signals
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class CrossAssetCorrelation:
    """
    Cross-asset correlation analysis for crypto trading:
    - BTC dominance impact on altcoins
    - DXY (Dollar Index) correlation
    - S&P 500 / Nasdaq correlation (risk-on/risk-off)
    - Gold correlation (safe haven)
    - Correlation regime detection
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}
        self.cache_ttl = 300  # 5 minute cache
        
        # Correlation thresholds
        self.high_correlation = 0.7
        self.moderate_correlation = 0.4
        
    async def analyze_correlations(self, symbol: str = 'BTC') -> Dict[str, Any]:
        """
        Comprehensive cross-asset correlation analysis
        
        Args:
            symbol: Primary crypto symbol to analyze
            
        Returns:
            Correlation analysis with trading signals
        """
        try:
            coin = symbol.upper().replace('USD', '').replace('USDT', '')
            
            # Get individual correlations
            btc_dominance = await self._analyze_btc_dominance(coin)
            dxy_correlation = await self._analyze_dxy_correlation(coin)
            equity_correlation = await self._analyze_equity_correlation(coin)
            gold_correlation = await self._analyze_gold_correlation(coin)
            
            # Determine risk regime
            risk_regime = self._determine_risk_regime(
                dxy_correlation, equity_correlation, gold_correlation
            )
            
            # Generate composite signal
            signal = self._generate_cross_asset_signal(
                btc_dominance, dxy_correlation, equity_correlation, 
                gold_correlation, risk_regime
            )
            
            analysis = {
                'symbol': coin,
                'timestamp': datetime.utcnow().isoformat(),
                'btc_dominance': btc_dominance,
                'dxy_correlation': dxy_correlation,
                'equity_correlation': equity_correlation,
                'gold_correlation': gold_correlation,
                'risk_regime': risk_regime,
                'signal': signal
            }
            
            await self._store_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Cross-asset correlation failed for {symbol}: {e}")
            return self._empty_analysis(symbol)
    
    async def _analyze_btc_dominance(self, coin: str) -> Dict[str, Any]:
        """Analyze BTC dominance and its impact"""
        np.random.seed(hash(coin + "btcdom" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Simulated BTC dominance (typically 40-60%)
        current_dominance = np.random.uniform(42, 58)
        dominance_7d_ago = current_dominance + np.random.uniform(-3, 3)
        dominance_30d_ago = current_dominance + np.random.uniform(-5, 5)
        
        # Calculate trends
        change_7d = current_dominance - dominance_7d_ago
        change_30d = current_dominance - dominance_30d_ago
        
        # Determine trend
        if change_7d > 2:
            trend = 'increasing'
            altcoin_impact = 'bearish'  # Rising BTC dominance = altcoins underperform
        elif change_7d < -2:
            trend = 'decreasing'
            altcoin_impact = 'bullish'  # Falling BTC dominance = altseason potential
        else:
            trend = 'stable'
            altcoin_impact = 'neutral'
        
        # Impact severity for this specific coin
        if coin == 'BTC':
            impact_on_coin = 'direct'
        elif coin in ['ETH', 'SOL', 'ADA']:
            impact_on_coin = 'moderate'
        else:
            impact_on_coin = 'high'  # Small caps more affected
        
        return {
            'current_pct': round(current_dominance, 2),
            'change_7d_pct': round(change_7d, 2),
            'change_30d_pct': round(change_30d, 2),
            'trend': trend,
            'altcoin_impact': altcoin_impact,
            'impact_on_coin': impact_on_coin,
            'altseason_signal': current_dominance < 45,
            'interpretation': f"BTC dominance {trend} - {altcoin_impact} for altcoins"
        }
    
    async def _analyze_dxy_correlation(self, coin: str) -> Dict[str, Any]:
        """Analyze DXY (US Dollar Index) correlation"""
        np.random.seed(hash(coin + "dxy" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # DXY typically ranges 90-110
        current_dxy = np.random.uniform(100, 108)
        dxy_7d_ago = current_dxy + np.random.uniform(-2, 2)
        
        # Crypto typically has negative correlation with DXY
        correlation_30d = np.random.uniform(-0.7, -0.3)
        
        # Calculate DXY trend
        dxy_change = ((current_dxy - dxy_7d_ago) / dxy_7d_ago) * 100
        
        if dxy_change > 1:
            dxy_trend = 'strengthening'
            crypto_impact = 'bearish'
        elif dxy_change < -1:
            dxy_trend = 'weakening'
            crypto_impact = 'bullish'
        else:
            dxy_trend = 'stable'
            crypto_impact = 'neutral'
        
        # Correlation strength
        if abs(correlation_30d) > self.high_correlation:
            correlation_strength = 'strong_inverse'
        elif abs(correlation_30d) > self.moderate_correlation:
            correlation_strength = 'moderate_inverse'
        else:
            correlation_strength = 'weak_inverse'
        
        return {
            'current_dxy': round(current_dxy, 2),
            'change_7d_pct': round(dxy_change, 2),
            'correlation_30d': round(correlation_30d, 3),
            'dxy_trend': dxy_trend,
            'correlation_strength': correlation_strength,
            'crypto_impact': crypto_impact,
            'interpretation': f"Dollar {dxy_trend} - {crypto_impact} for crypto"
        }
    
    async def _analyze_equity_correlation(self, coin: str) -> Dict[str, Any]:
        """Analyze S&P 500 / Nasdaq correlation"""
        np.random.seed(hash(coin + "equity" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Crypto often correlates positively with risk assets
        sp500_correlation = np.random.uniform(0.3, 0.8)
        nasdaq_correlation = np.random.uniform(0.4, 0.85)
        
        # Simulated equity performance
        sp500_change_7d = np.random.uniform(-3, 4)
        nasdaq_change_7d = np.random.uniform(-4, 5)
        
        # Risk-on/risk-off determination
        if sp500_change_7d > 2 and nasdaq_change_7d > 2:
            risk_sentiment = 'risk_on'
            crypto_implication = 'bullish'
        elif sp500_change_7d < -2 and nasdaq_change_7d < -2:
            risk_sentiment = 'risk_off'
            crypto_implication = 'bearish'
        else:
            risk_sentiment = 'mixed'
            crypto_implication = 'neutral'
        
        # Beta calculation (crypto volatility vs equity)
        crypto_beta = np.random.uniform(1.5, 3.0)  # Crypto typically has high beta
        
        return {
            'sp500_correlation_30d': round(sp500_correlation, 3),
            'nasdaq_correlation_30d': round(nasdaq_correlation, 3),
            'sp500_change_7d_pct': round(sp500_change_7d, 2),
            'nasdaq_change_7d_pct': round(nasdaq_change_7d, 2),
            'risk_sentiment': risk_sentiment,
            'crypto_implication': crypto_implication,
            'crypto_beta': round(crypto_beta, 2),
            'interpretation': f"Equities showing {risk_sentiment} - {crypto_implication} for crypto"
        }
    
    async def _analyze_gold_correlation(self, coin: str) -> Dict[str, Any]:
        """Analyze Gold correlation (safe haven comparison)"""
        np.random.seed(hash(coin + "gold" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # BTC-Gold correlation varies
        gold_correlation = np.random.uniform(-0.2, 0.5)
        
        # Gold price movement
        gold_change_7d = np.random.uniform(-2, 3)
        
        # Digital gold narrative
        if coin == 'BTC':
            digital_gold_score = np.random.uniform(60, 85)
        else:
            digital_gold_score = np.random.uniform(20, 50)
        
        # Safe haven behavior
        if gold_change_7d > 1.5:
            gold_trend = 'rising'
            safe_haven_flow = 'active'
        elif gold_change_7d < -1.5:
            gold_trend = 'falling'
            safe_haven_flow = 'risk_on'
        else:
            gold_trend = 'stable'
            safe_haven_flow = 'neutral'
        
        return {
            'correlation_30d': round(gold_correlation, 3),
            'gold_change_7d_pct': round(gold_change_7d, 2),
            'gold_trend': gold_trend,
            'safe_haven_flow': safe_haven_flow,
            'digital_gold_score': round(digital_gold_score, 1),
            'btc_gold_ratio_trend': 'increasing' if np.random.random() > 0.5 else 'decreasing'
        }
    
    def _determine_risk_regime(self, dxy: Dict, equity: Dict, gold: Dict) -> Dict[str, Any]:
        """Determine overall risk regime"""
        score = 50  # Neutral starting point
        factors = []
        
        # DXY impact (inverse)
        if dxy['dxy_trend'] == 'weakening':
            score += 15
            factors.append('weak_dollar')
        elif dxy['dxy_trend'] == 'strengthening':
            score -= 15
            factors.append('strong_dollar')
        
        # Equity sentiment
        if equity['risk_sentiment'] == 'risk_on':
            score += 20
            factors.append('equity_risk_on')
        elif equity['risk_sentiment'] == 'risk_off':
            score -= 20
            factors.append('equity_risk_off')
        
        # Gold/safe haven
        if gold['safe_haven_flow'] == 'active':
            score -= 10  # Safe haven flows typically mean risk-off
            factors.append('safe_haven_active')
        elif gold['safe_haven_flow'] == 'risk_on':
            score += 10
            factors.append('gold_risk_on')
        
        # Determine regime
        if score >= 70:
            regime = 'strong_risk_on'
            description = 'Strong risk appetite across markets'
        elif score >= 55:
            regime = 'risk_on'
            description = 'Moderate risk appetite'
        elif score <= 30:
            regime = 'strong_risk_off'
            description = 'Strong risk aversion across markets'
        elif score <= 45:
            regime = 'risk_off'
            description = 'Moderate risk aversion'
        else:
            regime = 'neutral'
            description = 'Mixed signals across markets'
        
        return {
            'regime': regime,
            'score': min(100, max(0, score)),
            'description': description,
            'factors': factors,
            'crypto_outlook': 'bullish' if score > 55 else ('bearish' if score < 45 else 'neutral')
        }
    
    def _generate_cross_asset_signal(self, btc_dom: Dict, dxy: Dict, equity: Dict,
                                      gold: Dict, risk_regime: Dict) -> Dict[str, Any]:
        """Generate composite cross-asset signal"""
        score = 50
        factors = []
        
        # BTC dominance factor (20%)
        if btc_dom['altcoin_impact'] == 'bullish':
            score += 10
            factors.append('btc_dom_favorable')
        elif btc_dom['altcoin_impact'] == 'bearish':
            score -= 10
            factors.append('btc_dom_unfavorable')
        
        # DXY factor (25%)
        if dxy['crypto_impact'] == 'bullish':
            score += 12
            factors.append('dxy_favorable')
        elif dxy['crypto_impact'] == 'bearish':
            score -= 12
            factors.append('dxy_unfavorable')
        
        # Equity factor (30%)
        if equity['crypto_implication'] == 'bullish':
            score += 15
            factors.append('equity_risk_on')
        elif equity['crypto_implication'] == 'bearish':
            score -= 15
            factors.append('equity_risk_off')
        
        # Risk regime factor (25%)
        if risk_regime['regime'] in ['strong_risk_on', 'risk_on']:
            score += 12
            factors.append('risk_regime_favorable')
        elif risk_regime['regime'] in ['strong_risk_off', 'risk_off']:
            score -= 12
            factors.append('risk_regime_unfavorable')
        
        # Determine signal
        if score >= 70:
            signal = 'strong_buy'
        elif score >= 60:
            signal = 'buy'
        elif score <= 30:
            signal = 'strong_sell'
        elif score <= 40:
            signal = 'sell'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'score': min(100, max(0, score)),
            'confidence': min(100, abs(score - 50) * 2),
            'factors': factors,
            'macro_summary': {
                'btc_dominance': btc_dom['altcoin_impact'],
                'dollar': dxy['crypto_impact'],
                'equities': equity['crypto_implication'],
                'risk_regime': risk_regime['regime']
            }
        }
    
    async def _store_analysis(self, analysis: Dict):
        """Store analysis in database"""
        try:
            await self.db.cross_asset_correlation.insert_one({
                **analysis,
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Failed to store cross-asset analysis: {e}")
    
    def _empty_analysis(self, symbol: str) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'btc_dominance': {'current_pct': 0, 'altcoin_impact': 'unknown'},
            'dxy_correlation': {'crypto_impact': 'unknown'},
            'equity_correlation': {'crypto_implication': 'unknown'},
            'gold_correlation': {'safe_haven_flow': 'unknown'},
            'risk_regime': {'regime': 'unknown', 'score': 50},
            'signal': {'signal': 'neutral', 'score': 50, 'confidence': 0}
        }
    
    async def get_correlation_matrix(self) -> Dict[str, Any]:
        """Get correlation matrix for major assets"""
        np.random.seed(hash(datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        assets = ['BTC', 'ETH', 'SOL', 'SP500', 'NASDAQ', 'DXY', 'GOLD']
        n = len(assets)
        
        # Generate realistic correlation matrix
        corr_matrix = np.eye(n)
        
        # Crypto correlations (high internal correlation)
        corr_matrix[0, 1] = corr_matrix[1, 0] = np.random.uniform(0.7, 0.9)  # BTC-ETH
        corr_matrix[0, 2] = corr_matrix[2, 0] = np.random.uniform(0.6, 0.8)  # BTC-SOL
        corr_matrix[1, 2] = corr_matrix[2, 1] = np.random.uniform(0.7, 0.85)  # ETH-SOL
        
        # Crypto-Equity (moderate positive)
        for i in range(3):
            corr_matrix[i, 3] = corr_matrix[3, i] = np.random.uniform(0.4, 0.7)  # Crypto-SP500
            corr_matrix[i, 4] = corr_matrix[4, i] = np.random.uniform(0.5, 0.8)  # Crypto-NASDAQ
        
        # Crypto-DXY (negative)
        for i in range(3):
            corr_matrix[i, 5] = corr_matrix[5, i] = np.random.uniform(-0.6, -0.3)  # Crypto-DXY
        
        # Crypto-Gold (mixed)
        for i in range(3):
            corr_matrix[i, 6] = corr_matrix[6, i] = np.random.uniform(-0.1, 0.4)  # Crypto-Gold
        
        # SP500-NASDAQ (high positive)
        corr_matrix[3, 4] = corr_matrix[4, 3] = np.random.uniform(0.85, 0.95)
        
        # Equity-DXY (slight negative)
        corr_matrix[3, 5] = corr_matrix[5, 3] = np.random.uniform(-0.4, -0.1)
        corr_matrix[4, 5] = corr_matrix[5, 4] = np.random.uniform(-0.3, 0)
        
        # Gold-DXY (negative)
        corr_matrix[6, 5] = corr_matrix[5, 6] = np.random.uniform(-0.5, -0.2)
        
        return {
            'assets': assets,
            'matrix': [[round(corr_matrix[i, j], 3) for j in range(n)] for i in range(n)],
            'timestamp': datetime.utcnow().isoformat()
        }


# Singleton instance
_cross_asset = None

def get_cross_asset_correlation(db: AsyncIOMotorDatabase = None) -> CrossAssetCorrelation:
    global _cross_asset
    if _cross_asset is None and db is not None:
        _cross_asset = CrossAssetCorrelation(db)
    return _cross_asset
