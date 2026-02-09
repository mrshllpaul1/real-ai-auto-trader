import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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

    for _ in range(25):
        model.update_from_feedback(features, human_rating=4)

    later_lr = model.last_effective_lr

    assert later_lr < first_lr
    assert later_lr >= model.min_learning_rate

    signal = model.get_training_signal()
    assert signal["samples"] == 26
    assert signal["last_update_at"] is not None
