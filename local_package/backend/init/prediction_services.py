"""
Prediction Services Initialization Module
Handles initialization of the 8 prediction enhancement services
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def init_prediction_services(db: AsyncIOMotorDatabase, task_manager) -> dict:
    """
    Initialize all 8 prediction enhancement services
    
    Args:
        db: MongoDB database connection
        task_manager: Background task manager for async operations
        
    Returns:
        Dictionary of prediction services
    """
    services = {}
    
    # #1: Order Book Analyzer
    from services.order_book_analyzer import get_order_book_analyzer
    services['order_book'] = get_order_book_analyzer(db)
    logger.info("  ✅ #1 Order Book Analyzer initialized")
    
    # #2: On-Chain Analytics
    from services.on_chain_analytics import get_on_chain_analytics
    services['on_chain'] = get_on_chain_analytics(db)
    logger.info("  ✅ #2 On-Chain Analytics initialized")
    
    # #3: Social Sentiment Pipeline
    from services.social_sentiment_pipeline import get_social_sentiment
    services['social'] = get_social_sentiment(db)
    logger.info("  ✅ #3 Social Sentiment Pipeline initialized")
    
    # #4: Transformer Predictor
    from services.transformer_predictor import get_transformer_predictor
    services['transformer'] = get_transformer_predictor(db)
    logger.info("  ✅ #4 Transformer Predictor initialized")
    
    # #5: RL Trading Agent
    from services.rl_trading_agent import get_rl_agent
    services['rl_agent'] = get_rl_agent(db)
    services['rl_agent'].set_task_manager(task_manager)
    logger.info("  ✅ #5 RL Trading Agent initialized")
    
    # #6: Cross-Asset Correlation
    from services.cross_asset_correlation import get_cross_asset_correlation
    services['cross_asset'] = get_cross_asset_correlation(db)
    logger.info("  ✅ #6 Cross-Asset Correlation initialized")
    
    # #7 & #8: Advanced Technical Analysis (Volatility & Momentum)
    from services.advanced_technical_analysis import get_advanced_ta
    services['advanced_ta'] = get_advanced_ta(db)
    logger.info("  ✅ #7-8 Advanced Technical Analysis initialized")
    
    logger.info("✅ Prediction Enhancements initialized (8 services)")
    
    return services


def inject_prediction_services(automated_trader, prediction_services: dict):
    """
    Inject prediction services into the automated trader
    
    Args:
        automated_trader: The automated trading service
        prediction_services: Dictionary of prediction services
    """
    automated_trader.prediction_services = {
        'order_book': prediction_services['order_book'],
        'on_chain': prediction_services['on_chain'],
        'social': prediction_services['social'],
        'transformer': prediction_services['transformer'],
        'rl_agent': prediction_services['rl_agent'],
        'cross_asset': prediction_services['cross_asset'],
        'advanced_ta': prediction_services['advanced_ta']
    }
    logger.info("✅ Automated Trader updated with Prediction Enhancement Services")
