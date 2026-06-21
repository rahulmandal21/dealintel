from crewai import Crew, Task, Agent, LLM
import os
import litellm
litellm.cache = None
import json
import time
from dotenv import load_dotenv

# Import the actual MCP tool functions — same ones the MCP server exposes.
# This is the real architecture: agents fetch data through MCP tools,
# not by hitting external APIs directly.
from mcp_server.server import get_company_facts, search_deal_news, get_comparable_deals

load_dotenv()

def run_deal_analysis(acquirer_ticker: str, target_ticker: str, deal_premium: float = 20.0):
    print(f"\n🚀 Starting DealIntel analysis: {acquirer_ticker} acquiring {target_ticker}\n")

    print("📊 Calling MCP tool: get_company_facts...")
    target_data = get_company_facts(target_ticker)
    acquirer_data = get_company_facts(acquirer_ticker)
    print(f"✅ Target: {target_data.get('company', target_ticker)}")
    print(f"✅ Acquirer: {acquirer_data.get('company', acquirer_ticker)}")

    print("📰 Calling MCP tool: get_comparable_deals...")
    comparables = get_comparable_deals(target_data.get("company", target_ticker))

    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )

    analyst = Agent(
        role="Senior M&A Analyst",
        goal="Analyze deals and write Investment Memorandums",
        backstory="You are a Managing Director at Goldman Sachs with 20 years of M&A experience. You are known for producing detailed, numbers-driven Investment Memorandums.",
        tools=[],
        llm=llm,
        verbose=True
    )

    task = Task(
        description=f"""
Analyze {acquirer_ticker} ({acquirer_data.get('company', acquirer_ticker)}) acquiring {target_ticker} ({target_data.get('company', target_ticker)}) at a {deal_premium}% premium.

REAL FINANCIAL DATA FROM SEC EDGAR (fetched via MCP tool get_company_facts):

TARGET ({target_ticker}):
- Revenue by year: {json.dumps(target_data.get('revenue_by_year', {}))}
- Net Income by year: {json.dumps(target_data.get('net_income_by_year', {}))}
- Total Assets by year: {json.dumps(target_data.get('total_assets_by_year', {}))}

ACQUIRER ({acquirer_ticker}):
- Revenue by year: {json.dumps(acquirer_data.get('revenue_by_year', {}))}
- Net Income by year: {json.dumps(acquirer_data.get('net_income_by_year', {}))}

COMPARABLE DEALS (fetched via MCP tool get_comparable_deals):
{json.dumps(comparables, indent=2)[:1500]}

Calculate real numbers from the data above. Write a complete professional Investment Memorandum:

# Investment Memorandum: {acquirer_ticker} Acquiring {target_ticker}

## Transaction Overview
[Describe the deal with actual company names and deal size estimate]

## Executive Summary
[3-4 sentences summarizing the deal thesis]

## Valuation Analysis
### DCF Valuation (WACC: 10%, Terminal Growth: 3%)
[Calculate using actual revenue/income numbers. Show the math.]

### Comparable Transactions
[Apply sector multiples to actual financials]

### Football Field Summary
| Methodology | Low ($B) | High ($B) |
|---|---|---|
| DCF | X | Y |
| Comparable Transactions | X | Y |
| Implied Deal Value ({deal_premium}% premium) | X | Y |

## Risk Assessment
### Top 5 Deal Risks
[5 specific risks with numbers where possible]

### Regulatory Risk Score: X/5
[Specific regulatory analysis]

## Synergy Analysis
[3 synergies with estimated dollar values]

## Recommendation: BUY ✅ or PASS ❌
[Clear recommendation with specific justification using the numbers above]

## Key Conditions for Proceeding
[4-5 specific conditions]
""",
        agent=analyst,
        expected_output="Complete Investment Memorandum with real numbers and BUY or PASS recommendation."
    )

    crew = Crew(
        agents=[analyst],
        tasks=[task],
        verbose=True
    )

    for attempt in range(3):
        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < 2:
                print(f"Rate limit, waiting 60s... ({attempt+1}/3)")
                time.sleep(60)
            else:
                raise e

if __name__ == "__main__":
    memo = run_deal_analysis("MSFT", "NVS", 25.0)
    print("\n" + "="*60)
    print("INVESTMENT MEMORANDUM")
    print("="*60)
    print(memo)