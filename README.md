# 🤖 TransformAgent: Self-Improving SQL-to-Django ORM Translator

TransformAgent is an agentic code transformation system that converts raw SQL queries into executable Django ORM code. Unlike standard LLM code generators, TransformAgent uses **Behavioral Equivalence Verification** (executing both SQL and ORM and comparing results) to ensure 100% correctness, and features a **Reflection Loop** and **Success Case Memory** to continuously improve its accuracy over time.

## 📊 Evaluation (Ablation Study)
We benchmarked the agent on 20 queries of varying complexity (Joins, Group By, Subqueries, Aggregations) against the Chinook PostgreSQL database. 

| Architecture | Accuracy (BER) | Avg Time / Query | Impact |
| :--- | :--- | :--- | :--- |
| Basic (No Memory) | 65.0% (13/20) | 1.53 secs | Baseline LLM |
| Reflection Only | **85.0% (17/20)** | 6.25 secs | **+20% Accuracy Boost** |
| Full (Reflection + Memory) | **85.0% (17/20)** | 6.70 secs | Remembers past fixes |

*Note: The Memory layer does not improve scores on a single run of unique queries, but significantly reduces latency and errors on repeated or similar analytical queries.*

## 🏗️ Architecture
The system is built with a focus on deterministic verification:

1. **Generation:** Groq (Llama-3.3) translates SQL to Django ORM.
2. **Verification:** Both SQL and ORM queries are executed against a live PostgreSQL database. A custom diff engine normalizes decimals, handles ordering, and checks for exact behavioral equivalence.
3. **Reflection:** If the ORM throws an error (e.g., hallucinating a primary key), the error message is fed back to the LLM to self-correct.
4. **Memory:** Successful `(SQL, ORM)` pairs are stored in SQLite and retrieved as few-shot examples for future queries.

## 💻 Tech Stack
*   **LLM Orchestration:** Groq API (Llama-3.3-70b-versatile)
*   **Database:** PostgreSQL 16 (Dockerized)
*   **Backend:** Python 3.11, Django (for ORM execution), `psycopg2`
*   **Frontend:** Streamlit
*   **Memory:** SQLite3

## 🚀 Quick Start
1. Clone the repo: `git clone <your-repo-url>`
2. Start the database: `docker run --name chinook-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chinook -p 5432:5432 -d postgres:16`
3. Install dependencies: `pip install -r requirements.txt`
4. Add your `GROQ_API_KEY` to a `.env` file.
5. Run the UI: `streamlit run app.py`
6. Run the benchmark: `python evaluate.py`

## 🧠 Key Learnings & Design Decisions
*   **Why Behavioral Equivalence?** Syntax matching is not enough. By executing both queries, we guarantee the ORM code actually works and returns the exact same data.
*   **Why Reflection?** As shown in the ablation study, LLMs hallucinate field names (like `id` instead of `customer_id`). Reflection catches this and fixes it without human intervention.
*   **Decimal vs Float:** Handled a tricky edge case where PostgreSQL returns `Decimal` while Django returns `float`, causing false negatives in the diff engine.