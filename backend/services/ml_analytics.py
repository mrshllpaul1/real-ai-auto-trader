"""ML Analytics Service

Provides:
- Confidence calibration analysis
- Model drift detection
- A/B testing infrastructure expansion
"""

import os
import json
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """Analyzes prediction confidence vs actual accuracy."""
    
    def __init__(self):
        self._predictions: List[Dict] = []
        self._calibration_bins = 10
        self._min_samples_per_bin = 5
    
    def record_prediction(
        self,
        prediction_id: str,
        coin_id: str,
        predicted_action: str,  # BUY, SELL, HOLD
        confidence: float,  # 0-1
        model_name: str,
        timestamp: Optional[datetime] = None
    ):
        """Record a prediction for later calibration analysis."""
        self._predictions.append({
            "id": prediction_id,
            "coin_id": coin_id,
            "predicted_action": predicted_action,
            "confidence": confidence,
            "model_name": model_name,
            "timestamp": timestamp or datetime.utcnow(),
            "actual_outcome": None,
            "outcome_recorded_at": None
        })
    
    def record_outcome(
        self,
        prediction_id: str,
        actual_correct: bool
    ):
        """Record the actual outcome of a prediction."""
        for pred in self._predictions:
            if pred["id"] == prediction_id:
                pred["actual_outcome"] = actual_correct
                pred["outcome_recorded_at"] = datetime.utcnow()
                break
    
    def get_calibration_curve(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Calculate calibration curve showing confidence vs actual accuracy."""
        # Filter predictions with outcomes
        filtered = [
            p for p in self._predictions
            if p["actual_outcome"] is not None
            and (model_name is None or p["model_name"] == model_name)
        ]
        
        if len(filtered) < self._min_samples_per_bin:
            return {
                "error": "Insufficient data",
                "samples": len(filtered),
                "required": self._min_samples_per_bin
            }
        
        # Bin predictions by confidence
        bins = defaultdict(list)
        for pred in filtered:
            bin_idx = min(int(pred["confidence"] * self._calibration_bins), self._calibration_bins - 1)
            bins[bin_idx].append(pred["actual_outcome"])
        
        # Calculate accuracy per bin
        calibration_data = []
        for bin_idx in range(self._calibration_bins):
            bin_center = (bin_idx + 0.5) / self._calibration_bins
            if len(bins[bin_idx]) >= self._min_samples_per_bin:
                accuracy = sum(bins[bin_idx]) / len(bins[bin_idx])
                calibration_data.append({
                    "confidence_range": f"{bin_idx/self._calibration_bins:.0%}-{(bin_idx+1)/self._calibration_bins:.0%}",
                    "mean_confidence": bin_center,
                    "actual_accuracy": accuracy,
                    "sample_count": len(bins[bin_idx]),
                    "calibration_error": abs(bin_center - accuracy),
                    "is_overconfident": bin_center > accuracy,
                    "is_underconfident": bin_center < accuracy
                })
        
        # Calculate overall calibration metrics
        if calibration_data:
            ece = sum(d["sample_count"] * d["calibration_error"] for d in calibration_data) / len(filtered)
            mce = max(d["calibration_error"] for d in calibration_data)
        else:
            ece = mce = 0
        
        return {
            "model_name": model_name or "all_models",
            "total_predictions": len(filtered),
            "calibration_curve": calibration_data,
            "metrics": {
                "expected_calibration_error": round(ece, 4),
                "max_calibration_error": round(mce, 4),
                "calibration_quality": "good" if ece < 0.05 else "moderate" if ece < 0.10 else "poor"
            },
            "recommendations": self._get_calibration_recommendations(calibration_data, ece)
        }
    
    def _get_calibration_recommendations(self, curve: List[Dict], ece: float) -> List[str]:
        """Generate recommendations based on calibration analysis."""
        recommendations = []
        
        if ece > 0.10:
            recommendations.append("Model is poorly calibrated. Consider temperature scaling or Platt scaling.")
        
        overconfident_bins = [d for d in curve if d.get("is_overconfident")]
        if len(overconfident_bins) > len(curve) / 2:
            recommendations.append("Model tends to be overconfident. Consider reducing confidence scores or improving uncertainty estimation.")
        
        underconfident_bins = [d for d in curve if d.get("is_underconfident")]
        if len(underconfident_bins) > len(curve) / 2:
            recommendations.append("Model tends to be underconfident. Predictions may be more reliable than indicated.")
        
        if not recommendations:
            recommendations.append("Model is well-calibrated. Confidence scores are reliable.")
        
        return recommendations
    
    def get_accuracy_by_confidence_level(self) -> Dict[str, Any]:
        """Get accuracy breakdown by confidence level (HIGH/MEDIUM/LOW/VERY_LOW)."""
        filtered = [p for p in self._predictions if p["actual_outcome"] is not None]
        
        levels = {
            "HIGH": {"min": 0.80, "max": 1.00, "predictions": [], "color": "#22c55e"},
            "MEDIUM": {"min": 0.60, "max": 0.80, "predictions": [], "color": "#eab308"},
            "LOW": {"min": 0.40, "max": 0.60, "predictions": [], "color": "#f97316"},
            "VERY_LOW": {"min": 0.00, "max": 0.40, "predictions": [], "color": "#ef4444"}
        }
        
        for pred in filtered:
            conf = pred["confidence"]
            for level_name, level_data in levels.items():
                if level_data["min"] <= conf < level_data["max"] or (level_name == "HIGH" and conf == 1.0):
                    level_data["predictions"].append(pred)
                    break
        
        results = {}
        for level_name, level_data in levels.items():
            preds = level_data["predictions"]
            if preds:
                accuracy = sum(1 for p in preds if p["actual_outcome"]) / len(preds)
                results[level_name] = {
                    "range": f"{level_data['min']:.0%}-{level_data['max']:.0%}",
                    "count": len(preds),
                    "accuracy": round(accuracy * 100, 2),
                    "correct": sum(1 for p in preds if p["actual_outcome"]),
                    "incorrect": sum(1 for p in preds if not p["actual_outcome"]),
                    "color": level_data["color"]
                }
            else:
                results[level_name] = {
                    "range": f"{level_data['min']:.0%}-{level_data['max']:.0%}",
                    "count": 0,
                    "accuracy": None,
                    "color": level_data["color"]
                }
        
        return {
            "levels": results,
            "total_predictions": len(filtered),
            "overall_accuracy": round(sum(1 for p in filtered if p["actual_outcome"]) / len(filtered) * 100, 2) if filtered else None
        }


class ModelDriftDetector:
    """Detects model performance drift over time."""
    
    def __init__(self, window_size: int = 100, alert_threshold: float = 0.15):
        self._predictions: List[Dict] = []
        self._window_size = window_size
        self._alert_threshold = alert_threshold
        self._alerts: List[Dict] = []
        self._baseline_accuracy: Dict[str, float] = {}
    
    def record_prediction_outcome(
        self,
        model_name: str,
        is_correct: bool,
        timestamp: Optional[datetime] = None
    ):
        """Record a prediction outcome for drift detection."""
        self._predictions.append({
            "model_name": model_name,
            "is_correct": is_correct,
            "timestamp": timestamp or datetime.utcnow()
        })
        
        # Check for drift after each new prediction
        self._check_drift(model_name)
    
    def set_baseline(self, model_name: str, accuracy: float):
        """Set baseline accuracy for a model."""
        self._baseline_accuracy[model_name] = accuracy
    
    def _check_drift(self, model_name: str):
        """Check if model has drifted from baseline."""
        # Get recent predictions for this model
        model_preds = [
            p for p in self._predictions
            if p["model_name"] == model_name
        ][-self._window_size:]
        
        if len(model_preds) < self._window_size // 2:
            return  # Not enough data
        
        recent_accuracy = sum(1 for p in model_preds if p["is_correct"]) / len(model_preds)
        
        # Compare to baseline
        baseline = self._baseline_accuracy.get(model_name, 0.5)
        drift = baseline - recent_accuracy
        
        if abs(drift) > self._alert_threshold:
            alert = {
                "id": f"drift_{model_name}_{datetime.utcnow().timestamp()}",
                "model_name": model_name,
                "alert_type": "performance_drift",
                "severity": "high" if abs(drift) > 0.25 else "medium",
                "baseline_accuracy": round(baseline * 100, 2),
                "current_accuracy": round(recent_accuracy * 100, 2),
                "drift_percentage": round(drift * 100, 2),
                "direction": "degradation" if drift > 0 else "improvement",
                "window_size": len(model_preds),
                "timestamp": datetime.utcnow().isoformat(),
                "recommendation": self._get_drift_recommendation(drift)
            }
            
            # Only add if not duplicate recent alert
            recent_alerts = [
                a for a in self._alerts
                if a["model_name"] == model_name
                and (datetime.utcnow() - datetime.fromisoformat(a["timestamp"])).seconds < 3600
            ]
            if not recent_alerts:
                self._alerts.append(alert)
    
    def _get_drift_recommendation(self, drift: float) -> str:
        """Generate recommendation based on drift."""
        if drift > 0.25:
            return "Critical: Model performance has degraded significantly. Consider retraining immediately."
        elif drift > 0.15:
            return "Warning: Model performance is declining. Schedule retraining and review recent market conditions."
        elif drift < -0.15:
            return "Info: Model performance has improved. Consider updating baseline metrics."
        return "Monitor: Keep tracking performance."
    
    def get_drift_status(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current drift status for models."""
        models = {model_name} if model_name else set(p["model_name"] for p in self._predictions)
        
        status = {}
        for model in models:
            model_preds = [
                p for p in self._predictions
                if p["model_name"] == model
            ][-self._window_size:]
            
            if model_preds:
                current_accuracy = sum(1 for p in model_preds if p["is_correct"]) / len(model_preds)
                baseline = self._baseline_accuracy.get(model, 0.5)
                drift = baseline - current_accuracy
                
                status[model] = {
                    "baseline_accuracy": round(baseline * 100, 2),
                    "current_accuracy": round(current_accuracy * 100, 2),
                    "drift_percentage": round(drift * 100, 2),
                    "sample_count": len(model_preds),
                    "status": "critical" if abs(drift) > 0.25 else "warning" if abs(drift) > 0.15 else "healthy",
                    "last_updated": model_preds[-1]["timestamp"].isoformat() if model_preds else None
                }
        
        return {
            "models": status,
            "alert_threshold": f"{self._alert_threshold:.0%}",
            "window_size": self._window_size
        }
    
    def get_alerts(self, acknowledged: bool = False) -> List[Dict]:
        """Get drift alerts."""
        return [a for a in self._alerts if a.get("acknowledged", False) == acknowledged]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge a drift alert."""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                break


class ABTestManager:
    """Extended A/B testing infrastructure for strategy variants."""
    
    def __init__(self):
        self._tests: Dict[str, Dict] = {}
        self._results: Dict[str, List[Dict]] = {}
    
    def create_test(
        self,
        test_id: str,
        test_name: str,
        variants: List[Dict[str, Any]],
        traffic_split: Optional[List[float]] = None,
        metric: str = "win_rate"
    ) -> Dict[str, Any]:
        """Create a new A/B test."""
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if len(traffic_split) != len(variants):
            return {"error": "Traffic split must match number of variants"}
        
        if abs(sum(traffic_split) - 1.0) > 0.01:
            return {"error": "Traffic split must sum to 1.0"}
        
        self._tests[test_id] = {
            "id": test_id,
            "name": test_name,
            "variants": [
                {
                    "id": f"{test_id}_variant_{i}",
                    "name": v.get("name", f"Variant {chr(65+i)}"),
                    "config": v,
                    "traffic_share": traffic_split[i]
                }
                for i, v in enumerate(variants)
            ],
            "metric": metric,
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
            "total_samples": 0
        }
        self._results[test_id] = []
        
        return self._tests[test_id]
    
    def record_result(
        self,
        test_id: str,
        variant_id: str,
        outcome: float,  # e.g., 1 for win, 0 for loss, or actual return
        metadata: Optional[Dict] = None
    ):
        """Record a result for an A/B test variant."""
        if test_id not in self._tests:
            return
        
        self._results[test_id].append({
            "variant_id": variant_id,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        self._tests[test_id]["total_samples"] += 1
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get results for an A/B test with statistical analysis."""
        if test_id not in self._tests:
            return {"error": "Test not found"}
        
        test = self._tests[test_id]
        results = self._results.get(test_id, [])
        
        variant_stats = {}
        for variant in test["variants"]:
            v_results = [r for r in results if r["variant_id"] == variant["id"]]
            if v_results:
                outcomes = [r["outcome"] for r in v_results]
                variant_stats[variant["id"]] = {
                    "name": variant["name"],
                    "samples": len(outcomes),
                    "mean": round(np.mean(outcomes), 4),
                    "std": round(np.std(outcomes), 4) if len(outcomes) > 1 else 0,
                    "min": round(min(outcomes), 4),
                    "max": round(max(outcomes), 4),
                    "confidence_interval": self._calculate_ci(outcomes)
                }
            else:
                variant_stats[variant["id"]] = {
                    "name": variant["name"],
                    "samples": 0,
                    "mean": None
                }
        
        # Determine winner
        winner = None
        if variant_stats:
            valid_variants = [(vid, v) for vid, v in variant_stats.items() if v["mean"] is not None]
            if valid_variants:
                winner_id, winner_data = max(valid_variants, key=lambda x: x[1]["mean"])
                winner = {
                    "variant_id": winner_id,
                    "name": winner_data["name"],
                    "mean": winner_data["mean"],
                    "confidence": self._calculate_significance(variant_stats)
                }
        
        return {
            "test": test,
            "variant_results": variant_stats,
            "winner": winner,
            "total_samples": len(results),
            "recommendation": self._get_ab_recommendation(variant_stats, winner)
        }
    
    def _calculate_ci(self, outcomes: List[float], confidence: float = 0.95) -> Dict:
        """Calculate confidence interval."""
        if len(outcomes) < 2:
            return {"lower": None, "upper": None}
        
        mean = np.mean(outcomes)
        std_err = np.std(outcomes) / np.sqrt(len(outcomes))
        z_score = 1.96  # 95% CI
        
        return {
            "lower": round(mean - z_score * std_err, 4),
            "upper": round(mean + z_score * std_err, 4)
        }
    
    def _calculate_significance(self, variant_stats: Dict) -> str:
        """Calculate statistical significance."""
        valid_variants = [v for v in variant_stats.values() if v["samples"] >= 30]
        
        if len(valid_variants) < 2:
            return "insufficient_data"
        
        # Simple check: non-overlapping confidence intervals
        sorted_variants = sorted(valid_variants, key=lambda x: x["mean"], reverse=True)
        top = sorted_variants[0]
        second = sorted_variants[1]
        
        if top["confidence_interval"]["lower"] and second["confidence_interval"]["upper"]:
            if top["confidence_interval"]["lower"] > second["confidence_interval"]["upper"]:
                return "statistically_significant"
        
        return "not_significant"
    
    def _get_ab_recommendation(self, stats: Dict, winner: Optional[Dict]) -> str:
        """Generate recommendation based on A/B test results."""
        total_samples = sum(v["samples"] for v in stats.values() if v["samples"])
        
        if total_samples < 100:
            return f"Need more data. Currently {total_samples}/100 minimum samples."
        
        if winner and winner["confidence"] == "statistically_significant":
            return f"Winner found: {winner['name']} with {winner['mean']:.2%} {winner.get('metric', 'performance')}. Safe to deploy."
        
        return "No clear winner yet. Continue running the test."
    
    def list_tests(self, status: Optional[str] = None) -> List[Dict]:
        """List all A/B tests."""
        tests = list(self._tests.values())
        if status:
            tests = [t for t in tests if t["status"] == status]
        return tests
    
    def stop_test(self, test_id: str) -> Dict:
        """Stop an A/B test."""
        if test_id in self._tests:
            self._tests[test_id]["status"] = "stopped"
            self._tests[test_id]["stopped_at"] = datetime.utcnow().isoformat()
            return self._tests[test_id]
        return {"error": "Test not found"}


# Singleton instances
_confidence_calibrator: Optional[ConfidenceCalibrator] = None
_drift_detector: Optional[ModelDriftDetector] = None
_ab_manager: Optional[ABTestManager] = None


def get_confidence_calibrator() -> ConfidenceCalibrator:
    """Get or create confidence calibrator."""
    global _confidence_calibrator
    if _confidence_calibrator is None:
        _confidence_calibrator = ConfidenceCalibrator()
    return _confidence_calibrator


def get_drift_detector() -> ModelDriftDetector:
    """Get or create drift detector."""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = ModelDriftDetector()
    return _drift_detector


def get_ab_manager() -> ABTestManager:
    """Get or create A/B test manager."""
    global _ab_manager
    if _ab_manager is None:
        _ab_manager = ABTestManager()
    return _ab_manager
