"""
Performance Optimization Service
Provides utilities for improving app performance during training and general operations
"""

import asyncio
import gc
import psutil
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps
import time

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and report system performance metrics"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.metrics_history = []
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()
            
            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def log_metrics(self, operation: str = ""):
        """Log current performance metrics"""
        metrics = self.get_current_metrics()
        if operation:
            logger.info(f"Performance [{operation}]: CPU={metrics.get('cpu_percent', 0)}%, Memory={metrics.get('memory_mb', 0)}MB")
        return metrics


class MemoryOptimizer:
    """Optimize memory usage during long-running operations"""
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection to free memory"""
        gc.collect()
        logger.debug("Forced garbage collection")
    
    @staticmethod
    def clear_cache(cache_obj):
        """Clear cache object if it has a clear method"""
        if hasattr(cache_obj, 'clear'):
            cache_obj.clear()
            logger.debug(f"Cleared cache: {type(cache_obj).__name__}")
    
    @staticmethod
    async def periodic_cleanup(interval_seconds: int = 300):
        """Run periodic memory cleanup"""
        while True:
            await asyncio.sleep(interval_seconds)
            MemoryOptimizer.force_garbage_collection()
            logger.info("Periodic memory cleanup completed")


class BatchProcessor:
    """Process large datasets in batches to avoid memory issues"""
    
    @staticmethod
    async def process_in_batches(
        items: list,
        batch_size: int,
        process_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> list:
        """
        Process items in batches
        
        Args:
            items: List of items to process
            batch_size: Number of items per batch
            process_func: Async function to process each batch
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of all results
        """
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            # Process batch
            batch_results = await process_func(batch)
            results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
            
            # Progress callback
            if progress_callback:
                await progress_callback({
                    "batch": batch_num,
                    "total_batches": total_batches,
                    "progress": (batch_num / total_batches) * 100,
                    "items_processed": i + len(batch)
                })
            
            # Force GC after each batch to free memory
            if batch_num % 5 == 0:  # Every 5 batches
                MemoryOptimizer.force_garbage_collection()
        
        return results
    
    @staticmethod
    def chunk_list(items: list, chunk_size: int) -> list:
        """Split list into chunks"""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


class AsyncTrainingOptimizer:
    """Optimize training operations for better performance"""
    
    @staticmethod
    def training_task(task_name: str = ""):
        """Decorator for training tasks with performance monitoring"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                monitor = PerformanceMonitor()
                start_metrics = monitor.get_current_metrics()
                
                logger.info(f"Starting training task: {task_name or func.__name__}")
                logger.info(f"Initial metrics: CPU={start_metrics.get('cpu_percent')}%, Memory={start_metrics.get('memory_mb')}MB")
                
                try:
                    # Run the training function
                    result = await func(*args, **kwargs)
                    
                    # Log completion metrics
                    end_metrics = monitor.get_current_metrics()
                    duration = time.time() - time.time()
                    
                    logger.info(f"Completed training task: {task_name or func.__name__}")
                    logger.info(f"Final metrics: CPU={end_metrics.get('cpu_percent')}%, Memory={end_metrics.get('memory_mb')}MB")
                    
                    # Force garbage collection
                    MemoryOptimizer.force_garbage_collection()
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Training task failed: {task_name or func.__name__}: {e}")
                    raise
                    
            return wrapper
        return decorator
    
    @staticmethod
    async def incremental_training(
        data_loader,
        model,
        batch_size: int = 32,
        checkpoint_every: int = 10,
        save_checkpoint_func: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Train model incrementally with checkpoints
        
        Args:
            data_loader: Generator or iterable of training data
            model: Model to train
            batch_size: Batch size for training
            checkpoint_every: Save checkpoint every N batches
            save_checkpoint_func: Function to save checkpoints
            progress_callback: Callback for progress updates
        """
        batch_num = 0
        
        async for batch_data in data_loader:
            batch_num += 1
            
            # Train on batch
            loss = await model.train_on_batch(batch_data)
            
            # Checkpoint
            if checkpoint_every and batch_num % checkpoint_every == 0:
                if save_checkpoint_func:
                    await save_checkpoint_func(model, batch_num)
                    logger.info(f"Checkpoint saved at batch {batch_num}")
                
                # Memory cleanup
                MemoryOptimizer.force_garbage_collection()
            
            # Progress update
            if progress_callback and batch_num % 5 == 0:
                await progress_callback({
                    "batch": batch_num,
                    "loss": loss,
                    "timestamp": datetime.utcnow().isoformat()
                })


class DatabaseQueryOptimizer:
    """Optimize database queries for better performance"""
    
    @staticmethod
    def optimize_aggregation(pipeline: list) -> list:
        """
        Optimize MongoDB aggregation pipeline
        
        Args:
            pipeline: Original aggregation pipeline
        
        Returns:
            Optimized pipeline
        """
        optimized = []
        
        # Add $match stages early to reduce document count
        match_stages = [stage for stage in pipeline if '$match' in stage]
        other_stages = [stage for stage in pipeline if '$match' not in stage]
        
        # Match first, then other operations
        optimized.extend(match_stages)
        optimized.extend(other_stages)
        
        # Add $project to limit fields early if not present
        has_project = any('$project' in stage for stage in optimized)
        if not has_project and len(optimized) > 1:
            # Add after first stage to reduce data transfer
            logger.debug("Adding $project stage for optimization")
        
        return optimized
    
    @staticmethod
    def add_batch_size_hint(cursor, batch_size: int = 1000):
        """Add batch size hint to cursor for better performance"""
        return cursor.batch_size(batch_size)
    
    @staticmethod
    async def fetch_in_batches(collection, query: dict, batch_size: int = 1000):
        """Fetch large result sets in batches"""
        cursor = collection.find(query).batch_size(batch_size)
        results = []
        
        async for document in cursor:
            results.append(document)
            
            # Yield control every batch_size documents
            if len(results) % batch_size == 0:
                await asyncio.sleep(0)  # Yield to event loop
        
        return results


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return _performance_monitor


# Start periodic cleanup task
async def start_periodic_cleanup(interval: int = 300):
    """Start periodic memory cleanup task"""
    asyncio.create_task(MemoryOptimizer.periodic_cleanup(interval))
    logger.info(f"Started periodic memory cleanup (every {interval}s)")
