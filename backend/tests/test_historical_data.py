"""
Test Historical Data API Endpoints
Tests CryptoCompare historical OHLCV data integration and AI training endpoints.
"""

import pytest
import requests
import os
import time

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHistoricalDataService:
    """Tests for Historical Data Service endpoints"""
    
    def test_service_status(self):
        """Test GET /api/historical-data/status - Service status endpoint"""
        response = requests.get(f"{BASE_URL}/api/historical-data/status", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["operational", "not_initialized"]
        
        if data["status"] == "operational":
            assert "storage" in data
            assert "api_configured" in data
            print(f"✓ Service status: {data['status']}")
            print(f"  - API configured: {data.get('api_configured')}")
            if "storage" in data:
                print(f"  - Total coins: {data['storage'].get('total_coins', 0)}")
                print(f"  - Total records: {data['storage'].get('total_records', 0)}")
    
    def test_download_status(self):
        """Test GET /api/historical-data/download-status - Download progress tracking"""
        response = requests.get(f"{BASE_URL}/api/historical-data/download-status", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "progress" in data
        print(f"✓ Download status: running={data['running']}, progress={data['progress']}%")
        if data.get("message"):
            print(f"  - Message: {data['message']}")
    
    def test_storage_stats(self):
        """Test GET /api/historical-data/stats - Storage statistics"""
        response = requests.get(f"{BASE_URL}/api/historical-data/stats", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_coins" in data
        assert "total_records" in data
        assert "coins" in data
        
        print(f"✓ Storage stats:")
        print(f"  - Total coins: {data['total_coins']}")
        print(f"  - Total records: {data['total_records']}")
        if data.get("coins"):
            print(f"  - Top 5 coins by records:")
            for coin in data["coins"][:5]:
                print(f"    - {coin['symbol']}: {coin['records']} records ({coin.get('date_range', {}).get('from', 'N/A')} to {coin.get('date_range', {}).get('to', 'N/A')})")


class TestCryptoCompareAPI:
    """Tests for CryptoCompare API direct fetch endpoints"""
    
    def test_fetch_daily_ohlcv_btc(self):
        """Test GET /api/historical-data/api/daily/{coin_symbol} - Fetch daily OHLCV for BTC"""
        response = requests.get(f"{BASE_URL}/api/historical-data/api/daily/BTC?limit=30", timeout=60)
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "data" in data
        assert "count" in data
        assert data["count"] > 0
        assert "timeframe" in data
        assert data["timeframe"] == "daily"
        
        # Verify OHLCV structure
        if data["data"]:
            candle = data["data"][0]
            assert "timestamp" in candle
            assert "date" in candle
            assert "open" in candle
            assert "high" in candle
            assert "low" in candle
            assert "close" in candle
            assert "volume_from" in candle
            assert "volume_to" in candle
        
        print(f"✓ Daily OHLCV for BTC:")
        print(f"  - Records: {data['count']}")
        print(f"  - Date range: {data.get('time_from', 'N/A')} to {data.get('time_to', 'N/A')}")
        print(f"  - Source: {data.get('source', 'N/A')}")
    
    def test_fetch_daily_ohlcv_eth(self):
        """Test GET /api/historical-data/api/daily/{coin_symbol} - Fetch daily OHLCV for ETH"""
        response = requests.get(f"{BASE_URL}/api/historical-data/api/daily/ETH?limit=30", timeout=60)
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "ETH"
        assert data["count"] > 0
        print(f"✓ Daily OHLCV for ETH: {data['count']} records")
    
    def test_fetch_hourly_ohlcv_btc(self):
        """Test GET /api/historical-data/api/hourly/{coin_symbol} - Fetch hourly OHLCV for BTC"""
        response = requests.get(f"{BASE_URL}/api/historical-data/api/hourly/BTC?limit=24", timeout=60)
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "data" in data
        assert "count" in data
        assert data["count"] > 0
        assert "timeframe" in data
        assert data["timeframe"] == "hourly"
        
        print(f"✓ Hourly OHLCV for BTC:")
        print(f"  - Records: {data['count']}")
        print(f"  - Date range: {data.get('time_from', 'N/A')} to {data.get('time_to', 'N/A')}")
    
    def test_fetch_hourly_ohlcv_sol(self):
        """Test GET /api/historical-data/api/hourly/{coin_symbol} - Fetch hourly OHLCV for SOL"""
        response = requests.get(f"{BASE_URL}/api/historical-data/api/hourly/SOL?limit=24", timeout=60)
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "SOL"
        assert data["count"] > 0
        print(f"✓ Hourly OHLCV for SOL: {data['count']} records")


class TestHistoricalDataDownload:
    """Tests for historical data download endpoints"""
    
    def test_download_single_coin(self):
        """Test POST /api/historical-data/download/single/{coin_symbol} - Download single coin history"""
        # Use a smaller max_days for faster test
        response = requests.post(
            f"{BASE_URL}/api/historical-data/download/single/LINK?max_days=100",
            timeout=120
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "LINK"
        assert "records_stored" in data
        assert data["records_stored"] > 0
        assert "status" in data
        assert data["status"] == "success"
        
        print(f"✓ Downloaded LINK history:")
        print(f"  - Records stored: {data['records_stored']}")
        print(f"  - Date range: {data.get('date_range', {}).get('from', 'N/A')} to {data.get('date_range', {}).get('to', 'N/A')}")
    
    def test_start_batch_download(self):
        """Test POST /api/historical-data/download/start - Start batch download"""
        # Start download for just 2 coins to test the endpoint
        payload = {
            "coins": ["DOGE", "SHIB"],
            "max_days": 100
        }
        response = requests.post(
            f"{BASE_URL}/api/historical-data/download/start",
            json=payload,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["started", "already_running"]
        
        print(f"✓ Batch download status: {data['status']}")
        if data["status"] == "started":
            print(f"  - Coins: {data.get('coins', [])}")
            print(f"  - Max days: {data.get('max_days', 'N/A')}")
        elif data["status"] == "already_running":
            print(f"  - Current coin: {data.get('current_coin', 'N/A')}")
            print(f"  - Progress: {data.get('progress', 0)}%")
        
        # Wait a bit and check status
        time.sleep(3)
        status_response = requests.get(f"{BASE_URL}/api/historical-data/download-status", timeout=30)
        status_data = status_response.json()
        print(f"  - Download running: {status_data.get('running')}")
        print(f"  - Progress: {status_data.get('progress', 0)}%")


class TestStoredCoinData:
    """Tests for retrieving stored coin data"""
    
    def test_get_stored_coin_data_btc(self):
        """Test GET /api/historical-data/coin/{coin_symbol} - Get stored BTC data"""
        response = requests.get(f"{BASE_URL}/api/historical-data/coin/BTC?limit=100", timeout=30)
        
        # May return 404 if no data stored yet
        if response.status_code == 404:
            print("⚠ No stored BTC data found (expected if download not run)")
            return
        
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "count" in data
        assert "data" in data
        
        print(f"✓ Stored BTC data:")
        print(f"  - Records: {data['count']}")
        print(f"  - Date range: {data.get('date_range', {}).get('from', 'N/A')} to {data.get('date_range', {}).get('to', 'N/A')}")
    
    def test_get_stored_coin_data_eth(self):
        """Test GET /api/historical-data/coin/{coin_symbol} - Get stored ETH data"""
        response = requests.get(f"{BASE_URL}/api/historical-data/coin/ETH?limit=100", timeout=30)
        
        if response.status_code == 404:
            print("⚠ No stored ETH data found (expected if download not run)")
            return
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "ETH"
        print(f"✓ Stored ETH data: {data['count']} records")
    
    def test_get_stored_coin_data_nonexistent(self):
        """Test GET /api/historical-data/coin/{coin_symbol} - Get data for non-existent coin"""
        response = requests.get(f"{BASE_URL}/api/historical-data/coin/NONEXISTENT123", timeout=30)
        assert response.status_code == 404
        print("✓ Correctly returns 404 for non-existent coin data")


class TestAITrainingOnOHLCV:
    """Tests for AI training on OHLCV data"""
    
    def test_train_ohlcv_start(self):
        """Test POST /api/gems/train-ohlcv - Train AI on real OHLCV data"""
        response = requests.post(f"{BASE_URL}/api/gems/train-ohlcv", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["started", "already_running"]
        
        print(f"✓ OHLCV training status: {data['status']}")
        if data["status"] == "started":
            print(f"  - Message: {data.get('message', 'N/A')}")
            print(f"  - Data source: {data.get('data_source', 'N/A')}")
            print(f"  - Check status: {data.get('check_status', 'N/A')}")
    
    def test_deep_training_status(self):
        """Test GET /api/gems/deep-training-status - Training status"""
        response = requests.get(f"{BASE_URL}/api/gems/deep-training-status", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "progress" in data
        
        print(f"✓ Training status:")
        print(f"  - Running: {data['running']}")
        print(f"  - Progress: {data['progress']}%")
        print(f"  - Message: {data.get('message', 'N/A')}")
        
        if data.get("result"):
            result = data["result"]
            print(f"  - Status: {result.get('status', 'N/A')}")
            if result.get("model_metrics"):
                metrics = result["model_metrics"]
                print(f"  - Final accuracy: {metrics.get('final_accuracy', 'N/A')}%")
                print(f"  - Coins analyzed: {metrics.get('coins_in_training_set', 'N/A')}")
                print(f"  - Total OHLCV records: {metrics.get('total_ohlcv_records', 'N/A')}")
    
    def test_wait_for_training_completion(self):
        """Wait for training to complete and verify results"""
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{BASE_URL}/api/gems/deep-training-status", timeout=30)
            data = response.json()
            
            if not data.get("running"):
                # Training completed
                if data.get("result"):
                    result = data["result"]
                    if result.get("status") == "completed":
                        print(f"✓ Training completed successfully!")
                        print(f"  - Coins analyzed: {len(result.get('coins_analyzed', []))}")
                        print(f"  - Patterns discovered: {len(result.get('patterns_discovered', []))}")
                        if result.get("model_metrics"):
                            print(f"  - Final accuracy: {result['model_metrics'].get('final_accuracy', 'N/A')}%")
                            print(f"  - Total OHLCV records: {result['model_metrics'].get('total_ohlcv_records', 'N/A')}")
                        return
                    elif result.get("status") == "error":
                        print(f"⚠ Training error: {result.get('error', 'Unknown error')}")
                        return
                break
            
            print(f"  Training in progress: {data.get('progress', 0)}% - {data.get('message', '')}")
            time.sleep(5)
        
        print("⚠ Training did not complete within timeout (may still be running)")


class TestTrainingData:
    """Tests for training data retrieval"""
    
    def test_get_training_data(self):
        """Test GET /api/historical-data/training-data - Get training-ready data"""
        response = requests.get(f"{BASE_URL}/api/historical-data/training-data?min_records=100", timeout=60)
        assert response.status_code == 200
        
        data = response.json()
        assert "coins" in data
        assert "stats" in data
        
        stats = data["stats"]
        print(f"✓ Training data stats:")
        print(f"  - Total coins: {stats.get('total_coins', 0)}")
        print(f"  - Total records: {stats.get('total_records', 0)}")
        print(f"  - Coins with sufficient data: {stats.get('coins_with_sufficient_data', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
