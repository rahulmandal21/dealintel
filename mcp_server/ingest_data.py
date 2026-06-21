import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# Seed M&A deal data — real public deals
deals = [
    {
        "id": "deal_1",
        "text": "Microsoft acquired Activision Blizzard for $68.7 billion in 2023. The deal was valued at 26x EBITDA. Gaming sector consolidation. FTC challenged the merger but courts allowed it.",
        "source": "SEC 8-K filing"
    },
    {
        "id": "deal_2",
        "text": "Hindalco Industries acquired Novelis for $6 billion in 2007. EV/EBITDA multiple of 9.5x. Aluminum rolling sector. Strategic acquisition to gain global flat-rolled products capacity.",
        "source": "SEC 8-K filing"
    },
    {
        "id": "deal_3",
        "text": "Amazon acquired MGM Studios for $8.5 billion in 2022. Deal multiple 27x EBITDA. Media and entertainment sector. Synergies through Prime Video content library expansion.",
        "source": "SEC 8-K filing"
    },
    {
        "id": "deal_4",
        "text": "Pfizer acquired BioNTech partner Wyeth for $68 billion. Pharma sector M&A. High regulatory scrutiny from FDA and FTC. Revenue synergies estimated at $4 billion annually.",
        "source": "SEC filing"
    },
    {
        "id": "deal_5",
        "text": "JP Morgan acquired First Republic Bank for $10.6 billion in 2023. Banking sector distressed acquisition. P/B multiple of 0.3x. FDIC assisted transaction during regional banking crisis.",
        "source": "SEC 8-K filing"
    },
    {
        "id": "deal_6",
        "text": "Elon Musk acquired Twitter for $44 billion in 2022. Deal at 16x revenue. Social media sector. High leverage with $13 billion in debt financing. Significant integration risks.",
        "source": "SEC filing"
    },
    {
        "id": "deal_7",
        "text": "Broadcom acquired VMware for $61 billion in 2023. Enterprise software sector. 12x revenue multiple. EU and UK regulators approved with conditions. Cost synergies of $8.5 billion targeted.",
        "source": "SEC 8-K filing"
    },
    {
        "id": "deal_8",
        "text": "Technology sector M&A faces high antitrust scrutiny from DOJ and FTC. Average EV/EBITDA multiples range from 15x to 30x. Key risks include integration failure and talent retention.",
        "source": "Industry report"
    },
    {
        "id": "deal_9",
        "text": "Banking sector mergers typically priced at 1.2x to 2.0x book value. Regulatory approval from Federal Reserve required. CRA compliance and branch overlap divestitures common conditions.",
        "source": "Industry report"
    },
    {
        "id": "deal_10",
        "text": "Pharmaceutical M&A driven by pipeline acquisition and patent cliff mitigation. Average deal multiples 4x to 8x revenue. FDA approval risk and clinical trial data are key valuation factors.",
        "source": "Industry report"
    }
]

# Upsert into Pinecone
records = []
for deal in deals:
    records.append({
        "id": deal["id"],
        "text": deal["text"],
        "source": deal["source"]
    })

index.upsert_records("deals", records)
print(f"✅ Ingested {len(records)} deals into Pinecone!")
print("Go check your Pinecone dashboard — you should see 10 records now.")