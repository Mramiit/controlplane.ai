import streamlit as st
import requests
import json

st.set_page_config(page_title="ControlPlane Dashboard", layout="wide")

st.title("🛡️ ControlPlane.ai Gateway")
st.markdown("Enterprise AI Governance Middleware Prototype")

# Sidebar Configuration
st.sidebar.header("Gateway Configuration")
scenario_mapping = {
    "Customer Support (Speed & PII)": "scenario_a_support",
    "Internal Knowledge (Strict Fact-Checking)": "scenario_b_internal",
    "Regulated Finance (Human Escalation)": "scenario_c_finance"
}
selected_name = st.sidebar.selectbox("Active Enterprise Scenario", list(scenario_mapping.keys()))
active_scenario = scenario_mapping[selected_name]

st.sidebar.markdown("---")
st.sidebar.write("**Gateway Endpoint:** `POST /v1/chat/completions`")

# Main Interface
prompt = st.text_area("Enter User Prompt:", height=150, placeholder="e.g. What is the projected Q4 revenue?")

if st.button("Send Request to Gateway"):
    if prompt.strip():
        with st.spinner("Processing through ControlPlane..."):
            headers = {"X-Use-Case": active_scenario}
            payload = {"prompt": prompt}
            
            try:
                # Call the FastAPI backend
                res = requests.post("http://127.0.0.1:8000/v1/chat/completions", json=payload, headers=headers)
                
                if res.status_code != 200:
                    st.error(f"Backend Error (HTTP {res.status_code}): {res.text}")
                    st.stop()
                    
                data = res.json()
                
                # Display Results
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    action = data.get("action", "UNKNOWN")
                    if action == "BLOCK":
                        st.error(f"🛑 {data['response']}")
                    elif action == "ESCALATE":
                        st.warning(f"⚠️ {data['response']}")
                    else:
                        st.success(f"✅ **Output:**\n\n{data['response']}")
                        
                    with st.expander("View Raw API Response"):
                        st.json(data)
                        
                with col2:
                    st.subheader("Telemetry Logs")
                    st.metric("Total Latency", f"{data.get('latency_ms', 0)} ms")
                    st.metric("Model Execution", f"{data.get('model_latency_ms', 0)} ms")
                    
                    if data.get("source") == "SEMANTIC_CACHE":
                        st.info("⚡ Served instantly from FAISS Cache")
                    
                    st.write("**Cost Metrics:**")
                    st.json(data.get("metrics", {}))
                    
                    st.write("**Guardrail Audit:**")
                    st.json(data.get("audit", {}))
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to FastAPI backend. Ensure `python app/main.py` is running.")