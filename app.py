import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from textwrap import dedent
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS for enhanced UI
st.markdown("""
<style>
div[data-testid="stExpander"] details summary p {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 0;
    color: #2a9d8f;
}
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

def validate_feature_name(feature_name):
    """Check if feature name is specific enough"""
    if len(feature_name) < 5:
        return False, "Feature name is too short (min 5 characters)"
    vague_terms = ["feature", "system", "tool", "solution", "platform"]
    if any(term in feature_name.lower() for term in vague_terms):
        return False, "Feature name seems generic. Try to be more specific!"
    return True, ""

def generate_analysis(feature_name, industry, business_goal, business_model, feature_context):
    """Generate analysis using OpenAI API with enhanced prompt engineering"""
    prompt = dedent(f"""
    Act as a senior product manager with 15+ years experience analyzing features for {industry} companies.
    Analyze the following feature while considering the user's business context:

    Feature Name: {feature_name}
    Industry: {industry}
    Business Goal: {business_goal if business_goal else "Not specified"}
    Business Model: {business_model if business_model else "Not specified"}
    Additional Context: {feature_context if feature_context else "No additional context provided"}

    Provide analysis with:
    1. RICE scoring with 1-10 scales (Effort: 1=low, 10=high)
    2. Risk assessment considering industry-specific factors
    3. Practical MVP recommendations
    4. Monetization strategies matching business model

    Format response as JSON with this structure:
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
        "industry_specific_considerations": string,
        "recommended_monetization": string
    }}
    """)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a product management expert providing structured analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        analysis = json.loads(response.choices[0].message.content)
        return analysis, None
    except Exception as e:
        return None, f"API Error: {str(e)}"

# App Interface
st.title("🚀 AI Feature Prioritization Pro")
st.markdown("""
<div style="border-left: 4px solid #2a9d8f; padding-left: 1rem; margin: 2rem 0;">
    <p style="font-size: 1.1rem;">Analyze product features using AI-powered RICE scoring, risk assessment, and strategic recommendations.</p>
</div>
""", unsafe_allow_html=True)

# Input Section
with st.form("feature_inputs"):
    st.header("📋 Feature Details")
    
    # Main Inputs
    col1, col2 = st.columns(2)
    with col1:
        feature_name = st.text_input("Feature Name*", placeholder="e.g., AI-Powered Fraud Detection")
    with col2:
        industry = st.selectbox(
            "Industry*", 
            ['FinTech', 'EdTech', 'SaaS', 'Healthcare', 'E-commerce', 'AI Tools', 'Custom'],
            help="Select industry for contextual analysis"
        )
        if industry == 'Custom':
            industry = st.text_input("Custom Industry*")
    
    # Enhanced Feature Context
    feature_context = st.text_area(
        "Additional Context (Optional)",
        height=120,
        placeholder="Describe your feature in more detail...\nExample: This feature uses ML to detect payment fraud in real-time..."
    )
    
    # Business Parameters
    with st.expander("⚙️ Business Parameters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            business_goal = st.selectbox(
                "Primary Business Goal",
                ['None', 'User Experience', 'Revenue Growth', 'Cost Reduction', 'Market Expansion', 'Custom'],
                index=0
            )
            if business_goal == 'Custom':
                business_goal = st.text_input("Custom Business Goal")
        with col2:
            business_model = st.selectbox(
                "Business Model",
                ['None', 'B2B SaaS', 'Subscription', 'Transaction Fees', 'Freemium', 'Custom'],
                index=0
            )
            if business_model == 'Custom':
                business_model = st.text_input("Custom Business Model")
    
    submitted = st.form_submit_button("🚦 Analyze Feature")

# Processing
if submitted:
    validation_passed = True
    warnings = []
    
    # Input Validation
    if not feature_name.strip():
        st.error("Feature name is required!")
        st.stop()
        
    valid_feature, feature_msg = validate_feature_name(feature_name)
    if not valid_feature:
        st.warning(f"Feature Name Warning: {feature_msg}")
        validation_passed = False
        
    if industry == 'Custom' and not industry.strip():
        st.error("Custom industry required!")
        st.stop()
    
    # Show validation warnings
    if not validation_passed:
        st.markdown("""
        <div class="custom-warning">
            <h4>⚠️ Recommendation:</h4>
            <p>For better results, consider:</p>
            <ul>
                <li>Using specific outcomes in feature name (e.g., "Reduce checkout time by 30%")</li>
                <li>Including technical details in Additional Context</li>
                <li>Completing Business Parameters</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if not st.checkbox("Proceed with current inputs"):
            st.stop()
    
    # Generate Analysis
    with st.spinner("🔍 Analyzing feature (typically 10-15 seconds)..."):
        analysis, error = generate_analysis(
            feature_name, industry, 
            business_goal, business_model,
            feature_context
        )
        
    if error:
        st.error(f"Analysis Failed: {error}")
        st.stop()

    # Display Results
    st.header("📊 Analysis Results")
    st.markdown(f"""
    <div class="feature-pill">
        Analyzing: <strong>{feature_name}</strong> for <strong>{industry}</strong> industry
    </div>
    """, unsafe_allow_html=True)
    
    # Visualization Section
    with st.expander("📈 Strategic Overview", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            # Dynamic Risk Matrix
            risk_levels = {
                "technical_complexity": analysis["risks"]["technical_complexity"],
                "business_model": analysis["risks"]["business_model"],
                "adoption": analysis["risks"]["adoption"],
                "competition": analysis["risks"]["competition"]
            }
            
            risk_df = pd.DataFrame({
                "Risk Factor": risk_levels.keys(),
                "Assessment": risk_levels.values(),
                "Score": [7, 3, 8, 5]  # Replace with actual scores if available
            })
            
            fig = px.bar(risk_df, x="Risk Factor", y="Score", color="Risk Factor",
                        title="Risk Assessment Matrix",
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Priority Score Card
            rice = analysis["rice_scores"]
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px;">
                <h3 style="color: #2a9d8f; margin: 0 0 1rem 0;">Priority Score</h3>
                <div style="font-size: 2.5rem; font-weight: 700; color: #264653;">
                    {rice['final_rice_score']:.1f}
                </div>
                <div style="color: #6c757d; margin-top: 0.5rem;">
                    (Reach {rice['Reach']['value']} × Impact {rice['Impact']['value']} × Confidence {rice['Confidence']['value']}) / Effort {rice['Effort']['value']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Detailed Analysis Sections
    with st.expander("🧮 RICE Score Breakdown", expanded=True):
        rice = analysis["rice_scores"]
        cols = st.columns(4)
        metrics = [
            ("Reach", "#2a9d8f", rice["Reach"]),
            ("Impact", "#e76f51", rice["Impact"]),
            ("Confidence", "#f4a261", rice["Confidence"]),
            ("Effort", "#264653", rice["Effort"])
        ]
        
        for col, (name, color, data) in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding-left: 1rem; margin: 0.5rem 0;">
                    <h4 style="color: {color}; margin: 0 0 0.5rem 0;">{name}</h4>
                    <div style="font-size: 1.8rem; font-weight: 700;">{data['value']}</div>
                    <div style="color: #6c757d; font-size: 0.9rem;">{data['reason']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Roadmap Section
    with st.expander("🚀 Implementation Roadmap", expanded=True):
        tab1, tab2, tab3 = st.tabs(["MVP Strategy", "Development Plan", "Monetization"])
        
        with tab1:
            st.markdown(f"""
            <div style="background: #e9f5f3; padding: 1rem; border-radius: 10px;">
                <h4 style="color: #264653;">Minimum Viable Product</h4>
                <p>{analysis['mvp_recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            timeline = pd.DataFrame({
                "Phase": ["Research", "Design", "Development", "Testing", "Launch"],
                "Timeline": ["2 weeks", "3 weeks", "6 weeks", "2 weeks", "1 week"],
                "Resources": ["PM + UX", "Full Team", "Dev Team", "QA Team", "Marketing"]
            })
            st.dataframe(
                timeline.style.applymap(lambda x: "color: #2a9d8f", subset=["Phase"])
                          .set_properties(**{'background-color': '#f8f9fa'}),
                use_container_width=True
            )
        
        with tab3:
            st.markdown(f"""
            <div style="background: #fff5eb; padding: 1rem; border-radius: 10px;">
                <h4 style="color: #e76f51;">Revenue Strategy</h4>
                <p>{analysis['recommended_monetization']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Industry Insights
    with st.expander("🌍 Industry Considerations", expanded=True):
        st.markdown(f"""
        <div style="border-left: 4px solid #f4a261; padding-left: 1rem;">
            <h4>{industry} Specific Guidance</h4>
            <p>{analysis['industry_specific_considerations']}</p>
        </div>
        """, unsafe_allow_html=True)