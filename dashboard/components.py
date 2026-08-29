"""
File: dashboard/components.py
Project: ControlPlane.ai Prototype
Contributors: Rahul and Amit

Description:
This file contains the modularized UI components for the Streamlit dashboard. 
It separates the analytical visualizations and sidebar controls from the main app logic, 
keeping the codebase clean and maintainable.

Updates Executed:
- Built the render_sidebar_controls() function to handle dynamic policy selection.
- Built the render_telemetry_dashboard() function to visualize token savings and latency.
- Built the render_chat_message() function to display custom tags for intercepted gateway actions.
"""

import streamlit as st

def render_sidebar_controls():
    with st.sidebar:
        st.header("⚙️ Policy Configuration")
        
        scenario = st.selectbox(
            "Active Enterprise Scenario",
            options=[
                "Scenario A: Customer Support", 
                "Scenario B: Internal RAG", 
                "Scenario C: Regulated Financial"
            ],
            index=0
        )
        
        st.divider()
        
        st.subheader("Active Thresholds")
        if "Scenario A" in scenario:
            st.info("**Latency Budget:** < 35 ms\n\n**PII Action:** Redact Inline\n\n**Tolerance:** Zero")
        elif "Scenario B" in scenario:
            st.info("**Latency Budget:** < 120 ms\n\n**Hallucination Check:** Strict (NLI)\n\n**Context:** Employee Handbook")
        else:
            st.warning("**Latency Budget:** Asynchronous\n\n**Ambiguity:** Escalate to Human\n\n**Audit:** Strict Logging")
            
        return scenario

def render_telemetry_dashboard(metrics, scenario):
    st.subheader("📊 Live Gateway Metrics")
    
    st.markdown("#### Cost Dimension")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Cache Hits", value="3", delta="100% Compute Saved")
    with col2:
        st.metric(label="Tokens Saved", value=f"{metrics['tokens_saved']}")
        
    st.divider()
    
    st.markdown("#### Egress Interceptor")
    st.metric(label="Guardrail Latency Overhead", value=f"{metrics['latency_ms']} ms", delta="-2 ms", delta_color="inverse")
    
    status_color = "normal"
    if metrics["risk_status"] != "Clean":
        status_color = "inverse"
    
    st.metric(label="Last Action Matrix Result", value=metrics["risk_status"], delta_color=status_color)
    
    st.divider()
    st.markdown("#### 🚨 Real-Time Audit Log")
    with st.expander("View Recent Gateway Actions", expanded=True):
        st.code("""
[10:45:01] PASS - Valid Query
[10:46:22] EDIT - PII Masked (Regex)
[10:47:10] HIT  - Semantic Cache (Cost Saved)
        """, language="plaintext")

def render_chat_message(role, content, action=None):
    with st.chat_message(role):
        st.write(content)
        
        if action and action != "PASS":
            if action == "EDIT":
                st.caption("🛡️ *Edited by ControlPlane (PII Redacted)*")
            elif action == "BLOCK":
                st.error("🚨 *Blocked by ControlPlane (Toxicity/Hallucination)*")
            elif action == "ESCALATE":
                st.warning("⚠️ *Escalated for Human Review*")