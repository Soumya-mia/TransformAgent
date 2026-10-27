import os
import django
import time

print("🚀 Starting evaluation script...") # WE ADDED THIS TO VERIFY IT RUNS

# 1. Setup Django BEFORE importing any models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ta_core.settings")
django.setup()

# 2. Now import the engine
from engine import generate_orm, reflect_and_fix, run_sql, run_orm, compare, memory

# A benchmark of 20 queries ranging from simple to complex
BENCHMARK_QUERIES = [
    # Simple
    "SELECT customer_id, first_name, last_name FROM customer LIMIT 5;",
    "SELECT name FROM artist ORDER BY name DESC LIMIT 3;",
    "SELECT title, unit_price FROM track WHERE unit_price > 0.99 LIMIT 4;",
    "SELECT SUM(total) as total_revenue FROM invoice;",
    "SELECT AVG(total) as avg_invoice FROM invoice;",
    # Medium
    "SELECT country, COUNT(*) as total FROM customer GROUP BY country ORDER BY total DESC LIMIT 3;",
    "SELECT first_name, email FROM customer WHERE email LIKE '%gmail%' LIMIT 3;",
    "SELECT billing_country, COUNT(*) as c FROM invoice GROUP BY billing_country HAVING COUNT(*) > 5 LIMIT 3;",
    "SELECT name FROM track WHERE composer IS NOT NULL LIMIT 3;",
    "SELECT COUNT(*) FROM invoice WHERE total > 10;",
    # Complex (Joins, Aggregations)
    "SELECT i.invoice_id, c.first_name, i.total FROM invoice i JOIN customer c ON i.customer_id = c.customer_id LIMIT 3;",
    "SELECT t.name, ar.name as artist_name FROM track t JOIN album al ON t.album_id = al.album_id JOIN artist ar ON al.artist_id = ar.artist_id LIMIT 3;",
    "SELECT c.first_name, SUM(i.total) as total_spent FROM customer c JOIN invoice i ON c.customer_id = i.customer_id GROUP BY c.first_name ORDER BY total_spent DESC LIMIT 3;",
    "SELECT p.name, COUNT(pt.track_id) as track_count FROM playlist p JOIN playlist_track pt ON p.playlist_id = pt.playlist_id GROUP BY p.name LIMIT 3;",
    "SELECT g.name, COUNT(t.track_id) as tracks FROM genre g JOIN track t ON g.genre_id = t.genre_id GROUP BY g.name ORDER BY tracks DESC LIMIT 3;",
    "SELECT e.first_name, e.last_name, COUNT(c.customer_id) as customers FROM employee e JOIN customer c ON e.employee_id = c.support_rep_id GROUP BY e.first_name, e.last_name LIMIT 3;",
    "SELECT t.name, t.unit_price FROM track t WHERE t.unit_price > (SELECT AVG(unit_price) FROM track) LIMIT 5;",
    "SELECT c.first_name, i.invoice_date, i.total FROM customer c JOIN invoice i ON c.customer_id = i.customer_id WHERE i.total > 15 LIMIT 3;",
    "SELECT name FROM playlist WHERE playlist_id IN (SELECT playlist_id FROM playlist_track GROUP BY playlist_id HAVING COUNT(*) > 10) LIMIT 3;",
    "SELECT title, milliseconds FROM track ORDER BY milliseconds DESC LIMIT 3;"
]

def run_benchmark():
    print(f"Starting Benchmark on {len(BENCHMARK_QUERIES)} queries...\n")
    
    results = {
        "Basic (No Memory)": {"passed": 0, "time": 0.0},
        "Reflection Only": {"passed": 0, "time": 0.0},
        "Full (Reflection + Memory)": {"passed": 0, "time": 0.0}
    }

    # Clear memory for a fair test
    memory.cursor.execute("DELETE FROM success_cases")
    memory.conn.commit()

    for i, sql in enumerate(BENCHMARK_QUERIES, 1):
        print(f"Testing Query {i}/{len(BENCHMARK_QUERIES)}...", end=" ", flush=True)
        
        # --- 1. Basic (No reflection, no memory) ---
        start_t = time.time()
        try:
            orm = generate_orm(sql)
            sql_r = run_sql(sql)
            orm_r = run_orm(orm)
            ok, _ = compare(sql_r, orm_r)
            if ok: results["Basic (No Memory)"]["passed"] += 1
        except:
            pass
        results["Basic (No Memory)"]["time"] += (time.time() - start_t)

        # --- 2. Reflection Only (No memory save/retrieve) ---
        start_t = time.time()
        success = False
        orm = generate_orm(sql)
        for attempt in range(3):
            try:
                sql_r = run_sql(sql)
                orm_r = run_orm(orm)
                ok, diff = compare(sql_r, orm_r)
                if ok: 
                    success = True
                    break
                else:
                    orm = reflect_and_fix(sql, orm, diff)
            except Exception as e:
                orm = reflect_and_fix(sql, orm, str(e))
        
        if success: results["Reflection Only"]["passed"] += 1
        results["Reflection Only"]["time"] += (time.time() - start_t)

        # --- 3. Full System (Memory + Reflection) ---
        start_t = time.time()
        success = False
        orm = generate_orm(sql) # generate_orm now uses memory
        for attempt in range(3):
            try:
                sql_r = run_sql(sql)
                orm_r = run_orm(orm)
                ok, diff = compare(sql_r, orm_r)
                if ok: 
                    success = True
                    memory.add_success(sql, orm) # Save to memory!
                    break
                else:
                    orm = reflect_and_fix(sql, orm, diff)
            except Exception as e:
                orm = reflect_and_fix(sql, orm, str(e))
                
        if success: results["Full (Reflection + Memory)"]["passed"] += 1
        results["Full (Reflection + Memory)"]["time"] += (time.time() - start_t)

        print("Done.")
        
        # --- DELAY TO PREVENT RATE LIMITS ---
        time.sleep(5) 

    # Print Results
    print("\n" + "="*60)
    print("📊 ABLATION STUDY RESULTS")
    print("="*60)
    print(f"{'Architecture':<30} | {'Accuracy (BER)':<15} | {'Avg Time / Query':<15}")
    print("-" * 60)
    
    total = len(BENCHMARK_QUERIES)
    for arch, data in results.items():
        ber = (data['passed'] / total) * 100
        avg_time = data['time'] / total
        print(f"{arch:<30} | {ber:>6.1f}% ({data['passed']}/{total}) | {avg_time:>10.2f} secs")
    
    print("="*60)

# CALL THE FUNCTION DIRECTLY
run_benchmark()