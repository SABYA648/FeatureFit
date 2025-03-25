import logging
import os
import json
from textwrap import dedent
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
import openai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
logger.info("Application started in multi-call mode")

###############################################################################
# SINGLE-CALL GPT ANALYSIS
###############################################################################
def generate_visual_analysis(feature_data):
    """
    Temperature is kept low (0.1) to limit variability and produce more logical,
    stable data. Everything else remains the same.
    """

    system_message = dedent("""
    You are an experienced product management assistant specializing in feature analysis.
    Your role is to provide comprehensive, realistic, and data-driven analysis of product features.
    You must be conservative in scoring and provide detailed justifications for all assessments.
    Focus on providing practical and contextual insights based on the provided feature details.
    """)

    custom_instructions = dedent("""
    Please provide a realistic confidence score on a 0-10 scale:
    - 0-3 if the user input is nonsense or severely incomplete,
    - 4-6 if there's partial or questionable data,
    - 7-8 if the data is decent or typical,
    - 9-10 if the input is extremely thorough with no ambiguities.

    For the default scenario (AI-Powered Transaction Fraud Detection + FinTech), 
    it should be at least 7 or higher if the user inputs appear coherent and feasible.
    """)

    prompt = dedent(f"""
    {custom_instructions}

    Analyze the following feature and provide a comprehensive evaluation in valid JSON.
    The user does NOT want to display raw JSON on screen, only visual outputs.

    Also provide any clarifying questions you'd like to ask the user as a JSON array named "clarifying_questions",
    e.g. "clarifying_questions": ["question1", "question2", ...]

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

    Return valid JSON only with no extra text or formatting.
    """)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000,
            top_p=1.0
        )
        final_text = response.choices[0].message.content.strip()
        return json.loads(final_text)
    except Exception as exc:
        logger.warning(f"GPT call failed: {exc}")
        return None

###############################################################################
# KEEPING THE SAME LAYOUT, EXCEPT UPDATED HEADING TEXT
###############################################################################
st.title("🚀 FeatureFit: AI-Powered Feature Prioritization")
st.markdown("No partial or JSON outputs will appear on screen. Only final visuals will be displayed.")

# 1) ABOUT
st.sidebar.markdown("## About")
st.sidebar.markdown("""
Evaluate your feature ideas fast with AI-powered insights. 
Use the defaults to see a high-confidence example!
""")

placeholder_confidence = st.sidebar.empty()
placeholder_assumptions = st.sidebar.empty()
placeholder_clarifying = st.sidebar.empty()

# QUICK LINKS at the bottom
st.sidebar.markdown("## Quick Links")
st.sidebar.markdown("[Portfolio](https://sabyasachimishra.dev)")
st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/sabyasachimishra007)")
st.sidebar.markdown("[GitHub](https://github.com/SABYA648)")
st.sidebar.markdown("[Blogs](https://medium.com/@sabya)\n")

with st.form("visual_form"):
    st.header("📌 Feature Configuration")
    col1, col2 = st.columns(2)
    with col1:
        feature_name = st.text_input("Feature Name *", "AI-Powered Transaction Fraud Detection")
    with col2:
        industry_option = st.selectbox(
            "Industry *",
            ['FinTech', 'EdTech', 'SaaS', 'Healthcare', 'E-commerce', 'AI Tools', 'Custom'],
            index=0
        )
        if industry_option == 'Custom':
            industry = st.text_input("Enter Custom Industry", "FinTech")
        else:
            industry = industry_option
    
    business_goal = st.text_input("Business Goal", "Increase Revenue")
    business_model = st.text_input("Business Model", "B2B SaaS")
    context = st.text_area("Additional Context", "Detects fraudulent transactions in real time using advanced AI.")
    
    proceed_button = st.form_submit_button("Analyze Feature")

if proceed_button:
    if not feature_name or not industry:
        st.error("Please provide both a Feature Name and Industry.")
        st.stop()

    # Build feature_data
    feature_data = {
        "feature_name": feature_name,
        "industry": industry,
        "business_goal": business_goal,
        "business_model": business_model,
        "context": context
    }

    with st.spinner("Generating final analysis (visual only)..."):
        final_analysis = generate_visual_analysis(feature_data)

    if not final_analysis:
        st.warning("No final analysis returned. Please retry later.")
        st.stop()

    # Extract fields
    rice_scores = final_analysis.get("rice_scores", {})
    moscow_priority = final_analysis.get("moscow_priority", {})
    risks = final_analysis.get("risks", {})
    business_value = final_analysis.get("business_value", {})
    implementation = final_analysis.get("implementation", {})
    mvp_recommendation = final_analysis.get("mvp_recommendation", "")
    roadmap = final_analysis.get("roadmap", [])
    industry_spec = final_analysis.get("industry_specific_considerations", "")
    recommended_monetization = final_analysis.get("recommended_monetization", "")
    overall_confidence = final_analysis.get("overall_confidence", 7.0)
    confidence_improvements = final_analysis.get("confidence_improvement_areas", {})
    swot_analysis = final_analysis.get("swot_analysis", {})
    assumption_line = final_analysis.get("assumption_line", "")
    clarifying_questions = final_analysis.get("clarifying_questions", [])

    # 2) OVERALL CONFIDENCE
    if overall_confidence < 5:
        conf_color = "#ff4b4b"
    elif overall_confidence < 7:
        conf_color = "#f4a261"
    else:
        conf_color = "#2a9d8f"

    confidence_html = f"""
    <div style="font-size:1.816em;">
      Overall Confidence: <span style="color:{conf_color};">{overall_confidence:.1f} / 10</span>
    </div>
    """
    placeholder_confidence.markdown(confidence_html, unsafe_allow_html=True)

    # 3) ASSUMPTIONS
    if assumption_line:
        placeholder_assumptions.write(f"**Assumptions**: {assumption_line}")

    # 4) CLARIFYING QUESTIONS
    if clarifying_questions:
        placeholder_clarifying.markdown("## Clarifying Questions")
        with placeholder_clarifying.form("clarifications"):
            clarifying_answers = {}
            for i, question in enumerate(clarifying_questions, start=1):
                answer = st.text_input(f"{i}) {question}", "")
                clarifying_answers[i] = answer
            done_btn = st.form_submit_button("Submit Clarifications")
        if done_btn:
            st.success("Clarifications submitted. (No further changes in this demo.)")

    # MAIN VISUAL ANALYSIS
    st.header("Visual Analysis")

    st.subheader("RICE Score & Priority")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### RICE Radar")
        r_vals = [
            rice_scores.get("Reach",{}).get("value", 0),
            rice_scores.get("Impact",{}).get("value", 0),
            rice_scores.get("Confidence",{}).get("value", 0),
            rice_scores.get("Effort",{}).get("value", 0)
        ]
        radar_data = pd.DataFrame({
            "Metric": ["Reach", "Impact", "Confidence", "Effort"],
            "Score": r_vals
        })
        radar_fig = px.line_polar(
            radar_data,
            r="Score",
            theta="Metric",
            line_close=True,
            color_discrete_sequence=['#2a9d8f'],
            template="plotly_white"
        )
        st.plotly_chart(radar_fig, use_container_width=True)

    with col2:
        st.markdown("#### Priority Gauge")
        final_rice_score = rice_scores.get("final_rice_score", 0)
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=final_rice_score,
            title={"text": "Feature Priority"},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': "darkblue"},
                'bar': {'color': "#264653"},
                'steps': [
                    {'range': [0, 40], 'color': "#e9c46a"},
                    {'range': [40, 70], 'color': "#f4a261"},
                    {'range': [70, 100], 'color': "#2a9d8f"}
                ]
            }
        ))
        st.plotly_chart(gauge_fig, use_container_width=True)

    st.markdown(f"**MoSCoW Priority**: {moscow_priority.get('category','N/A')}")
    st.markdown(f"*Justification*: {moscow_priority.get('justification','')}")

    st.subheader("Implementation Overview")
    st.markdown(f"**Complexity**: {implementation.get('complexity','N/A')}<br/>"
                f"**Dependencies**: {implementation.get('dependencies','N/A')}<br/>"
                f"**Timeline**: {implementation.get('timeline','N/A')}",
                unsafe_allow_html=True)

    st.subheader("RICE Scoring Breakdown")
    bar_df = pd.DataFrame({
        "Component": ["Reach","Impact","Confidence","Effort"],
        "Score": r_vals
    })
    bar_fig = px.bar(
        bar_df,
        x="Component",
        y="Score",
        color="Component",
        color_discrete_sequence=['#264653','#2a9d8f','#e9c46a','#f4a261'],
        text="Score",
        title="RICE Components"
    )
    bar_fig.update_traces(textfont_size=12, textangle=0, textposition="outside")
    st.plotly_chart(bar_fig, use_container_width=True)

    st.subheader("Risk Assessment")
    st.markdown(f"""
    - **Technical Complexity**: {risks.get('technical_complexity','N/A')}
    - **Business Model**: {risks.get('business_model','N/A')}
    - **Adoption**: {risks.get('adoption','N/A')}
    - **Competition**: {risks.get('competition','N/A')}
    """)

    st.subheader("MVP Roadmap")
    st.markdown(f"**Recommendation**: {mvp_recommendation}")
    if roadmap:
        st.markdown("**Roadmap Phases**:")
        roadmap_df = pd.DataFrame(roadmap)
        st.dataframe(roadmap_df.style.background_gradient(cmap='Blues'), use_container_width=True)
    else:
        st.info("No roadmap data provided.")

    st.subheader("Industry Insights")
    st.markdown(f"{industry_spec}")

    st.subheader("Monetization Strategy")
    st.markdown(f"{recommended_monetization}")

    st.subheader("Confidence Improvement Areas")
    if confidence_improvements:
        for k, v in confidence_improvements.items():
            st.markdown(f"• **{k}**: {v}")
    else:
        st.markdown("_No specific improvements provided._")

    st.subheader("SWOT Analysis")
    strengths = swot_analysis.get("Strengths","N/A")
    weaknesses = swot_analysis.get("Weaknesses","N/A")
    opportunities = swot_analysis.get("Opportunities","N/A")
    threats = swot_analysis.get("Threats","N/A")
    swot_table = f"""
    <style>
        .swot-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        .swot-table th, .swot-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .swot-table th {{
            background-color: #2a9d8f;
            color: white;
        }}
        .swot-table td {{
            background-color: #e9f5f3;
        }}
        .swot-table .opportunities {{
            background-color: #f4a261;
        }}
        .swot-table .threats {{
            background-color: #ff4b4b;
            color: white;
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
else:
    st.markdown("Fill out the form above and click **Analyze Feature** to see visual outputs.\n\nNote: Clarifying questions will appear in the left panel if provided by the AI analysis.")

###############################################################################
# FLOATING BUTTONS
###############################################################################
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
        background: #7851A9; /* Royal purple */
        color: #fff;
        padding: 8px 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        transition: background 0.2s;
    }
    .float-btns a:hover {
        background: #6C4397;
    }

    @media screen and (max-width: 768px) {
        .float-btns {
            bottom: 90px; 
            right: 10px;
            gap: 12px;
            padding: 16px;
        }
        .float-btns .blogs-link {
            display: none; /* hide Blogs in mobile */
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
