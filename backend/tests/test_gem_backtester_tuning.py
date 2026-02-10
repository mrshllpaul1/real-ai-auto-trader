import math

from services.gem_backtester import GemBacktester


def _base_weights():
    return {
        "volume_surge": 0.20,
        "price_momentum": 0.15,
        "market_cap_potential": 0.10,
        "technical_setup": 0.15,
        "volatility_score": 0.10,
        "sentiment": 0.10,
        "relative_strength": 0.20,
    }


def test_analyze_factors_returns_precision_recall_and_validation_metrics():
    backtester = GemBacktester(db=None)
    predictions = [
        {"gem_score": 0.9, "predicted_gem": True, "actual_gem": True, "correct": True},
        {"gem_score": 0.8, "predicted_gem": True, "actual_gem": False, "correct": False},
        {"gem_score": 0.2, "predicted_gem": False, "actual_gem": True, "correct": False},
        {"gem_score": 0.1, "predicted_gem": False, "actual_gem": False, "correct": True},
        {"gem_score": 0.7, "predicted_gem": True, "actual_gem": True, "correct": True},
        {"gem_score": 0.3, "predicted_gem": False, "actual_gem": False, "correct": True},
    ]

    analysis = backtester._analyze_factors(predictions, _base_weights())

    assert analysis["false_positive_count"] == 1
    assert analysis["false_negative_count"] == 1
    assert math.isclose(analysis["precision"], 0.6667, rel_tol=1e-4)
    assert math.isclose(analysis["recall"], 0.6667, rel_tol=1e-4)
    assert math.isclose(analysis["f1"], 0.6667, rel_tol=1e-4)
    assert "val_f1" in analysis and "train_f1" in analysis
    assert analysis["overfit_gap"] >= 0


def test_improve_weights_reacts_to_low_precision():
    backtester = GemBacktester(db=None)
    current_weights = _base_weights()
    iter_result = {
        "accuracy": 60,
        "factor_analysis": {
            "false_positive_count": 4,
            "false_negative_count": 1,
            "precision": 0.5,
            "recall": 0.8,
            "val_precision": 0.5,
            "val_recall": 0.8,
            "val_f1": 0.615,
            "overfit_gap": 0.0,
        },
    }

    result = backtester._improve_weights(current_weights, iter_result, current_threshold=0.7)

    assert result["new_threshold"] > 0.7
    assert result["new_weights"]["relative_strength"] > current_weights["relative_strength"]


def test_improve_weights_regularizes_on_overfit_gap():
    backtester = GemBacktester(db=None)
    current_weights = _base_weights()
    iter_result = {
        "accuracy": 72,
        "factor_analysis": {
            "false_positive_count": 0,
            "false_negative_count": 0,
            "precision": 0.8,
            "recall": 0.8,
            "train_f1": 0.82,
            "val_f1": 0.6,
            "val_precision": 0.7,
            "val_recall": 0.55,
            "overfit_gap": 0.22,
        },
    }

    result = backtester._improve_weights(current_weights, iter_result, current_threshold=0.7)

    assert result["new_threshold"] > 0.7
    assert abs(sum(result["new_weights"].values()) - 1.0) < 1e-6
    assert "Validation F1" in result["reason"]
