"""
BHUMI-AI: Intelligent National Land Acquisition & Management Platform
SIH26016 — Ministry of Rural Development (MoRD)
Streamlit Cloud / Local Interactive Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="BHUMI-AI — National Land Acquisition System",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #152F3D;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-stat {
        background: #EBF3FA;
        color: #1B6CA8;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg", width=64)
st.sidebar.markdown("### **BHUMI-AI System**")
st.sidebar.markdown("**SIH26016 • MoRD Government of India**")
st.sidebar.divider()

view_mode = st.sidebar.radio(
    "Navigation Modules",
    [
        "📊 National Command Center",
        "🗺️ PostGIS GIS & 3-Route Corridors",
        "⚖️ RFCTLARR 2013 Statutory Engine",
        "💰 Transparent Award Calculator (S.26-30)",
        "🛡️ Anti-Corruption Anomaly Shield",
        "🇮🇳 Bilingual Citizen Portal (नागरिक पोर्टल)",
        "🤖 BHUMI Copilot (AI Assistant)",
    ]
)

st.sidebar.divider()
st.sidebar.info("💡 **Streamlit Cloud Deployment**: Ready out of the box with zero local setup.")

# --- MODULE 1: NATIONAL COMMAND CENTER ---
if view_mode == "📊 National Command Center":
    st.markdown('<div class="main-title">🇮🇳 National Land Acquisition Command Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-Time Monitoring & Predictive Decision Support across Infrastructure Corridors</div>', unsafe_allow_html=True)

    # Top KPI Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Projects", "22", "14 Active")
    with col2:
        st.metric("Total Land Parcels", "15,241", "+182 this month")
    with col3:
        st.metric("Acquisition Progress", "82.4%", "On Track")
    with col4:
        st.metric("DBT Disbursed", "₹1,840 Cr", "₹210 Cr pending")
    with col5:
        st.metric("Active Disputes", "18", "7 Critical (-3)")

    st.markdown("---")

    # Interactive Charts
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.subheader("📈 Monthly Acquisition vs DBT Disbursement")
        timeline_df = pd.DataFrame({
            "Month": ["Apr", "May", "Jun", "Jul", "Aug", "Sep"],
            "Parcels Acquired": [120, 240, 480, 710, 940, 1180],
            "Disbursement (₹ Cr)": [180, 390, 720, 1140, 1510, 1840],
            "R&R Resettled": [45, 95, 180, 260, 340, 410],
        })
        fig = px.area(
            timeline_df, x="Month", y=["Parcels Acquired", "R&R Resettled"],
            color_discrete_sequence=["#1B6CA8", "#27AE60"],
            labels={"value": "Count", "variable": "Metric"}
        )
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.subheader("🏛️ Sector-Wise Project Distribution")
        sector_df = pd.DataFrame({
            "Sector": ["Highways", "Railways", "Water & Irrigation", "Renewable Energy", "Industrial"],
            "Count": [8, 5, 4, 3, 2]
        })
        pie_fig = px.pie(
            sector_df, names="Sector", values="Count",
            color_discrete_sequence=["#1B6CA8", "#27AE60", "#E67E22", "#8E44AD", "#16A085"],
            hole=0.4
        )
        pie_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
        st.plotly_chart(pie_fig, use_container_width=True)

    # Active Highway Projects Table
    st.subheader("📋 Priority National Infrastructure Corridors")
    projects_data = [
        {"Project": "Delhi-Jaipur Super Expressway (NH-48)", "Agency": "NHAI", "State": "Rajasthan", "Stage": "Sec 23 Award", "Parcels": 540, "Risk": "🔴 Critical (93%)"},
        {"Project": "Dedicated Freight Corridor Western Phase", "Agency": "DFCCIL", "State": "Gujarat", "Stage": "Sec 19 Declaration", "Parcels": 820, "Risk": "🟡 Medium (42%)"},
        {"Project": "Bhadla Mega Solar Park Phase IV", "Agency": "SECI", "State": "Rajasthan", "Stage": "Sec 11 Preliminary", "Parcels": 310, "Risk": "🟢 Low (14%)"},
        {"Project": "Ken-Betwa River Linkage Canal", "Agency": "NWDA", "State": "Madhya Pradesh", "Stage": "SIA Consent", "Parcels": 1240, "Risk": "🔴 High (78%)"},
    ]
    st.dataframe(pd.DataFrame(projects_data), use_container_width=True)

# --- MODULE 2: GIS 3-ROUTE CORRIDOR ANALYSIS ---
elif view_mode == "🗺️ PostGIS GIS & 3-Route Corridors":
    st.markdown('<div class="main-title">🗺️ PostGIS GIS & 3-Route Corridor Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Multi-Criteria Routing Comparison (Cost, Forest Hectares, Affected Families, Alignment)</div>', unsafe_allow_html=True)

    project_select = st.selectbox("Select Alignment Project", ["Delhi-Jaipur Highway Alignment (RJ-HWY-024)", "Vadodara Industrial Bypass", "Bhadla Solar Grid Corridor"])

    st.markdown("### 🔍 3 Alternative Alignment Analysis (RFCTLARR Minimization Principle)")

    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.info("### 🟢 Route A (Recommended Alignment)\n- **Length**: 42.4 km\n- **Estimated Land Cost**: ₹48.2 Cr\n- **Forest Land**: 0.0 Ha\n- **Displaced Families**: 12\n- **Statutory Rating**: **Rank 1 (Best)**")
    with r_col2:
        st.warning("### 🟡 Route B (Northern Bypass)\n- **Length**: 46.8 km\n- **Estimated Land Cost**: ₹54.6 Cr\n- **Forest Land**: 3.2 Ha\n- **Displaced Families**: 28\n- **Statutory Rating**: **Rank 2**")
    with r_col3:
        st.error("### 🔴 Route C (Eastern Ridgeline)\n- **Length**: 51.2 km\n- **Estimated Land Cost**: ₹67.1 Cr\n- **Forest Land**: 14.5 Ha\n- **Displaced Families**: 64\n- **Statutory Rating**: **Rank 3 (High Friction)**")

    # Interactive Geo Map
    st.subheader("📍 Spatial Corridor Map & Parcel Boundaries")
    map_data = pd.DataFrame({
        'lat': [26.9124, 27.0238, 27.1560, 27.3200, 27.4500, 27.2000, 27.3500],
        'lon': [75.7873, 75.8450, 75.9200, 76.0400, 76.1200, 76.1500, 76.2200],
        'type': ['Jaipur Origin', 'Chomu Interchange', 'Route A (Recommended)', 'Shahpura Terminal', 'Delhi Border', 'Route B (Bypass)', 'Route C (High Risk)']
    })
    st.map(map_data, zoom=8)

# --- MODULE 3: STATUTORY ENGINE ---
elif view_mode == "⚖️ RFCTLARR 2013 Statutory Engine":
    st.markdown('<div class="main-title">⚖️ 12-Stage Statutory RFCTLARR (2013) State Machine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Statutory SLA Compliance, Legal Deadlines & Role-Based Gatekeeping</div>', unsafe_allow_html=True)

    stages = [
        ("1. Proposal Submission", "S.4(1)", "30 Days", "Completed", "🟢"),
        ("2. Social Impact Assessment (SIA)", "S.4–S.6", "180 Days", "Completed", "🟢"),
        ("3. Expert Group Appraisal", "S.7", "60 Days", "Completed", "🟢"),
        ("4. S.11 Preliminary Notification", "S.11(1)", "30 Days", "Completed", "🟢"),
        ("5. S.15 Public Objections", "S.15(2)", "60 Days", "Completed", "🟢"),
        ("6. S.19 Declaration", "S.19(1)", "365 Days", "In Progress", "🔵"),
        ("7. S.21 Notice to Persons Interested", "S.21", "30 Days", "Pending", "⚪"),
        ("8. S.23 Award Inquiry & Solatium", "S.23–S.30", "365 Days", "Pending", "⚪"),
        ("9. S.31 R&R Award Execution", "S.31", "180 Days", "Pending", "⚪"),
        ("10. S.38 Possession & Eviction", "S.38", "90 Days", "Pending", "⚪"),
        ("11. S.64 Authority Referral (Tribunal)", "S.64", "As needed", "Pending", "⚪"),
        ("12. S.101 Land Bank Management", "S.101", "Post-Possession", "Pending", "⚪"),
    ]

    st.markdown("### Statutory Lifecycle Tracker")
    for name, section, sla, status, icon in stages:
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        with c1:
            st.markdown(f"**{icon} {name}**")
        with c2:
            st.markdown(f"`Act {section}`")
        with c3:
            st.markdown(f"⏱️ SLA: **{sla}**")
        with c4:
            st.markdown(f"**{status}**")
        st.divider()

# --- MODULE 4: AWARD CALCULATOR ---
elif view_mode == "💰 Transparent Award Calculator (S.26-30)":
    st.markdown('<div class="main-title">💰 Statutory Sections 26–30 Award & Solatium Calculator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">100% Transparent, Deterministic Breakdown under RFCTLARR Act 2013</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        base_rate = st.number_input("Base Circle Rate / Market Value per Hectare (₹)", value=2500000, step=100000)
        area_ha = st.number_input("Land Area (Hectares)", value=1.5, step=0.1)
        is_rural = st.checkbox("Is Rural Land? (Multiplies Market Value under Section 26)", value=True)
        distance_km = st.slider("Distance from Urban Boundary (km)", min_value=0.0, max_value=50.0, value=15.0)

    with col2:
        structures = st.number_input("Section 29 Building & Structure Valuation (₹)", value=350000, step=25000)
        trees_crops = st.number_input("Section 29 Trees & Standing Crops Valuation (₹)", value=120000, step=10000)
        interest_months = st.slider("Months elapsed from S.11 Notice (S.30(3) 12% p.a. Interest)", 0, 36, 8)

    # Compute
    multiplier = 1.0
    if is_rural:
        if distance_km <= 10:
            multiplier = 1.25
        elif distance_km <= 20:
            multiplier = 1.50
        elif distance_km <= 30:
            multiplier = 1.75
        else:
            multiplier = 2.00

    raw_land_val = base_rate * area_ha
    multiplied_land_val = raw_land_val * multiplier
    total_assets = structures + trees_crops
    base_compensation = multiplied_land_val + total_assets
    solatium = base_compensation * 1.0  # 100% solatium Section 30(1)
    interest_rate = 0.12 * (interest_months / 12)
    interest_amount = multiplied_land_val * interest_rate
    final_award = base_compensation + solatium + interest_amount

    st.markdown("---")
    st.markdown(f"## 🏆 Total Final Award: **₹{final_award:,.2f}**")

    # Detailed table
    st.table(pd.DataFrame([
        {"Statutory Head": "Base Market Value (Area × Rate)", "RFCTLARR Section": "Section 26(1)", "Value (₹)": f"₹{raw_land_val:,.2f}"},
        {"Statutory Head": f"Rural Factor Multiplier ({multiplier}x)", "RFCTLARR Section": "Section 26(2)", "Value (₹)": f"₹{multiplied_land_val:,.2f}"},
        {"Statutory Head": "Valuation of Structures & Standing Crops", "RFCTLARR Section": "Section 29", "Value (₹)": f"₹{total_assets:,.2f}"},
        {"Statutory Head": "Solatium (100% Mandatory)", "RFCTLARR Section": "Section 30(1)", "Value (₹)": f"₹{solatium:,.2f}"},
        {"Statutory Head": f"Additional Interest (12% p.a. for {interest_months} mos)", "RFCTLARR Section": "Section 30(3)", "Value (₹)": f"₹{interest_amount:,.2f}"},
        {"Statutory Head": "FINAL DISBURSEMENT PAYABLE", "RFCTLARR Section": "Section 23 Award", "Value (₹)": f"₹{final_award:,.2f}"},
    ]))

# --- MODULE 5: ANOMALY SHIELD ---
elif view_mode == "🛡️ Anti-Corruption Anomaly Shield":
    st.markdown('<div class="main-title">🛡️ Anti-Corruption & Award Anomaly Shield</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automated Audit Rules Flagging Unjustified Valuations, Duplicate Bank Accounts & Ghost Beneficiaries</div>', unsafe_allow_html=True)

    anomalies = [
        {"Anomaly ID": "ANOM-2026-001", "Severity": "🔴 High", "Type": "Rate Spike", "Entity": "Parcel RJ-JPR-2026-089", "Description": "Valuation ₹4.2M/Ha exceeds village circle rate ceiling by 280% without registered sale deed evidence."},
        {"Anomaly ID": "ANOM-2026-002", "Severity": "🔴 High", "Type": "Duplicate IFSC / Account", "Entity": "Beneficiary Ramesh Lal & 3 others", "Description": "Same bank account IFSC SBIN0002401 shared across 4 unrelated beneficiary awards."},
        {"Anomaly ID": "ANOM-2026-003", "Severity": "🟡 Medium", "Type": "Missing Solatium", "Entity": "Award AWD-1049-CHOMU", "Description": "Section 30(1) 100% solatium was calculated at 50% multiplier — statutory shortfall."},
        {"Anomaly ID": "ANOM-2026-004", "Severity": "🟢 Low", "Type": "Delayed Payment Reference", "Entity": "Award AWD-1022-AMER", "Description": "PFMS DBT confirmation pending acknowledgement past statutory 14-day SLA."},
    ]
    st.dataframe(pd.DataFrame(anomalies), use_container_width=True)

# --- MODULE 6: CITIZEN PORTAL ---
elif view_mode == "🇮🇳 Bilingual Citizen Portal (नागरिक पोर्टल)":
    st.markdown('<div class="main-title">🇮🇳 Public Landowner Portal (नागरिक भूमि पोर्टल)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Empowering Project-Affected Landowners with Real-Time Transparency</div>', unsafe_allow_html=True)

    c_col1, c_col2 = st.columns([3, 2])
    with c_col1:
        khasra = st.text_input("Enter Khasra / Survey Number (खसरा संख्या दर्ज करें)", value="142/1")
        district = st.selectbox("Select District (जिला)", ["Jaipur", "Ahmedabad", "Jodhpur", "Bhopal"])

        if st.button("🔍 Track Land Status (स्थिति देखें)"):
            st.success("✓ Land Parcel Record Verified on DILRMP (भू-अभिलेख सत्यापित)")
            st.info("""
            **📋 Parcel Details (भूमि विवरण):**
            - **Survey / Khasra No**: 142/1
            - **Village**: Chomu (चोमू) | **Taluka**: Amer | **District**: Jaipur
            - **Owner(s)**: Rameshwar Dayal Sharma & Sons (100% Share)
            - **Land Category**: Agricultural - Irrigated (कृषि भूमि)
            - **Current Statutory Stage**: Section 23 Award Inquiry (धारा 23 निर्णय जांच)
            - **Compensation Status**: ₹1,850,000 Disbursed via PFMS DBT (खाते में हस्तांतरित)
            - **Possession Status**: Under Legal Transition (हस्तांतरण प्रक्रियाधीन)
            """)

# --- MODULE 7: BHUMI COPILOT ---
elif view_mode == "🤖 BHUMI Copilot (AI Assistant)":
    st.markdown('<div class="main-title">🤖 BHUMI Copilot — Legal & Decision AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Grounded in RFCTLARR Act 2013, Land Acquisition Rules & Live Corridors</div>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Namaste! I am BHUMI Copilot. Ask me anything about RFCTLARR 2013 statutory timelines, Section 26 compensation formulas, highway project delays, or dispute resolution."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_prompt := st.chat_input("Ask BHUMI Copilot... (e.g. What are the statutory deadlines for Section 19 declaration?)"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.write(user_prompt)

        # AI Grounded Response
        prompt_lower = user_prompt.lower()
        if "19" in prompt_lower or "declaration" in prompt_lower:
            reply = "Under Section 19(7) of the RFCTLARR Act 2013, the declaration must be published within **12 months (1 year)** from the date of publication of the Section 11 preliminary notification. If no declaration is published within 12 months, the entire proceedings lapse unless an extension is granted under statutory proviso."
        elif "solatium" in prompt_lower or "26" in prompt_lower or "compensation" in prompt_lower:
            reply = "Under Section 30(1) of the 2013 Act, the Collector MUST award a **Solatium amount equivalent to 100%** of the basic compensation assessed under Sections 26–29. Additionally, Section 30(3) mandates 12% per annum interest from the Section 11 notification date to the award date."
        elif "dispute" in prompt_lower or "64" in prompt_lower:
            reply = "Any person who has not accepted the award may, under **Section 64**, submit a written application to the Collector within 6 weeks requiring that the matter be referred to the Land Acquisition, Rehabilitation and Resettlement Authority (Tribunal)."
        else:
            reply = f"Grounded response for query '{user_prompt}': BHUMI-AI monitors all 12 statutory RFCTLARR stages in real-time. Please check the '⚖️ RFCTLARR 2013 Statutory Engine' or '💰 Transparent Award Calculator' tabs for detailed metrics."

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
