import logging
from typing import Any, Dict


async def check_database_connection(db_client: Any) -> Dict[str, Any]:
    """
    Perform a lightweight database health check.

    Args:
        db_client: Object exposing ``admin.command("ping")`` coroutine for connectivity checks.

    Returns a dictionary with:
      - status: "healthy" when the ping succeeds, otherwise "unhealthy"
      - database: connection detail string
    """
    if not db_client:
        return {"status": "unhealthy", "database": "error: no database client"}

    try:
        await db_client.admin.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        logging.getLogger(__name__).warning("Database ping failed: %s", exc)
        return {"status": "unhealthy", "database": "error: database unavailable"}
