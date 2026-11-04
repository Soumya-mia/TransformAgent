import streamlit as st
import graphviz

st.set_page_config(page_title="Architecture - TransformAgent", page_icon="🏗️", layout="wide")

# Apply Dark Theme CSS
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    h1, h2, h3 { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

st.title("🏗️ System Architecture")
st.markdown("TransformAgent is built using a highly scalable, decoupled microservice architecture.")

st.divider()

# Generate the Graphviz Diagram dynamically
dot = graphviz.Digraph()
dot.attr(rankdir='LR', bgcolor='transparent', fontname='Helvetica', fontcolor='white')
dot.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontcolor='white', penwidth='2')
dot.attr('edge', color='#4b5563', fontname='Helvetica', fontcolor='#a0aabf', fontsize='10')

# Nodes
dot.node('UI', 'Streamlit Frontend', fillcolor='#1e2433', color='#3b82f6')
dot.node('API', 'FastAPI Backend', fillcolor='#1e2433', color='#8b5cf6')
dot.node('SECURITY', 'Security Guardrail', fillcolor='#1e2433', color='#8b5cf6')
dot.node('CACHE', 'Query Cache', fillcolor='#1e2433', color='#8b5cf6')
dot.node('ENGINE', 'Reflection Engine', fillcolor='#1e2433', color='#10b981')
dot.node('LLM', 'Groq LLM', fillcolor='#1e2433', color='#10b981')
dot.node('MEMORY', 'Agent Memory', fillcolor='#1e2433', color='#10b981')
dot.node('POSTGRES', 'PostgreSQL', shape='cylinder', fillcolor='#1e2433', color='#f59e0b')
dot.node('SQLITE', 'SQLite', shape='cylinder', fillcolor='#1e2433', color='#f59e0b')

# Edges
dot.edge('UI', 'API', label='HTTP POST')
dot.edge('API', 'SECURITY', label='Validate')
dot.edge('SECURITY', 'CACHE', label='Check')
dot.edge('CACHE', 'ENGINE', label='Miss')
dot.edge('ENGINE', 'LLM', label='Reflect', dir='both')
dot.edge('ENGINE', 'POSTGRES', label='Execute', dir='both')
dot.edge('ENGINE', 'MEMORY', label='Learn', dir='both')
dot.edge('MEMORY', 'SQLITE', label='Store', dir='both')

# Render in Streamlit
st.graphviz_chart(dot)

st.divider()

st.subheader("Component Details")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Frontend & API**
    - **Streamlit:** Renders the dashboard, telemetry, and reflection timeline.
    - **FastAPI:** Handles high-concurrency REST requests and auto-generates Swagger docs.
    """)
    st.markdown("""
    **Security & Performance**
    - **Guardrail:** Blocks destructive SQL (DROP, DELETE) using Regex.
    - **Cache:** Prevents duplicate LLM calls, reducing latency to 0ms.
    """)

with col2:
    st.markdown("""
    **Agentic Engine**
    - **Reflection Loop:** Catches Python Exceptions from the ORM and self-corrects.
    - **LLM (Groq):** Lightning-fast Llama 3 inference.
    """)
    st.markdown("""
    **Data Layer**
    - **PostgreSQL:** Live relational database used for behavioral equivalence.
    - **SQLite:** Persistent memory bank of successful translations.
    """)