import subprocess
import json
import os
import requests
from dotenv import load_dotenv
from pinecone import Pinecone
from crewai.tools import tool

load_dotenv()

HEADERS = {"User-Agent": "dealintel rahul@example.com"}

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# ── Tool 1: Get Company Financial Facts ──────────────────────────
_TICKER_CIK_CACHE = None


def _get_ticker_to_cik_map():
    """Download and cache SEC's official ticker-to-CIK mapping (US-listed companies only)."""
    global _TICKER_CIK_CACHE
    if _TICKER_CIK_CACHE is None:
        resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS
        )
        resp.raise_for_status()
        data = resp.json()
        _TICKER_CIK_CACHE = {
            entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
            for entry in data.values()
        }
    return _TICKER_CIK_CACHE


@tool("get_company_facts")
def get_company_facts(ticker: str) -> str:
    """Fetch real financial facts for a company from SEC EDGAR. 
    Input is a US stock ticker like AAPL or MSFT. Only works for companies 
    listed on US exchanges and registered with the SEC — non-US tickers 
    (e.g. Indian, European exchanges) will not be found."""

    ticker = ticker.upper().strip()

    try:
        ticker_map = _get_ticker_to_cik_map()
    except Exception as e:
        return f"Could not load SEC ticker database: {str(e)}"

    cik = ticker_map.get(ticker)
    if not cik:
        return f"'{ticker}' was not found in SEC's database. This tool only covers US-listed, SEC-registered companies."

    facts_resp = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        headers=HEADERS
    )

    if facts_resp.status_code != 200:
        return f"Could not fetch financial facts for ticker {ticker} (CIK {cik})"

    facts = facts_resp.json()
    company_name = facts.get("entityName", "Unknown")
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    def get_annual(concept_name):
        concept = us_gaap.get(concept_name, {})
        units = concept.get("units", {}).get("USD", [])
        annual = [x for x in units if x.get("form") == "10-K"]
        seen = {}
        for entry in annual:
            year = entry["end"][:4]
            seen[year] = entry["val"]
        return seen

    revenue = get_annual("RevenueFromContractWithCustomerExcludingAssessedTax") or get_annual("Revenues")
    net_income = get_annual("NetIncomeLoss")
    assets = get_annual("Assets")

    result = {
        "company": company_name,
        "ticker": ticker,
        "cik": cik,
        "revenue_by_year": revenue,
        "net_income_by_year": net_income,
        "total_assets_by_year": assets
    }

    return json.dumps(result, indent=2)


# ── Tool 2: Search Deal News ─────────────────────────────────────
@tool("search_deal_news")
def search_deal_news(query: str) -> str:
    """Search financial news and M&A deal intelligence semantically.
    Input is a search query like 'tech sector merger risks'."""

    try:
        results = index.search(
            namespace="deals",
            query={
                "inputs": {"text": query},
                "top_k": 5
            }
        )

        hits = results.get("result", {}).get("hits", [])

        if not hits:
            return "No results found in deal database."

        output = []
        for hit in hits:
            fields = hit.get("fields", {})
            output.append(f"[Score: {hit.get('_score'):.3f}] {fields.get('text', '')}")

        return "\n\n".join(output)

    except Exception as e:
        return f"Search error: {str(e)}"


# ── Tool 3: Get Comparable Deals ─────────────────────────────────
@tool("get_comparable_deals")
def get_comparable_deals(sector: str) -> str:
    """Find comparable M&A deals for a given industry sector.
    Input is a sector name like 'technology' or 'banking'."""

    try:
        results = index.search(
            namespace="deals",
            query={
                "inputs": {"text": f"M&A acquisition merger deal in {sector} sector valuation multiples EV EBITDA"},
                "top_k": 5
            }
        )

        hits = results.get("result", {}).get("hits", [])

        if not hits:
            return f"No comparable deals found for {sector} sector."

        output = []
        for hit in hits:
            fields = hit.get("fields", {})
            output.append(f"[Score: {hit.get('_score'):.3f}] {fields.get('text', '')}")

        return "\n\n".join(output)

    except Exception as e:
        return f"Comparables error: {str(e)}"