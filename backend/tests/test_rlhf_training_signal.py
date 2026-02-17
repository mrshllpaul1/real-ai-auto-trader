import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services import rlhf_trainer
from backend.services.rlhf_trainer import RewardModel


def _sample_features():
    return {
        "profit_pct": 8.0,
        "hold_time_hours": 6,
        "entry_timing_score": 0.7,
        "exit_timing_score": 0.65,
        "risk_reward_ratio": 1.8,
        "position_size_score": 0.9,
    }


def test_reward_model_learns_from_positive_feedback():
    model = RewardModel()
    features = _sample_features()

    initial_reward = model.predict_reward(features)
    model.update_from_feedback(features, human_rating=5)
    updated_reward = model.predict_reward(features)

    assert updated_reward > initial_reward

    signal = model.get_training_signal()
    assert signal["samples"] == 1
    assert signal["effective_learning_rate"] <= model.base_learning_rate
    assert signal["avg_adjustment_magnitude"] >= 0


def test_learning_rate_decays_with_more_feedback():
    model = RewardModel()
    features = _sample_features()

    model.update_from_feedback(features, human_rating=5)
    first_lr = model.last_effective_lr

    min_decay_iterations = 5  # prevents zero-iteration edge cases in the test
    decay_test_iterations = max(min_decay_iterations, int(1 / model.decay_rate))  # ensures we see a noticeable LR decay step
    for _ in range(decay_test_iterations):
        model.update_from_feedback(features, human_rating=4)

    later_lr = model.last_effective_lr

    assert later_lr < first_lr
    assert later_lr >= model.min_learning_rate

    signal = model.get_training_signal()
    assert signal["samples"] == decay_test_iterations + 1
    assert signal["last_update_at"] is not None


def test_feature_normalization_and_cached_lr():
    model = RewardModel()
    
    # Feature-specific clamping/normalization
    assert model._normalize_feature_value("profit_pct", 500) == model._normalize_feature_value("profit_pct", 200)  # clamped to max
    assert model._normalize_feature_value("hold_time_hours", -10) == 0  # clamped to min 0
    assert model._normalize_feature_value("entry_timing_score", 1.5) <= 1  # capped at 1
    assert model._normalize_feature_value("risk_reward_ratio", 0) == 0  # safe default
    
    # Invalid scale falls back to default normalization scale
    rlhf_trainer.FEATURE_RULES["tmp_bad_scale"] = {"scale": 0}
    try:
        fallback_val = model._normalize_feature_value("tmp_bad_scale", 5)
        expected = float(np.tanh(5 / model.normalization_scale))
        assert fallback_val == expected
    finally:
        rlhf_trainer.FEATURE_RULES.pop("tmp_bad_scale", None)
    
    # Learning rate caching with stable sample_count
    lr1 = model._get_effective_learning_rate()
    cache_count = model._lr_cache_count
    lr2 = model._get_effective_learning_rate()
    assert lr1 == lr2
    assert cache_count == model._lr_cache_count
    
    # When sample_count changes, cache updates
    model.sample_count = 3
    lr3 = model._get_effective_learning_rate()
    assert lr3 <= lr1
    assert model._lr_cache_count == model.sample_count
