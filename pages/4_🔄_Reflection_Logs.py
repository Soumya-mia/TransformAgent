import streamlit as st

st.set_page_config(page_title="Reflection Logs - TransformAgent", page_icon="🔄", layout="wide")

st.title("🔄 How the Reflection Loop Works")
st.markdown("""
The core novelty of TransformAgent is its ability to **read its own errors and fix them**. 
Instead of just failing when the LLM hallucinates a field name, the system executes the code, catches the exception, and feeds it back to the LLM for a second attempt.
""")

st.divider()

st.subheader("The Self-Correction Pipeline")

# Streamlit natively supports Mermaid.js diagrams
mermaid_code = """
graph TD
    A[User Inputs SQL] --> B[LLM Generates ORM]
    B --> C{Execute ORM}
    C -->|Success| D[Verify Data Match]
    C -->|Python Exception| E[Catch Error Message]
    D -->|Mismatch| E
    D -->|Exact Match| F[Return Data Table]
    E --> G[Feed Error Back to LLM]
    G --> H[LLM Rewrites ORM]
    H --> C
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style F fill:#d4edda,stroke:#28a745,stroke-width:2px
    style E fill:#f8d7da,stroke:#dc3545,stroke-width:2px
"""
st.markdown(f"```mermaid\n{mermaid_code}\n```")

st.divider()

st.subheader("Real-World Example")
st.markdown("Here is an example of what happens behind the scenes when a query fails:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Attempt 1 (Fails)**")
    st.code("Customer.objects.values('country').annotate(total=Count('id'))", language="python")
    st.error("💥 Exception: Cannot resolve keyword 'id' into field. Choices are: customer_id, first_name...")

with col2:
    st.markdown("**Attempt 2 (Passes)**")
    st.code("Customer.objects.values('country').annotate(total=Count('customer_id'))", language="python")
    st.success("✅ Verified Successfully!")