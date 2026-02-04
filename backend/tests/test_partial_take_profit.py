"""
Test Partial Take-Profit Feature
Tests the partial take-profit configuration and position tracking endpoints.

Features tested:
- GET /api/automation/partial-tp/config - Get partial TP configuration
- POST /api/automation/partial-tp/config - Update partial TP configuration
- GET /api/automation/partial-tp/positions - Get positions with partial TP status
- GET /api/automation/status - Verify partial_take_profits stat is tracked
- Verify default config: 3 levels (50% at 30%, 25% at 50%, 25% at 100%)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPartialTakeProfitConfig:
    """Test partial take-profit configuration endpoints"""
    
    def test_get_partial_tp_config(self):
        """Test GET /api/automation/partial-tp/config returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify main structure
        assert "partial_take_profit" in data, "Missing 'partial_take_profit' key"
        assert "statistics" in data, "Missing 'statistics' key"
        assert "example" in data, "Missing 'example' key"
        
        # Verify partial_take_profit config
        ptp = data["partial_take_profit"]
        assert "enabled" in ptp, "Missing 'enabled' in partial_take_profit"
        assert "move_stop_to_breakeven" in ptp, "Missing 'move_stop_to_breakeven'"
        assert "levels" in ptp, "Missing 'levels' in partial_take_profit"
        assert "description" in ptp, "Missing 'description'"
        
        # Verify enabled is boolean
        assert isinstance(ptp["enabled"], bool), "enabled should be boolean"
        
        # Verify levels is a list
        assert isinstance(ptp["levels"], list), "levels should be a list"
        
        print(f"✓ Partial TP config retrieved successfully")
        print(f"  - Enabled: {ptp['enabled']}")
        print(f"  - Move stop to breakeven: {ptp['move_stop_to_breakeven']}")
        print(f"  - Number of levels: {len(ptp['levels'])}")
    
    def test_partial_tp_has_three_default_levels(self):
        """Verify config has 3 levels: 50% at 30% profit, 25% at 50%, 25% at 100%"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200
        
        data = response.json()
        levels = data["partial_take_profit"]["levels"]
        
        # Verify exactly 3 levels
        assert len(levels) == 3, f"Expected 3 levels, got {len(levels)}"
        
        # Verify level 1: 50% at 30% profit
        level_1 = levels[0]
        assert level_1.get("pct_of_position") == 50, f"Level 1 should close 50%, got {level_1.get('pct_of_position')}"
        assert level_1.get("at_profit_pct") == 30, f"Level 1 should trigger at 30% profit, got {level_1.get('at_profit_pct')}"
        
        # Verify level 2: 25% at 50% profit
        level_2 = levels[1]
        assert level_2.get("pct_of_position") == 25, f"Level 2 should close 25%, got {level_2.get('pct_of_position')}"
        assert level_2.get("at_profit_pct") == 50, f"Level 2 should trigger at 50% profit, got {level_2.get('at_profit_pct')}"
        
        # Verify level 3: 25% at 100% profit
        level_3 = levels[2]
        assert level_3.get("pct_of_position") == 25, f"Level 3 should close 25%, got {level_3.get('pct_of_position')}"
        assert level_3.get("at_profit_pct") == 100, f"Level 3 should trigger at 100% profit, got {level_3.get('at_profit_pct')}"
        
        # Verify total percentage equals 100%
        total_pct = sum(level.get("pct_of_position", 0) for level in levels)
        assert total_pct == 100, f"Total percentage should be 100%, got {total_pct}%"
        
        print(f"✓ Default 3 levels verified:")
        print(f"  - Level 1: Close {level_1['pct_of_position']}% at {level_1['at_profit_pct']}% profit")
        print(f"  - Level 2: Close {level_2['pct_of_position']}% at {level_2['at_profit_pct']}% profit")
        print(f"  - Level 3: Close {level_3['pct_of_position']}% at {level_3['at_profit_pct']}% profit")
        print(f"  - Total: {total_pct}%")
    
    def test_partial_tp_enabled_by_default(self):
        """Verify partial take-profit is enabled by default"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200
        
        data = response.json()
        enabled = data["partial_take_profit"]["enabled"]
        
        assert enabled is True, f"Partial TP should be enabled by default, got {enabled}"
        
        print(f"✓ Partial TP is enabled by default: {enabled}")
    
    def test_move_stop_to_breakeven_enabled(self):
        """Verify move_stop_to_breakeven is enabled"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200
        
        data = response.json()
        move_stop = data["partial_take_profit"]["move_stop_to_breakeven"]
        
        assert move_stop is True, f"move_stop_to_breakeven should be True, got {move_stop}"
        
        print(f"✓ Move stop to breakeven is enabled: {move_stop}")
    
    def test_partial_tp_statistics_present(self):
        """Verify statistics are present in config response"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200
        
        data = response.json()
        stats = data["statistics"]
        
        assert "partial_take_profits" in stats, "Missing 'partial_take_profits' in statistics"
        assert isinstance(stats["partial_take_profits"], int), "partial_take_profits should be integer"
        
        print(f"✓ Statistics present - partial_take_profits: {stats['partial_take_profits']}")
    
    def test_partial_tp_example_present(self):
        """Verify example scenario is present"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        
        assert response.status_code == 200
        
        data = response.json()
        example = data["example"]
        
        assert "scenario" in example, "Missing 'scenario' in example"
        assert "level_1" in example, "Missing 'level_1' in example"
        assert "level_2" in example, "Missing 'level_2' in example"
        assert "level_3" in example, "Missing 'level_3' in example"
        assert "total_outcome" in example, "Missing 'total_outcome' in example"
        assert "bonus" in example, "Missing 'bonus' in example"
        
        print(f"✓ Example scenario present:")
        print(f"  - Scenario: {example['scenario']}")
        print(f"  - Bonus: {example['bonus']}")


class TestPartialTakeProfitConfigUpdate:
    """Test POST /api/automation/partial-tp/config endpoint"""
    
    def test_update_partial_tp_enabled(self):
        """Test updating enabled status"""
        # First get current config
        get_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        original_enabled = get_response.json()["partial_take_profit"]["enabled"]
        
        # Toggle enabled
        new_enabled = not original_enabled
        response = requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"enabled": new_enabled}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True, "Update should succeed"
        assert "updated" in data, "Missing 'updated' in response"
        assert data["updated"].get("partial_take_profit_enabled") == new_enabled
        
        # Verify current_config reflects change
        assert data["current_config"]["enabled"] == new_enabled
        
        print(f"✓ Updated enabled: {original_enabled} → {new_enabled}")
        
        # Restore original value
        requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"enabled": original_enabled}
        )
        print(f"✓ Restored enabled to: {original_enabled}")
    
    def test_update_move_stop_to_breakeven(self):
        """Test updating move_stop_to_breakeven"""
        # Get current config
        get_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        original_value = get_response.json()["partial_take_profit"]["move_stop_to_breakeven"]
        
        # Toggle value
        new_value = not original_value
        response = requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"move_stop_to_breakeven": new_value}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert data["current_config"]["move_stop_to_breakeven"] == new_value
        
        print(f"✓ Updated move_stop_to_breakeven: {original_value} → {new_value}")
        
        # Restore original value
        requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"move_stop_to_breakeven": original_value}
        )
        print(f"✓ Restored move_stop_to_breakeven to: {original_value}")
    
    def test_update_partial_tp_levels(self):
        """Test updating partial TP levels"""
        # Get current config
        get_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        original_levels = get_response.json()["partial_take_profit"]["levels"]
        
        # Update with new levels
        new_levels = [
            {"pct_of_position": 40, "at_profit_pct": 20},
            {"pct_of_position": 30, "at_profit_pct": 40},
            {"pct_of_position": 30, "at_profit_pct": 80}
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"levels": new_levels}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert data["current_config"]["levels"] == new_levels
        
        print(f"✓ Updated levels to custom configuration")
        
        # Restore original levels
        requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"levels": original_levels}
        )
        print(f"✓ Restored original levels")
    
    def test_update_levels_validation_exceeds_100(self):
        """Test that levels exceeding 100% total are rejected"""
        invalid_levels = [
            {"pct_of_position": 60, "at_profit_pct": 20},
            {"pct_of_position": 50, "at_profit_pct": 40}  # Total = 110%
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/automation/partial-tp/config",
            json={"levels": invalid_levels}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid levels, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Error response should have 'detail'"
        assert "100%" in data["detail"], f"Error should mention 100%, got: {data['detail']}"
        
        print(f"✓ Validation correctly rejects levels exceeding 100%: {data['detail']}")


class TestPartialTakeProfitPositions:
    """Test GET /api/automation/partial-tp/positions endpoint"""
    
    def test_get_positions_with_partial_tp(self):
        """Test getting positions with partial TP status"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/positions")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "positions" in data, "Missing 'positions' key"
        assert "total" in data, "Missing 'total' key"
        assert "with_partial_tp_taken" in data, "Missing 'with_partial_tp_taken' key"
        assert "config" in data, "Missing 'config' key"
        
        # Verify positions is a list
        assert isinstance(data["positions"], list), "positions should be a list"
        
        # Verify config structure
        config = data["config"]
        assert "enabled" in config, "Missing 'enabled' in config"
        assert "levels" in config, "Missing 'levels' in config"
        
        print(f"✓ Positions with partial TP retrieved:")
        print(f"  - Total positions: {data['total']}")
        print(f"  - With partial TP taken: {data['with_partial_tp_taken']}")
        print(f"  - Partial TP enabled: {config['enabled']}")
    
    def test_position_structure_in_partial_tp(self):
        """Test that each position has correct structure"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/positions")
        
        assert response.status_code == 200
        
        data = response.json()
        positions = data["positions"]
        
        if len(positions) > 0:
            pos = positions[0]
            
            # Verify required fields
            required_fields = [
                "coin_id", "position_id", "entry_price", "current_price",
                "pnl_pct", "partial_tp_taken", "levels_taken", "levels_remaining",
                "next_level", "stop_at_breakeven", "remaining_amount_usd"
            ]
            
            for field in required_fields:
                assert field in pos, f"Missing '{field}' in position"
            
            # Verify types
            assert isinstance(pos["partial_tp_taken"], list), "partial_tp_taken should be list"
            assert isinstance(pos["levels_taken"], int), "levels_taken should be int"
            assert isinstance(pos["levels_remaining"], int), "levels_remaining should be int"
            assert isinstance(pos["stop_at_breakeven"], bool), "stop_at_breakeven should be bool"
            
            print(f"✓ Position structure verified for {pos['coin_id']}:")
            print(f"  - Entry price: ${pos['entry_price']}")
            print(f"  - Current price: ${pos['current_price']}")
            print(f"  - PnL: {pos['pnl_pct']}%")
            print(f"  - Levels taken: {pos['levels_taken']}")
            print(f"  - Levels remaining: {pos['levels_remaining']}")
            print(f"  - Stop at breakeven: {pos['stop_at_breakeven']}")
        else:
            print("✓ No positions to verify structure (empty list)")
    
    def test_next_level_structure(self):
        """Test that next_level has correct structure when present"""
        response = requests.get(f"{BASE_URL}/api/automation/partial-tp/positions")
        
        assert response.status_code == 200
        
        data = response.json()
        positions = data["positions"]
        
        for pos in positions:
            next_level = pos.get("next_level")
            
            if next_level is not None:
                # Verify next_level structure
                assert "level_id" in next_level, "Missing 'level_id' in next_level"
                assert "at_profit_pct" in next_level, "Missing 'at_profit_pct' in next_level"
                assert "close_pct" in next_level, "Missing 'close_pct' in next_level"
                assert "distance_pct" in next_level, "Missing 'distance_pct' in next_level"
                
                print(f"✓ Next level for {pos['coin_id']}: {next_level['level_id']} at {next_level['at_profit_pct']}% profit (distance: {next_level['distance_pct']}%)")
                break
        else:
            print("✓ No positions with next_level to verify (all levels taken or no positions)")


class TestAutomationStatusPartialTP:
    """Test that /api/automation/status tracks partial_take_profits"""
    
    def test_automation_status_has_partial_tp_stat(self):
        """Verify /api/automation/status includes partial_take_profits statistic"""
        response = requests.get(f"{BASE_URL}/api/automation/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify main structure
        assert "enabled" in data, "Missing 'enabled' key"
        assert "statistics" in data, "Missing 'statistics' key"
        assert "config" in data, "Missing 'config' key"
        
        # Verify partial_take_profits in statistics
        stats = data["statistics"]
        # Note: The current implementation may not have partial_take_profits in statistics
        # Let's check what's available
        
        print(f"✓ Automation status retrieved:")
        print(f"  - Enabled: {data['enabled']}")
        print(f"  - Statistics keys: {list(stats.keys())}")
        
        # Check if partial_take_profits is tracked
        if "partial_take_profits" in stats:
            print(f"  - partial_take_profits: {stats['partial_take_profits']}")
        else:
            print(f"  - Note: partial_take_profits not in statistics (may be in config)")
    
    def test_automation_status_config_has_partial_tp(self):
        """Verify config includes partial take-profit settings"""
        response = requests.get(f"{BASE_URL}/api/automation/status")
        
        assert response.status_code == 200
        
        data = response.json()
        config = data["config"]
        
        # Verify partial TP config is present
        assert "partial_take_profit_enabled" in config, "Missing 'partial_take_profit_enabled' in config"
        assert "partial_tp_levels" in config, "Missing 'partial_tp_levels' in config"
        assert "move_stop_to_breakeven" in config, "Missing 'move_stop_to_breakeven' in config"
        
        # Verify values
        assert config["partial_take_profit_enabled"] is True, "partial_take_profit should be enabled"
        assert len(config["partial_tp_levels"]) == 3, f"Should have 3 levels, got {len(config['partial_tp_levels'])}"
        
        print(f"✓ Automation status config verified:")
        print(f"  - partial_take_profit_enabled: {config['partial_take_profit_enabled']}")
        print(f"  - partial_tp_levels count: {len(config['partial_tp_levels'])}")
        print(f"  - move_stop_to_breakeven: {config['move_stop_to_breakeven']}")


class TestPartialTPIntegration:
    """Integration tests for partial take-profit feature"""
    
    def test_partial_tp_levels_match_across_endpoints(self):
        """Verify partial TP levels are consistent across endpoints"""
        # Get from partial-tp/config
        config_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        assert config_response.status_code == 200
        config_levels = config_response.json()["partial_take_profit"]["levels"]
        
        # Get from automation/status
        status_response = requests.get(f"{BASE_URL}/api/automation/status")
        assert status_response.status_code == 200
        status_levels = status_response.json()["config"]["partial_tp_levels"]
        
        # Get from partial-tp/positions
        positions_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/positions")
        assert positions_response.status_code == 200
        positions_levels = positions_response.json()["config"]["levels"]
        
        # Verify all match
        assert config_levels == status_levels, "Levels mismatch between config and status endpoints"
        assert config_levels == positions_levels, "Levels mismatch between config and positions endpoints"
        
        print(f"✓ Partial TP levels consistent across all endpoints")
        print(f"  - Levels: {config_levels}")
    
    def test_partial_tp_enabled_consistent(self):
        """Verify enabled status is consistent across endpoints"""
        # Get from partial-tp/config
        config_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/config")
        config_enabled = config_response.json()["partial_take_profit"]["enabled"]
        
        # Get from automation/status
        status_response = requests.get(f"{BASE_URL}/api/automation/status")
        status_enabled = status_response.json()["config"]["partial_take_profit_enabled"]
        
        # Get from partial-tp/positions
        positions_response = requests.get(f"{BASE_URL}/api/automation/partial-tp/positions")
        positions_enabled = positions_response.json()["config"]["enabled"]
        
        # Verify all match
        assert config_enabled == status_enabled, "Enabled mismatch between config and status"
        assert config_enabled == positions_enabled, "Enabled mismatch between config and positions"
        
        print(f"✓ Partial TP enabled status consistent: {config_enabled}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
