import streamlit as st
import os

st.set_page_config(page_title="Database - TransformAgent", page_icon="🗄️", layout="wide")

st.title("🗄️ Database Explorer")
st.markdown("TransformAgent uses Django's `inspectdb` to auto-generate models from the PostgreSQL database. Here are the available tables and fields you can query.")

st.divider()

# Read the models.py file
models_path = "ta_core/models.py"
try:
    with open(models_path, "r") as f:
        models_code = f.read()
    
    st.info("The following Python classes represent the database schema. The LLM uses this exact registry to write ORM code.")
    
    # Display the code with syntax highlighting
    st.code(models_code, language="python")
    
except FileNotFoundError:
    st.error(f"Could not find {models_path}. Make sure you are running Streamlit from the project root.")