from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sqlite3
import time
from api.schemas import QueryRequest, VerificationResult, HealthResponse
from engine import generate_orm, reflect_and_fix, run_sql, run_orm, compare, memory

app = FastAPI(
    title="TransformAgent API",
    description="Enterprise API for translating SQL to Django ORM.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TransformAgent | Developer Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Fira+Code&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-card: #151a26;
            --bg-sidebar: #0f131c;
            --border: #2e3a52;
            --text-main: #ffffff;
            --text-muted: #a0aabf;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 0; display: flex; height: 100vh;
            font-family: 'Inter', sans-serif; background-color: var(--bg-main);
            color: var(--text-main);
        }
        
        /* Sidebar */
        .sidebar {
            width: 260px; background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border); padding: 24px;
            display: flex; flex-direction: column;
        }
        .logo { display: flex; align-items: center; gap: 12px; margin-bottom: 40px; }
        .logo-icon { font-size: 28px; }
        .logo-text { font-size: 20px; font-weight: 700; }
        .nav-item {
            padding: 12px; border-radius: 8px; color: var(--text-muted);
            font-weight: 600; cursor: pointer; margin-bottom: 8px;
            transition: 0.2s; display: flex; align-items: center; gap: 10px;
        }
        .nav-item:hover { background-color: var(--bg-card); color: var(--text-main); }
        .nav-item.active { background-color: rgba(59, 130, 246, 0.1); color: var(--accent); border-left: 3px solid var(--accent); }
        .nav-badge { margin-left: auto; font-size: 12px; background: var(--accent); color: white; padding: 2px 8px; border-radius: 12px; }
        
        /* Main Content */
        .main-content { flex: 1; padding: 40px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; }
        .status-badge { 
            background: rgba(16, 185, 129, 0.1); color: var(--success); 
            padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 14px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Grid Layout */
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        .card {
            background-color: var(--bg-card); border: 1px solid var(--border);
            border-radius: 12px; padding: 24px;
        }
        .card h3 { margin-top: 0; margin-bottom: 16px; font-size: 16px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Inputs */
        textarea {
            width: 100%; height: 120px; background-color: var(--bg-main);
            color: #00ff00; border: 1px solid var(--border); border-radius: 8px;
            padding: 16px; font-family: 'Fira Code', monospace; font-size: 14px;
            resize: none; margin-bottom: 16px;
        }
        button {
            width: 100%; padding: 14px; border-radius: 8px; border: none;
            background-color: var(--accent); color: white; font-weight: 600;
            font-size: 15px; cursor: pointer; transition: 0.2s; font-family: 'Inter', sans-serif;
        }
        button:hover { background-color: var(--accent-hover); }
        
        /* Output Boxes */
        .code-box {
            background-color: #000; color: #00ff00; padding: 16px;
            border-radius: 8px; font-family: 'Fira Code', monospace; font-size: 14px;
            overflow-x: auto; border: 1px solid #333; white-space: pre-wrap;
            max-height: 250px; overflow-y: auto;
        }
        .json-box { color: #3b82f6; }
        
        /* Status */
        .status-box {
            padding: 16px; border-radius: 8px; font-weight: 600; margin-bottom: 16px; display: none;
        }
        .status-success { background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid var(--success); display: block; }
        .status-error { background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid var(--danger); display: block; }
        .status-loading { background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid var(--warning); display: block; }

        /* History Table */
        table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
        th { text-align: left; padding: 12px; border-bottom: 1px solid var(--border); color: var(--text-muted); font-weight: 600; }
        td { padding: 12px; border-bottom: 1px solid var(--border); }
        .tag-success { color: var(--success); background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 4px; font-weight: 600; }
        .tag-fail { color: var(--danger); background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 4px; font-weight: 600; }

        /* API Routes */
        .route { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); }
        .method { font-weight: 700; font-size: 12px; padding: 4px 8px; border-radius: 4px; }
        .method.get { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        .method.post { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .route-path { font-family: 'Fira Code', monospace; color: var(--text-main); }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="logo">
            <span class="logo-icon">⚡</span>
            <span class="logo-text">TransformAgent</span>
        </div>
        
        <div class="nav-item active">
            <span>📊</span> API Dashboard
        </div>
        <div class="nav-item" onclick="window.open('/docs', '_blank')">
            <span>📖</span> Swagger Docs
        </div>
        <div class="nav-item" onclick="window.open('http://localhost:8501', '_blank')">
            <span>🖥️</span> Streamlit UI
        </div>
        
        <div style="margin-top: auto; font-size: 12px; color: var(--text-muted);">
            <div style="margin-bottom: 8px;">v1.0.0 | Enterprise Edition</div>
            <div id="memory-count">Memory: Loading...</div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
            <div>
                <h1>API Developer Portal</h1>
                <p style="margin: 5px 0 0 0; color: var(--text-muted);">Test the REST API, monitor health, and view execution history.</p>
            </div>
            <div class="status-badge" id="health-badge">🟢 Checking System...</div>
        </div>

        <!-- Top Grid -->
        <div class="grid">
            <!-- Playground -->
            <div class="card">
                <h3>🚀 API Playground</h3>
                <textarea id="sqlInput">SELECT country, COUNT(*) as total FROM customer GROUP BY country ORDER BY total DESC LIMIT 3;</textarea>
                <button onclick="executeQuery()" id="executeBtn">Execute Query</button>
            </div>

            <!-- Results -->
            <div class="card">
                <h3>🔍 Verification Results</h3>
                <div id="statusBox" class="status-box"></div>
                <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px;">Generated ORM Code:</div>
                <div id="ormOutput" class="code-box">// Waiting for execution...</div>
            </div>
        </div>

        <!-- Bottom Grid -->
        <div class="grid">
            <!-- JSON Viewer -->
            <div class="card">
                <h3>📦 Raw JSON Response</h3>
                <div id="jsonOutput" class="code-box json-box">// Waiting for API response...</div>
            </div>

            <!-- API Routes -->
            <div class="card">
                <h3>🛠️ Available API Routes</h3>
                <div class="route">
                    <span class="method get">GET</span>
                    <span class="route-path">/health</span>
                </div>
                <div class="route">
                    <span class="method post">POST</span>
                    <span class="route-path">/api/v1/translate</span>
                </div>
                <div class="route">
                    <span class="method get">GET</span>
                    <span class="route-path">/docs</span>
                </div>
                <div class="route">
                    <span class="method get">GET</span>
                    <span class="route-path">/openapi.json</span>
                </div>
            </div>
        </div>

        <!-- History Table -->
        <div class="card" style="margin-top: 24px;">
            <h3>📜 Session History</h3>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>SQL Query</th>
                        <th>Attempts</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="historyBody">
                    <tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No queries executed yet.</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Fetch Health on Load
        function checkHealth() {
            fetch('/health')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('health-badge').innerHTML = `🟢 API Online | ${data.memory_count} Cases in Memory`;
                    document.getElementById('memory-count').innerText = `Memory: ${data.memory_count} cases`;
                })
                .catch(() => {
                    document.getElementById('health-badge').innerHTML = `🔴 API Offline`;
                    document.getElementById('health-badge').style.color = 'var(--danger)';
                    document.getElementById('health-badge').style.background = 'rgba(239, 68, 68, 0.1)';
                });
        }
        checkHealth();

        async function executeQuery() {
            const sql = document.getElementById('sqlInput').value;
            const btn = document.getElementById('executeBtn');
            const statusBox = document.getElementById('statusBox');
            const ormOutput = document.getElementById('ormOutput');
            const jsonOutput = document.getElementById('jsonOutput');
            
            btn.innerText = 'Processing...';
            btn.disabled = true;
            statusBox.className = 'status-box status-loading';
            statusBox.innerText = 'Executing via LLM and verifying...';
            ormOutput.innerText = 'Generating...';
            jsonOutput.innerText = 'Waiting...';

            try {
                const response = await fetch('/api/v1/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sql, max_retries: 2 })
                });

                const data = await response.json();

                // Update UI
                if (data.success) {
                    statusBox.className = 'status-box status-success';
                    statusBox.innerText = `✅ Verified in ${data.attempts} attempt(s)`;
                } else {
                    statusBox.className = 'status-box status-error';
                    statusBox.innerText = `❌ Failed: ${data.error_message}`;
                }

                ormOutput.innerText = data.final_orm;
                jsonOutput.innerText = JSON.stringify(data, null, 2);
                
                // Add to History Table
                addHistoryRow(sql, data.attempts, data.success);
                
                // Refresh Health (to update memory count)
                checkHealth();

            } catch (error) {
                statusBox.className = 'status-box status-error';
                statusBox.innerText = `💥 API Error: ${error.message}`;
            } finally {
                btn.innerText = 'Execute Query';
                btn.disabled = false;
            }
        }

        function addHistoryRow(sql, attempts, success) {
            const tbody = document.getElementById('historyBody');
            
            // Clear placeholder if it's the first query
            if (tbody.innerHTML.includes('No queries executed')) {
                tbody.innerHTML = '';
            }

            const tr = document.createElement('tr');
            const time = new Date().toLocaleTimeString();
            const statusTag = success 
                ? '<span class="tag-success">Success</span>' 
                : '<span class="tag-fail">Failed</span>';
            const truncatedSql = sql.length > 40 ? sql.substring(0, 40) + '...' : sql;

            tr.innerHTML = `
                <td>${time}</td>
                <td style="font-family: 'Fira Code', monospace; color: var(--text-muted);">${truncatedSql}</td>
                <td>${attempts}</td>
                <td>${statusTag}</td>
            `;
            
            // Prepend to table
            tbody.insertBefore(tr, tbody.firstChild);
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_DASHBOARD

@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        with sqlite3.connect("agent_memory.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM success_cases")
            count = cursor.fetchone()[0]
        return {"status": "healthy", "database": "connected", "memory_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/v1/translate", response_model=VerificationResult)
def translate_sql(request: QueryRequest):
    start_time = time.time()
    
    try:
        original_orm = generate_orm(request.sql)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM Generation failed: {str(e)}")
        
    current_orm = original_orm
    attempt = 0
    success = False
    last_error = ""
    final_data = None

    while attempt <= request.max_retries and not success:
        try:
            sql_rows = run_sql(request.sql)
            orm_rows = run_orm(current_orm)
            ok, diff = compare(sql_rows, orm_rows)
            
            if ok:
                success = True
                final_data = sql_rows
                memory.add_success(request.sql, current_orm)
            else:
                last_error = diff
        except Exception as e:
            last_error = str(e)

        if not success and attempt < request.max_retries:
            current_orm = reflect_and_fix(request.sql, current_orm, last_error)
            attempt += 1
        else:
            break

    return VerificationResult(
        success=success,
        attempts=attempt + 1,
        original_orm=original_orm,
        final_orm=current_orm,
        error_message=None if success else last_error,
        data=final_data
    )