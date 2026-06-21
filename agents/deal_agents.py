from crewai import Agent, LLM
import os
import litellm
litellm.cache = None
from dotenv import load_dotenv
from agents.mcp_client import get_company_facts, get_comparable_deals

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Analyze the target company's financials and calculate valuation metrics",
    backstory="You are a seasoned investment banking analyst with 10 years of M&A valuation experience.",
    tools=[get_company_facts, get_comparable_deals],
    llm=llm,
    verbose=True
)

news_analyst = Agent(
    role="Deal Intelligence Analyst",
    goal="Surface the top deal risks and synergy opportunities",
    backstory="You are an expert in financial due diligence and deal intelligence with deep knowledge of M&A risks.",
    tools=[],
    llm=llm,
    verbose=True
)

regulatory_analyst = Agent(
    role="Regulatory Risk Analyst",
    goal="Assess antitrust and regulatory risks and assign a risk score",
    backstory="You are a specialist in merger control and competition law with deep knowledge of DOJ, FTC, and EU regulations.",
    tools=[],
    llm=llm,
    verbose=True
)

synthesis_agent = Agent(
    role="Managing Director — M&A Advisory",
    goal="Synthesize all analysis into a professional Investment Memorandum",
    backstory="You are a Managing Director at a top investment bank with 20 years of M&A experience.",
    tools=[],
    llm=llm,
    verbose=True
)
