# Up Bank MCP Server

An opinionated [FastMCP](https://github.com/jlowin/fastmcp) server that wraps the entire [Up Bank public API](https://developer.up.com.au/) surface area, including accounts, transactions, attachments, categories, tags, and webhook utilities.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/shaunakg/up-mcp)

## Local Development

### Setup

```bash
git clone <your-repo-url>
cd up-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export UP_API_TOKEN="your-up-personal-access-token"
```

> 💡 Generate a Personal Access Token from the Up dashboard. The server refuses to start if `UP_API_TOKEN` is missing.

### Test

```bash
python src/server.py
# in another terminal:
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using the “Streamable HTTP” transport (make sure to include `/mcp` in the URL).

## Deployment

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Render will automatically detect the `render.yaml` configuration

Your server will be available at `https://your-service-name.onrender.com/mcp` (NOTE THE `/mcp`!)

## Poke Setup

You can connect your MCP server to Poke at (poke.com/settings/connections)[poke.com/settings/connections].
To test the connection explitly, ask poke somethink like `Tell the subagent to use the "{connection name}" integration's "{tool name}" tool`.
If you run into persistent issues of poke not calling the right MCP (e.g. after you've renamed the connection) you may send `clearhistory` to poke to delete all message history and start fresh.
We're working hard on improving the integration use of Poke :)


## Available Tools

The MCP server exposes first-class tools for every Up API resource:

- `up_ping` – Up utility ping
- `list_accounts`, `get_account`
- `list_transactions`, `get_transaction`, `list_account_transactions`
- `list_attachments`, `get_attachment`
- `list_categories`, `get_category`, `categorize_transaction`, `clear_transaction_category`
- `list_tags`, `add_tags_to_transaction`, `remove_tags_from_transaction`
- `list_webhooks`, `create_webhook`, `get_webhook`, `delete_webhook`, `ping_webhook`, `list_webhook_logs`

Pagination cursors, filtering, and mutation payloads mirror the official API spec so that tooling can be composed directly from chat instructions.
