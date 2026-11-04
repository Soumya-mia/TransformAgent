import streamlit as st

st.set_page_config(page_title="Architecture - TransformAgent", page_icon="ℹ️", layout="wide")

st.title("ℹ️ System Architecture")
st.markdown("TransformAgent is built with production-grade, scalable technologies.")

st.divider()

st.subheader("Technology Stack")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Frontend")
    st.markdown("- **Streamlit**: Interactive UI\n- **Pandas**: Data manipulation\n- **Mermaid.js**: Architecture diagrams")

with col2:
    st.markdown("### Backend & AI")
    st.markdown("- **Python 3.11**\n- **Groq API**: Llama-3.3-70b\n- **Django ORM**: Execution engine\n- **OpenAI SDK**: API client")

with col3:
    st.markdown("### Data & DevOps")
    st.markdown("- **PostgreSQL 16**: Primary DB\n- **SQLite**: Memory library\n- **Docker**: Containerization\n- **Git**: Version control")

st.divider()

st.subheader("System Data Flow")

mermaid_code = """
sequenceDiagram
    participant User
    participant Streamlit UI
    participant Engine (Python)
    participant Groq (LLM)
    participant PostgreSQL
    
    User->>Streamlit UI: Input SQL Query
    Streamlit UI->>Engine: generate_orm(sql)
    Engine->>Groq: Prompt (Schema + SQL)
    Groq-->>Engine: Generated ORM Code
    Engine->>PostgreSQL: Execute Original SQL
    Engine->>PostgreSQL: Execute Generated ORM
    PostgreSQL-->>Engine: SQL Results
    PostgreSQL-->>Engine: ORM Results
    
    alt Results Match
        Engine-->>Streamlit UI: Verification Success
        Streamlit UI-->>User: Display Data Table
    else Results Mismatch / Error
        Engine->>Groq: Reflection Prompt (SQL + Error)
        Groq-->>Engine: Corrected ORM Code
        Engine->>PostgreSQL: Execute Corrected ORM
        PostgreSQL-->>Engine: New Results
        Engine-->>Streamlit UI: Verification Success
        Streamlit UI-->>User: Display Data Table
    end
"""
st.markdown(f"```mermaid\n{mermaid_code}\n```")