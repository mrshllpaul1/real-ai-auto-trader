"""
Scheduler Services Initialization Module
Handles initialization of scheduler and automation services
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def init_scheduler_services(
    db: AsyncIOMotorDatabase,
    core_services: dict,
    ai_services: dict
) -> dict:
    """
    Initialize scheduler and automation services
    
    Args:
        db: MongoDB database connection
        core_services: Dictionary of core services
        ai_services: Dictionary of AI services
        
    Returns:
        Dictionary of scheduler services
    """
    services = {}
    
    # Historical Trainers
    from services.historical_trainer import HistoricalTrainer
    from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
    services['historical_trainer'] = HistoricalTrainer(db)
    services['enhanced_trainer'] = EnhancedHistoricalTrainer(db)
    logger.info("✅ Historical Trainers initialized")
    
    # Scheduler Service
    from services.scheduler_service import SchedulerService
    services['scheduler'] = SchedulerService(
        db=db,
        growth_engine=core_services['growth_engine'],
        automated_trader=core_services['automated_trader'],
        alert_service=core_services['alert_service']
    )
    services['scheduler'].set_trainers(
        services['historical_trainer'],
        services['enhanced_trainer']
    )
    logger.info("✅ Scheduler Service initialized")
    
    # Stop-Loss Automation
    from services.stop_loss_automation import get_stop_loss_automation
    services['stop_loss'] = get_stop_loss_automation(
        db=db,
        kraken_service=core_services['kraken'],
        isolated_portfolio=core_services['isolated_portfolio'],
        alert_service=core_services['alert_service']
    )
    services['scheduler'].set_stop_loss_automation(services['stop_loss'])
    
    # Add stop-loss check job (every 5 minutes)
    await services['scheduler'].add_stop_loss_job(interval_minutes=5)
    logger.info("✅ Stop-Loss Automation initialized (checking every 5 minutes)")
    
    # Background Task Manager
    from services.background_tasks import get_task_manager
    services['task_manager'] = get_task_manager(db)
    logger.info("✅ Background Task Manager initialized")
    
    # Update automated trader with task manager
    core_services['automated_trader'].task_manager = services['task_manager']
    
    return services


async def init_universe_services(
    db: AsyncIOMotorDatabase,
    core_services: dict,
    data_services: dict
) -> dict:
    """
    Initialize universe and discovery services
    
    Args:
        db: MongoDB database connection
        core_services: Dictionary of core services
        data_services: Dictionary of data services
        
    Returns:
        Dictionary of universe services
    """
    services = {}
    
    # Event Triggers Service
    from services.event_triggers import get_event_trigger_service
    services['event_triggers'] = get_event_trigger_service(
        db=db,
        coindesk_service=data_services['coindesk'],
        correlation_engine=data_services['correlation_engine'],
        kraken_service=core_services['kraken'],
        alert_service=core_services['alert_service']
    )
    logger.info("✅ Event Trigger Service initialized")
    
    # Kraken Universe Service
    from services.kraken_universe import get_kraken_universe
    services['kraken_universe'] = get_kraken_universe(db)
    logger.info("✅ Kraken Universe Service initialized")
    
    # CoinDesk Universe Service
    from services.coindesk_universe import get_coindesk_universe
    services['coindesk_universe'] = get_coindesk_universe(db)
    logger.info("✅ CoinDesk Universe Service initialized")
    
    # Dynamic Coin Universe
    from services.dynamic_coin_universe import get_dynamic_universe
    services['dynamic_universe'] = get_dynamic_universe(db)
    logger.info("✅ Dynamic Coin Universe initialized")
    
    return services


async def init_additional_services(
    db: AsyncIOMotorDatabase,
    core_services: dict,
    ai_services: dict
) -> dict:
    """
    Initialize additional/optional services
    
    Args:
        db: MongoDB database connection
        core_services: Dictionary of core services
        ai_services: Dictionary of AI services
        
    Returns:
        Dictionary of additional services
    """
    services = {}
    
    # Custom Strategy Builder
    from services.custom_strategy_builder import get_strategy_builder
    services['strategy_builder'] = get_strategy_builder(db)
    logger.info("✅ Custom Strategy Builder initialized")
    
    # Push Notification Service
    from services.push_notification_service import get_push_service
    services['push_notifications'] = get_push_service(db)
    core_services['automated_trader'].notification_service = services['push_notifications']
    logger.info("✅ Push Notification Service initialized")
    
    # CryptoPanic Service
    try:
        from services.cryptopanic_service import get_cryptopanic_service
        services['cryptopanic'] = get_cryptopanic_service()
        logger.info("✅ CryptoPanic service initialized")
    except Exception as e:
        logger.warning(f"CryptoPanic service not available: {e}")
    
    return services
