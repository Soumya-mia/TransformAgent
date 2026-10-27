import os
import django
import sqlite3
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
        
        examples = "\n\nHere are some past successful translations to guide you:\n"
        for sql, orm in rows:
            examples += f"SQL: {sql}\nORM: {orm}\n\n"
        return examples

memory = AgentMemory()

# 4. Prompts
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