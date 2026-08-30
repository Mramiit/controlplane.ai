# ControlPlane.ai 🛡️

**Enterprise AI Governance Middleware & Deterministic Safety Proxy**

ControlPlane.ai is a multi-tenant reverse proxy designed to evaluate AI responses in real time and flag or block bias, hallucination risk, or privacy leaks before they reach a user[cite: 1]. Developed for the Accenture Innovation Challenge 2026 (Round 2 - Prototype Development)[cite: 1], this middleware sits between enterprise frontends and external LLM APIs (like Google Gemini and OpenAI). It intercepts traffic to enforce deterministic safety rules, track telemetry, and optimize API costs without requiring changes to the underlying foundation models.

## Demo Video

[![Watch the ControlPlane.ai Demo](https://drive.google.com/file/d/12GWhx6tD3u03eddUMXM3GtzGeatrhvao/view?usp=drivesdk)](https://drive.google.com/file/d/1vx89-zbDwS0mrpJS_ff1IcyxGZ4yH9AG/view?usp=drivesdk)


## Core Architecture

ControlPlane acts as a unified `POST /v1/chat/completions` endpoint. Instead of routing directly to an LLM, requests pass through a YAML-configured governance pipeline.

### Ingress Guardrails (Pre-LLM)
*   **PII Scrubbing:** Intercepts sensitive entities (credit cards, emails) and replaces them with redacted tags (e.g., `[CREDIT_CARD_REDACTED]`) before the payload leaves the corporate network.
*   **FAISS Semantic Caching:** Vectorizes incoming prompts and searches for semantic matches in prior interactions. Hits bypass the LLM entirely, returning verified answers with 0ms LLM latency and zero token cost.
*   **Isolated RAG Pipelines:** Maintains strict separation of context via scenario-specific FAISS vector stores. Support bots cannot access HR databases, and vice versa.

### Egress Guardrails (Post-LLM)
*   **NLI Hallucination Verification:** Employs a Natural Language Inference checker to score LLM outputs against retrieved context. If the model hallucinates outside the bounds of the ground-truth document, the payload is destroyed and marked as `BLOCK`.
*   **Heuristic Escalation:** Scans outputs for high-liability ambiguity or forward-looking financial terms. High-risk payloads trigger an `ESCALATE` action, appending an `[AUDIT QUEUE ESCALATION]` tag for asynchronous Human-in-the-Loop (HITL) review.

## Multi-Tenant Scenarios

The engine dynamically switches policies based on the `scenario` parameter sent in the JSON payload.

1.  **Scenario A: Customer Support (Speed & Privacy)**
    *   **Engine:** Fast open-source model (`openai/gpt-oss-20b`).
    *   **Rules:** Inline PII redaction (`EDIT` action). High reliance on semantic caching and e-commerce FAQ retrieval.
2.  **Scenario B: Internal HR (Strict Fact-Checking)**
    *   **Engine:** Fast open-source model (`openai/gpt-oss-20b`).
    *   **Rules:** Zero-tolerance for ungrounded claims. Answers contradicting the internal employee handbook trigger an immediate `BLOCK`.
3.  **Scenario C: Regulated Finance (Human-in-the-Loop)**
    *   **Engine:** Heavy reasoning model (`gemini-3.6-flash`).
    *   **Rules:** Forward-looking financial projections are flagged by the ambiguity scanner and trigger an `ESCALATE` action to a human compliance queue.

## Tech Stack

*   **Backend:** FastAPI, Python 3.10+
*   **AI/ML:** LangChain, FAISS, HuggingFace Embeddings (`all-MiniLM-L6-v2`)
*   **LLM Providers:** Google GenAI SDK (Gemini), OpenAI API (or OSS equivalents)
*   **Frontend UI:** Streamlit, Plotly (Telemetry & Cost Analytics)
*   **Configuration:** YAML-driven policy engine

## Project Structure

```text
controlplane.ai/
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── core/
│   │   └── engine.py              # Main ControlPlane orchestration
│   ├── services/
│   │   ├── llm_client.py          # LLM API abstraction (Gemini/OpenAI)
│   │   ├── rag_pipeline.py        # FAISS document loaders and retrievers
│   │   └── guardrails.py          # PII, NLI, and Heuristic scanners
│   ├── config.yaml                # Multi-tenant governance rules
│   └── main.py                    # Uvicorn server entry point
├── data/
│   ├── scenario_a_support/        # e-commerce FAQ docs
│   ├── scenario_b_internal/       # HR handbook markdown
│   └── scenario_c_finance/        # Financial reports
├── dashboard/
│   └── app.py                     # Streamlit frontend with Plotly
├── requirements.txt
└── README.md
```
## Installation & Setup

Clone the repository
```
Bash
git clone [https://github.com/yourusername/controlplane.ai.git](https://github.com/yourusername/controlplane.ai.git)
cd controlplane.ai
```

Set up a virtual environment
```
Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install dependencies

```
Bash
pip install -r requirements.txt
```


Configure Environment Variables
Create a .env file in the root directory and add your API keys:
```
Code snippet
GEMINI_API_KEY=your_google_genai_key
OPENAI_API_KEY=your_openai_key

```

Start the FastAPI Backend
```
Bash
python -m app.main
```
The server will start on http://127.0.0.1:8000 and initialize the FAISS vector stores.


Start the Streamlit Dashboard
Open a new terminal window, activate the venv, and run:
```
Bash
streamlit run dashboard/app.py
```

### Using the Dashboard
Select an Active Scenario Policy from the left sidebar.

Enter a prompt designed to test the specific guardrail of that scenario.

Click Dispatch Request.

Observe the Gateway Resolution Output for action tags (PASS, EDIT, BLOCK, ESCALATE).

Review the Live Telemetry & Cost Analytics charts to see latency breakdowns (Middleware vs. LLM compute) and token consumption drops during cache hits.

Inspect the Payload Inspection & Audit Trail tab to view the raw JSON data and governance violations flagged by the dispatcher.

