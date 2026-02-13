"""
Event Prediction Backtesting Service
=====================================
Backtest event predictions against historical data to measure accuracy.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class HistoricalEvent:
    """A historical event that actually occurred"""
    event_id: str
    event_type: str
    description: str
    occurred_date: str
    actual_impact: str  # 'positive', 'negative', 'mixed'
    price_before: float
    price_after: float
    price_change_pct: float
    affected_coins: List[str]
    source: str  # Where this was documented


@dataclass
class PredictionResult:
    """Result of a prediction vs actual event comparison"""
    prediction_id: str
    event_type: str
    predicted_date: str
    actual_date: Optional[str]
    prediction_probability: float
    predicted_impact: str
    actual_impact: Optional[str]
    
    # Accuracy metrics
    date_accuracy_days: Optional[int]  # How close was the date prediction
    impact_correct: Optional[bool]
    event_occurred: bool
    
    # Scoring
    accuracy_score: float  # 0-100
    
    created_at: str


@dataclass
class EventTypeAccuracy:
    """Accuracy statistics for a specific event type"""
    event_type: str
    total_predictions: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    avg_date_accuracy_days: float
    impact_accuracy_pct: float
    overall_accuracy_pct: float
    precision: float  # TP / (TP + FP)
    recall: float  # TP / (TP + FN)
    f1_score: float


class EventBacktestService:
    """
    Event prediction backtesting service that:
    1. Compares predictions against historical events
    2. Calculates accuracy metrics for each event type
    3. Identifies prediction strengths and weaknesses
    4. Provides recommendations for improving predictions
    """
    
    # Historical events database for backtesting
    HISTORICAL_EVENTS = [
        # Bitcoin Halvings - highly predictable
        {"event_type": "bitcoin_halving", "date": "2024-04-19", "impact": "positive", "price_change": 15.2, "description": "4th Bitcoin halving"},
        {"event_type": "bitcoin_halving", "date": "2020-05-11", "impact": "positive", "price_change": 300.0, "description": "3rd Bitcoin halving"},
        {"event_type": "bitcoin_halving", "date": "2016-07-09", "impact": "positive", "price_change": 280.0, "description": "2nd Bitcoin halving"},
        
        # FOMC Meetings
        {"event_type": "fomc_meeting", "date": "2024-12-18", "impact": "negative", "price_change": -5.2, "description": "Fed signals fewer cuts"},
        {"event_type": "fomc_meeting", "date": "2024-09-18", "impact": "positive", "price_change": 8.1, "description": "Fed cuts 50bps"},
        {"event_type": "fomc_meeting", "date": "2024-06-12", "impact": "mixed", "price_change": -1.2, "description": "Fed holds steady"},
        {"event_type": "fomc_meeting", "date": "2024-03-20", "impact": "negative", "price_change": -3.5, "description": "Hawkish stance"},
        {"event_type": "fomc_meeting", "date": "2023-12-13", "impact": "positive", "price_change": 6.8, "description": "Dovish pivot"},
        
        # Options Expiry
        {"event_type": "options_expiry", "date": "2024-12-27", "impact": "mixed", "price_change": 2.1, "description": "Monthly options expiry"},
        {"event_type": "options_expiry", "date": "2024-11-29", "impact": "negative", "price_change": -4.2, "description": "Large OI expiry"},
        {"event_type": "options_expiry", "date": "2024-10-25", "impact": "positive", "price_change": 3.5, "description": "Monthly expiry"},
        {"event_type": "options_expiry", "date": "2024-09-27", "impact": "mixed", "price_change": -0.8, "description": "Quarterly expiry"},
        
        # ETF Events
        {"event_type": "etf_launch", "date": "2024-01-11", "impact": "positive", "price_change": 7.2, "description": "Spot BTC ETF approval"},
        {"event_type": "etf_launch", "date": "2024-07-23", "impact": "positive", "price_change": 5.1, "description": "Spot ETH ETF launch"},
        
        # Whale Activity
        {"event_type": "whale_accumulation", "date": "2024-10-15", "impact": "positive", "price_change": 12.5, "description": "Major accumulation phase"},
        {"event_type": "whale_distribution", "date": "2024-03-14", "impact": "negative", "price_change": -8.3, "description": "Post-ATH distribution"},
        {"event_type": "whale_accumulation", "date": "2023-10-01", "impact": "positive", "price_change": 25.0, "description": "Pre-ETF accumulation"},
        
        # Network Upgrades
        {"event_type": "network_upgrade", "date": "2024-03-13", "impact": "positive", "price_change": 4.2, "description": "Ethereum Dencun upgrade"},
        {"event_type": "network_upgrade", "date": "2022-09-15", "impact": "mixed", "price_change": -2.1, "description": "Ethereum Merge"},
        
        # DeFi Exploits
        {"event_type": "defi_exploit", "date": "2024-02-09", "impact": "negative", "price_change": -3.2, "description": "PlayDapp hack $290M"},
        {"event_type": "defi_exploit", "date": "2023-11-22", "impact": "negative", "price_change": -1.8, "description": "KyberSwap exploit $47M"},
        {"event_type": "defi_exploit", "date": "2023-07-30", "impact": "negative", "price_change": -2.5, "description": "Curve exploit $70M"},
        
        # Institutional Events
        {"event_type": "institutional_buy", "date": "2024-11-18", "impact": "positive", "price_change": 8.5, "description": "MicroStrategy buys 51K BTC"},
        {"event_type": "institutional_buy", "date": "2024-09-13", "impact": "positive", "price_change": 4.2, "description": "MicroStrategy buys 18K BTC"},
        
        # Regulatory Events
        {"event_type": "regulatory_action", "date": "2024-04-24", "impact": "negative", "price_change": -5.1, "description": "Samourai Wallet arrests"},
        {"event_type": "regulatory_action", "date": "2023-11-21", "impact": "mixed", "price_change": 1.2, "description": "Binance settlement"},
        
        # Regime Shifts
        {"event_type": "regime_shift", "date": "2024-10-01", "impact": "positive", "price_change": 15.0, "description": "Bear to bull transition"},
        {"event_type": "regime_shift", "date": "2024-04-15", "impact": "negative", "price_change": -12.0, "description": "Correction phase start"},
        {"event_type": "regime_shift", "date": "2023-01-01", "impact": "positive", "price_change": 40.0, "description": "Recovery phase start"},
        
        # Macro Events
        {"event_type": "macro_crisis", "date": "2023-03-10", "impact": "mixed", "price_change": 18.0, "description": "SVB collapse - BTC rallies"},
        {"event_type": "macro_crisis", "date": "2022-11-08", "impact": "negative", "price_change": -25.0, "description": "FTX collapse"},
    ]
    
    def __init__(self, db):
        self.db = db
        self.historical_events: List[HistoricalEvent] = []
        self.prediction_results: List[PredictionResult] = []
        self.event_type_accuracy: Dict[str, EventTypeAccuracy] = {}
        
        # Load historical events
        self._load_historical_events()
        
        logger.info("✅ Event Backtest Service initialized")
    
    def _load_historical_events(self):
        """Load historical events from database"""
        for event_data in self.HISTORICAL_EVENTS:
            # Calculate price change (simulated based on impact)
            base_price = 45000 if "2023" in event_data["date"] else 65000 if "2024" in event_data["date"] else 30000
            price_change = event_data["price_change"]
            
            event = HistoricalEvent(
                event_id=f"hist_{event_data['event_type']}_{event_data['date']}",
                event_type=event_data["event_type"],
                description=event_data["description"],
                occurred_date=event_data["date"],
                actual_impact=event_data["impact"],
                price_before=base_price,
                price_after=base_price * (1 + price_change / 100),
                price_change_pct=price_change,
                affected_coins=["BTC", "ETH"],
                source="historical_database"
            )
            self.historical_events.append(event)
    
    async def backtest_predictions(
        self,
        predictions: List[Dict],
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Backtest a list of predictions against historical events.
        
        Args:
            predictions: List of predicted events with event_type, predicted_date, probability, expected_impact
            start_date: Filter historical events from this date
            end_date: Filter historical events until this date
        
        Returns:
            Comprehensive backtest results with accuracy metrics
        """
        results = []
        now = datetime.now(timezone.utc)
        
        # Filter historical events by date range
        filtered_events = self.historical_events
        if start_date:
            filtered_events = [e for e in filtered_events if e.occurred_date >= start_date]
        if end_date:
            filtered_events = [e for e in filtered_events if e.occurred_date <= end_date]
        
        # Create lookup by event type
        events_by_type = defaultdict(list)
        for event in filtered_events:
            events_by_type[event.event_type].append(event)
        
        # Evaluate each prediction
        for pred in predictions:
            event_type = pred.get("event_type")
            predicted_date = pred.get("predicted_date", "")
            probability = pred.get("probability", 0.5)
            predicted_impact = pred.get("expected_impact", "mixed")
            
            # Find matching historical event
            matching_events = events_by_type.get(event_type, [])
            best_match = None
            best_date_diff = float('inf')
            
            for hist_event in matching_events:
                try:
                    pred_dt = datetime.strptime(predicted_date, "%Y-%m-%d")
                    actual_dt = datetime.strptime(hist_event.occurred_date, "%Y-%m-%d")
                    date_diff = abs((pred_dt - actual_dt).days)
                    
                    if date_diff < best_date_diff:
                        best_date_diff = date_diff
                        best_match = hist_event
                except:
                    continue
            
            # Calculate accuracy metrics
            if best_match and best_date_diff <= 30:  # Within 30 days is a match
                event_occurred = True
                date_accuracy = best_date_diff
                impact_correct = predicted_impact == best_match.actual_impact
                actual_impact = best_match.actual_impact
                actual_date = best_match.occurred_date
                
                # Score calculation
                date_score = max(0, 100 - date_accuracy * 3)  # Lose 3 points per day off
                impact_score = 100 if impact_correct else 30
                prob_score = probability * 100
                accuracy_score = (date_score * 0.3 + impact_score * 0.4 + prob_score * 0.3)
            else:
                # No matching event found
                event_occurred = False
                date_accuracy = None
                impact_correct = None
                actual_impact = None
                actual_date = None
                
                # Penalize false positive more if high probability
                accuracy_score = max(0, 50 - probability * 50)
            
            result = PredictionResult(
                prediction_id=pred.get("event_id", str(uuid.uuid4())),
                event_type=event_type,
                predicted_date=predicted_date,
                actual_date=actual_date,
                prediction_probability=probability,
                predicted_impact=predicted_impact,
                actual_impact=actual_impact,
                date_accuracy_days=date_accuracy,
                impact_correct=impact_correct,
                event_occurred=event_occurred,
                accuracy_score=accuracy_score,
                created_at=now.isoformat()
            )
            results.append(result)
            self.prediction_results.append(result)
        
        # Calculate aggregate metrics
        metrics = self._calculate_aggregate_metrics(results)
        
        # Save results to database
        for result in results:
            await self.db.prediction_results.insert_one(asdict(result))
        
        return {
            "status": "completed",
            "total_predictions": len(predictions),
            "total_historical_events": len(filtered_events),
            "results": [asdict(r) for r in results],
            "aggregate_metrics": metrics,
            "event_type_breakdown": self._get_event_type_breakdown(results),
            "recommendations": self._generate_recommendations(metrics)
        }
    
    def _calculate_aggregate_metrics(self, results: List[PredictionResult]) -> Dict[str, Any]:
        """Calculate aggregate accuracy metrics"""
        if not results:
            return {}
        
        total = len(results)
        true_positives = sum(1 for r in results if r.event_occurred and r.prediction_probability >= 0.5)
        false_positives = sum(1 for r in results if not r.event_occurred and r.prediction_probability >= 0.5)
        true_negatives = sum(1 for r in results if not r.event_occurred and r.prediction_probability < 0.5)
        false_negatives = sum(1 for r in results if r.event_occurred and r.prediction_probability < 0.5)
        
        # Precision and Recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Impact accuracy
        impact_predictions = [r for r in results if r.impact_correct is not None]
        impact_accuracy = sum(1 for r in impact_predictions if r.impact_correct) / len(impact_predictions) if impact_predictions else 0
        
        # Date accuracy (for matched events)
        date_accuracies = [r.date_accuracy_days for r in results if r.date_accuracy_days is not None]
        avg_date_accuracy = sum(date_accuracies) / len(date_accuracies) if date_accuracies else None
        
        # Overall accuracy score
        avg_accuracy_score = sum(r.accuracy_score for r in results) / total
        
        return {
            "total_predictions": total,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "impact_accuracy_pct": round(impact_accuracy * 100, 2),
            "avg_date_accuracy_days": round(avg_date_accuracy, 1) if avg_date_accuracy else None,
            "avg_accuracy_score": round(avg_accuracy_score, 2),
            "hit_rate": round(true_positives / total * 100, 2) if total > 0 else 0
        }
    
    def _get_event_type_breakdown(self, results: List[PredictionResult]) -> Dict[str, Dict]:
        """Get accuracy breakdown by event type"""
        by_type = defaultdict(list)
        for result in results:
            by_type[result.event_type].append(result)
        
        breakdown = {}
        for event_type, type_results in by_type.items():
            tp = sum(1 for r in type_results if r.event_occurred)
            fp = sum(1 for r in type_results if not r.event_occurred)
            impact_correct = sum(1 for r in type_results if r.impact_correct)
            
            dates = [r.date_accuracy_days for r in type_results if r.date_accuracy_days is not None]
            avg_date = sum(dates) / len(dates) if dates else None
            
            breakdown[event_type] = {
                "total_predictions": len(type_results),
                "events_occurred": tp,
                "false_alarms": fp,
                "hit_rate": round(tp / len(type_results) * 100, 2) if type_results else 0,
                "impact_accuracy": round(impact_correct / len(type_results) * 100, 2) if type_results else 0,
                "avg_date_accuracy_days": round(avg_date, 1) if avg_date else None,
                "avg_accuracy_score": round(sum(r.accuracy_score for r in type_results) / len(type_results), 2)
            }
        
        return breakdown
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on backtest results"""
        recommendations = []
        
        precision = metrics.get("precision", 0)
        recall = metrics.get("recall", 0)
        impact_accuracy = metrics.get("impact_accuracy_pct", 0)
        avg_date = metrics.get("avg_date_accuracy_days")
        
        if precision < 70:
            recommendations.append(
                "Precision is low - too many false positives. Consider increasing prediction thresholds "
                "or requiring more confirmation signals before generating alerts."
            )
        
        if recall < 70:
            recommendations.append(
                "Recall is low - missing many actual events. Consider adding more lead indicators "
                "or lowering detection thresholds for important event types."
            )
        
        if impact_accuracy < 60:
            recommendations.append(
                "Impact prediction accuracy is low. Consider using more market sentiment indicators "
                "and historical impact analysis to improve impact predictions."
            )
        
        if avg_date and avg_date > 7:
            recommendations.append(
                f"Average date prediction is {avg_date:.0f} days off. Consider using more precise "
                "scheduling data for recurring events (FOMC, options expiry)."
            )
        
        if metrics.get("f1_score", 0) > 80:
            recommendations.append(
                "✅ Overall prediction quality is excellent! Continue monitoring and fine-tuning."
            )
        
        if not recommendations:
            recommendations.append(
                "Performance is acceptable. Continue collecting data to improve predictions over time."
            )
        
        return recommendations
    
    async def get_historical_accuracy(self, event_type: str = None) -> Dict[str, Any]:
        """Get historical prediction accuracy"""
        results = self.prediction_results
        
        if event_type:
            results = [r for r in results if r.event_type == event_type]
        
        if not results:
            return {"message": "No prediction results available", "results": []}
        
        metrics = self._calculate_aggregate_metrics(results)
        breakdown = self._get_event_type_breakdown(results)
        
        return {
            "total_predictions_evaluated": len(results),
            "metrics": metrics,
            "event_type_breakdown": breakdown,
            "recommendations": self._generate_recommendations(metrics)
        }
    
    async def simulate_predictions(self, n_predictions: int = 50) -> Dict[str, Any]:
        """
        Generate simulated predictions and backtest them.
        Useful for demonstrating the system.
        """
        from services.adaptive_strategy_service import get_adaptive_strategy_service
        
        predictions = []
        event_types = [
            "bitcoin_halving", "fomc_meeting", "options_expiry", "whale_accumulation",
            "whale_distribution", "network_upgrade", "defi_exploit", "institutional_buy",
            "regulatory_action", "regime_shift", "etf_launch"
        ]
        
        # Generate predictions based on historical events
        for _ in range(n_predictions):
            # Pick a random historical event
            hist_event = random.choice(self.historical_events)
            
            # Create a prediction with some noise
            date_offset = random.randint(-10, 10)  # +/- 10 days
            try:
                base_date = datetime.strptime(hist_event.occurred_date, "%Y-%m-%d")
                pred_date = base_date + timedelta(days=date_offset)
            except:
                pred_date = datetime.now()
            
            # Add some randomness to impact prediction
            if random.random() < 0.75:  # 75% chance of correct impact
                pred_impact = hist_event.actual_impact
            else:
                pred_impact = random.choice(["positive", "negative", "mixed"])
            
            predictions.append({
                "event_id": f"sim_{random.randint(10000, 99999)}",
                "event_type": hist_event.event_type,
                "predicted_date": pred_date.strftime("%Y-%m-%d"),
                "probability": random.uniform(0.5, 0.95),
                "expected_impact": pred_impact
            })
        
        # Run backtest
        return await self.backtest_predictions(predictions)
    
    async def get_event_type_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each event type"""
        if not self.prediction_results:
            # Generate some simulated results first
            await self.simulate_predictions(100)
        
        breakdown = self._get_event_type_breakdown(self.prediction_results)
        
        # Rank event types by accuracy
        ranked = sorted(
            breakdown.items(),
            key=lambda x: x[1]["avg_accuracy_score"],
            reverse=True
        )
        
        return {
            "event_types": dict(ranked),
            "best_performing": ranked[0] if ranked else None,
            "worst_performing": ranked[-1] if ranked else None,
            "total_event_types": len(breakdown)
        }


# Import uuid for generating IDs
import uuid

# Singleton instance
_event_backtest_service = None


def get_event_backtest_service(db=None):
    """Get or create event backtest service instance"""
    global _event_backtest_service
    
    if _event_backtest_service is None and db is not None:
        _event_backtest_service = EventBacktestService(db)
    
    return _event_backtest_service
