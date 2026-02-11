"""
Enhanced Training Wrapper
Wraps existing training functions with performance optimizations
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from datetime import datetime

from services.performance_optimizer import (
    AsyncTrainingOptimizer,
    BatchProcessor,
    MemoryOptimizer,
    get_performance_monitor
)
from services.training_progress_manager import get_progress_manager

logger = logging.getLogger(__name__)


def optimized_training(
    task_type: str = "training",
    batch_size: int = 100,
    checkpoint_interval: int = 10
):
    """
    Decorator to optimize training functions with:
    - Performance monitoring
    - Batch processing
    - Memory management
    - Progress tracking
    - Automatic checkpointing
    
    Args:
        task_type: Type of training task
        batch_size: Number of items to process per batch
        checkpoint_interval: Save checkpoint every N batches
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate task ID
            task_id = f"{task_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Get progress manager
            progress_manager = get_progress_manager()
            
            # Get performance monitor
            perf_monitor = get_performance_monitor()
            
            # Create training task
            task = progress_manager.create_task(
                task_id=task_id,
                task_type=task_type,
                total_items=kwargs.get('total_items', 0)
            )
            
            # Start task
            await progress_manager.start_task(task_id, f"Starting {task_type}...")
            
            # Log initial metrics
            start_metrics = perf_monitor.get_current_metrics()
            logger.info(f"Training started: {task_type}")
            logger.info(f"Initial: CPU={start_metrics.get('cpu_percent')}%, Memory={start_metrics.get('memory_mb')}MB")
            
            try:
                # Execute training function
                result = await func(*args, **kwargs)
                
                # Mark as completed
                await progress_manager.complete_task(
                    task_id,
                    result=result,
                    message=f"{task_type} completed successfully"
                )
                
                # Log completion metrics
                end_metrics = perf_monitor.get_current_metrics()
                logger.info(f"Training completed: {task_type}")
                logger.info(f"Final: CPU={end_metrics.get('cpu_percent')}%, Memory={end_metrics.get('memory_mb')}MB")
                
                # Force garbage collection
                MemoryOptimizer.force_garbage_collection()
                
                return result
                
            except Exception as e:
                # Mark as failed
                await progress_manager.fail_task(
                    task_id,
                    error=str(e),
                    message=f"{task_type} failed"
                )
                
                logger.error(f"Training failed: {task_type}: {e}")
                raise
                
        return wrapper
    return decorator


async def batch_train_models(
    items: List[Any],
    train_func: Callable,
    batch_size: int = 10,
    progress_callback: Optional[Callable] = None
) -> List[Any]:
    """
    Train models in batches to manage memory and provide progress updates
    
    Args:
        items: List of items to train on (coins, datasets, etc.)
        train_func: Async training function
        batch_size: Items per batch
        progress_callback: Optional callback for progress updates
    
    Returns:
        List of training results
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    logger.info(f"Starting batch training: {len(items)} items, {total_batches} batches")
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches}")
        
        # Train batch
        batch_results = await train_func(batch)
        results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
        
        # Progress callback
        if progress_callback:
            await progress_callback({
                "batch": batch_num,
                "total_batches": total_batches,
                "progress": (batch_num / total_batches) * 100,
                "items_processed": i + len(batch),
                "total_items": len(items)
            })
        
        # Memory cleanup every 5 batches
        if batch_num % 5 == 0:
            logger.info(f"Running memory cleanup after batch {batch_num}")
            MemoryOptimizer.force_garbage_collection()
            await asyncio.sleep(0.1)  # Brief pause to let GC complete
    
    logger.info(f"Batch training completed: {len(results)} results")
    return results


async def incremental_model_training(
    data_generator,
    model,
    epochs: int = 10,
    checkpoint_func: Optional[Callable] = None,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Train model incrementally with checkpoints and progress tracking
    
    Args:
        data_generator: Generator yielding training batches
        model: Model to train
        epochs: Number of training epochs
        checkpoint_func: Function to save checkpoints
        progress_callback: Callback for progress updates
    
    Returns:
        Training results
    """
    results = {
        "epochs_completed": 0,
        "total_batches": 0,
        "avg_loss": 0,
        "checkpoints_saved": 0
    }
    
    total_loss = 0
    batch_count = 0
    
    for epoch in range(epochs):
        logger.info(f"Starting epoch {epoch + 1}/{epochs}")
        epoch_loss = 0
        epoch_batches = 0
        
        async for batch_data in data_generator:
            batch_count += 1
            epoch_batches += 1
            
            # Train on batch
            if hasattr(model, 'train_on_batch'):
                loss = await model.train_on_batch(batch_data)
            else:
                # Fallback for models without train_on_batch
                loss = await model.fit(batch_data, epochs=1, verbose=0)
                loss = loss.history['loss'][0] if hasattr(loss, 'history') else 0
            
            epoch_loss += loss
            total_loss += loss
            
            # Checkpoint every 10 batches
            if checkpoint_func and batch_count % 10 == 0:
                await checkpoint_func(model, epoch, batch_count)
                results["checkpoints_saved"] += 1
                logger.info(f"Checkpoint saved at epoch {epoch + 1}, batch {batch_count}")
            
            # Progress update
            if progress_callback and batch_count % 5 == 0:
                await progress_callback({
                    "epoch": epoch + 1,
                    "total_epochs": epochs,
                    "batch": batch_count,
                    "avg_loss": total_loss / batch_count,
                    "current_loss": loss
                })
            
            # Memory cleanup every 20 batches
            if batch_count % 20 == 0:
                MemoryOptimizer.force_garbage_collection()
        
        results["epochs_completed"] = epoch + 1
        
        # Log epoch stats
        avg_epoch_loss = epoch_loss / epoch_batches if epoch_batches > 0 else 0
        logger.info(f"Epoch {epoch + 1} completed: avg_loss={avg_epoch_loss:.4f}")
    
    results["total_batches"] = batch_count
    results["avg_loss"] = total_loss / batch_count if batch_count > 0 else 0
    
    return results


class OptimizedTrainingService:
    """Service providing optimized training operations"""
    
    def __init__(self, db):
        self.db = db
        self.perf_monitor = get_performance_monitor()
        self.progress_manager = get_progress_manager()
    
    async def train_with_monitoring(
        self,
        train_func: Callable,
        task_name: str,
        items: List[Any] = None,
        batch_size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute training with full monitoring and optimization
        
        Args:
            train_func: Training function to execute
            task_name: Name of the training task
            items: Optional list of items to train on
            batch_size: Batch size if items are provided
            **kwargs: Additional arguments for train_func
        
        Returns:
            Training results with performance metrics
        """
        # Create task
        task_id = f"{task_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        task = self.progress_manager.create_task(
            task_id=task_id,
            task_type=task_name,
            total_items=len(items) if items else 0
        )
        
        # Start monitoring
        await self.progress_manager.start_task(task_id, f"Starting {task_name}...")
        start_metrics = self.perf_monitor.get_current_metrics()
        start_time = datetime.utcnow()
        
        try:
            # Execute with or without batching
            if items and batch_size:
                async def progress_update(update):
                    await self.progress_manager.update_progress(
                        task_id,
                        progress=int(update.get("progress", 0)),
                        message=f"Batch {update.get('batch', 0)}/{update.get('total_batches', 0)}"
                    )
                
                result = await batch_train_models(
                    items=items,
                    train_func=train_func,
                    batch_size=batch_size,
                    progress_callback=progress_update
                )
            else:
                result = await train_func(**kwargs)
            
            # Calculate metrics
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            end_metrics = self.perf_monitor.get_current_metrics()
            
            # Complete task
            await self.progress_manager.complete_task(
                task_id,
                result={
                    "success": True,
                    "duration_seconds": duration,
                    "memory_used_mb": end_metrics.get("memory_mb", 0),
                    "result": result
                },
                message=f"{task_name} completed in {duration:.1f}s"
            )
            
            # Cleanup
            MemoryOptimizer.force_garbage_collection()
            
            return {
                "success": True,
                "task_id": task_id,
                "duration_seconds": duration,
                "memory_start_mb": start_metrics.get("memory_mb", 0),
                "memory_end_mb": end_metrics.get("memory_mb", 0),
                "result": result
            }
            
        except Exception as e:
            await self.progress_manager.fail_task(
                task_id,
                error=str(e),
                message=f"{task_name} failed: {str(e)}"
            )
            logger.error(f"Training failed: {task_name}: {e}", exc_info=True)
            raise


# Singleton instance
_training_service = None

def get_optimized_training_service(db):
    """Get or create optimized training service"""
    global _training_service
    if _training_service is None:
        _training_service = OptimizedTrainingService(db)
    return _training_service
