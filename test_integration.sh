#!/bin/bash
# Integration Testing Script for Performance Enhancements
# Tests all newly integrated features

echo "🧪 Testing Performance Enhancements Integration"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local description=$3
    
    echo -n "Testing $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001$endpoint)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:8001$endpoint)
    fi
    
    if [ "$response" = "200" ] || [ "$response" = "422" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        ((TESTS_FAILED++))
    fi
}

echo "1. Testing System Performance API"
echo "-----------------------------------"
test_endpoint "/api/system-performance/metrics" "GET" "Get system metrics"
test_endpoint "/api/system-performance/memory" "GET" "Get memory stats"
test_endpoint "/api/system-performance/health" "GET" "Health check"
test_endpoint "/api/system-performance/bottlenecks" "GET" "Identify bottlenecks"
test_endpoint "/api/system-performance/cleanup" "POST" "Force memory cleanup"
echo ""

echo "2. Testing CSV Export API"
echo "-------------------------"
test_endpoint "/api/export/trades/csv?user_id=test" "GET" "Export trades"
test_endpoint "/api/export/portfolio/csv?user_id=test" "GET" "Export portfolio"
test_endpoint "/api/export/performance/csv?user_id=test" "GET" "Export performance"
test_endpoint "/api/export/strategies/csv?user_id=test" "GET" "Export strategies"
echo ""

echo "3. Testing Email Digest API"
echo "----------------------------"
test_endpoint "/api/digest/preferences?user_id=test" "GET" "Get digest preferences"
echo ""

echo "4. Testing Frontend (Code Splitting)"
echo "-------------------------------------"
if [ -f "frontend/src/App.jsx" ]; then
    if grep -q "React.lazy\|lazy(" frontend/src/App.jsx; then
        echo -e "${GREEN}✓ PASS${NC} - Code splitting enabled (React.lazy found)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - Code splitting not enabled"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - Frontend file not found"
fi

if [ -f "frontend/src/hooks/usePerformance.js" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Performance hooks available"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Performance hooks not found"
    ((TESTS_FAILED++))
fi
echo ""

echo "5. Testing Middleware Integration"
echo "----------------------------------"
# Check if compression middleware is in server.py
if grep -q "CompressionMiddleware" backend/server.py; then
    echo -e "${GREEN}✓ PASS${NC} - Compression middleware integrated"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Compression middleware not integrated"
    ((TESTS_FAILED++))
fi

# Check if periodic cleanup is in server.py
if grep -q "start_periodic_cleanup" backend/server.py; then
    echo -e "${GREEN}✓ PASS${NC} - Periodic cleanup integrated"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Periodic cleanup not integrated"
    ((TESTS_FAILED++))
fi
echo ""

echo "6. Testing Route Registration"
echo "------------------------------"
# Check if routes are registered
if grep -q "system_performance_routes" backend/init/routes.py; then
    echo -e "${GREEN}✓ PASS${NC} - System performance routes registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - System performance routes not registered"
    ((TESTS_FAILED++))
fi

if grep -q "export_routes" backend/init/routes.py; then
    echo -e "${GREEN}✓ PASS${NC} - Export routes registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Export routes not registered"
    ((TESTS_FAILED++))
fi

if grep -q "digest_routes" backend/init/routes.py; then
    echo -e "${GREEN}✓ PASS${NC} - Digest routes registered"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Digest routes not registered"
    ((TESTS_FAILED++))
fi
echo ""

echo "=================================================="
echo "Test Results:"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
