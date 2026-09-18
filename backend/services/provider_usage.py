import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict

import requests

import env


ProviderFetcher = Callable[[], Awaitable[Dict[str, Any]]]


class ProviderUsageService:
    def __init__(self, cache_seconds: int = 60):
        self.cache_seconds = cache_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    def invalidate(self):
        self._cached_at = 0.0
        self._cache = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _not_configured(dashboard_url: str) -> Dict[str, Any]:
        return {
            "status": "not_configured",
            "source": "provider_reported",
            "retrieved_at": ProviderUsageService._timestamp(),
            "reporting_period": None,
            "metrics": [],
            "dashboard_url": dashboard_url,
            "stale": False,
        }

    async def _get_json(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        def request():
            response = requests.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(request)

    async def fetch_gemini(self) -> Dict[str, Any]:
        dashboard = "https://aistudio.google.com/usage"
        if not env.GOOGLE_CLOUD_PROJECT or not env.GOOGLE_CLOUD_ACCESS_TOKEN:
            result = self._not_configured(dashboard)
            result["status"] = "unsupported" if env.GEMINI_API_KEY else "not_configured"
            result["error_code"] = "cloud_quota_credentials_required"
            return result

        url = (
            "https://serviceusage.googleapis.com/v1/projects/"
            f"{env.GOOGLE_CLOUD_PROJECT}/services/generativelanguage.googleapis.com/consumerQuotaMetrics"
        )
        payload = await self._get_json(
            "GET",
            url,
            headers={"Authorization": f"Bearer {env.GOOGLE_CLOUD_ACCESS_TOKEN}"},
            params={"view": "FULL", "pageSize": 200},
        )
        metrics = []
        for metric in payload.get("metrics", []):
            for limit in metric.get("consumerQuotaLimits", []):
                for bucket in limit.get("quotaBuckets", []):
                    effective_limit = bucket.get("effectiveLimit")
                    if effective_limit is not None:
                        metrics.append(
                            {
                                "name": metric.get("displayName") or metric.get("metric"),
                                "value": effective_limit,
                                "unit": metric.get("unit", "quota"),
                                "dimensions": bucket.get("dimensions", {}),
                            }
                        )
        return {
            "status": "available",
            "source": "provider_reported",
            "retrieved_at": self._timestamp(),
            "reporting_period": "provider_defined",
            "metrics": metrics,
            "dashboard_url": dashboard,
            "stale": False,
        }

    async def fetch_openrouter(self) -> Dict[str, Any]:
        dashboard = "https://openrouter.ai/settings/credits"
        if not env.OPENROUTER_MANAGEMENT_KEY:
            return self._not_configured(dashboard)

        payload = await self._get_json(
            "GET",
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {env.OPENROUTER_MANAGEMENT_KEY}"},
        )
        credits = payload.get("data", payload)
        total = float(credits.get("total_credits", 0) or 0)
        used = float(credits.get("total_usage", 0) or 0)
        return {
            "status": "available",
            "source": "provider_reported",
            "retrieved_at": self._timestamp(),
            "reporting_period": "account_lifetime",
            "metrics": [
                {"name": "credits_total", "value": total, "unit": "USD"},
                {"name": "credits_used", "value": used, "unit": "USD"},
                {"name": "credits_remaining", "value": max(total - used, 0), "unit": "USD"},
            ],
            "dashboard_url": dashboard,
            "stale": False,
        }

    async def fetch_cloudflare(self) -> Dict[str, Any]:
        dashboard = "https://dash.cloudflare.com/?to=/:account/r2/overview"
        if not env.CLOUDFLARE_ACCOUNT_ID or not env.CLOUDFLARE_ANALYTICS_TOKEN:
            return self._not_configured(dashboard)

        query = """
        query R2Usage($accountTag: string!, $since: Date!, $until: Date!) {
          viewer { accounts(filter: { accountTag: $accountTag }) {
            r2StorageAdaptiveGroups(limit: 1, filter: { date_geq: $since, date_leq: $until }) {
              max { payloadSize }
            }
            r2OperationsAdaptiveGroups(limit: 10000, filter: { date_geq: $since, date_leq: $until }) {
              sum { requests }
              dimensions { actionType }
            }
          } }
        }
        """
        now = datetime.now(timezone.utc)
        payload = await self._get_json(
            "POST",
            "https://api.cloudflare.com/client/v4/graphql",
            headers={"Authorization": f"Bearer {env.CLOUDFLARE_ANALYTICS_TOKEN}"},
            json={
                "query": query,
                "variables": {
                    "accountTag": env.CLOUDFLARE_ACCOUNT_ID,
                    "since": now.replace(day=1).date().isoformat(),
                    "until": now.date().isoformat(),
                },
            },
        )
        if payload.get("errors"):
            raise RuntimeError("Cloudflare analytics query was rejected")
        accounts = payload.get("data", {}).get("viewer", {}).get("accounts", [])
        account = accounts[0] if accounts else {}
        storage = account.get("r2StorageAdaptiveGroups", [])
        operations = account.get("r2OperationsAdaptiveGroups", [])
        metrics = [
            {
                "name": "storage_bytes",
                "value": storage[0].get("max", {}).get("payloadSize", 0) if storage else 0,
                "unit": "bytes",
            }
        ]
        for operation in operations:
            metrics.append(
                {
                    "name": f"operations_{operation.get('dimensions', {}).get('actionType', 'unknown')}",
                    "value": operation.get("sum", {}).get("requests", 0),
                    "unit": "requests",
                }
            )
        return {
            "status": "available",
            "source": "provider_reported",
            "retrieved_at": self._timestamp(),
            "reporting_period": "month_to_date",
            "metrics": metrics,
            "dashboard_url": dashboard,
            "stale": False,
        }

    async def _safe_fetch(self, name: str, fetcher: ProviderFetcher) -> Dict[str, Any]:
        try:
            return await fetcher()
        except Exception:
            previous = self._cache.get(name)
            if previous and previous.get("status") == "available":
                return {**previous, "stale": True, "error_code": "provider_request_failed"}
            return {
                "status": "error",
                "source": "provider_reported",
                "retrieved_at": self._timestamp(),
                "reporting_period": None,
                "metrics": [],
                "dashboard_url": None,
                "stale": False,
                "error_code": "provider_request_failed",
            }

    async def refresh(self, force: bool = False) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            if not force and self._cache and time.monotonic() - self._cached_at < self.cache_seconds:
                return self._cache
            names = ("gemini", "openrouter", "cloudflare")
            fetchers = (self.fetch_gemini, self.fetch_openrouter, self.fetch_cloudflare)
            results = await asyncio.gather(
                *(self._safe_fetch(name, fetcher) for name, fetcher in zip(names, fetchers))
            )
            self._cache = dict(zip(names, results))
            self._cached_at = time.monotonic()
            return self._cache


provider_usage_service = ProviderUsageService(env.PROVIDER_USAGE_CACHE_SECONDS)