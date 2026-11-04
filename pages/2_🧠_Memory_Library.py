import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Memory - TransformAgent", page_icon="🧠", layout="wide")

st.title("🧠 Success Case Library")
st.markdown("The agent saves successful `(SQL, ORM)` translations to a local SQLite database. Next time a similar query is asked, it uses these past successes as few-shot prompts to increase accuracy.")

st.divider()

def load_memory():
    # Fresh connection for Streamlit
    with sqlite3.connect("agent_memory.db") as conn:
        query = "SELECT sql, orm FROM success_cases ORDER BY id DESC"
        return pd.read_sql_query(query, conn)

try:
    df = load_memory()
    
    if df.empty:
        st.info("The memory library is currently empty. Go to the Playground and run some queries to populate it!")
    else:
        st.metric("Total Verified Queries Saved", len(df))
        
        st.subheader("Recent Translations")
        # Format as a readable table
        for index, row in df.iterrows():
            with st.expander(f"SQL: {row['sql'][:60]}..."):
                st.markdown("**SQL Query:**")
                st.code(row['sql'], language="sql")
                st.markdown("**Verified Django ORM:**")
                st.code(row['orm'], language="python")
                
except Exception as e:
    st.error(f"Error loading memory database: {e}")