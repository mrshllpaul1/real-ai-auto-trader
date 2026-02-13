"""
Event Correlation Engine and Historical Events Database Tests
Tests for:
- POST /api/events/database/seed - Seed 38 major events
- GET /api/events/database/stats - Events statistics
- POST /api/events/database/calculate-impact - Price impact calculation
- GET /api/events/what-caused - Find what caused price change
- GET /api/events/search - Search by keyword
- GET /api/events/on-date - Get events on specific date
- GET /api/events/database/category/{category} - Filter by category
- GET /api/events/database/coin/{coin} - Filter by coin
- POST /api/ai-chat/execute-command with event query - AI chat event detection
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestEventDatabaseSeeding:
    """Test seeding the historical events database with 38 major events"""
    
    def test_seed_events_database(self):
        """POST /api/events/database/seed - Seed 38 major events"""
        response = requests.post(f"{BASE_URL}/api/events/database/seed")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected success status, got: {data}"
        assert data.get("total_events") == 38, f"Expected 38 events, got: {data.get('total_events')}"
        
        # Verify inserted or updated count
        total_processed = data.get("inserted", 0) + data.get("updated", 0)
        assert total_processed == 38, f"Expected 38 events processed, got: {total_processed}"
        
        print(f"✓ Seeded {data.get('total_events')} events - {data.get('inserted')} inserted, {data.get('updated')} updated")


class TestEventDatabaseStats:
    """Test getting statistics about stored events"""
    
    def test_get_events_stats(self):
        """GET /api/events/database/stats - Events statistics"""
        response = requests.get(f"{BASE_URL}/api/events/database/stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify total events
        assert data.get("total_events") >= 38, f"Expected at least 38 events, got: {data.get('total_events')}"
        
        # Verify categories exist
        by_category = data.get("by_category", {})
        assert len(by_category) > 0, "Expected categories in stats"
        
        # Verify expected categories
        expected_categories = ["regulatory", "exchange", "institutional", "technology", "celebrity"]
        for cat in expected_categories:
            assert cat in by_category, f"Expected category '{cat}' in stats"
        
        # Verify impact distribution
        by_impact = data.get("by_impact", {})
        assert "positive" in by_impact or "negative" in by_impact, "Expected impact distribution"
        
        # Verify date range
        date_range = data.get("date_range", {})
        assert date_range.get("oldest") is not None, "Expected oldest date"
        assert date_range.get("newest") is not None, "Expected newest date"
        
        print(f"✓ Stats: {data.get('total_events')} events, categories: {list(by_category.keys())}")
        print(f"  Date range: {date_range.get('oldest')} to {date_range.get('newest')}")


class TestEventDatabasePriceImpact:
    """Test calculating price impact for events"""
    
    def test_calculate_price_impact(self):
        """POST /api/events/database/calculate-impact - Price impact calculation"""
        response = requests.post(f"{BASE_URL}/api/events/database/calculate-impact")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected success status, got: {data}"
        
        # Verify events were processed
        events_processed = data.get("events_processed", 0)
        events_updated = data.get("events_updated", 0)
        
        print(f"✓ Price impact: {events_processed} events processed, {events_updated} updated")


class TestWhatCausedPriceChange:
    """Test finding what caused price changes"""
    
    def test_ftx_collapse_correlation(self):
        """GET /api/events/what-caused - FTX collapse on 2022-11-09"""
        response = requests.get(
            f"{BASE_URL}/api/events/what-caused",
            params={"coin": "BTC", "date": "2022-11-09", "direction": "down"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("coin") == "BTC", f"Expected BTC, got: {data.get('coin')}"
        assert data.get("date") == "2022-11-09", f"Expected 2022-11-09, got: {data.get('date')}"
        
        # Check if price change was found or message returned
        if data.get("price_change"):
            assert data.get("direction") == "down", f"Expected down direction, got: {data.get('direction')}"
            print(f"✓ FTX collapse: {data.get('price_change')} price change")
            
            # Check for likely cause
            likely_cause = data.get("likely_cause")
            if likely_cause:
                print(f"  Likely cause: {likely_cause.get('title', 'Unknown')}")
                print(f"  Category: {likely_cause.get('category', 'Unknown')}")
                print(f"  Confidence: {likely_cause.get('confidence', 0)}%")
        else:
            # May not have OHLCV data for this date
            print(f"✓ Query returned: {data.get('message', 'No significant movement found')}")
    
    def test_what_caused_without_direction(self):
        """GET /api/events/what-caused - Without direction filter"""
        response = requests.get(
            f"{BASE_URL}/api/events/what-caused",
            params={"coin": "BTC", "date": "2021-02-08"}  # Tesla BTC purchase
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("coin") == "BTC", f"Expected BTC, got: {data.get('coin')}"
        print(f"✓ Tesla BTC purchase date query: {data.get('price_change', data.get('message', 'No data'))}")
    
    def test_what_caused_invalid_date(self):
        """GET /api/events/what-caused - Invalid date format"""
        response = requests.get(
            f"{BASE_URL}/api/events/what-caused",
            params={"coin": "BTC", "date": "invalid-date"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
        print("✓ Invalid date format correctly rejected")


class TestEventSearch:
    """Test searching events by keyword"""
    
    def test_search_elon_events(self):
        """GET /api/events/search - Search for 'elon' keyword"""
        response = requests.get(
            f"{BASE_URL}/api/events/search",
            params={"keyword": "elon", "days_back": 730, "limit": 30}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("keyword") == "elon", f"Expected keyword 'elon', got: {data.get('keyword')}"
        
        events_found = data.get("events_found", 0)
        events = data.get("events", [])
        
        print(f"✓ Elon search: {events_found} events found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('title', 'No title')[:80]}...")
    
    def test_search_ftx_events(self):
        """GET /api/events/search - Search for 'ftx' keyword"""
        response = requests.get(
            f"{BASE_URL}/api/events/search",
            params={"keyword": "ftx", "days_back": 730, "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        events_found = data.get("events_found", 0)
        
        print(f"✓ FTX search: {events_found} events found")
    
    def test_search_etf_events(self):
        """GET /api/events/search - Search for 'etf' keyword"""
        response = requests.get(
            f"{BASE_URL}/api/events/search",
            params={"keyword": "etf", "days_back": 730, "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        events_found = data.get("events_found", 0)
        
        print(f"✓ ETF search: {events_found} events found")


class TestEventsOnDate:
    """Test getting events on specific dates"""
    
    def test_events_on_ftx_collapse_date(self):
        """GET /api/events/on-date - Events on 2022-11-09 (FTX collapse)"""
        response = requests.get(
            f"{BASE_URL}/api/events/on-date",
            params={"date": "2022-11-09", "coin": "BTC"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("date") == "2022-11-09", f"Expected date 2022-11-09, got: {data.get('date')}"
        
        events_found = data.get("events_found", 0)
        events = data.get("events", [])
        high_impact = data.get("high_impact_events", [])
        
        print(f"✓ Events on 2022-11-09: {events_found} found, {len(high_impact)} high impact")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('title', 'No title')[:80]}...")
    
    def test_events_on_date_without_coin(self):
        """GET /api/events/on-date - Events without coin filter"""
        response = requests.get(
            f"{BASE_URL}/api/events/on-date",
            params={"date": "2024-01-10"}  # ETF approval date
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ Events on 2024-01-10 (ETF approval): {data.get('events_found', 0)} found")
    
    def test_events_on_date_invalid(self):
        """GET /api/events/on-date - Invalid date format"""
        response = requests.get(
            f"{BASE_URL}/api/events/on-date",
            params={"date": "not-a-date"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
        print("✓ Invalid date format correctly rejected")


class TestEventsByCategory:
    """Test filtering events by category"""
    
    def test_celebrity_events(self):
        """GET /api/events/database/category/celebrity - Celebrity events (Elon, etc.)"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/celebrity")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("category") == "celebrity", f"Expected category 'celebrity', got: {data.get('category')}"
        
        count = data.get("count", 0)
        events = data.get("events", [])
        
        print(f"✓ Celebrity events: {count} found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('date')}: {event.get('event', 'No event')[:60]}...")
    
    def test_regulatory_events(self):
        """GET /api/events/database/category/regulatory - Regulatory events"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/regulatory")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        print(f"✓ Regulatory events: {count} found")
    
    def test_exchange_events(self):
        """GET /api/events/database/category/exchange - Exchange events (FTX, etc.)"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/exchange")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        events = data.get("events", [])
        
        print(f"✓ Exchange events: {count} found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('date')}: {event.get('event', 'No event')[:60]}...")
    
    def test_institutional_events(self):
        """GET /api/events/database/category/institutional - Institutional events"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/institutional")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        print(f"✓ Institutional events: {count} found")
    
    def test_technology_events(self):
        """GET /api/events/database/category/technology - Technology events (halvings, forks)"""
        response = requests.get(f"{BASE_URL}/api/events/database/category/technology")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        print(f"✓ Technology events: {count} found")


class TestEventsByCoin:
    """Test filtering events by coin"""
    
    def test_btc_events(self):
        """GET /api/events/database/coin/BTC - Bitcoin events"""
        response = requests.get(f"{BASE_URL}/api/events/database/coin/BTC")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("coin") == "BTC", f"Expected coin 'BTC', got: {data.get('coin')}"
        
        count = data.get("count", 0)
        events = data.get("events", [])
        
        # BTC should have many events
        assert count >= 10, f"Expected at least 10 BTC events, got: {count}"
        
        print(f"✓ BTC events: {count} found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('date')}: {event.get('event', 'No event')[:60]}...")
    
    def test_eth_events(self):
        """GET /api/events/database/coin/ETH - Ethereum events"""
        response = requests.get(f"{BASE_URL}/api/events/database/coin/ETH")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        print(f"✓ ETH events: {count} found")
    
    def test_doge_events(self):
        """GET /api/events/database/coin/DOGE - Dogecoin events (Elon tweets)"""
        response = requests.get(f"{BASE_URL}/api/events/database/coin/DOGE")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        events = data.get("events", [])
        
        print(f"✓ DOGE events: {count} found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('date')}: {event.get('event', 'No event')[:60]}...")
    
    def test_sol_events(self):
        """GET /api/events/database/coin/SOL - Solana events (FTX related)"""
        response = requests.get(f"{BASE_URL}/api/events/database/coin/SOL")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        print(f"✓ SOL events: {count} found")


class TestAIChatEventDetection:
    """Test AI chat event detection via execute-command"""
    
    def test_ai_chat_what_happened_btc(self):
        """POST /api/ai-chat/execute-command - What happened to BTC on 2022-11-09?"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json={
                "query": "What happened to BTC on 2022-11-09?",
                "session_id": "test_event_detection"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("error") == False, f"Expected no error, got: {data.get('error')}"
        
        # Check for event data in response
        event_data = data.get("event_data")
        actions_executed = data.get("actions_executed", [])
        
        print(f"✓ AI Chat event query: {len(actions_executed)} actions executed")
        if event_data:
            print(f"  Event type: {event_data.get('type')}")
            if event_data.get('price_change'):
                print(f"  Price change: {event_data.get('price_change')}")
            if event_data.get('likely_cause'):
                print(f"  Likely cause: {event_data.get('likely_cause', {}).get('title', 'Unknown')}")
        
        # Check response text
        response_text = data.get("response", "")
        assert len(response_text) > 0, "Expected non-empty response"
        print(f"  Response preview: {response_text[:200]}...")
    
    def test_ai_chat_elon_events(self):
        """POST /api/ai-chat/execute-command - Find Elon Musk crypto events"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json={
                "query": "Find Elon Musk crypto events",
                "session_id": "test_event_detection"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        event_data = data.get("event_data")
        
        print(f"✓ AI Chat Elon events query")
        if event_data:
            print(f"  Event type: {event_data.get('type')}")
            events = event_data.get('events', [])
            if events:
                print(f"  Found {len(events)} events")
    
    def test_ai_chat_ftx_crash(self):
        """POST /api/ai-chat/execute-command - Why did FTX crash?"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json={
                "query": "Why did FTX crash?",
                "session_id": "test_event_detection"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        event_data = data.get("event_data")
        
        print(f"✓ AI Chat FTX crash query")
        if event_data:
            print(f"  Event type: {event_data.get('type')}")
            keyword = event_data.get('keyword')
            if keyword:
                print(f"  Keyword: {keyword}")
    
    def test_ai_chat_btc_events(self):
        """POST /api/ai-chat/execute-command - What events affected BTC?"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json={
                "query": "What events affected BTC?",
                "session_id": "test_event_detection"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        event_data = data.get("event_data")
        
        print(f"✓ AI Chat BTC events query")
        if event_data:
            print(f"  Event type: {event_data.get('type')}")
            if event_data.get('coin'):
                print(f"  Coin: {event_data.get('coin')}")


class TestEventDatabaseSearch:
    """Test searching events in the database"""
    
    def test_database_search_elon(self):
        """GET /api/events/database/search - Search 'elon' in database"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/search",
            params={"keyword": "elon", "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        events = data.get("events", [])
        
        print(f"✓ Database search 'elon': {count} events found")
        if events:
            for event in events[:3]:
                print(f"  - {event.get('date')}: {event.get('event', 'No event')[:60]}...")
    
    def test_database_search_ftx(self):
        """GET /api/events/database/search - Search 'FTX' in database"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/search",
            params={"keyword": "FTX", "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        # FTX should have multiple events
        assert count >= 2, f"Expected at least 2 FTX events, got: {count}"
        
        print(f"✓ Database search 'FTX': {count} events found")
    
    def test_database_search_halving(self):
        """GET /api/events/database/search - Search 'halving' in database"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/search",
            params={"keyword": "halving", "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        # Should have at least 2 halvings (2020, 2024)
        assert count >= 2, f"Expected at least 2 halving events, got: {count}"
        
        print(f"✓ Database search 'halving': {count} events found")


class TestEventDatabaseList:
    """Test listing events with filters"""
    
    def test_list_all_events(self):
        """GET /api/events/database/list - List all events"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/list",
            params={"limit": 50}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        
        assert count >= 38, f"Expected at least 38 events, got: {count}"
        
        print(f"✓ List all events: {count} events")
    
    def test_list_events_with_filters(self):
        """GET /api/events/database/list - List with coin and category filters"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/list",
            params={"coin": "BTC", "category": "regulatory", "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        filters = data.get("filters", {})
        
        assert filters.get("coin") == "BTC", f"Expected coin filter 'BTC', got: {filters.get('coin')}"
        assert filters.get("category") == "regulatory", f"Expected category filter 'regulatory', got: {filters.get('category')}"
        
        print(f"✓ List BTC regulatory events: {count} events")
    
    def test_list_events_by_impact(self):
        """GET /api/events/database/list - List by impact (negative)"""
        response = requests.get(
            f"{BASE_URL}/api/events/database/list",
            params={"impact": "negative", "limit": 20}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        count = data.get("count", 0)
        events = data.get("events", [])
        
        # Verify all returned events have negative impact
        for event in events:
            assert event.get("impact") == "negative", f"Expected negative impact, got: {event.get('impact')}"
        
        print(f"✓ List negative impact events: {count} events")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
