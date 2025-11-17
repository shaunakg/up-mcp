#!/usr/bin/env python3
"""FastMCP server that exposes the full Up Bank public API surface."""

from __future__ import annotations

import os
from typing import List, Optional

from fastmcp import FastMCP
from fastmcp.server.auth.providers.debug import DebugTokenVerifier
from fastmcp.server.dependencies import get_access_token

from up_api import UpAPI, UpAPIConfig, UpAPIError


mcp = FastMCP("Up Bank MCP Server", auth=DebugTokenVerifier())


def _resolve_token_from_request() -> Optional[str]:
    """Try to pull a bearer token from the active FastMCP request."""
    try:
        access_token = get_access_token()
    except RuntimeError:
        # Occurs if we are outside a request context (e.g., startup)
        return None

    if access_token and access_token.token:
        return access_token.token

    return None


def _get_client() -> UpAPI:
    token = _resolve_token_from_request() or os.environ.get("UP_API_TOKEN")
    if not token:
        raise RuntimeError(
            "An Up API token is required. Either include a bearer token in the "
            "FastMCP request or set the UP_API_TOKEN environment variable."
        )
    return UpAPI(UpAPIConfig(token=token))


def _run_api_call(fn):
    try:
        return fn()
    except UpAPIError as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description=(
        "Perform a lightweight health check against the Up API utility ping "
        "endpoint."
    )
)
def up_ping() -> dict:
    client = _get_client()
    return _run_api_call(client.ping)


@mcp.tool(description="List Up accounts with optional pagination.")
def list_accounts(
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_accounts(
            page_size=page_size, after=cursor_after, before=cursor_before
        )
    )


@mcp.tool(description="Retrieve a specific Up account by its identifier.")
def get_account(account_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.get_account(account_id))


@mcp.tool(
    description=(
        "List transactions across all accounts with filters for status, "
        "category, tag, and time range."
    )
)
def list_transactions(
    status: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_transactions(
            status=status,
            since=since,
            until=until,
            category=category,
            tag=tag,
            page_size=page_size,
            after=cursor_after,
            before=cursor_before,
        )
    )


@mcp.tool(description="Retrieve a transaction by its identifier.")
def get_transaction(transaction_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.get_transaction(transaction_id))


@mcp.tool(
    description=(
        "List transactions belonging to a specific account with the same "
        "filter options as the global listing."
    )
)
def list_account_transactions(
    account_id: str,
    status: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    tag: Optional[str] = None,
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_transactions_by_account(
            account_id=account_id,
            status=status,
            since=since,
            until=until,
            tag=tag,
            page_size=page_size,
            after=cursor_after,
            before=cursor_before,
        )
    )


@mcp.tool(description="List attachments with optional transaction filter.")
def list_attachments(
    transaction_id: Optional[str] = None,
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_attachments(
            transaction_id=transaction_id,
            page_size=page_size,
            after=cursor_after,
            before=cursor_before,
        )
    )


@mcp.tool(description="Retrieve a specific attachment.")
def get_attachment(attachment_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.get_attachment(attachment_id))


@mcp.tool(description="List categories or filter to a specific parent.")
def list_categories(
    parent_category_id: Optional[str] = None,
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_categories(
            parent_category_id=parent_category_id,
            page_size=page_size,
            after=cursor_after,
            before=cursor_before,
        )
    )


@mcp.tool(description="Retrieve a single category.")
def get_category(category_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.get_category(category_id))


@mcp.tool(
    description="Assign a category to a transaction using a category identifier."
)
def categorize_transaction(transaction_id: str, category_id: str) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.categorize_transaction(transaction_id, category_id)
    )


@mcp.tool(description="Remove the category assignment from a transaction.")
def clear_transaction_category(transaction_id: str) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.remove_transaction_category(transaction_id)
    )


@mcp.tool(description="List all tags currently available.")
def list_tags() -> dict:
    client = _get_client()
    return _run_api_call(client.list_tags)


@mcp.tool(description="Add one or more tags to a transaction.")
def add_tags_to_transaction(transaction_id: str, tags: List[str]) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.add_tags_to_transaction(transaction_id, tags)
    )


@mcp.tool(description="Remove one or more tags from a transaction.")
def remove_tags_from_transaction(transaction_id: str, tags: List[str]) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.remove_tags_from_transaction(transaction_id, tags)
    )


@mcp.tool(description="List configured webhooks.")
def list_webhooks(
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_webhooks(
            page_size=page_size, after=cursor_after, before=cursor_before
        )
    )


@mcp.tool(description="Create a webhook for Up transaction events.")
def create_webhook(
    url: str,
    description: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.create_webhook(
            url=url, description=description, secret_key=secret_key
        )
    )


@mcp.tool(description="Retrieve a webhook by id.")
def get_webhook(webhook_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.get_webhook(webhook_id))


@mcp.tool(description="Delete a webhook by id.")
def delete_webhook(webhook_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.delete_webhook(webhook_id))


@mcp.tool(description="Trigger a ping event for a webhook.")
def ping_webhook(webhook_id: str) -> dict:
    client = _get_client()
    return _run_api_call(lambda: client.ping_webhook(webhook_id))


@mcp.tool(description="List delivery logs for a webhook.")
def list_webhook_logs(
    webhook_id: str,
    page_size: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> dict:
    client = _get_client()
    return _run_api_call(
        lambda: client.list_webhook_logs(
            webhook_id=webhook_id,
            page_size=page_size,
            after=cursor_after,
            before=cursor_before,
        )
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting FastMCP server on {host}:{port}")

    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True,
    )
