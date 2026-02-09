import os
import sys
from pathlib import Path
import pytest
import types

# Ensure backend modules are importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Stub dotenv to avoid import issues in isolated tests
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))


@pytest.mark.asyncio
async def test_real_trading_safety_lock_blocks_without_flag(monkeypatch):
    """Real trading should be blocked unless ENABLE_REAL_TRADING is true."""
    from services.automated_trader import AutomatedWeeklyTrader

    # Ensure flag is unset/false
    monkeypatch.delenv("ENABLE_REAL_TRADING", raising=False)

    trader = AutomatedWeeklyTrader(
        db=None,
        kraken_service=None,
        ai_trainer=None,
        gem_finder=None
    )

    result = await trader.execute_spot_trade(
        symbol="BTC",
        side="buy",
        amount_usd=10.0,
        paper_trade=False
    )

    assert result.get("success") is False
    assert result.get("safety_lock") is True
    assert "Real trading disabled" in result.get("error", "")
