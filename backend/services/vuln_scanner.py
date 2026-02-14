"""
Vulnerability Scanner Service
Runs pip-audit and yarn audit on a schedule, stores results in MongoDB.
"""

import subprocess
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

COLLECTION = "vulnerability_scans"


class VulnerabilityScannerService:

    def __init__(self, db):
        self.db = db

    async def run_full_scan(self) -> dict:
        """Run both backend and frontend vulnerability audits."""
        started = datetime.now(timezone.utc)
        logger.info("Vulnerability scan started")

        backend_result = self._run_backend_audit()
        frontend_result = self._run_frontend_audit()

        total = backend_result["count"] + frontend_result["count"]
        status = "clean" if total == 0 else "vulnerabilities_found"

        report = {
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "total_vulnerabilities": total,
            "backend": backend_result,
            "frontend": frontend_result,
        }

        # Persist to MongoDB
        await self.db[COLLECTION].insert_one({**report, "created_at": started})

        if total > 0:
            logger.warning(
                f"Vulnerability scan complete: {total} issues found "
                f"(backend={backend_result['count']}, frontend={frontend_result['count']})"
            )
        else:
            logger.info("Vulnerability scan complete: 0 issues found")

        return report

    # ------------------------------------------------------------------
    def _run_backend_audit(self) -> dict:
        """Run pip-audit and parse output."""
        try:
            proc = subprocess.run(
                ["python3", "-m", "pip_audit", "--format", "json", "--output", "-"],
                capture_output=True, text=True, timeout=120,
                cwd="/app/backend",
            )
            data = json.loads(proc.stdout) if proc.stdout.strip() else {}
            deps = data.get("dependencies", [])
            vulns = [d for d in deps if d.get("vulns")]
            items = []
            for dep in vulns:
                for v in dep["vulns"]:
                    items.append({
                        "package": dep["name"],
                        "version": dep["version"],
                        "id": v.get("id", ""),
                        "fix_versions": v.get("fix_versions", []),
                        "description": v.get("description", ""),
                    })
            return {"count": len(items), "vulnerabilities": items, "error": None}
        except subprocess.TimeoutExpired:
            logger.error("pip-audit timed out")
            return {"count": 0, "vulnerabilities": [], "error": "pip-audit timed out"}
        except Exception as e:
            logger.error(f"pip-audit failed: {e}")
            return {"count": 0, "vulnerabilities": [], "error": str(e)}

    def _run_frontend_audit(self) -> dict:
        """Run yarn audit and parse output."""
        try:
            proc = subprocess.run(
                ["yarn", "audit", "--json"],
                capture_output=True, text=True, timeout=120,
                cwd="/app/frontend",
            )
            items = []
            for line in proc.stdout.strip().splitlines():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "auditAdvisory":
                    adv = entry["data"]["advisory"]
                    items.append({
                        "package": adv.get("module_name", ""),
                        "severity": adv.get("severity", ""),
                        "title": adv.get("title", ""),
                        "vulnerable_versions": adv.get("vulnerable_versions", ""),
                        "patched_versions": adv.get("patched_versions", ""),
                        "id": adv.get("github_advisory_id", ""),
                        "cves": adv.get("cves", []),
                    })
            return {"count": len(items), "vulnerabilities": items, "error": None}
        except subprocess.TimeoutExpired:
            logger.error("yarn audit timed out")
            return {"count": 0, "vulnerabilities": [], "error": "yarn audit timed out"}
        except Exception as e:
            logger.error(f"yarn audit failed: {e}")
            return {"count": 0, "vulnerabilities": [], "error": str(e)}

    async def get_latest_scan(self) -> Optional[dict]:
        """Return the most recent scan result."""
        doc = await self.db[COLLECTION].find_one(
            {}, {"_id": 0}, sort=[("created_at", -1)]
        )
        return doc

    async def get_scan_history(self, limit: int = 30) -> list:
        """Return recent scan history (summary only)."""
        cursor = self.db[COLLECTION].find(
            {},
            {"_id": 0, "backend.vulnerabilities": 0, "frontend.vulnerabilities": 0},
            sort=[("created_at", -1)],
        ).limit(limit)
        return await cursor.to_list(length=limit)
