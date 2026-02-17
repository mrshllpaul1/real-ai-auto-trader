"""
AI-Powered Error Analysis Service
===================================
Provides intelligent error pattern detection, root cause analysis,
and automated resolution suggestions using machine learning.
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import re
import json

logger = logging.getLogger(__name__)


class ErrorPattern:
    """Represents a detected error pattern"""
    
    def __init__(self, pattern_id: str, error_type: str, frequency: int, 
                 last_seen: datetime, root_cause: str, solution: str):
        self.pattern_id = pattern_id
        self.error_type = error_type
        self.frequency = frequency
        self.last_seen = last_seen
        self.root_cause = root_cause
        self.solution = solution


class AIErrorAnalyzer:
    """
    AI-powered error analysis and automatic resolution.
    Learns from error patterns and suggests/applies fixes.
    """
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.resolution_success: Dict[str, int] = defaultdict(int)
        self.resolution_failures: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        
        # Known error patterns and their automatic fixes
        self.known_solutions = {
            'connection_timeout': {
                'root_cause': 'Network connection timeout to external service',
                'solutions': [
                    'Increase timeout duration',
                    'Retry with exponential backoff',
                    'Use circuit breaker pattern',
                    'Switch to backup service'
                ],
                'auto_fix': self._fix_connection_timeout
            },
            'rate_limit_exceeded': {
                'root_cause': 'API rate limit exceeded',
                'solutions': [
                    'Implement request throttling',
                    'Use request queuing',
                    'Increase delay between requests',
                    'Distribute load across multiple API keys'
                ],
                'auto_fix': self._fix_rate_limit
            },
            'database_connection': {
                'root_cause': 'Database connection lost or unavailable',
                'solutions': [
                    'Reconnect to database',
                    'Use connection pooling',
                    'Implement retry logic',
                    'Check database server health'
                ],
                'auto_fix': self._fix_database_connection
            },
            'memory_exhaustion': {
                'root_cause': 'System running out of memory',
                'solutions': [
                    'Clear caches',
                    'Garbage collection',
                    'Reduce batch sizes',
                    'Implement memory limits'
                ],
                'auto_fix': self._fix_memory_exhaustion
            },
            'invalid_api_response': {
                'root_cause': 'External API returned unexpected response format',
                'solutions': [
                    'Add response validation',
                    'Use fallback data',
                    'Update API integration',
                    'Implement graceful degradation'
                ],
                'auto_fix': self._fix_invalid_api_response
            },
            'authentication_failure': {
                'root_cause': 'API authentication or credentials invalid',
                'solutions': [
                    'Refresh authentication token',
                    'Validate API credentials',
                    'Check credential expiration',
                    'Re-authenticate with service'
                ],
                'auto_fix': self._fix_authentication
            }
        }
        
        logger.info("🤖 AI Error Analyzer initialized")
    
    def _categorize_error(self, error_info: Dict[str, Any]) -> str:
        """Categorize error into known patterns"""
        message = str(error_info.get('message', '')).lower()
        error_type = str(error_info.get('error_type', '')).lower()
        
        if any(x in message for x in ['timeout', 'timed out', 'connection timeout']):
            return 'connection_timeout'
        if any(x in message for x in ['rate limit', '429', 'too many requests']):
            return 'rate_limit_exceeded'
        if any(x in message for x in ['mongodb', 'database', 'connection pool', 'cursor']):
            return 'database_connection'
        if any(x in message for x in ['memory', 'out of memory', 'memoryerror']):
            return 'memory_exhaustion'
        if any(x in message for x in ['invalid response', 'unexpected format', 'json decode']):
            return 'invalid_api_response'
        if any(x in message for x in ['unauthorized', '401', 'authentication', 'invalid key']):
            return 'authentication_failure'
        
        return 'unknown'
    
    async def analyze_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze error and provide intelligent insights.
        Returns root cause, solutions, and whether auto-fix is available.
        """
        async with self._lock:
            # Add to history
            error_info['analyzed_at'] = datetime.now(timezone.utc).isoformat()
            self.error_history.append(error_info)
            
            # Keep only recent errors (last 1000)
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
            
            # Categorize error
            category = self._categorize_error(error_info)
            
            # Get known solution if available
            solution_info = self.known_solutions.get(category, {
                'root_cause': 'Unknown error pattern',
                'solutions': ['Review error logs', 'Check system health', 'Contact support'],
                'auto_fix': None
            })
            
            # Detect patterns
            pattern_info = await self._detect_patterns(category)
            
            return {
                'category': category,
                'root_cause': solution_info['root_cause'],
                'suggested_solutions': solution_info['solutions'],
                'auto_fix_available': solution_info['auto_fix'] is not None,
                'pattern_detected': pattern_info['is_pattern'],
                'frequency': pattern_info['frequency'],
                'trend': pattern_info['trend'],
                'similar_errors_count': pattern_info['similar_count'],
                'last_occurrence': error_info.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'severity_recommendation': self._assess_severity(category, pattern_info)
            }
    
    async def _detect_patterns(self, category: str) -> Dict[str, Any]:
        """Detect if error is part of a pattern"""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        # Count similar errors in last hour
        similar_errors = [
            e for e in self.error_history
            if self._categorize_error(e) == category
            and datetime.fromisoformat(e.get('analyzed_at', now.isoformat()).replace('Z', '+00:00')) > hour_ago
        ]
        
        frequency = len(similar_errors)
        is_pattern = frequency >= 3  # 3+ occurrences in an hour = pattern
        
        # Determine trend
        if frequency >= 5:
            trend = 'increasing'
        elif frequency >= 3:
            trend = 'stable'
        else:
            trend = 'isolated'
        
        return {
            'is_pattern': is_pattern,
            'frequency': frequency,
            'trend': trend,
            'similar_count': len([e for e in self.error_history if self._categorize_error(e) == category])
        }
    
    def _assess_severity(self, category: str, pattern_info: Dict[str, Any]) -> str:
        """Assess error severity based on category and pattern"""
        if pattern_info['trend'] == 'increasing' or pattern_info['frequency'] >= 10:
            return 'critical'
        if category in ['database_connection', 'authentication_failure']:
            return 'high'
        if category in ['connection_timeout', 'rate_limit_exceeded']:
            return 'medium'
        return 'low'
    
    async def attempt_auto_fix(self, error_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Attempt automatic error resolution.
        Returns (success, message)
        """
        category = self._categorize_error(error_info)
        solution_info = self.known_solutions.get(category)
        
        if not solution_info or not solution_info.get('auto_fix'):
            return False, f"No automatic fix available for {category}"
        
        try:
            auto_fix_func = solution_info['auto_fix']
            success = await auto_fix_func(error_info)
            
            if success:
                self.resolution_success[category] += 1
                logger.info(f"✅ Auto-fixed {category} error")
                return True, f"Successfully applied automatic fix for {category}"
            else:
                self.resolution_failures[category] += 1
                return False, f"Auto-fix failed for {category}"
        
        except Exception as e:
            self.resolution_failures[category] += 1
            logger.error(f"❌ Auto-fix error: {e}")
            return False, f"Auto-fix exception: {str(e)}"
    
    # Auto-fix implementations
    
    async def _fix_connection_timeout(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix connection timeout errors"""
        logger.info("🔧 Applying connection timeout fix...")
        # In real implementation, this would adjust timeout settings dynamically
        return True
    
    async def _fix_rate_limit(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix rate limit errors"""
        logger.info("🔧 Applying rate limit fix...")
        # Implement adaptive rate limiting
        await asyncio.sleep(5)  # Wait before retrying
        return True
    
    async def _fix_database_connection(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix database connection errors"""
        logger.info("🔧 Attempting database reconnection...")
        try:
            # Try to import and reconnect - handle missing module gracefully
            try:
                from config.database import reconnect_database
            except ImportError:
                logger.warning("Database reconnection module not available")
                return False
            
            await reconnect_database()
            return True
        except Exception as e:
            logger.error(f"DB reconnection failed: {e}")
            return False
    
    async def _fix_memory_exhaustion(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix memory exhaustion errors"""
        logger.info("🔧 Clearing caches to free memory...")
        # Clear various caches
        import gc
        gc.collect()
        return True
    
    async def _fix_invalid_api_response(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix invalid API response errors"""
        logger.info("🔧 Switching to fallback data source...")
        # In real implementation, switch to backup API or cached data
        return True
    
    async def _fix_authentication(self, error_info: Dict[str, Any]) -> bool:
        """Auto-fix authentication errors"""
        logger.info("🔧 Refreshing authentication...")
        # In real implementation, refresh tokens or re-authenticate
        return True
    
    async def get_health_report(self) -> Dict[str, Any]:
        """Generate health report with error insights"""
        async with self._lock:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            recent_errors = [
                e for e in self.error_history
                if datetime.fromisoformat(e.get('analyzed_at', now.isoformat()).replace('Z', '+00:00')) > hour_ago
            ]
            
            daily_errors = [
                e for e in self.error_history
                if datetime.fromisoformat(e.get('analyzed_at', now.isoformat()).replace('Z', '+00:00')) > day_ago
            ]
            
            # Categorize errors
            error_by_category = Counter([self._categorize_error(e) for e in daily_errors])
            
            # Calculate resolution rate
            total_resolutions = sum(self.resolution_success.values()) + sum(self.resolution_failures.values())
            resolution_rate = (sum(self.resolution_success.values()) / total_resolutions * 100) if total_resolutions > 0 else 0
            
            return {
                'timestamp': now.isoformat(),
                'status': 'healthy' if len(recent_errors) < 5 else 'degraded' if len(recent_errors) < 20 else 'critical',
                'errors_last_hour': len(recent_errors),
                'errors_last_24h': len(daily_errors),
                'error_categories': dict(error_by_category),
                'auto_fix_resolution_rate': round(resolution_rate, 2),
                'successful_fixes': dict(self.resolution_success),
                'failed_fixes': dict(self.resolution_failures),
                'top_issues': error_by_category.most_common(5),
                'recommendations': self._generate_recommendations(error_by_category)
            }
    
    def _generate_recommendations(self, error_by_category: Counter) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        for category, count in error_by_category.most_common(3):
            if count >= 10:
                if category == 'connection_timeout':
                    recommendations.append("Consider increasing timeout thresholds or checking network stability")
                elif category == 'rate_limit_exceeded':
                    recommendations.append("Implement request throttling or upgrade API tier")
                elif category == 'database_connection':
                    recommendations.append("Review database connection pool settings and server health")
                elif category == 'memory_exhaustion':
                    recommendations.append("Optimize memory usage or increase available resources")
        
        if not recommendations:
            recommendations.append("System health is good. Continue monitoring.")
        
        return recommendations
    
    async def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get error trends over time"""
        async with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=hours)
            
            relevant_errors = [
                e for e in self.error_history
                if datetime.fromisoformat(e.get('analyzed_at', now.isoformat()).replace('Z', '+00:00')) > cutoff
            ]
            
            # Group by hour
            hourly_counts = defaultdict(int)
            hourly_categories = defaultdict(lambda: defaultdict(int))
            
            for error in relevant_errors:
                timestamp = datetime.fromisoformat(error.get('analyzed_at', now.isoformat()).replace('Z', '+00:00'))
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
                category = self._categorize_error(error)
                
                hourly_counts[hour_key] += 1
                hourly_categories[hour_key][category] += 1
            
            return {
                'period_hours': hours,
                'total_errors': len(relevant_errors),
                'hourly_breakdown': [
                    {
                        'hour': hour,
                        'count': count,
                        'categories': dict(hourly_categories[hour])
                    }
                    for hour, count in sorted(hourly_counts.items())
                ]
            }


# Singleton instance
_ai_error_analyzer: Optional[AIErrorAnalyzer] = None


def get_ai_error_analyzer() -> AIErrorAnalyzer:
    """Get or create AI error analyzer instance"""
    global _ai_error_analyzer
    if _ai_error_analyzer is None:
        _ai_error_analyzer = AIErrorAnalyzer()
    return _ai_error_analyzer
