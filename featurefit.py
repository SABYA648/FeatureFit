import streamlit as st
import os
from dotenv import load_dotenv
import openai
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from textwrap import dedent

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Mobile-Friendly Meta & CSS ---
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* Responsive typography and layout for mobile devices */
body {
    font-family: sans-serif;
    line-height: 1.5;
}
div[data-testid="stExpander"] details summary p {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 0;
}
.risk-high { color: #ff4b4b; }
.risk-med { color: #ffa600; }
.risk-low { color: #00d154; }

/* Adjust padding and margins for small screens */
@media only screen and (max-width: 600px) {
    .css-1d391kg { padding: 0 10px !important; }
    h1, h2, h3, h4 { font-size: 1.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# Function to generate analysis using the new ChatCompletion interface
def generate_analysis(feature_name, industry, business_goal, business_model, context):
    prompt = dedent(f"""
    You are an experienced product management assistant analyzing product features.
    Given the following inputs, provide a detailed analysis using the RICE framework (Reach, Impact, Confidence, Effort) and risk assessment, and then provide recommendations for MVP and monetization.
    
    Additionally, evaluate how much the provided input and your output analysis make sense and provide an overall confidence score (always on the lower side for conservatism). Include a detailed technical explanation of how the analysis was derived.
    
    If you detect that the provided data is nonsensical or merely test data (BS), include a mild roast in the "roast" field.
    
    Use the following inputs:
    - Feature Name: {feature_name}
    - Industry: {industry}
    - Business Goal: {business_goal if business_goal else "N/A"}
    - Business Model: {business_model if business_model else "N/A"}
    - Additional Context: {context if context else "N/A"}
    
    Return the analysis in strictly valid JSON with the following structure:
    {{
      "rice_scores": {{
        "Reach": {{"value": int, "reason": string}},
        "Impact": {{"value": int, "reason": string}},
        "Confidence": {{"value": int, "reason": string}},
        "Effort": {{"value": int, "reason": string}},
        "final_rice_score": float
      }},
      "risks": {{
        "technical_complexity": string,
        "business_model": string,
        "adoption": string,
        "competition": string
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
      "technical_explanation": string,
      "roast": string,
      "swot_analysis": {{
          "Strengths": string,
          "Weaknesses": string,
          "Opportunities": string,
          "Threats": string
      }}
    }}
    Only return valid JSON.
    """)
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful product management assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
    )
    analysis_text = response.choices[0].message.content.strip()
    try:
        analysis = json.loads(analysis_text)
    except json.JSONDecodeError:
        st.error("Network error: please try again")
        analysis = None
    return analysis

# Custom CSS for styling expanders and risk text
st.markdown("""
<style>
.custom-warning { 
    background-color: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 1rem;
    margin: 1rem 0;
}
.feature-pill {
    background-color: #e9f5f3;
    border-radius: 20px;
    padding: 0.5rem 1rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("🚀 AI-Powered Feature Prioritization Tool")
st.markdown("""
**Quickly assess and prioritize your product features using AI-driven RICE scoring, risk analysis, and actionable recommendations.**
""")

# --- Sidebar: About the Tool ---
st.sidebar.markdown("## About")
st.sidebar.markdown("""
Evaluate your feature ideas fast with AI-powered insights. Use the defaults to see a high-confidence example!
""")

# --- Input Section ---
with st.form("feature_inputs"):
    st.header("📌 Feature Details")
    
    # Mandatory inputs: Feature Name and Industry with default test values
    col1, col2 = st.columns(2)
    with col1:
        # Changed default to include a FinTech keyword ("Transaction") for high confidence analysis
        feature_name = st.text_input("Feature Name*", value="AI-Powered Transaction Fraud Detection")
    with col2:
        industry_option = st.selectbox(
            "Industry*",
            ['FinTech', 'EdTech', 'SaaS', 'Healthcare', 'E-commerce', 'AI Tools', 'Custom'],
            index=0,
            help="Select industry for contextual analysis"
        )
        if industry_option == 'Custom':
            industry = st.text_input("Enter Custom Industry*", value="FinTech")
        else:
            industry = industry_option
    
    # Optional parameters: Business Goal, Business Model, and Additional Context with default values
    st.subheader("Optional Parameters")
    business_goal_option = st.selectbox(
        "Business Goal",
        ['None', 'Improve User Experience', 'Increase Revenue', 'Reduce Costs', 'Gain Competitive Advantage', 'Custom'],
        index=2,
        help="Primary business objective for this feature"
    )
    if business_goal_option == 'Custom':
        business_goal = st.text_input("Enter custom Business Goal", value="Increase Revenue")
    else:
        business_goal = business_goal_option if business_goal_option != 'None' else ""
    
    business_model_option = st.selectbox(
        "Business Model",
        ['None', 'B2B SaaS', 'One-time Purchase', 'API Licensing', 'Freemium', 'Ads', 'Custom'],
        index=1,
        help="Preferred monetization approach"
    )
    if business_model_option == 'Custom':
        business_model = st.text_input("Enter custom Business Model", value="B2B SaaS")
    else:
        business_model = business_model_option if business_model_option != 'None' else ""
    
    context = st.text_area("Additional Context (Optional)", 
                           value="This feature leverages advanced AI to detect fraudulent transactions in real time using machine learning algorithms.",
                           help="Provide any extra details, background, or constraints related to the feature.")
    
    submitted = st.form_submit_button("Analyze Feature")

# --- Process Submission ---
if submitted and feature_name and industry:
    # Lower confidence flag: For FinTech, if feature name lacks typical keywords.
    fintech_keywords = ["bank", "loan", "payment", "credit", "account", "transaction", "investment", "insurance"]
    lower_confidence_flag = False
    if industry.lower() == "fintech" and not any(keyword in feature_name.lower() for keyword in fintech_keywords):
        lower_confidence_flag = True

    # Show spinner while generating analysis
    with st.spinner("Generating analysis, please wait..."):
        analysis = generate_analysis(feature_name, industry, business_goal, business_model, context)
    if analysis is None:
        st.error("No analysis was generated due to a network error. Please try again.")
        st.stop()

    st.header("📊 Analysis Results")
    
    # Sidebar: Overall Confidence Score and Technical Explanation
    if "overall_confidence" in analysis:
        conf_score = analysis["overall_confidence"]
    else:
        conf_score = 6.5  # Conservative fallback value

    # Determine color based on confidence score
    if conf_score < 5:
        conf_color = "#ff4b4b"  # red
    elif conf_score < 7:
        conf_color = "#f4a261"  # orange/yellow
    else:
        conf_color = "#2a9d8f"  # green

    st.sidebar.markdown(
        f"### Overall Confidence: <span style='color:{conf_color};'>{conf_score} / 10</span>",
        unsafe_allow_html=True
    )
    st.sidebar.info("Reliable outputs are considered when confidence is **7.0+**.")
    technical_explanation = """
**Technical Explanation:**

- Uses RICE: (Reach × Impact × Confidence) / Effort.
- Benchmarks input against industry norms.
- Conservative scoring ensures only well-substantiated ideas score high.
    """
    st.sidebar.markdown(technical_explanation)
    
    if lower_confidence_flag:
        roast_msg = "It seems you're testing with questionable data. Consider using more realistic inputs."
    else:
        roast_msg = ""
    st.sidebar.markdown(f"**Roast:** {roast_msg}")

    # --- Strategic Visualizations ---
    with st.expander("📈 Strategic Visualizations", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("RICE Score Radar")
            radar_df = pd.DataFrame({
                "Metric": ["Reach", "Impact", "Confidence", "Effort"],
                "Score": [
                    analysis["rice_scores"]["Reach"]["value"],
                    analysis["rice_scores"]["Impact"]["value"],
                    analysis["rice_scores"]["Confidence"]["value"],
                    analysis["rice_scores"]["Effort"]["value"]
                ]
            })
            radar_fig = px.line_polar(
                radar_df, 
                r="Score", 
                theta="Metric", 
                line_close=True,
                color_discrete_sequence=['#2a9d8f'],
                template="plotly_white"
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        with col2:
            st.subheader("Priority Gauge")
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=analysis["rice_scores"]["final_rice_score"],
                title={"text": "Feature Priority Score"},
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
        
        st.subheader("Implementation Matrix")
        matrix_data = {
            "Phase": ["Discovery", "MVP", "Full Launch"],
            "Timeline": ["1-2 weeks", "3-5 weeks", "6-8 weeks"],
            "Resources": ["Product Team", "2 Developers", "Cross-functional"],
            "Success Metrics": ["User Research", "Early Adoption", "Revenue Impact"]
        }
        st.dataframe(pd.DataFrame(matrix_data), hide_index=True)

    # --- RICE Scores Breakdown ---
    with st.expander("🧮 RICE Scoring Breakdown", expanded=True):
        rice = analysis["rice_scores"]
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Final Priority Score", 
                      f"{rice['final_rice_score']:.1f}",
                      help="(Reach × Impact × Confidence) / Effort")
            st.markdown(f"""
            <div style="border-left: 4px solid #2a9d8f; padding-left: 1rem;">
                <h4 style="margin:0">Component Analysis</h4>
                <p style="color:#264653">{rice['Reach']['reason']}</p>
                <p style="color:#e76f51">{rice['Impact']['reason']}</p>
                <p style="color:#f4a261">{rice['Confidence']['reason']}</p>
                <p style="color:#2a9d8f">{rice['Effort']['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            fig = px.bar(
                pd.DataFrame({
                    "Component": ["Reach", "Impact", "Confidence", "Effort"],
                    "Score": [
                        rice["Reach"]["value"], 
                        rice["Impact"]["value"], 
                        rice["Confidence"]["value"], 
                        rice["Effort"]["value"]
                    ]
                }),
                x="Component",
                y="Score",
                color="Component",
                color_discrete_sequence=['#264653', '#2a9d8f', '#e9c46a', '#f4a261'],
                text="Score",
                title="RICE Component Scores"
            )
            fig.update_traces(textfont_size=12, textangle=0, textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # --- Risk Assessment Matrix ---
    with st.expander("⚠️ Risk Assessment Matrix", expanded=True):
        demo_risk_data = pd.DataFrame({
            "Risk Area": ["Technical Complexity", "Business Model", "Market Adoption", "Competitive Landscape"],
            "Risk Score (out of 10)": [7, 3, 9, 7],
            "Description": [
                "Requires integration with legacy systems.",
                "Supports recurring revenue with minimal adjustments.",
                "High risk due to market saturation.",
                "Moderate risk; few direct competitors."
            ]
        })
        st.subheader("Demo Risk Profile")
        st.table(demo_risk_data)
        heatmap_fig = px.imshow(
            [[7, 3, 9, 7]],
            labels=dict(x="Risk Area", y="", color="Risk Score"),
            x=["Technical Complexity", "Business Model", "Market Adoption", "Competitive Landscape"],
            color_continuous_scale="RdYlGn_r",
            aspect="auto"
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)

    # --- MVP Recommendation & Roadmap ---
    with st.expander("🚀 MVP Roadmap", expanded=True):
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:1rem; border-radius:10px;">
            <h4 style="color:#264653">Recommended MVP Strategy</h4>
            <p style="color:#2a9d8f; font-size:1.1rem">📌 {analysis['mvp_recommendation']}</p>
        </div>
        """, unsafe_allow_html=True)
        # Use the roadmap provided by GPT
        if "roadmap" in analysis and analysis["roadmap"]:
            roadmap_df = pd.DataFrame(analysis["roadmap"])
            st.dataframe(roadmap_df.style.background_gradient(cmap='Blues'), use_container_width=True)
        else:
            st.info("No roadmap data provided by GPT.")

    # --- Industry Insights ---
    with st.expander("🏭 Industry Insights", expanded=True):
        st.markdown(f"""
        <div style="border-left: 4px solid #e76f51; padding-left: 1rem;">
            <h4 style="color:#264653">{industry} Considerations</h4>
            <p style="color:#2a9d8f; font-size:1.1rem">📌 {analysis['industry_specific_considerations']}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Monetization Guidance ---
    with st.expander("💵 Revenue Strategy", expanded=True):
        st.markdown(f"""
        <div style="background-color:#fff5eb; padding:1rem; border-radius:10px;">
            <h4 style="color:#264653">Monetization Recommendations</h4>
            <p style="color:#e76f51; font-size:1.1rem">💡 {analysis['recommended_monetization']}</p>
        </div>
        """, unsafe_allow_html=True)
        pricing_model = pd.DataFrame({
            "Tier": ["Basic", "Pro", "Enterprise"],
            "Price": ["$29/mo", "$99/mo", "Custom"],
            "Features": ["Core Features", "+ Analytics", "+ Premium Support"],
            "Target": ["Startups", "SMBs", "Large Enterprises"]
        })
        st.dataframe(pricing_model.style.highlight_max(props="background-color: #e9f5f3"), use_container_width=True)

    # --- SWOT Analysis ---
    with st.expander("📝 SWOT Analysis", expanded=True):
        swot = analysis.get("swot_analysis", {})
        strengths = swot.get("Strengths", "N/A")
        weaknesses = swot.get("Weaknesses", "N/A")
        opportunities = swot.get("Opportunities", "N/A")
        threats = swot.get("Threats", "N/A")
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

elif submitted:
    st.error("❗ Please fill required fields: Feature Name and Industry")