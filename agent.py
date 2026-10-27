import os
import django
import sqlite3
import json
from decimal import Decimal

# 1. Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ta_core.settings")
django.setup()

from django.db import connection
from django.db.models import Model, Sum, Count, Avg, Min, Max, F, Q
from openai import OpenAI
from dotenv import load_dotenv
from ta_core import models

# 2. Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# 3. The Memory Layer (Success Case Library)
class AgentMemory:
    def __init__(self, db_path="agent_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        # Create table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS success_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sql TEXT UNIQUE,
                orm TEXT
            )
        """)
        self.conn.commit()

    def add_success(self, sql, orm):
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO success_cases (sql, orm) VALUES (?, ?)", 
                (sql, orm)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Memory error: {e}")

    def get_recent_successes(self, limit=3):
        self.cursor.execute("SELECT sql, orm FROM success_cases ORDER BY id DESC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        if not rows:
            return ""
        
        # Format as few-shot examples for the prompt
        examples = "\n\nHere are some past successful translations to guide you:\n"
        for sql, orm in rows:
            examples += f"SQL: {sql}\nORM: {orm}\n\n"
        return examples

memory = AgentMemory()

# 4. Prompts (Now dynamic based on memory)
BASE_PROMPT = """You are a Django ORM expert. Convert the following SQL query into a Django ORM expression.

Available models (from ta_core.models): Album, Artist, Customer, Employee, Genre, Invoice, InvoiceLine, MediaType, Playlist, PlaylistTrack, Track.

Return ONLY the valid Python expression. 
Do not include imports, print statements, markdown formatting, or explanations.
Assume all models are imported.
IMPORTANT: Always use `.values('col1', 'col2')` to return a dictionary format. NEVER use `.values_list()`.
{memory}
Now convert this SQL:
SQL: {sql}
ORM: """

REFLECT_PROMPT = """You are a Django ORM expert. You previously generated the following ORM code for a SQL query, but it failed.

SQL Query: {sql}
Failed ORM: {orm_code}
Error Message: {error_msg}

Please fix the ORM code based on the error message. Look closely at the available fields and relationships.
IMPORTANT: Always use `.values('col1', 'col2')` to return a dictionary format. NEVER use `.values_list()`.
Return ONLY the fixed valid Python expression. Do not include any explanations or markdown.

Fixed ORM: """

def generate_orm(sql: str) -> str:
    mem_context = memory.get_recent_successes()
    prompt = BASE_PROMPT.format(memory=mem_context, sql=sql)
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    orm_code = response.choices[0].message.content.strip()
    return orm_code.replace("```python", "").replace("```", "").strip()

def reflect_and_fix(sql: str, orm_code: str, error_msg: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": REFLECT_PROMPT.format(
            sql=sql, orm_code=orm_code, error_msg=error_msg
        )}],
        temperature=0,
    )
    fixed_orm = response.choices[0].message.content.strip()
    return fixed_orm.replace("```python", "").replace("```", "").strip()

# 5. Execution & Comparison
def run_sql(sql: str) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def run_orm(orm_code: str) -> list[dict]:
    namespace = {**vars(models), "Decimal": Decimal, "Sum": Sum, "Count": Count, "Avg": Avg, "Min": Min, "Max": Max, "F": F, "Q": Q}
    result = eval(orm_code, namespace)
    
    if isinstance(result, dict): return [result]
    if hasattr(result, '__iter__'): result = list(result)
    
    clean_result = []
    for item in result:
        if isinstance(item, Model):
            clean_result.append({k: v for k, v in item.__dict__.items() if not k.startswith('_')})
        elif isinstance(item, dict):
            clean_result.append(item)
        else:
            clean_result.append({"result": item})
    return clean_result

def normalize(rows: list[dict]) -> list[tuple]:
    clean = []
    for row in rows:
        sorted_items = sorted(row.items(), key=lambda x: x[0])
        clean_row = tuple(float(v) if isinstance(v, Decimal) else v for k, v in sorted_items)
        clean.append(clean_row)
    return sorted(clean, key=lambda r: [str(x) for x in r])

def compare(sql_rows, orm_rows) -> tuple[bool, str]:
    a, b = normalize(sql_rows), normalize(orm_rows)
    if a == b: return True, ""
    diff_msg = f"Row count mismatch: {len(a)} vs {len(b)}"
    if len(a) == len(b):
        diff_msg = f"Values mismatch.\nSQL: {a[:2]}\nORM: {b[:2]}"
    return False, diff_msg

# 6. Harder Test Queries
TEST_QUERIES = [
    "SELECT customer_id, first_name, last_name FROM customer LIMIT 5;",
    "SELECT name FROM artist ORDER BY name DESC LIMIT 3;",
    "SELECT country, COUNT(*) as total FROM customer GROUP BY country ORDER BY total DESC LIMIT 3;",
    "SELECT name, unit_price FROM track WHERE unit_price > 0.99 LIMIT 4;",
    "SELECT SUM(total) as total_revenue FROM invoice;",
    "SELECT i.invoice_id, c.first_name, i.total FROM invoice i JOIN customer c ON i.customer_id = c.customer_id LIMIT 3;",
    "SELECT first_name, email FROM customer WHERE email LIKE '%gmail%' LIMIT 3;",
    "SELECT billing_country, COUNT(*) as c FROM invoice GROUP BY billing_country HAVING COUNT(*) > 5 LIMIT 3;",
    "SELECT t.name, ar.name as artist_name FROM track t JOIN album al ON t.album_id = al.album_id JOIN artist ar ON al.artist_id = ar.artist_id LIMIT 3;",
    "SELECT AVG(total) as avg_invoice FROM invoice;"
]

# 7. Main Loop
if __name__ == "__main__":
    passed = 0
    print(f"Running {len(TEST_QUERIES)} queries...\n")

    for i, sql in enumerate(TEST_QUERIES, 1):
        print(f"--- Query {i} ---")
        print(f"SQL: {sql}")
        
        orm_code = generate_orm(sql)
        print(f"Initial ORM: {orm_code}")

        max_retries = 2
        attempt = 0
        success = False
        last_error = ""

        while attempt <= max_retries and not success:
            try:
                sql_rows = run_sql(sql)
                orm_rows = run_orm(orm_code)
                ok, diff = compare(sql_rows, orm_rows)
                
                if ok:
                    success = True
                    print("✅ PASS")
                    passed += 1
                    # SAVE TO MEMORY!
                    memory.add_success(sql, orm_code)
                else:
                    last_error = diff
                    print(f"❌ FAIL — {diff}")
                    
            except Exception as e:
                last_error = str(e)
                print(f"💥 ERROR: {last_error}")

            if not success and attempt < max_retries:
                print(f"🔄 Reflection attempt {attempt + 1}...")
                orm_code = reflect_and_fix(sql, orm_code, last_error)
                print(f"   New ORM: {orm_code}")
                attempt += 1
            else:
                break
                
        print("-" * 20)

    print(f"\n=== Final BER: {passed}/{len(TEST_QUERIES)} ({passed/len(TEST_QUERIES):.0%}) ===")
    print(f"Memory contains {len(memory.get_recent_successes(100))} successful cases saved.")