from typing import Any, Dict, Tuple


async def check_database_connection(db_client: Any) -> Dict[str, Any]:
    """
    Perform a lightweight database health check.

    Returns a dictionary with:
      - status: "healthy" when the ping succeeds, otherwise "unhealthy"
      - database: connection detail string
    """
    if not db_client:
        return {"status": "unhealthy", "database": "error: no database client"}

    try:
        await db_client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:  # pragma: no cover - string value asserted in tests
        return {"status": "unhealthy", "database": f"error: {exc}"}
