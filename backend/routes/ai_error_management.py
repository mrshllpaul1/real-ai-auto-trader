"""
AI Error Management Routes
===========================
API endpoints for AI-powered error analysis and automatic correction.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from backend.services.ai_error_analyzer import get_ai_error_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/ai-error', tags=['ai-error-management'])


class ErrorAnalysisRequest(BaseModel):
    """Request model for error analysis"""
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class ErrorFixRequest(BaseModel):
    """Request model for automatic error fix"""
    error_type: str
    message: str
    context: Optional[Dict[str, Any]] = None


@router.post('/analyze')
async def analyze_error(request: ErrorAnalysisRequest):
    """
    Analyze an error and get intelligent insights.
    
    Returns:
    - Error category
    - Root cause analysis
    - Suggested solutions
    - Auto-fix availability
    - Pattern detection
    """
    try:
        analyzer = get_ai_error_analyzer()
        
        error_info = {
            'error_type': request.error_type,
            'message': request.message,
            'stack_trace': request.stack_trace,
            'context': request.context or {},
            'timestamp': request.timestamp or datetime.utcnow().isoformat()
        }
        
        analysis = await analyzer.analyze_error(error_info)
        
        return {
            'status': 'success',
            'analysis': analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post('/auto-fix')
async def auto_fix_error(request: ErrorFixRequest):
    """
    Attempt automatic error resolution.
    
    Returns:
    - Success status
    - Applied fix details
    - Recommendations
    """
    try:
        analyzer = get_ai_error_analyzer()
        
        error_info = {
            'error_type': request.error_type,
            'message': request.message,
            'context': request.context or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success, message = await analyzer.attempt_auto_fix(error_info)
        
        return {
            'status': 'success' if success else 'failed',
            'fixed': success,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Auto-fix failed: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-fix failed: {str(e)}")


@router.get('/health-report')
async def get_health_report():
    """
    Get comprehensive health report with error insights.
    
    Returns:
    - System health status
    - Error statistics
    - Auto-fix success rate
    - Top issues
    - Recommendations
    """
    try:
        analyzer = get_ai_error_analyzer()
        report = await analyzer.get_health_report()
        
        return {
            'status': 'success',
            'report': report
        }
    
    except Exception as e:
        logger.error(f"Health report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get('/trends')
async def get_error_trends(hours: int = 24):
    """
    Get error trends over specified time period.
    
    Parameters:
    - hours: Number of hours to analyze (default: 24)
    
    Returns:
    - Hourly error breakdown
    - Category distribution
    - Trend analysis
    """
    try:
        if hours < 1 or hours > 168:  # Max 7 days
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        analyzer = get_ai_error_analyzer()
        trends = await analyzer.get_error_trends(hours)
        
        return {
            'status': 'success',
            'trends': trends,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get('/patterns')
async def get_error_patterns():
    """
    Get detected error patterns and their frequencies.
    
    Returns:
    - Detected patterns
    - Pattern frequencies
    - Root causes
    - Suggested solutions
    """
    try:
        analyzer = get_ai_error_analyzer()
        
        # Get health report which includes pattern info
        report = await analyzer.get_health_report()
        
        return {
            'status': 'success',
            'patterns': {
                'top_issues': report['top_issues'],
                'error_categories': report['error_categories'],
                'recommendations': report['recommendations']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")


@router.get('/resolution-stats')
async def get_resolution_stats():
    """
    Get statistics about automatic error resolution.
    
    Returns:
    - Total resolutions attempted
    - Success/failure breakdown by category
    - Overall resolution rate
    """
    try:
        analyzer = get_ai_error_analyzer()
        report = await analyzer.get_health_report()
        
        return {
            'status': 'success',
            'stats': {
                'resolution_rate': report['auto_fix_resolution_rate'],
                'successful_fixes': report['successful_fixes'],
                'failed_fixes': report['failed_fixes'],
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Resolution stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post('/batch-analyze')
async def batch_analyze_errors(errors: List[ErrorAnalysisRequest]):
    """
    Analyze multiple errors in batch.
    
    Returns:
    - Analysis results for each error
    - Common patterns detected
    - Batch recommendations
    """
    try:
        if len(errors) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 errors per batch")
        
        analyzer = get_ai_error_analyzer()
        results = []
        
        for error in errors:
            error_info = {
                'error_type': error.error_type,
                'message': error.message,
                'stack_trace': error.stack_trace,
                'context': error.context or {},
                'timestamp': error.timestamp or datetime.utcnow().isoformat()
            }
            
            analysis = await analyzer.analyze_error(error_info)
            results.append({
                'error': error.dict(),
                'analysis': analysis
            })
        
        return {
            'status': 'success',
            'count': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")
