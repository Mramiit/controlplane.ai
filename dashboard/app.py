"""
File: dashboard/app.py
Project: ControlPlane.ai Prototype
Contributors: Rahul and Amit
"""

import streamlit as st
import requests
import json
import time

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="ControlPlane.ai | Egress Gateway",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CYBER-MINIMALIST CSS INJECTION
# ==========================================
def load_dynamic_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');
        
        /* Core Background */
        .stApp {
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid #1f2937;
        }
        
        /* Dynamic Typography */
        h1, h2, h3 {
            font-weight: 600 !important;
            color: #f8fafc !important;
        }
        
        /* Metric Cards - Divide & Conquer */
        [data-testid="stMetric"] {
            background: #1e293b;
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        [data-testid="stMetricValue"] {
            color: #60a5fa !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 1.8rem !important;
        }
        
        /* Status Tags */
        .status-badge-clean { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; border: 1px solid #10b981;}
        .status-badge-warn { background: rgba(245, 158, 11, 0.1); color: #f59e0b; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; border: 1px solid #f59e0b;}
        .status-badge-block { background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; border: 1px solid #ef4444;}
        
        /* Expanders (The Fall Effect) */
        .streamlit-expanderHeader {
            background-color: #1e293b !important;
            border-radius: 4px !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* Clean up */
        #MainMenu, footer {visibility: hidden;}
        header {background-color: transparent !important;}
        .block-container { padding-top: 2rem !important; max-width: 98% !important; }
        </style>
    """, unsafe_allow_html=True)

load_dynamic_css()

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cache_hits" not in st.session_state:
    st.session_state.cache_hits = 0
if "tokens_saved" not in st.session_state:
    st.session_state.tokens_saved = 0
if "last_latency" not in st.session_state:
    st.session_state.last_latency = 0
if "last_action" not in st.session_state:
    st.session_state.last_action = "None"
if "last_payload" not in st.session_state:
    st.session_state.last_payload = "{}"

# ==========================================
# 4. SIDEBAR: DYNAMIC ROUTING & FEATURES
# ==========================================
with st.sidebar:
    st.markdown("### ⚡ Gateway Configuration")
    scenario_selection = st.selectbox(
        "Active Policy Engine",
        [
            "Scenario A: Customer Support",
            "Scenario B: Internal RAG",
            "Scenario C: Regulated Financial"
        ]
    )
    
    st.markdown("---")
    st.markdown("### 🎛️ Dynamic Thresholds")
    # These sliders are visually interactive for the demo
    confidence_slider = st.slider("NLI Hallucination Confidence", min_value=0.5, max_value=0.99, value=0.85, step=0.01)
    latency_slider = st.slider("Max Latency Budget (ms)", min_value=10, max_value=500, value=120, step=10)
    
    if "Scenario A" in scenario_selection:
        scenario_id = "scenario_a_support"
    elif "Scenario B" in scenario_selection:
        scenario_id = "scenario_b_internal"
    else:
        scenario_id = "scenario_c_finance"

    st.markdown("---")
    st.caption("Active Engine: v2.1.4-beta")
    st.caption(f"NLI Threshold: {confidence_slider}")

# ==========================================
# 5. MAIN LAYOUT: DIVIDE & CONQUER
# ==========================================
st.title("ControlPlane.ai ⚡")
st.markdown("Advanced Multi-Vector Egress Proxy & Telemetry Dashboard")
st.markdown("---")

# The Divide: Chat on Left, Telemetry/Logs on Right
chat_col, gap, metrics_col = st.columns([2, 0.1, 1.2])

with chat_col:
    st.markdown("#### Application Layer (Chat)")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Inject payload into egress gateway..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                start_time = time.time()
                response = requests.post(
                    "http://localhost:8000/process", 
                    json={"prompt": prompt, "scenario": scenario_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("response", "Error: Proxy returned empty body.")
                    
                    # Update State
                    if data.get("action") == "PASS" and data.get("risk_status") == "Cache Hit":
                        st.session_state.cache_hits += 1
                        
                    st.session_state.tokens_saved += data.get("tokens_saved", 0)
                    st.session_state.last_latency = data.get("latency_ms", 0)
                    st.session_state.last_action = data.get("risk_status", "Clean")
                    st.session_state.last_payload = json.dumps(data, indent=2)
                    
                    message_placeholder.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                else:
                    error_msg = f"API Error: {response.status_code}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.exceptions.ConnectionError:
                error_msg = "Gateway Connection Failed."
                message_placeholder.error(error_msg)

# ==========================================
# 6. METRICS & DROPDOWNS (THE FALL)
# ==========================================
with metrics_col:
    st.markdown("#### Proxy Telemetry")
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Cache Hits", st.session_state.cache_hits)
    m_col2.metric("Tokens Saved", st.session_state.tokens_saved)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Guardrail Processing Overhead", f"{st.session_state.last_latency} ms")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Real-Time Action Matrix:**")
    
    action_text = st.session_state.last_action
    if "Hit" in action_text or "Clean" in action_text:
        st.markdown(f"<span class='status-badge-clean'>✅ {action_text}</span>", unsafe_allow_html=True)
    elif "PII" in action_text:
        st.markdown(f"<span class='status-badge-warn'>⚠️ {action_text}</span>", unsafe_allow_html=True)
    elif "Block" in action_text:
        st.markdown(f"<span class='status-badge-block'>🚨 {action_text}</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='status-badge-clean'>✅ {action_text}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # The "Fall" - Collapsible JSON Trace Log
    with st.expander("🔍 View Raw Interceptor Payload"):
        st.code(st.session_state.last_payload, language="json")