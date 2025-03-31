import os
import json
import logging
from textwrap import dedent
import hashlib

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import openai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
# PDF generation is currently disabled (Coming Soon)

# -----------------------------------------------------------------------------
# Logging & Environment Setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "")
logger.info("Application started in LIVE mode")

# -----------------------------------------------------------------------------
# CUSTOM CSS INJECTION (High Contrast & Button Styling)
# -----------------------------------------------------------------------------
def inject_custom_css():
    custom_css = """
    <style>
    /* Global high-contrast styling */
    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg, #1e1e1e);
        color: var(--text, #f0f0f0);
    }
    h1, h2, h3, h4 {
        font-family: 'Montserrat', sans-serif;
        color: var(--text, #f0f0f0);
    }
    input, textarea, select {
        border-radius: 6px;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 0.95rem;
        width: 100%;
    }
    .stMarkdown, .stTextInput>div>div>input {
        color: #333333;
        font-size: 1rem;
    }
    /* Floating buttons style */
    .float-btns a {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        background: #4a5eab;
        color: #fff;
        border-radius: 6px;
        padding: 10px 16px;
        text-decoration: none;
    }
    /* Sidebar customizations */
    .sidebar .sidebar-content {
        background-color: #2e2e2e;
        color: #f0f0f0;
    }
    .css-1d391kg {
        background-color: #444444;
        color: #f0f0f0;
    }
    /* Button styling for all buttons except main analysis */
    .stButton>button {
        background-color: white !important;
        color: red !important;
        border: 1px solid red !important;
        border-radius: 6px;
        padding: 10px 20px;
        transition: 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ffe6e6 !important;
    }
    /* Main Analysis button styling (inside container with id "main-analysis-btn-container") */
    #main-analysis-btn-container button {
        background-color: red !important;
        color: red !important;
        border: none !important;
        border-radius: 6px;
        padding: 10px 20px;
        transition: 0.3s ease;
    }
    #main-analysis-btn-container button:hover {
        background-color: darkred !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION (Clarifications Mechanism)
# -----------------------------------------------------------------------------
if 'clarifications' not in st.session_state:
    st.session_state['clarifications'] = ""
if 'gpt_response' not in st.session_state:
    st.session_state['gpt_response'] = None
if 'analysis_data' not in st.session_state:
    st.session_state['analysis_data'] = None

# -----------------------------------------------------------------------------
# STATE RESET FUNCTION (Reset Analysis Option)
# -----------------------------------------------------------------------------
def reset_analysis():
    st.session_state['clarifications'] = ""
    st.session_state['gpt_response'] = None
    st.session_state['analysis_data'] = None
    st.success("Analysis state has been reset. Clean slate, just like you needed!")

# -----------------------------------------------------------------------------
# GENERATE VISUAL ANALYSIS FUNCTION (LIVE MODE)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_visual_analysis(feature_data: dict) -> dict:
    """
    Constructs a detailed prompt and makes a live GPT API call.
    Returns the parsed JSON response.
    """
    system_message = dedent("""
        You are an experienced product management assistant specializing in feature analysis.
        Your role is to provide comprehensive, realistic, and data-driven analysis of product features.
        You must be conservative in scoring and provide detailed justifications for all assessments.
        Provide clarifying questions if you need more information from the user.
    """)
    custom_instructions = dedent("""
        Please provide a realistic confidence score on a 0-10 scale:
        - 0-3 if the user input is nonsense or severely incomplete,
        - 4-6 if there's partial or questionable data,
        - 7-8 if the data is decent or typical,
        - 9-10 if the input is extremely thorough with no ambiguities.

        Return valid JSON only with no extra text or formatting.
    """)
    prompt = dedent(f"""
        {custom_instructions}
    
        Analyze the following feature and provide a comprehensive evaluation in valid JSON.
        The user does NOT want to display raw JSON on screen, only final visuals.
        Also provide any clarifying questions you'd like to ask the user as a JSON array named "clarifying_questions".
    
        Feature Details:
        {json.dumps(feature_data, indent=2)}
    
        Mandatory JSON Structure:
        {{
          "rice_scores": {{
            "Reach": {{"value": int, "reason": string}},
            "Impact": {{"value": int, "reason": string}},
            "Confidence": {{"value": int, "reason": string}},
            "Effort": {{"value": int, "reason": string}},
            "final_rice_score": float
          }},
          "moscow_priority": {{
            "category": string,
            "justification": string
          }},
          "risks": {{
            "technical_complexity": string,
            "business_model": string,
            "adoption": string,
            "competition": string
          }},
          "business_value": {{
            "revenue_potential": string,
            "cost_savings": string,
            "market_positioning": string
          }},
          "implementation": {{
            "complexity": string,
            "dependencies": string,
            "timeline": string
          }},
          "mvp_recommendation": string,
          "roadmap": [
              {{
                  "Phase": string,
                  "Timeline": string,
                  "Milestone": string,
                  "Success Metric": string
              }}
          ],
          "industry_specific_considerations": string,
          "recommended_monetization": string,
          "overall_confidence": float,
          "confidence_improvement_areas": {{
              "Market Understanding": string,
              "Technical Feasibility": string,
              "Business Impact": string,
              "Implementation Clarity": string
          }},
          "swot_analysis": {{
            "Strengths": string,
            "Weaknesses": string,
            "Opportunities": string,
            "Threats": string
          }},
          "assumption_line": string,
          "clarifying_questions": [string, string, ...]
        }}
    """)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000,
            top_p=1.0
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as exc:
        logger.warning(f"GPT call failed: {exc}")
        return {}

# -----------------------------------------------------------------------------
# GENERATE PDF FUNCTION (Coming Soon placeholder)
# -----------------------------------------------------------------------------
def generate_pdf(analysis_data: dict) -> bytes:
    # For now, simply return a placeholder message
    return b"Coming Soon"

# -----------------------------------------------------------------------------
# DISPLAY ANALYSIS FUNCTION
# -----------------------------------------------------------------------------
def display_analysis(analysis_data: dict):
    # Extract RICE scores and values
    rice_scores = analysis_data.get("rice_scores", {})
    r_vals = [
        rice_scores.get("Reach", {}).get("value", 0),
        rice_scores.get("Impact", {}).get("value", 0),
        rice_scores.get("Confidence", {}).get("value", 0),
        rice_scores.get("Effort", {}).get("value", 0)
    ]
    
    # Display charts side-by-side in two columns
    col1, col2 = st.columns(2)
    with col1:
        # RICE Radar Chart
        radar_data = pd.DataFrame({
            "Metric": ["Reach", "Impact", "Confidence", "Effort"],
            "Score": r_vals
        })
        radar_fig = px.line_polar(
            radar_data,
            r="Score",
            theta="Metric",
            line_close=True,
            color_discrete_sequence=['#ffcc00'],
            template="plotly_dark",
            title="RICE Radar"
        )
        st.plotly_chart(radar_fig, use_container_width=True)
    with col2:
        # RICE Bar Chart with Effort annotation ("Lower is better")
        bar_data = pd.DataFrame({
            "Component": ["Reach", "Impact", "Confidence", "Effort"],
            "Score": r_vals
        })
        bar_fig = px.bar(
            bar_data,
            x="Component",
            y="Score",
            color="Component",
            color_discrete_sequence=['#00fa92','#b5838d','#ffae00','#00b8d9'],
            text="Score",
            title="RICE Components"
        )
        bar_fig.update_traces(textfont_size=12, textangle=0, textposition="outside")
        try:
            effort_value = bar_data.loc[bar_data["Component"] == "Effort", "Score"].iloc[0]
            bar_fig.add_annotation(
                x="Effort",
                y=effort_value + 5,
                text="Lower is better",
                showarrow=False,
                font=dict(color="#ffcc00", size=12)
            )
        except Exception:
            pass
        st.plotly_chart(bar_fig, use_container_width=True)
    
    # Save charts as PNGs for potential PDF export
    radar_fig.write_image("radar_chart.png", format="png", scale=2)
    bar_fig.write_image("bar_chart.png", format="png", scale=2)
    
    # Display additional analysis details
    st.header("Visual Analysis")
    
    st.subheader("RICE Justifications")
    justifications_list = []
    for comp in ["Reach", "Impact", "Confidence", "Effort"]:
        cinfo = rice_scores.get(comp, {})
        cVal = cinfo.get("value", 0)
        cReason = cinfo.get("reason", "No justification")
        justifications_list.append({
            "Component": comp,
            "Value": cVal,
            "Justification": cReason
        })
    st.table(pd.DataFrame(justifications_list))
    
    st.subheader("MoSCoW Priority")
    moscow_priority = analysis_data.get("moscow_priority", {})
    category_raw = moscow_priority.get("category", "N/A")
    justification_txt = moscow_priority.get("justification", "")
    cat_lower = category_raw.lower()
    if "must" in cat_lower:
        moscow_color = "#f25f5c"
    elif "should" in cat_lower:
        moscow_color = "#ffaa00"
    elif "could" in cat_lower:
        moscow_color = "#00fa92"
    else:
        moscow_color = "#94d0ff"
    st.markdown(
        f"<div style='font-size:1.1rem; color:{moscow_color};'><strong>{category_raw}</strong></div>",
        unsafe_allow_html=True
    )
    st.markdown(f"*Justification*: {justification_txt}")
    
    st.subheader("Implementation Overview")
    implementation = analysis_data.get("implementation", {})
    st.markdown(
        f"**Complexity**: {implementation.get('complexity','N/A')}<br/>"
        f"**Dependencies**: {implementation.get('dependencies','N/A')}<br/>"
        f"**Timeline**: {implementation.get('timeline','N/A')}",
        unsafe_allow_html=True
    )
    
    st.subheader("Risk Assessment")
    risks = analysis_data.get("risks", {})
    st.markdown(f"""
- **Technical Complexity**: {risks.get('technical_complexity','N/A')}
- **Business Model**: {risks.get('business_model','N/A')}
- **Adoption**: {risks.get('adoption','N/A')}
- **Competition**: {risks.get('competition','N/A')}
    """)
    
    st.subheader("MVP Roadmap")
    mvp_recommendation = analysis_data.get("mvp_recommendation", "")
    st.markdown(f"**Recommendation**: {mvp_recommendation}")
    roadmap = analysis_data.get("roadmap", [])
    if roadmap:
        st.markdown("**Roadmap Phases**:")
        roadmap_df = pd.DataFrame(roadmap)
        st.dataframe(roadmap_df.style.background_gradient(cmap='Blues'), use_container_width=True)
    else:
        st.info("No roadmap data provided.")
    
    st.subheader("Industry Insights")
    industry_spec = analysis_data.get("industry_specific_considerations", "")
    st.markdown(f"{industry_spec}")
    
    st.subheader("Monetization Strategy")
    recommended_monetization = analysis_data.get("recommended_monetization", "")
    st.markdown(f"{recommended_monetization}")
    
    st.subheader("Confidence Improvement Areas")
    confidence_improvements = analysis_data.get("confidence_improvement_areas", {})
    if confidence_improvements:
        for k, v in confidence_improvements.items():
            st.markdown(f"• **{k}**: {v}")
    else:
        st.markdown("_No specific improvements provided._")
    
    st.subheader("SWOT Analysis")
    swot_analysis = analysis_data.get("swot_analysis", {})
    strengths = swot_analysis.get("Strengths", "N/A")
    weaknesses = swot_analysis.get("Weaknesses", "N/A")
    opportunities = swot_analysis.get("Opportunities", "N/A")
    threats = swot_analysis.get("Threats", "N/A")
    swot_table = f"""
    <style>
        .swot-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        .swot-table th, .swot-table td {{
            border: 1px solid #3c3c3c;
            padding: 8px;
            text-align: left;
        }}
        .swot-table th {{
            background-color: #00b8d9;
            color: #ffffff;
        }}
        .swot-table td {{
            background-color: #2f3142;
            color: #ffffff;
        }}
        .swot-table .opportunities {{
            background-color: #ffaa00;
            color: #1d1f27;
        }}
        .swot-table .threats {{
            background-color: #f25f5c;
            color: #ffffff;
        }}
    </style>
    <table class="swot-table">
        <tr>
            <th>Strengths</th>
            <th>Weaknesses</th>
        </tr>
        <tr>
            <td>{strengths}</td>
            <td>{weaknesses}</td>
        </tr>
        <tr>
            <th>Opportunities</th>
            <th>Threats</th>
        </tr>
        <tr>
            <td class="opportunities">{opportunities}</td>
            <td class="threats">{threats}</td>
        </tr>
    </table>
    """
    st.markdown(swot_table, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAIN APPLICATION
# -----------------------------------------------------------------------------
def main():
    inject_custom_css()  # Inject custom CSS
    
    # -----------------------------------------------------------------------------
    # Sidebar: About, Confidence, Clarifying Questions, Reset, Extras
    # -----------------------------------------------------------------------------
    st.sidebar.markdown("## 🤖 About")
    st.sidebar.info("Evaluate your feature ideas fast with AI-powered insights. Use the form below and receive clarifying questions from GPT in the sidebar after analysis.")
    
    if st.session_state.get("analysis_data"):
        analysis_data = st.session_state["analysis_data"]
        overall_confidence = analysis_data.get("overall_confidence", 7.0)
        if overall_confidence < 5:
            conf_color = "#f25f5c"
        elif overall_confidence < 7:
            conf_color = "#ffaa00"
        else:
            conf_color = "#00fa92"
        st.sidebar.markdown(
            f"<div style='font-size:1.1rem;'><strong>Overall Confidence:</strong> <span style='color:{conf_color};'>{overall_confidence:.1f} / 10</span></div>",
            unsafe_allow_html=True
        )
        
        clarifying_questions = analysis_data.get("clarifying_questions", [])
        if clarifying_questions:
            with st.sidebar.expander("Clarifying Questions"):
                with st.form("clarifications_form"):
                    clarifying_answers = {}
                    for i, question in enumerate(clarifying_questions, start=1):
                        clarifying_answers[f"q{i}"] = st.text_input(f"{i}) {question}", "")
                    reanalyze = st.form_submit_button("Submit Clarifications & Re-Analyze")
                if reanalyze:
                    with st.spinner("Re-analyzing with clarifications... (Estimated time: 45 seconds)"):
                        new_clar_part = ""
                        for i, question in enumerate(clarifying_questions, start=1):
                            ans_text = clarifying_answers.get(f"q{i}", "").strip()
                            if ans_text:
                                new_clar_part += f"\n[QUESTION]: {question}\n[ANSWER]: {ans_text}\n"
                        st.session_state["clarifications"] += new_clar_part
                        new_feature_data = {
                            "feature_name": st.session_state["feature_name"],
                            "industry": st.session_state["industry"],
                            "business_goal": st.session_state["business_goal"],
                            "business_model": st.session_state["business_model"],
                            "context": "Detects fraudulent transactions in real time using advanced AI." + st.session_state["clarifications"]
                        }
                        st.session_state["analysis_data"] = generate_visual_analysis(new_feature_data)
                        if st.session_state["analysis_data"]:
                            st.sidebar.success("Re-analysis completed with clarifications.")
                        else:
                            st.sidebar.warning("Re-analysis did not return any result. Please retry.")
    
    if st.sidebar.button("Reset Analysis"):
        reset_analysis()
    
    st.sidebar.markdown("### Extra Features")
    if st.sidebar.button("Export Analysis to PDF"):
        st.sidebar.info("Export Analysis to PDF: Coming Soon!")
    if st.sidebar.button("Collaboration Mode"):
        st.sidebar.info("Collaboration Mode activated! Share your analysis with your team.")
    feedback = st.sidebar.text_input("Feedback (Rate GPT's accuracy):", "")
    if st.sidebar.button("Submit Feedback"):
        st.sidebar.success("Feedback submitted. Thanks for your input!")
    
    # -----------------------------------------------------------------------------
    # Main Form: Feature Configuration
    # -----------------------------------------------------------------------------
    if "feature_name" not in st.session_state:
        st.session_state["feature_name"] = "AI-Powered Transaction Fraud Detection"
    if "industry_option" not in st.session_state:
        st.session_state["industry_option"] = "FinTech"
    if "industry" not in st.session_state:
        st.session_state["industry"] = "FinTech"
    if "business_goal" not in st.session_state:
        st.session_state["business_goal"] = "Increase Revenue"
    if "business_model" not in st.session_state:
        st.session_state["business_model"] = "B2B SaaS"
    
    st.markdown("<h1 style='color:#ea4335;'>🚀 FeatureFit: AI-Powered Feature Prioritization</h1>", unsafe_allow_html=True)
    
    _business_models = [
        "B2B SaaS", "B2C SaaS", "Marketplace", "Subscription-based service", "Freemium",
        "Licensing", "On-premise software", "Advertising-based", "Pay-per-use",
        "Commission-based", "Affiliate marketing", "Consulting-based",
        "Peer-to-peer lending", "Crowdfunding", "Franchise model", "Direct sales",
        "Manufacturing", "Dropshipping", "Aggregator", "Community-based",
        "Data as a Service", "IoT-based", "Blockchain-based", "Open-source with support",
        "Hybrid licensing model", "Usage-based analytics", "Microtransactions",
        "In-app purchases", "Subscription box", "Government contracting"
    ]
    _industries = ["FinTech", "EdTech", "SaaS", "Healthcare", "E-commerce", "AI Tools", "Custom"]
    
    with st.form("analysis_form"):
        st.markdown("<h2 style='color:#4285f4;'>📌 Feature Configuration</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["feature_name"] = st.text_input(
                "Feature Name *",
                st.session_state["feature_name"]
            )
        with col2:
            try:
                idx_ind = _industries.index(st.session_state["industry_option"])
            except ValueError:
                idx_ind = 0
            st.session_state["industry_option"] = st.selectbox(
                "Industry *",
                _industries,
                index=idx_ind
            )
            if st.session_state["industry_option"] == "Custom":
                st.session_state["industry"] = st.text_input(
                    "Enter Custom Industry",
                    st.session_state["industry"]
                )
            else:
                st.session_state["industry"] = st.session_state["industry_option"]
    
        st.session_state["business_goal"] = st.text_input(
            "Business Goal",
            st.session_state["business_goal"]
        )
    
        try:
            idx_bm = _business_models.index(st.session_state["business_model"])
        except ValueError:
            idx_bm = 0
        st.session_state["business_model"] = st.selectbox(
            "Business Model",
            _business_models,
            index=idx_bm
        )
    
        base_context = "Detects fraudulent transactions in real time using advanced AI."
        if st.session_state["clarifications"]:
            base_context += "\n" + st.session_state["clarifications"]
    
        st.session_state["context"] = st.text_area(
            "Additional Context",
            base_context
        )
        submitted = st.form_submit_button("Analyze Feature")
    
    if submitted:
        with st.spinner("Generating final analysis (takes up to 45 seconds)..."):
            feature_data = {
                "feature_name": st.session_state["feature_name"],
                "industry": st.session_state["industry"],
                "business_goal": st.session_state["business_goal"],
                "business_model": st.session_state["business_model"],
                "context": st.session_state["context"]
            }
            st.session_state["analysis_data"] = generate_visual_analysis(feature_data)
    
    if st.session_state.get("analysis_data"):
        display_analysis(st.session_state["analysis_data"])
    else:
        st.markdown(
            "Configure your inputs above and click **Analyze Feature** to get results. Any clarifying questions from GPT will appear in the sidebar after analysis."
        )
    
    # -----------------------------------------------------------------------------
    # Floating Buttons (Quick Links)
    # -----------------------------------------------------------------------------
    st.markdown(
        """
        <style>
        .float-btns {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 9999;
        }
        .float-btns a {
            text-decoration: none;
            font-size: 14px;
            background: #4a5eab;
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            transition: background 0.2s;
        }
        .float-btns a:hover {
            background: #3c4b90;
        }
        @media screen and (max-width: 768px) {
            .float-btns {
                bottom: 90px;
                right: 10px;
                gap: 12px;
                padding: 16px;
            }
            .float-btns .blogs-link {
                display: none;
            }
        }
        </style>
        <div class="float-btns">
            <a href="https://sabyasachimishra.dev" target="_blank">Portfolio</a>
            <a href="https://www.linkedin.com/in/sabyasachimishra007" target="_blank">LinkedIn</a>
            <a href="https://github.com/SABYA648" target="_blank">GitHub</a>
            <a class="blogs-link" href="https://medium.com/@sabya" target="_blank">Blogs</a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()