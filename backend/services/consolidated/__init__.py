"""
Consolidated Services Package
=============================
This package provides a unified, simplified interface to all trading platform services.

Instead of 141+ individual services, we now have 10 consolidated services:
1. ExchangeService - All exchange/Kraken operations
2. AIService - AI predictions and explanations
3. AnalysisService - Technical analysis and indicators
4. SentimentService - News, social, fear/greed
5. TradingService - Trading execution and risk
6. MLService - Machine learning training/inference
7. DataService - Market data and OHLCV
8. StrategyService - Trading strategies and backtesting
9. NotificationService - Alerts and notifications
10. SystemService - Health, backups, monitoring

Usage:
    from services.consolidated import ServiceRegistry
    
    registry = ServiceRegistry(db)
    
    # Access services
    price = await registry.exchange.get_price("BTC")
    prediction = await registry.ai.get_prediction("BTC")
    analysis = await registry.analysis.quick_analysis("BTC", prices)
"""

from .exchange_service import ExchangeService, get_exchange_service
from .ai_service import AIService, get_ai_service
from .analysis_service import AnalysisService, get_analysis_service
from .sentiment_service import SentimentService, get_sentiment_service
from .trading_service import TradingService, get_trading_service
from .ml_service import MLService, get_ml_service
from .data_service import DataService, get_data_service
from .strategy_service import StrategyService, get_strategy_service
from .notification_service import NotificationService, get_notification_service
from .system_service import SystemService, get_system_service

__all__ = [
    # Services
    'ExchangeService',
    'AIService',
    'AnalysisService',
    'SentimentService',
    'TradingService',
    'MLService',
    'DataService',
    'StrategyService',
    'NotificationService',
    'SystemService',
    
    # Getters
    'get_exchange_service',
    'get_ai_service',
    'get_analysis_service',
    'get_sentiment_service',
    'get_trading_service',
    'get_ml_service',
    'get_data_service',
    'get_strategy_service',
    'get_notification_service',
    'get_system_service',
    
    # Registry
    'ServiceRegistry',
    'get_service_registry'
]


class ServiceRegistry:
    """
    Central registry for all consolidated services.
    Provides lazy-loaded access to all platform functionality.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._services = {}
    
    @property
    def exchange(self) -> ExchangeService:
        """Exchange operations (Kraken, orders, portfolio)"""
        if 'exchange' not in self._services:
            self._services['exchange'] = get_exchange_service(self.db)
        return self._services['exchange']
    
    @property
    def ai(self) -> AIService:
        """AI predictions and explanations"""
        if 'ai' not in self._services:
            self._services['ai'] = get_ai_service(self.db)
        return self._services['ai']
    
    @property
    def analysis(self) -> AnalysisService:
        """Technical analysis and indicators"""
        if 'analysis' not in self._services:
            self._services['analysis'] = get_analysis_service(self.db)
        return self._services['analysis']
    
    @property
    def sentiment(self) -> SentimentService:
        """Sentiment analysis (news, social, fear/greed)"""
        if 'sentiment' not in self._services:
            self._services['sentiment'] = get_sentiment_service(self.db)
        return self._services['sentiment']
    
    @property
    def trading(self) -> TradingService:
        """Trading execution and risk management"""
        if 'trading' not in self._services:
            self._services['trading'] = get_trading_service(self.db)
        return self._services['trading']
    
    @property
    def ml(self) -> MLService:
        """Machine learning training and inference"""
        if 'ml' not in self._services:
            self._services['ml'] = get_ml_service(self.db)
        return self._services['ml']
    
    @property
    def data(self) -> DataService:
        """Market data and OHLCV"""
        if 'data' not in self._services:
            self._services['data'] = get_data_service(self.db)
        return self._services['data']
    
    @property
    def strategy(self) -> StrategyService:
        """Trading strategies and backtesting"""
        if 'strategy' not in self._services:
            self._services['strategy'] = get_strategy_service(self.db)
        return self._services['strategy']
    
    @property
    def notification(self) -> NotificationService:
        """Notifications and alerts"""
        if 'notification' not in self._services:
            self._services['notification'] = get_notification_service(self.db)
        return self._services['notification']
    
    @property
    def system(self) -> SystemService:
        """System health, backups, monitoring"""
        if 'system' not in self._services:
            self._services['system'] = get_system_service(self.db)
        return self._services['system']
    
    def get_all_status(self) -> dict:
        """Get status of all services"""
        return {
            'exchange': self.exchange.get_status(),
            'ai': self.ai.get_status(),
            'analysis': self.analysis.get_status(),
            'sentiment': self.sentiment.get_status(),
            'trading': self.trading.get_status(),
            'ml': self.ml.get_status(),
            'data': self.data.get_status(),
            'strategy': self.strategy.get_status(),
            'notification': self.notification.get_status(),
            'system': self.system.get_status(),
        }


# Singleton registry
_registry = None

def get_service_registry(db=None) -> ServiceRegistry:
    """Get or create service registry singleton"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry(db)
    return _registry
