import pytest

from routes import performance


class DummyRegimePredictor:
    def __init__(self):
        self.model_accuracy = {
            "random_forest": 84.5,
            "gradient_boosting": 82.5,
            "lstm": 91.0,
        }
        self.model_metadata = {
            "random_forest": {"type": "ML", "category": "Tree"},
            "gradient_boosting": {"type": "ML", "category": "Ensemble"},
            "lstm": {"type": "DL", "category": "RNN"},
        }
        self.best_model = "lstm"
        self.is_trained = True


@pytest.mark.asyncio
async def test_compare_ml_vs_dl_recommendation_percent(monkeypatch):
    dummy_predictor = DummyRegimePredictor()
    monkeypatch.setattr(performance, "regime_predictor", dummy_predictor)

    result = await performance.compare_ml_vs_dl()

    assert result["summary"]["ml_avg_accuracy"] == pytest.approx(83.5)
    assert result["summary"]["dl_avg_accuracy"] == pytest.approx(91.0)
    assert "91.0%" in result["recommendation"]
