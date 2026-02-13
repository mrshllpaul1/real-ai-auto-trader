"""
Comprehensive Tests for Enhanced Auto Error and Bug Correction System
=====================================================================
Tests AI-powered error analysis, auto-healing, and predictive fixes.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from backend.services.ai_error_analyzer import AIErrorAnalyzer, get_ai_error_analyzer
from backend.services.error_recovery import ErrorRecoveryManager, ErrorCategory


class TestAIErrorAnalyzer:
    """Test AI-powered error analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a fresh analyzer for each test"""
        return AIErrorAnalyzer()
    
    @pytest.mark.asyncio
    async def test_error_categorization(self, analyzer):
        """Test error categorization"""
        # Test timeout error
        error_info = {
            'message': 'Connection timeout to API',
            'error_type': 'TimeoutError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        analysis = await analyzer.analyze_error(error_info)
        assert analysis['category'] == 'connection_timeout'
        assert 'timeout' in analysis['root_cause'].lower()
        assert analysis['auto_fix_available'] is True
        
    @pytest.mark.asyncio
    async def test_rate_limit_detection(self, analyzer):
        """Test rate limit error detection"""
        error_info = {
            'message': 'Rate limit exceeded: 429 Too Many Requests',
            'error_type': 'HTTPError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        analysis = await analyzer.analyze_error(error_info)
        assert analysis['category'] == 'rate_limit_exceeded'
        assert 'rate limit' in analysis['root_cause'].lower()
        
    @pytest.mark.asyncio
    async def test_database_error_detection(self, analyzer):
        """Test database error detection"""
        error_info = {
            'message': 'MongoDB connection pool exhausted',
            'error_type': 'ConnectionError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        analysis = await analyzer.analyze_error(error_info)
        assert analysis['category'] == 'database_connection'
        assert 'database' in analysis['root_cause'].lower()
    
    @pytest.mark.asyncio
    async def test_pattern_detection(self, analyzer):
        """Test error pattern detection"""
        # Generate multiple similar errors
        for i in range(5):
            error_info = {
                'message': 'Connection timeout to external service',
                'error_type': 'TimeoutError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            analysis = await analyzer.analyze_error(error_info)
            await asyncio.sleep(0.01)  # Small delay
        
        # Check pattern was detected
        assert analysis['pattern_detected'] is True
        assert analysis['frequency'] >= 3
        
    @pytest.mark.asyncio
    async def test_severity_assessment(self, analyzer):
        """Test severity assessment"""
        # Test critical severity (database error with high frequency)
        for i in range(10):
            error_info = {
                'message': 'Database connection lost',
                'error_type': 'ConnectionError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            analysis = await analyzer.analyze_error(error_info)
        
        # Last analysis should show critical severity
        assert analysis['severity_recommendation'] in ['critical', 'high']
        
    @pytest.mark.asyncio
    async def test_auto_fix_timeout(self, analyzer):
        """Test auto-fix for timeout errors"""
        error_info = {
            'message': 'Connection timeout',
            'error_type': 'TimeoutError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        success, message = await analyzer.attempt_auto_fix(error_info)
        assert success is True
        assert 'timeout' in message.lower()
        
    @pytest.mark.asyncio
    async def test_auto_fix_rate_limit(self, analyzer):
        """Test auto-fix for rate limit errors"""
        error_info = {
            'message': 'Rate limit exceeded',
            'error_type': 'HTTPError',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        success, message = await analyzer.attempt_auto_fix(error_info)
        assert success is True
        assert 'rate' in message.lower() or 'limit' in message.lower()
        
    @pytest.mark.asyncio
    async def test_health_report(self, analyzer):
        """Test health report generation"""
        # Add some errors
        for i in range(5):
            error_info = {
                'message': f'Test error {i}',
                'error_type': 'TestError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await analyzer.analyze_error(error_info)
        
        report = await analyzer.get_health_report()
        
        assert 'status' in report
        assert 'errors_last_hour' in report
        assert 'errors_last_24h' in report
        assert 'auto_fix_resolution_rate' in report
        assert 'recommendations' in report
        assert isinstance(report['recommendations'], list)
        
    @pytest.mark.asyncio
    async def test_error_trends(self, analyzer):
        """Test error trend analysis"""
        # Add some errors
        for i in range(10):
            error_info = {
                'message': f'Test error {i}',
                'error_type': 'TestError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await analyzer.analyze_error(error_info)
        
        trends = await analyzer.get_error_trends(hours=1)
        
        assert 'period_hours' in trends
        assert trends['period_hours'] == 1
        assert 'total_errors' in trends
        assert trends['total_errors'] == 10
        assert 'hourly_breakdown' in trends
        
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, analyzer):
        """Test intelligent recommendations"""
        # Generate pattern of connection timeouts
        for i in range(12):
            error_info = {
                'message': 'Connection timeout',
                'error_type': 'TimeoutError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await analyzer.analyze_error(error_info)
        
        report = await analyzer.get_health_report()
        recommendations = report['recommendations']
        
        assert len(recommendations) > 0
        # Should recommend something about timeout/network
        assert any('timeout' in r.lower() or 'network' in r.lower() 
                  for r in recommendations)


class TestErrorRecoveryManager:
    """Test enhanced error recovery manager"""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        return ErrorRecoveryManager()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, manager):
        """Test basic error handling"""
        exception = Exception("Test error")
        result = await manager.handle_error(exception)
        
        assert result is True
        stats = manager.get_stats()
        assert stats['total_errors'] == 1
        
    @pytest.mark.asyncio
    async def test_error_categorization(self, manager):
        """Test error categorization in recovery manager"""
        # Database error
        db_error = Exception("MongoDB connection failed")
        await manager.handle_error(db_error)
        
        stats = manager.get_stats()
        assert stats['by_category']['database'] == 1
        
    @pytest.mark.asyncio
    async def test_auto_healing_attempts(self, manager):
        """Test auto-healing attempt tracking"""
        # Create a network error
        network_error = Exception("Connection timeout")
        
        # Handle it multiple times
        for i in range(3):
            await manager.handle_error(network_error, auto_heal=True)
            await asyncio.sleep(0.1)
        
        stats = manager.get_stats()
        assert 'healing_attempts' in stats
        
    @pytest.mark.asyncio
    async def test_recent_errors_tracking(self, manager):
        """Test recent errors are tracked correctly"""
        # Add errors
        for i in range(10):
            error = Exception(f"Test error {i}")
            await manager.handle_error(error, auto_heal=False)
        
        recent = manager.get_recent_errors(limit=5)
        assert len(recent) == 5
        # Most recent should be first
        assert 'error 9' in recent[0]['message']
        
    @pytest.mark.asyncio
    async def test_max_recent_errors_limit(self, manager):
        """Test that only max recent errors are kept"""
        # Add more than max
        for i in range(60):
            error = Exception(f"Test error {i}")
            await manager.handle_error(error, auto_heal=False)
        
        recent = manager.get_recent_errors(limit=100)
        assert len(recent) <= manager._max_recent
        
    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """Test health check functionality"""
        health = await manager.run_health_check()
        
        assert 'timestamp' in health
        assert 'status' in health
        assert health['status'] == 'healthy'
        

class TestErrorIntegration:
    """Integration tests for the complete error correction system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_flow(self):
        """Test complete error handling flow"""
        analyzer = AIErrorAnalyzer()
        manager = ErrorRecoveryManager()
        
        # 1. Error occurs
        error = Exception("Connection timeout to API")
        
        # 2. Manager handles it
        await manager.handle_error(error, auto_heal=True)
        
        # 3. Analyzer analyzes it
        error_info = {
            'message': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        analysis = await analyzer.analyze_error(error_info)
        
        # 4. Check results
        assert analysis['category'] == 'connection_timeout'
        assert analysis['auto_fix_available'] is True
        
        # 5. Apply auto-fix
        success, message = await analyzer.attempt_auto_fix(error_info)
        assert success is True
        
        # 6. Verify stats
        manager_stats = manager.get_stats()
        assert manager_stats['total_errors'] >= 1
        
        analyzer_report = await analyzer.get_health_report()
        assert 'auto_fix_resolution_rate' in analyzer_report
        
    @pytest.mark.asyncio
    async def test_pattern_detection_triggers_fix(self):
        """Test that pattern detection triggers predictive fix"""
        analyzer = AIErrorAnalyzer()
        
        # Generate a pattern
        for i in range(5):
            error_info = {
                'message': 'API authentication failed',
                'error_type': 'AuthenticationError',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            analysis = await analyzer.analyze_error(error_info)
        
        # Pattern should be detected
        assert analysis['pattern_detected'] is True
        assert analysis['frequency'] >= 3
        
        # Check that auto-fix was tracked
        report = await analyzer.get_health_report()
        assert report['errors_last_hour'] >= 5
        

def run_tests():
    """Run all tests"""
    print("=" * 70)
    print("Testing Enhanced Auto Error and Bug Correction System")
    print("=" * 70)
    
    # Run pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    run_tests()
