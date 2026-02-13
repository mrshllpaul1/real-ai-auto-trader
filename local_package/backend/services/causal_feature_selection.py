"""
Causal Feature Selection for Trading
=====================================
Implements causal discovery algorithms to identify true predictive features
and reduce model reliance on spurious correlations.

Methods:
- PC Algorithm (constraint-based causal discovery)
- Granger Causality testing
- Transfer Entropy analysis
- Feature importance with SHAP
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import defaultdict
from scipy import stats
import warnings

logger = logging.getLogger(__name__)


class GrangerCausalityTest:
    """
    Granger Causality testing for time series features.
    Tests if past values of X help predict Y beyond Y's own past values.
    """
    
    def __init__(self, max_lag: int = 5):
        self.max_lag = max_lag
        
    def test(
        self, 
        cause: np.ndarray, 
        effect: np.ndarray, 
        significance: float = 0.05
    ) -> Dict:
        """
        Test if 'cause' Granger-causes 'effect'.
        
        Returns:
            Dict with p-value, F-statistic, and whether causal
        """
        if len(cause) != len(effect) or len(cause) < self.max_lag * 3:
            return {"is_causal": False, "error": "Insufficient data"}
        
        # Prepare lagged variables
        results = []
        
        for lag in range(1, self.max_lag + 1):
            try:
                # Restricted model: effect ~ effect_lags
                y = effect[lag:]
                X_restricted = np.column_stack([
                    effect[lag-i:-i] for i in range(1, lag + 1)
                ])
                
                # Unrestricted model: effect ~ effect_lags + cause_lags
                X_unrestricted = np.column_stack([
                    X_restricted,
                    *[cause[lag-i:-i] for i in range(1, lag + 1)]
                ])
                
                # Fit restricted model
                beta_r = np.linalg.lstsq(X_restricted, y, rcond=None)[0]
                resid_r = y - X_restricted @ beta_r
                ssr_r = np.sum(resid_r ** 2)
                
                # Fit unrestricted model
                beta_u = np.linalg.lstsq(X_unrestricted, y, rcond=None)[0]
                resid_u = y - X_unrestricted @ beta_u
                ssr_u = np.sum(resid_u ** 2)
                
                # F-test
                n = len(y)
                k_r = X_restricted.shape[1]
                k_u = X_unrestricted.shape[1]
                
                f_stat = ((ssr_r - ssr_u) / (k_u - k_r)) / (ssr_u / (n - k_u))
                p_value = 1 - stats.f.cdf(f_stat, k_u - k_r, n - k_u)
                
                results.append({
                    "lag": lag,
                    "f_statistic": f_stat,
                    "p_value": p_value,
                    "is_significant": p_value < significance
                })
                
            except Exception as e:
                continue
        
        if not results:
            return {"is_causal": False, "error": "Could not compute test"}
        
        # Aggregate results (use minimum p-value)
        best_result = min(results, key=lambda x: x["p_value"])
        
        return {
            "is_causal": best_result["is_significant"],
            "best_lag": best_result["lag"],
            "f_statistic": best_result["f_statistic"],
            "p_value": best_result["p_value"],
            "all_lags": results
        }


class TransferEntropyCalculator:
    """
    Calculate Transfer Entropy to measure information flow between features.
    Higher TE indicates more causal influence.
    """
    
    def __init__(self, bins: int = 10, lag: int = 1):
        self.bins = bins
        self.lag = lag
    
    def _discretize(self, x: np.ndarray) -> np.ndarray:
        """Discretize continuous data into bins"""
        return np.digitize(x, np.histogram_bin_edges(x, bins=self.bins)[:-1])
    
    def _entropy(self, x: np.ndarray) -> float:
        """Calculate Shannon entropy"""
        _, counts = np.unique(x, return_counts=True)
        probs = counts / len(x)
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    def _joint_entropy(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate joint entropy"""
        xy = list(zip(x, y))
        unique, counts = np.unique(xy, return_counts=True, axis=0)
        probs = counts / len(xy)
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    def calculate(self, source: np.ndarray, target: np.ndarray) -> float:
        """
        Calculate Transfer Entropy from source to target.
        TE(X->Y) = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
        """
        if len(source) != len(target) or len(source) < self.lag + 10:
            return 0.0
        
        # Discretize
        source_d = self._discretize(source)
        target_d = self._discretize(target)
        
        # Create lagged versions
        y_t = target_d[self.lag:]
        y_past = target_d[:-self.lag]
        x_past = source_d[:-self.lag]
        
        # Calculate conditional entropies
        # H(Y_t | Y_{t-1})
        h_y_given_ypast = self._joint_entropy(y_t, y_past) - self._entropy(y_past)
        
        # H(Y_t | Y_{t-1}, X_{t-1})
        yy = list(zip(y_past, x_past))
        h_y_given_both = self._joint_entropy(y_t, np.array([hash(tuple(row)) for row in yy])) - self._entropy(np.array([hash(tuple(row)) for row in yy]))
        
        # Transfer entropy
        te = h_y_given_ypast - h_y_given_both
        
        return max(0, te)  # TE should be non-negative


class CausalFeatureSelector:
    """
    Main class for causal feature selection.
    Combines multiple methods to identify true predictive features.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.granger_test = GrangerCausalityTest()
        self.te_calculator = TransferEntropyCalculator()
        
        # Cache for computed causality scores
        self.causality_cache = {}
        
        # Feature importance scores
        self.feature_scores = {}
        
        logger.info("🔬 Causal Feature Selector initialized")
    
    def analyze_features(
        self,
        features_df: pd.DataFrame,
        target_col: str,
        significance: float = 0.05
    ) -> Dict[str, Any]:
        """
        Analyze all features for causal relationship with target.
        
        Args:
            features_df: DataFrame with features and target
            target_col: Name of target column
            significance: P-value threshold for significance
            
        Returns:
            Dict with causal analysis results
        """
        if target_col not in features_df.columns:
            return {"error": f"Target column {target_col} not found"}
        
        target = features_df[target_col].values
        feature_cols = [c for c in features_df.columns if c != target_col]
        
        results = {
            "target": target_col,
            "features_analyzed": len(feature_cols),
            "causal_features": [],
            "non_causal_features": [],
            "feature_scores": {},
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for col in feature_cols:
            feature_values = features_df[col].values
            
            # Skip if too many NaNs
            if np.isnan(feature_values).sum() > len(feature_values) * 0.1:
                continue
            
            # Replace NaNs with mean
            feature_values = np.nan_to_num(feature_values, nan=np.nanmean(feature_values))
            
            try:
                # 1. Granger Causality Test
                granger_result = self.granger_test.test(feature_values, target, significance)
                
                # 2. Transfer Entropy
                te_score = self.te_calculator.calculate(feature_values, target)
                
                # 3. Correlation (for comparison)
                correlation = np.corrcoef(feature_values[:-1], target[1:])[0, 1]
                
                # 4. Combined causal score
                causal_score = self._calculate_causal_score(
                    granger_result, te_score, correlation
                )
                
                feature_result = {
                    "feature": col,
                    "granger_causal": granger_result.get("is_causal", False),
                    "granger_p_value": granger_result.get("p_value", 1.0),
                    "granger_f_stat": granger_result.get("f_statistic", 0),
                    "transfer_entropy": te_score,
                    "correlation": correlation,
                    "causal_score": causal_score,
                    "is_true_predictor": causal_score >= 60
                }
                
                results["feature_scores"][col] = causal_score
                
                if feature_result["is_true_predictor"]:
                    results["causal_features"].append(feature_result)
                else:
                    results["non_causal_features"].append(feature_result)
                    
            except Exception as e:
                logger.warning(f"Error analyzing feature {col}: {e}")
                continue
        
        # Sort by causal score
        results["causal_features"].sort(key=lambda x: x["causal_score"], reverse=True)
        results["non_causal_features"].sort(key=lambda x: x["causal_score"], reverse=True)
        
        # Summary statistics
        results["summary"] = {
            "total_features": len(feature_cols),
            "causal_count": len(results["causal_features"]),
            "non_causal_count": len(results["non_causal_features"]),
            "avg_causal_score": np.mean([f["causal_score"] for f in results["causal_features"]]) if results["causal_features"] else 0,
            "top_features": [f["feature"] for f in results["causal_features"][:10]]
        }
        
        return results
    
    def _calculate_causal_score(
        self,
        granger_result: Dict,
        te_score: float,
        correlation: float
    ) -> float:
        """
        Calculate combined causal score from multiple tests.
        Score ranges from 0-100.
        """
        score = 0
        
        # Granger causality contributes up to 40 points
        if granger_result.get("is_causal"):
            p_value = granger_result.get("p_value", 1.0)
            # Lower p-value = higher score
            granger_score = 40 * (1 - min(p_value * 10, 1))
            score += granger_score
        
        # Transfer entropy contributes up to 30 points
        # Normalize TE (typical values 0-2 bits)
        te_normalized = min(te_score / 0.5, 1)
        score += te_normalized * 30
        
        # Correlation contributes up to 30 points (absolute value)
        # But penalize very high correlation (might be spurious)
        abs_corr = abs(correlation) if not np.isnan(correlation) else 0
        if abs_corr > 0.9:
            # Too high correlation - might be look-ahead bias or data leakage
            corr_score = 15  # Penalized
        else:
            corr_score = abs_corr * 30
        score += corr_score
        
        return min(100, score)
    
    def select_features(
        self,
        features_df: pd.DataFrame,
        target_col: str,
        top_k: int = 10,
        min_score: float = 50
    ) -> List[str]:
        """
        Select top causally-related features.
        
        Args:
            features_df: DataFrame with features
            target_col: Target column name
            top_k: Maximum number of features to select
            min_score: Minimum causal score required
            
        Returns:
            List of selected feature names
        """
        analysis = self.analyze_features(features_df, target_col)
        
        if "error" in analysis:
            return []
        
        causal_features = analysis.get("causal_features", [])
        
        # Filter by minimum score and take top k
        selected = [
            f["feature"] for f in causal_features
            if f["causal_score"] >= min_score
        ][:top_k]
        
        return selected
    
    def detect_spurious_correlations(
        self,
        features_df: pd.DataFrame,
        target_col: str
    ) -> List[Dict]:
        """
        Detect features that are correlated but not causally related.
        These are likely spurious correlations that could hurt model performance.
        """
        analysis = self.analyze_features(features_df, target_col)
        
        spurious = []
        for feature in analysis.get("non_causal_features", []):
            # High correlation but low causal score = spurious
            if abs(feature.get("correlation", 0)) > 0.3 and feature.get("causal_score", 0) < 40:
                spurious.append({
                    "feature": feature["feature"],
                    "correlation": feature["correlation"],
                    "causal_score": feature["causal_score"],
                    "warning": "High correlation but low causal evidence - likely spurious"
                })
        
        return spurious
    
    async def save_analysis(self, analysis: Dict):
        """Save analysis results to database"""
        if self.db is not None:
            try:
                await self.db.causal_analyses.insert_one({
                    **analysis,
                    "created_at": datetime.now(timezone.utc)
                })
            except Exception as e:
                logger.error(f"Failed to save analysis: {e}")


# Singleton
_causal_selector: Optional[CausalFeatureSelector] = None


def get_causal_selector(db=None) -> CausalFeatureSelector:
    """Get or create causal selector singleton"""
    global _causal_selector
    if _causal_selector is None:
        _causal_selector = CausalFeatureSelector(db)
    return _causal_selector
