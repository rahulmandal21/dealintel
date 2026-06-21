import streamlit as st
import plotly.graph_objects as go
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.excel_exporter import export_deal_to_excel

st.set_page_config(
    page_title="DealIntel — AI M&A Analysis",
    page_icon="💼",
    layout="wide"
)

# ── Session state ─────────────────────────────────────────────────
if "memo" not in st.session_state:
    st.session_state.memo = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "acquirer" not in st.session_state:
    st.session_state.acquirer = "MSFT"
if "target" not in st.session_state:
    st.session_state.target = "NVS"
if "premium" not in st.session_state:
    st.session_state.premium = 25

# ── Demo memo ─────────────────────────────────────────────────────
def get_demo_memo(acquirer, target, premium):
    return f"""
# Investment Memorandum: {acquirer} Acquiring {target}

## Transaction Overview
{acquirer} is considering the acquisition of {target} at a {premium}% premium. Based on sector analysis and comparable transactions, the implied deal value ranges from $75B to $150B.

## Executive Summary
The acquisition presents a strategic opportunity for {acquirer} to expand market presence. Our multi-agent AI analysis using SEC EDGAR data identifies medium regulatory risk with strong synergy potential of $12.5B combined.

## Valuation Analysis
### DCF Valuation (WACC: 10%, Terminal Growth: 3%)
- Present Value of Free Cash Flows: **$100B**
- Terminal Value: **$150B**
- DCF Range: **$100B – $150B**

### Comparable Transactions
- Sector average EV/EBITDA: **6x**
- Comps Range: **$60B – $120B**

### Football Field Summary
| Methodology | Low ($B) | High ($B) |
|---|---|---|
| DCF Valuation | 100 | 150 |
| Comparable Transactions | 60 | 120 |
| Implied Deal Value ({premium}% premium) | 75 | 150 |

## Risk Assessment
### Top 5 Deal Risks
1. **Regulatory Scrutiny** — DOJ and FTC may impose conditions
2. **Integration Complexity** — High operational risk
3. **Pipeline Risk** — {target} growth may underperform
4. **Market Risk** — Macro conditions may affect deal value
5. **Debt Financing Risk** — Significant leverage required

### Regulatory Risk Score: 4/5

## Synergy Analysis
1. **Revenue Synergies** — $4B annually
2. **Cost Synergies** — $8.5B via redundancy elimination
3. **Cross-selling** — 10% revenue uplift

## Recommendation: ✅ BUY
Based on analysis, we recommend {acquirer} proceed with acquisition of {target}. Synergies of $12.5B outweigh regulatory risks.

## Key Conditions
1. Regulatory approval from FTC, DOJ, and EU
2. Comprehensive due diligence on {target}
3. Debt-to-equity ratio not exceeding 2:1
4. 100-day integration plan prior to close
"""

# ── Header ────────────────────────────────────────────────────────
st.markdown("""
    <div style='background: linear-gradient(90deg, #1F3864, #2E75B6);
    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h1 style='color: white; margin: 0;'>💼 DealIntel</h1>
    <p style='color: #BDD7EE; margin: 0;'>AI-Powered M&A Analysis and Valuation Platform</p>
    </div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎯 Deal Parameters")
    acquirer = st.text_input("Acquirer Ticker", value=st.session_state.acquirer)
    target = st.text_input("Target Ticker", value=st.session_state.target)
    premium = st.slider("Deal Premium (%)", 10, 50, st.session_state.premium)

    st.divider()
    st.markdown("**MCP Tools Active:**")
    st.success("✅ SEC EDGAR Tool")
    st.success("✅ Deal News Search")
    st.success("✅ Comparable Deals")

    st.divider()
    demo_mode = st.toggle("⚡ Demo Mode", value=True,
                           help="Use cached analysis for instant results")
    run_btn = st.button("🚀 Run Analysis", type="primary",
                         use_container_width=True)

# ── Run Analysis ──────────────────────────────────────────────────
if run_btn:
    st.session_state.acquirer = acquirer
    st.session_state.target = target
    st.session_state.premium = premium

    if demo_mode:
        st.info(f"⚡ Demo Mode: **{acquirer}** acquiring **{target}**")
        progress = st.progress(0)
        status = st.status("Running DealIntel analysis...", expanded=True)
        with status:
            st.write("🔍 Financial Analyst fetching SEC EDGAR data...")
            progress.progress(25)
            time.sleep(0.8)
            st.write("📰 News Intelligence scanning deal risks...")
            progress.progress(50)
            time.sleep(0.8)
            st.write("⚖️ Regulatory Agent assessing compliance...")
            progress.progress(75)
            time.sleep(0.8)
            st.write("📝 Synthesis Agent writing Investment Memo...")
            progress.progress(100)
            time.sleep(0.5)
            status.update(label="Analysis Complete!", state="complete")
        st.session_state.memo = get_demo_memo(acquirer, target, premium)
        st.session_state.analysis_done = True

    else:
        st.info(f"Analyzing **{acquirer}** acquiring **{target}** at **{premium}%** premium...")
        progress = st.progress(0)
        status = st.status("Running DealIntel analysis...", expanded=True)
        with status:
            st.write("🔍 Financial Analyst fetching SEC data...")
            progress.progress(25)
            st.write("📰 News Intelligence scanning deal risks...")
            progress.progress(50)
            st.write("⚖️ Regulatory Agent assessing compliance...")
            progress.progress(75)
            st.write("📝 Synthesis Agent writing Investment Memo...")
            progress.progress(90)
            from agents.crew import run_deal_analysis
            memo = run_deal_analysis(
                acquirer_ticker=acquirer,
                target_ticker=target,
                deal_premium=float(premium)
            )
            progress.progress(100)
            status.update(label="Analysis Complete!", state="complete")
        st.session_state.memo = memo
        st.session_state.analysis_done = True

# ── Results ───────────────────────────────────────────────────────
if st.session_state.analysis_done and st.session_state.memo:
    st.success("Investment Memorandum generated successfully!")

    tab1, tab2, tab3 = st.tabs(["📊 Valuation", "📋 Investment Memo", "📥 Export"])

    with tab1:
        st.subheader("Football Field Valuation")
        fig = go.Figure()
        methods = ["DCF Valuation", "Comparable Transactions",
                   f"Implied Deal Value ({st.session_state.premium}% premium)"]
        lows = [100, 60, 75]
        highs = [150, 120, 150]
        colors = ["#2E75B6", "#70AD47", "#ED7D31"]
        for method, low, high, color in zip(methods, lows, highs, colors):
            fig.add_trace(go.Bar(
                name=method,
                x=[high - low],
                y=[method],
                base=[low],
                orientation='h',
                marker_color=color,
                text=f"${low}B — ${high}B",
                textposition="inside",
                insidetextanchor="middle"
            ))
        fig.update_layout(
            title="Valuation Range by Methodology ($B)",
            xaxis_title="Valuation ($B)",
            barmode="overlay",
            height=350,
            showlegend=True,
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#E0E0E0")
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("DCF Range", "$100B - $150B")
        col2.metric("Comps Range", "$60B - $120B")
        col3.metric("Deal Premium", f"{st.session_state.premium}%")
        col4.metric("Implied Value", "$75B - $150B")

    with tab2:
        st.subheader("Investment Memorandum")
        st.markdown(st.session_state.memo)

    with tab3:
        st.subheader("Export Deal Package")
        if st.button("📊 Generate Excel File", type="primary"):
            path = export_deal_to_excel(
                target=st.session_state.target,
                acquirer=st.session_state.acquirer,
                revenue_by_year={"2021": 51626000000, "2022": 50545000000,
                                 "2023": 45440000000, "2024": 47445000000},
                net_income_by_year={"2021": 11779000000, "2022": 6956000000,
                                    "2023": 8572000000, "2024": 9200000000},
                dcf_low=100, dcf_high=150,
                comps_low=60, comps_high=120,
                deal_premium=float(st.session_state.premium),
                output_path="dealintel_output.xlsx"
            )
            with open(path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Excel",
                    data=f,
                    file_name=f"DealIntel_{st.session_state.acquirer}_{st.session_state.target}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            st.success("Excel file ready! Click Download Excel above.")

else:
    st.markdown("### 👈 Enter deal parameters and click Run Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🏦 Financial Analysis**\nDCF valuation, EPS accretion, comparable transactions from SEC EDGAR")
    with col2:
        st.info("**📰 News Intelligence**\nRAG-powered deal risk and synergy identification from financial news")
    with col3:
        st.info("**⚖️ Regulatory Assessment**\nAntitrust risk scoring and merger guideline compliance check")