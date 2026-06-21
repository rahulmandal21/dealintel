import requests
import json
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from pinecone import Pinecone

load_dotenv()

app = Server("dealintel-mcp")

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

HEADERS = {"User-Agent": "dealintel rahul@example.com"}

# Known CIK mappings for common tickers (non-US or hard-to-resolve tickers)
CIK_MAP = {
    "NVS": "0001114448",
    "MSFT": "0000789019",
    "AAPL": "0000320193",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "TSLA": "0001318605",
    "JPM": "0000019617",
    "BAC": "0000070858",
    "PFE": "0000078003",
    "NFLX": "0001065280",
}


# ════════════════════════════════════════════════════════════════
# REUSABLE TOOL FUNCTIONS
# These are the actual MCP "tools" — the single source of truth.
# Both the MCP server (call_tool below) AND the CrewAI agents
# (via agents/crew.py) import and call these directly.
# ════════════════════════════════════════════════════════════════

def get_company_facts(ticker: str) -> dict:
    """MCP Tool: Fetch real financial facts for a company from SEC EDGAR."""
    ticker = ticker.upper().strip()
    cik = CIK_MAP.get(ticker)

    if not cik:
        resp = requests.get(
            f"https://data.sec.gov/submissions/CIK{ticker}.json",
            headers=HEADERS
        )
        if resp.status_code != 200:
            return {"error": f"Could not find {ticker} on SEC EDGAR",
                    "ticker": ticker, "company": ticker}
        data = resp.json()
        cik = str(data.get("cik", "")).zfill(10)
        company_name = data.get("name", ticker)
    else:
        company_name = ticker

    facts_resp = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        headers=HEADERS
    )

    if facts_resp.status_code != 200:
        return {"company": company_name, "ticker": ticker, "cik": cik}

    facts = facts_resp.json()
    company_name = facts.get("entityName", company_name)
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    def get_annual(concept_name):
        concept = us_gaap.get(concept_name, {})
        units = concept.get("units", {}).get("USD", [])
        annual = [x for x in units if x.get("form") == "10-K"]
        seen = {}
        for entry in annual:
            year = entry["end"][:4]
            seen[year] = entry["val"]
        return dict(list(seen.items())[-5:])

    revenue = get_annual("RevenueFromContractWithCustomerExcludingAssessedTax") or get_annual("Revenues")
    net_income = get_annual("NetIncomeLoss")
    assets = get_annual("Assets")

    return {
        "company": company_name,
        "ticker": ticker,
        "cik": cik,
        "revenue_by_year": revenue,
        "net_income_by_year": net_income,
        "total_assets_by_year": assets
    }


def search_deal_news(query: str, k: int = 5) -> list:
    """MCP Tool: Search financial news and deal intelligence semantically."""
    try:
        results = index.search(
            namespace="deals",
            query={"inputs": {"text": query}, "top_k": k}
        )
        hits = results.get("result", {}).get("hits", [])
        output = []
        for hit in hits:
            fields = hit.get("fields", {})
            output.append({
                "score": hit.get("_score"),
                "text": fields.get("text", ""),
                "source": fields.get("source", "unknown")
            })
        return output
    except Exception as e:
        return [{"error": str(e)}]


def get_comparable_deals(sector: str) -> list:
    """MCP Tool: Find comparable M&A deals for a given industry sector."""
    try:
        results = index.search(
            namespace="deals",
            query={
                "inputs": {"text": f"M&A acquisition merger deal in {sector} sector valuation multiples EV EBITDA"},
                "top_k": 5
            }
        )
        hits = results.get("result", {}).get("hits", [])
        output = []
        for hit in hits:
            fields = hit.get("fields", {})
            output.append({
                "score": hit.get("_score"),
                "deal": fields.get("text", ""),
                "source": fields.get("source", "unknown")
            })
        return output
    except Exception as e:
        return [{"error": str(e)}]


# ════════════════════════════════════════════════════════════════
# MCP SERVER WIRING
# Exposes the functions above over the MCP protocol (stdio).
# This is what makes the server callable by Claude Desktop, MCP
# Inspector, or any MCP-compliant client.
# ════════════════════════════════════════════════════════════════

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_company_facts",
            description="Fetch financial facts for a company from SEC EDGAR using ticker symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol e.g. AAPL, MSFT"}
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="search_deal_news",
            description="Search financial news and deal intelligence using semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query e.g. 'merger risks in tech sector'"},
                    "k": {"type": "integer", "description": "Number of results to return", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_comparable_deals",
            description="Get comparable M&A deals from SEC filings for a given sector",
            inputSchema={
                "type": "object",
                "properties": {
                    "sector": {"type": "string", "description": "Industry sector e.g. technology, banking, pharma"}
                },
                "required": ["sector"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_company_facts":
        result = get_company_facts(arguments["ticker"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "search_deal_news":
        result = search_deal_news(arguments["query"], arguments.get("k", 5))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_comparable_deals":
        result = get_comparable_deals(arguments["sector"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())