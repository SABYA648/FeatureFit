import logging
import os
import json
from textwrap import dedent

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

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "")
logger.info("Application started in multi-call mode")


###############################################################################
# GPT ANALYSIS
###############################################################################
def generate_visual_analysis(feature_data: dict) -> dict:
    """
    Temperature is kept low (0.1) to limit variability and produce more logical,
    stable data. Everything else remains the same.

    Creates a ChatCompletion call to GPT-4, 
    returning a JSON structure with RICE scores, clarifying_questions, etc.
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

    if not openai.api_key:
        return {}

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
        return json.loads(response.choices[0].message.content.strip())
    except Exception as exc:
        logger.warning(f"GPT call failed: {exc}")
        return {}


def display_analysis(analysis_data: dict):
    """
    Displays the final analysis after it has been generated,
    including RICE visuals, clarifications, etc.
    """
    rice_scores = analysis_data.get("rice_scores", {})
    moscow_priority = analysis_data.get("moscow_priority", {})
    risks = analysis_data.get("risks", {})
    business_value = analysis_data.get("business_value", {})
    implementation = analysis_data.get("implementation", {})
    mvp_recommendation = analysis_data.get("mvp_recommendation", "")
    roadmap = analysis_data.get("roadmap", [])
    industry_spec = analysis_data.get("industry_specific_considerations", "")
    recommended_monetization = analysis_data.get("recommended_monetization", "")
    overall_confidence = analysis_data.get("overall_confidence", 7.0)
    confidence_improvements = analysis_data.get("confidence_improvement_areas", {})
    swot_analysis = analysis_data.get("swot_analysis", {})
    assumption_line = analysis_data.get("assumption_line", "")

    # 1) Overall Confidence
    if overall_confidence < 5:
        conf_color = "#f25f5c"  # bright red
    elif overall_confidence < 7:
        conf_color = "#ffaa00"  # neon orange
    else:
        conf_color = "#00fa92"  # neon green

    # Center analysis visuals
    st.header("Visual Analysis")

    # RICE Score
    st.subheader("RICE Score")
    col_left, col_right = st.columns(2)

    # Radar
    with col_left:
        st.markdown("#### RICE Radar")
        r_vals = [
            rice_scores.get("Reach",{}).get("value",0),
            rice_scores.get("Impact",{}).get("value",0),
            rice_scores.get("Confidence",{}).get("value",0),
            rice_scores.get("Effort",{}).get("value",0)
        ]
        radar_data = pd.DataFrame({
            "Metric": ["Reach","Impact","Confidence","Effort"],
            "Score": r_vals
        })
        # Use futuristic color palette
        radar_fig = px.line_polar(
            radar_data,
            r="Score",
            theta="Metric",
            line_close=True,
            color_discrete_sequence=['#00b8d9'],
            template="plotly_white"
        )
        st.plotly_chart(radar_fig, use_container_width=True)

    # Gauge
    with col_right:
        st.markdown("#### Priority Gauge")
        final_rice_score = rice_scores.get("final_rice_score", 0)
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=final_rice_score,
            title={"text": "Feature Priority", "font": {"color": "#94d0ff"}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': "#aaa", "tickwidth":1},
                'bar': {'color': "#00fa92"},
                'bgcolor': "#222222",
                'steps': [
                    {'range': [0, 40], 'color': "#6d6875"},
                    {'range': [40, 70], 'color': "#b5838d"},
                    {'range': [70, 100], 'color': "#00b8d9"}
                ]
            },
            number={"font":{"color":"#94d0ff"}}
        ))
        gauge_fig.update_layout(
            paper_bgcolor="#1d1f27",
            font={"color":"#94d0ff"}
        )
        st.plotly_chart(gauge_fig, use_container_width=True)

    # RICE Justifications
    st.markdown("#### RICE Justifications")
    justifications_list = []
    for comp in ["Reach","Impact","Confidence","Effort"]:
        cinfo = rice_scores.get(comp,{})
        cVal = cinfo.get("value",0)
        cReason = cinfo.get("reason","No justification")
        justifications_list.append({
            "Component": comp,
            "Value": cVal,
            "Justification": cReason
        })
    st.table(pd.DataFrame(justifications_list))

    # MoSCoW Priority
    st.subheader("MoSCoW Priority")
    category_raw = moscow_priority.get("category","N/A")
    justification_txt = moscow_priority.get("justification","")
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
        f"<div style='font-size:1.11rem; color:{moscow_color};'><strong>{category_raw}</strong></div>",
        unsafe_allow_html=True
    )
    st.markdown(f"*Justification*: {justification_txt}")

    # Implementation
    st.subheader("Implementation Overview")
    st.markdown(
        f"**Complexity**: {implementation.get('complexity','N/A')}<br/>"
        f"**Dependencies**: {implementation.get('dependencies','N/A')}<br/>"
        f"**Timeline**: {implementation.get('timeline','N/A')}",
        unsafe_allow_html=True
    )

    # RICE Scoring Breakdown
    st.subheader("RICE Scoring Breakdown")
    breakdown_data = pd.DataFrame({
        "Component": ["Reach","Impact","Confidence","Effort"],
        "Score": r_vals
    })
    bar_fig = px.bar(
        breakdown_data,
        x="Component",
        y="Score",
        color="Component",
        color_discrete_sequence=['#00fa92','#b5838d','#ffae00','#00b8d9'],
        text="Score",
        title="RICE Components"
    )
    bar_fig.update_traces(textfont_size=12, textangle=0, textposition="outside")
    bar_fig.update_layout(
        plot_bgcolor="#1d1f27",
        paper_bgcolor="#1d1f27",
        font={"color":"#94d0ff"}
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # Risks
    st.subheader("Risk Assessment")
    st.markdown(f"""
- **Technical Complexity**: {risks.get('technical_complexity','N/A')}
- **Business Model**: {risks.get('business_model','N/A')}
- **Adoption**: {risks.get('adoption','N/A')}
- **Competition**: {risks.get('competition','N/A')}
    """)

    # MVP Roadmap
    st.subheader("MVP Roadmap")
    st.markdown(f"**Recommendation**: {mvp_recommendation}")
    if roadmap:
        st.markdown("**Roadmap Phases**:")
        roadmap_df = pd.DataFrame(roadmap)
        st.dataframe(roadmap_df.style.background_gradient(cmap='Blues'), use_container_width=True)
    else:
        st.info("No roadmap data provided.")

    # Industry Insights
    st.subheader("Industry Insights")
    st.markdown(f"{industry_spec}")

    # Monetization
    st.subheader("Monetization Strategy")
    st.markdown(f"{recommended_monetization}")

    # Confidence Improvement
    st.subheader("Confidence Improvement Areas")
    if confidence_improvements:
        for k, v in confidence_improvements.items():
            st.markdown(f"• **{k}**: {v}")
    else:
        st.markdown("_No specific improvements provided._")

    # SWOT
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


def main():
    # State initialization
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
    if "clarifications" not in st.session_state:
        st.session_state["clarifications"] = ""
    if "analysis_data" not in st.session_state:
        st.session_state["analysis_data"] = {}

    st.title("🚀 FeatureFit: AI-Powered Feature Prioritization")

    # Insert global CSS to transform everything to a hi-tech, modern theme
    st.markdown(
        """
        <style>
        /* Global background and text color */
        body, .css-12oz5g7, .css-1dp5vir {
            background-color: #1d1f27 !important;
            color: #94d0ff !important;
        }

        /* Headers, subheaders styling */
        h1, h2, h3, h4, h5, h6 {
            color: #00ffa2 !important;
        }

        /* Make forms and containers have a mild neon border */
        .stTextInput, .stSelectbox, .stTextArea, .stDataFrame, .stTable {
            border: 1px solid #3c3c6c !important;
            background-color: #2f3142 !important;
        }
        .stDataFrame table, .stTable table {
            background-color: #2f3142 !important;
            color: #94d0ff !important;
        }

        /* Buttons */
        .stButton>button {
            background-color: #282a35 !important;
            color: #94d0ff !important;
            border: 1px solid #00b8d9;
            transition: background 0.2s, color 0.2s;
        }
        .stButton>button:hover {
            background-color: #00b8d9 !important;
            color: #1d1f27 !important;
        }

        /* Toast/spinner */
        .stSpinner, .stToast {
            background-color: #2f3142 !important;
            color:#94d0ff !important;
        }

        /* Sidebar specifics */
        [data-testid="stSidebar"] > div {
            background-color: #282a35 !important;
        }

        /* Horizontal lines, headings, code blocks */
        hr {
            border-top: 1px solid #ffffff33 !important;
        }

        code, pre {
            background-color: #2f3142 !important;
            color: #94d0ff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # SIDEBAR placeholders
    st.sidebar.markdown("## About")
    st.sidebar.markdown("""
Evaluate your feature ideas fast with AI-powered insights. 
Use the form below, and if there are clarifying questions from GPT, 
they will appear here in the sidebar after the first analysis.
    """)
    placeholder_confidence = st.sidebar.empty()
    placeholder_assumptions = st.sidebar.empty()
    placeholder_clarifying = st.sidebar.empty()
    st.sidebar.markdown("## Quick Links")
    st.sidebar.markdown("[Portfolio](https://sabyasachimishra.dev)")
    st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/sabyasachimishra007)")
    st.sidebar.markdown("[GitHub](https://github.com/SABYA648)")
    st.sidebar.markdown("[Blogs](https://medium.com/@sabya)\n")

    # Extended business models
    _business_models = [
        "B2B SaaS", "B2C SaaS", "Marketplace", "Subscription-based service", "Freemium",
        "Licensing", "On-premise software", "Advertising-based", "Pay-per-use",
        "Commission-based", "Affiliate marketing", "Consulting-based",
        "Peer-to-peer lending", "Crowdfunding", "Franchise model", "Direct sales",
        "Manufacturing", "Dropshipping", "Aggregator", "Community-based",
        "Data as a Service", "IoT-based", "Blockchain-based", "Open-source with support",
        "Hybrid licensing model", "Usage-based analytics", "Microtransactions",
        "In-app purchases", "Subscription box", "Government contracting",
        "Non-profit donor-funded", "Reseller model", "White-labeling",
        "Professional services", "Ecommerce store"
    ]

    # Industry options
    _industries = ["FinTech", "EdTech", "SaaS", "Healthcare", "E-commerce", "AI Tools", "Custom"]

    with st.form("analysis_form"):
        st.header("📌 Feature Configuration")
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

        # business model
        try:
            idx_bm = _business_models.index(st.session_state["business_model"])
        except ValueError:
            idx_bm = 0

        st.session_state["business_model"] = st.selectbox(
            "Business Model",
            _business_models,
            index=idx_bm
        )

        # Base context + clarifications
        base_context = "Detects fraudulent transactions in real time using advanced AI."
        if st.session_state["clarifications"]:
            base_context += "\n" + st.session_state["clarifications"]

        st.session_state["context"] = st.text_area(
            "Additional Context",
            base_context
        )

        submitted = st.form_submit_button("Analyze Feature")

    # If user clicks analyze
    if submitted:
        with st.spinner("Generating final analysis (visual only)..."):
            feature_data = {
                "feature_name": st.session_state["feature_name"],
                "industry": st.session_state["industry"],
                "business_goal": st.session_state["business_goal"],
                "business_model": st.session_state["business_model"],
                "context": st.session_state["context"]
            }
            st.session_state["analysis_data"] = generate_visual_analysis(feature_data)

    # If we have analysis data, display it
    if st.session_state["analysis_data"]:
        analysis_data = st.session_state["analysis_data"]
        overall_confidence = analysis_data.get("overall_confidence", 7.0)
        assumption_line = analysis_data.get("assumption_line", "")
        clarifying_questions = analysis_data.get("clarifying_questions", [])

        # Left sidebar placeholders
        if overall_confidence < 5:
            conf_color = "#f25f5c"
        elif overall_confidence < 7:
            conf_color = "#ffaa00"
        else:
            conf_color = "#00fa92"

        placeholder_confidence.markdown(
            f"""
            <div style="font-size:1.1rem;">
                <strong>Overall Confidence:</strong> 
                <span style="color:{conf_color};">{overall_confidence:.1f} / 10</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        if assumption_line:
            placeholder_assumptions.markdown(f"**Assumptions**: {assumption_line}")
        else:
            placeholder_assumptions.markdown("")

        if clarifying_questions:
            placeholder_clarifying.markdown("## Clarifying Questions")
            with placeholder_clarifying.form("clarifications_form"):
                clarifying_answers = {}
                for i, question in enumerate(clarifying_questions, start=1):
                    clarifying_answers[f"q{i}"] = st.text_input(f"{i}) {question}", "")
                reanalyze = st.form_submit_button("Submit Clarifications & Re-Analyze")

            if reanalyze:
                with st.spinner("Re-analyzing with clarifications..."):
                    # Append clarifications
                    new_clar_part = ""
                    for i, question in enumerate(clarifying_questions, start=1):
                        ans_text = clarifying_answers.get(f"q{i}","").strip()
                        if ans_text:
                            new_clar_part += f"\n[QUESTION]: {question}\n[ANSWER]: {ans_text}\n"

                    st.session_state["clarifications"] += new_clar_part

                    # Trigger new analysis
                    new_feature_data = {
                        "feature_name": st.session_state["feature_name"],
                        "industry": st.session_state["industry"],
                        "business_goal": st.session_state["business_goal"],
                        "business_model": st.session_state["business_model"],
                        "context": "Detects fraudulent transactions in real time using advanced AI."
                                   + st.session_state["clarifications"]
                    }
                    st.session_state["analysis_data"] = generate_visual_analysis(new_feature_data)

                    if st.session_state["analysis_data"]:
                        st.success("Re-analysis completed with clarifications.")
                        display_analysis(st.session_state["analysis_data"])
                    else:
                        st.warning("Re-analysis did not return any result. Please retry.")
                return  # end function
        else:
            placeholder_clarifying.markdown("")

        # If clarifications not triggered or no clarifying questions, display analysis
        display_analysis(analysis_data)
    else:
        st.markdown(
            "Configure your inputs above and click **Analyze Feature** to get results. "
            "Any clarifying questions from GPT will appear in the left sidebar after analysis."
        )

    # FLOATING BUTTONS
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
