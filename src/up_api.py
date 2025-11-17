from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence

import httpx


class UpAPIError(RuntimeError):
    """Raised when the Up API returns an error or cannot be reached."""


def _compact_params(params: Mapping[str, Optional[Any]]) -> Dict[str, Any]:
    """Remove parameters whose value is None."""
    return {key: value for key, value in params.items() if value is not None}


@dataclass(frozen=True)
class UpAPIConfig:
    """Configuration holder for Up API interactions."""

    token: str
    timeout: float = 30.0
    base_url: str = "https://api.up.com.au/api/v1"
    user_agent: str = "up-mcp/1.0 (+https://github.com/shaunakg/up-mcp)"


class UpAPI:
    """Typed helper for calling the Up Bank public API."""

    def __init__(self, config: UpAPIConfig) -> None:
        if not config.token:
            raise ValueError("A non-empty Personal Access Token is required.")

        self._config = config

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a HTTP request and return the JSON payload."""
        url = f"{self._config.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._config.token}",
            "User-Agent": self._config.user_agent,
            "Accept": "application/json",
        }

        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=self._config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                detail = exc.response.json()
            except Exception:  # pragma: no cover - defensive
                detail = exc.response.text
            message = (
                f"Up API request failed ({exc.response.status_code}): {detail}"
            )
            raise UpAPIError(message) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network issues
            raise UpAPIError(f"Unable to reach Up API: {exc}") from exc

        return response.json()

    @staticmethod
    def _pagination_params(
        page_size: Optional[int],
        after: Optional[str],
        before: Optional[str],
    ) -> Dict[str, Any]:
        return _compact_params(
            {
                "page[size]": page_size,
                "page[after]": after,
                "page[before]": before,
            }
        )

    # --------------------------------------------------------------------- #
    # Utility endpoints
    # --------------------------------------------------------------------- #
    def ping(self) -> Dict[str, Any]:
        return self._request("GET", "/util/ping")

    # --------------------------------------------------------------------- #
    # Accounts
    # --------------------------------------------------------------------- #
    def list_accounts(
        self,
        *,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = self._pagination_params(page_size, after, before)
        return self._request("GET", "/accounts", params=params)

    def get_account(self, account_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/accounts/{account_id}")

    # --------------------------------------------------------------------- #
    # Transactions
    # --------------------------------------------------------------------- #
    def list_transactions(
        self,
        *,
        status: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            **self._pagination_params(page_size, after, before),
            **_compact_params(
                {
                    "filter[status]": status,
                    "filter[since]": since,
                    "filter[until]": until,
                    "filter[category]": category,
                    "filter[tag]": tag,
                }
            ),
        }
        return self._request("GET", "/transactions", params=params)

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/transactions/{transaction_id}")

    def list_transactions_by_account(
        self,
        account_id: str,
        *,
        status: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        tag: Optional[str] = None,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            **self._pagination_params(page_size, after, before),
            **_compact_params(
                {
                    "filter[status]": status,
                    "filter[since]": since,
                    "filter[until]": until,
                    "filter[tag]": tag,
                }
            ),
        }
        return self._request(
            "GET", f"/accounts/{account_id}/transactions", params=params
        )

    # --------------------------------------------------------------------- #
    # Attachments
    # --------------------------------------------------------------------- #
    def list_attachments(
        self,
        *,
        transaction_id: Optional[str] = None,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            **self._pagination_params(page_size, after, before),
            **_compact_params({"filter[transaction]": transaction_id}),
        }
        return self._request("GET", "/attachments", params=params)

    def get_attachment(self, attachment_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/attachments/{attachment_id}")

    # --------------------------------------------------------------------- #
    # Categories
    # --------------------------------------------------------------------- #
    def list_categories(
        self,
        *,
        parent_category_id: Optional[str] = None,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {
            **self._pagination_params(page_size, after, before),
            **_compact_params({"filter[parent]": parent_category_id}),
        }
        return self._request("GET", "/categories", params=params)

    def get_category(self, category_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/categories/{category_id}")

    def categorize_transaction(
        self, transaction_id: str, category_id: str
    ) -> Dict[str, Any]:
        payload = {
            "data": {
                "type": "categories",
                "id": category_id,
            }
        }
        return self._request(
            "POST",
            f"/transactions/{transaction_id}/relationships/category",
            json=payload,
        )

    def remove_transaction_category(self, transaction_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            f"/transactions/{transaction_id}/relationships/category",
        )

    # --------------------------------------------------------------------- #
    # Tags
    # --------------------------------------------------------------------- #
    def list_tags(self) -> Dict[str, Any]:
        return self._request("GET", "/tags")

    def add_tags_to_transaction(
        self, transaction_id: str, tags: Sequence[str]
    ) -> Dict[str, Any]:
        if not tags:
            raise ValueError("At least one tag is required.")
        payload = {
            "data": [
                {
                    "type": "tags",
                    "id": tag,
                }
                for tag in tags
            ]
        }
        return self._request(
            "POST",
            f"/transactions/{transaction_id}/relationships/tags",
            json=payload,
        )

    def remove_tags_from_transaction(
        self, transaction_id: str, tags: Sequence[str]
    ) -> Dict[str, Any]:
        if not tags:
            raise ValueError("At least one tag is required.")
        payload = {
            "data": [
                {
                    "type": "tags",
                    "id": tag,
                }
                for tag in tags
            ]
        }
        return self._request(
            "DELETE",
            f"/transactions/{transaction_id}/relationships/tags",
            json=payload,
        )

    # --------------------------------------------------------------------- #
    # Webhooks
    # --------------------------------------------------------------------- #
    def list_webhooks(
        self,
        *,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = self._pagination_params(page_size, after, before)
        return self._request("GET", "/webhooks", params=params)

    def create_webhook(
        self,
        *,
        url: str,
        description: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "data": {
                "type": "webhooks",
                "attributes": _compact_params(
                    {
                        "url": url,
                        "description": description,
                        "secretKey": secret_key,
                    }
                ),
            }
        }
        return self._request("POST", "/webhooks", json=payload)

    def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/webhooks/{webhook_id}")

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/webhooks/{webhook_id}")

    def ping_webhook(self, webhook_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/webhooks/{webhook_id}/ping")

    def list_webhook_logs(
        self,
        webhook_id: str,
        *,
        page_size: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = self._pagination_params(page_size, after, before)
        return self._request(
            "GET", f"/webhooks/{webhook_id}/logs", params=params
        )

