import streamlit as st
import pandas as pd
import time
from engine import generate_orm, reflect_and_fix, run_sql, run_orm, compare, memory

# Page Config MUST be the first Streamlit command
st.set_page_config(page_title="TransformAgent", page_icon="🤖", layout="wide")

st.title("🤖 TransformAgent Playground")
st.markdown("""
Welcome to the **TransformAgent** interactive playground. 
This tool uses a self-correcting LLM agent to translate raw SQL into verified Django ORM code. 
*Type a SQL query below to see the agent generate code, test it, and fix its own bugs.*
""")

st.divider()

# Main Input Area
sql_input = st.text_area("Enter a SQL query:", height=100, placeholder="SELECT * FROM customer LIMIT 5;")

if st.button("🚀 Transform & Verify", type="primary"):
    if not sql_input.strip():
        st.warning("Please enter a SQL query.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Generated ORM")
            orm_code = generate_orm(sql_input)
            st.code(orm_code, language="python")
            
        with col2:
            st.subheader("2. Verification Engine")
            
            max_retries = 2
            attempt = 0
            success = False
            last_error = ""
            current_orm = orm_code
            
            status = st.status("Executing queries...", expanded=True)
            
            while attempt <= max_retries and not success:
                status.write(f"**Attempt {attempt + 1}**")
                try:
                    sql_rows = run_sql(sql_input)
                    orm_rows = run_orm(current_orm)
                    ok, diff = compare(sql_rows, orm_rows)
                    
                    if ok:
                        success = True
                        status.update(label="✅ Verified Successfully!", state="complete", expanded=False)
                        st.success("Behavioral Equivalence Verified! The ORM code returns the exact same data as the SQL.")
                        memory.add_success(sql_input, current_orm)
                    else:
                        last_error = diff
                        status.write(f"❌ Validation failed: {diff}")
                        
                except Exception as e:
                    last_error = str(e)
                    status.write(f"💥 Execution error: {last_error}")

                if not success and attempt < max_retries:
                    status.write("🔄 Triggering Reflection Loop...")
                    current_orm = reflect_and_fix(sql_input, current_orm, last_error)
                    st.write("**Corrected ORM:**")
                    st.code(current_orm, language="python")
                    attempt += 1
                else:
                    if not success:
                        status.update(label="❌ Failed after retries", state="error")
                    break
            
            # Display Results
            if success:
                st.subheader("Data Results")
                df = pd.DataFrame(sql_rows)
                st.dataframe(df, use_container_width=True)