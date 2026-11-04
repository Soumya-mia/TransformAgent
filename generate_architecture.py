import graphviz

def create_architecture_diagram():
    # Initialize a directed graph
    dot = graphviz.Digraph(comment='TransformAgent Architecture')
    
    # Global graph attributes for a professional dark-mode look
    dot.attr(rankdir='LR', bgcolor='#0b0f19', fontname='Helvetica', fontcolor='white')
    dot.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontcolor='white', penwidth='2')
    dot.attr('edge', color='#4b5563', fontname='Helvetica', fontcolor='#a0aabf', fontsize='10')

    # --- Clusters (Layers) ---
    
    # 1. Frontend Layer
    with dot.subgraph(name='cluster_frontend') as c:
        c.attr(label='Presentation Layer', color='#3b82f6', style='dashed', fontcolor='#3b82f6')
        c.node('UI', 'Streamlit Frontend\n(Dashboard & Playground)', fillcolor='#1e2433', color='#3b82f6')
        c.node('API_DOCS', 'FastAPI HTML Portal\n(Developer Portal)', fillcolor='#1e2433', color='#3b82f6')

    # 2. Backend Layer
    with dot.subgraph(name='cluster_backend') as c:
        c.attr(label='Application Layer', color='#8b5cf6', style='dashed', fontcolor='#8b5cf6')
        c.node('API', 'FastAPI Backend\n(REST Endpoints)', fillcolor='#1e2433', color='#8b5cf6')
        c.node('CACHE', 'In-Memory Cache\n(Query Optimization)', fillcolor='#1e2433', color='#8b5cf6')
        c.node('SECURITY', 'Security Guardrail\n(SQL Injection Blocker)', fillcolor='#1e2433', color='#8b5cf6')

    # 3. AI Agent Layer
    with dot.subgraph(name='cluster_ai') as c:
        c.attr(label='Agentic AI Layer', color='#10b981', style='dashed', fontcolor='#10b981')
        c.node('ENGINE', 'Core Engine\n(Reflection Loop)', fillcolor='#1e2433', color='#10b981')
        c.node('LLM', 'Groq API\n(Llama 3)', fillcolor='#1e2433', color='#10b981')
        c.node('MEMORY', 'Agent Memory\n(Success Cases)', fillcolor='#1e2433', color='#10b981')

    # 4. Data Layer
    with dot.subgraph(name='cluster_data') as c:
        c.attr(label='Data Layer', color='#f59e0b', style='dashed', fontcolor='#f59e0b')
        c.node('POSTGRES', 'PostgreSQL 16\n(Chinook DB)', shape='cylinder', fillcolor='#1e2433', color='#f59e0b')
        c.node('SQLITE', 'SQLite DB\n(agent_memory.db)', shape='cylinder', fillcolor='#1e2433', color='#f59e0b')

    # --- Edges (Data Flow) ---
    
    # User to Frontend
    dot.edge('UI', 'API', label='POST /translate')
    dot.edge('API_DOCS', 'API', label='POST /translate')
    
    # Backend routing
    dot.edge('API', 'SECURITY', label='1. Validate SQL')
    dot.edge('SECURITY', 'CACHE', label='2. Check Cache')
    
    # AI Agent Logic
    dot.edge('CACHE', 'ENGINE', label='3. Process')
    dot.edge('ENGINE', 'LLM', label='Generate ORM', dir='both', color='#10b981')
    dot.edge('ENGINE', 'MEMORY', label='Save/Load Context', dir='both', color='#10b981')
    
    # Database interactions
    dot.edge('ENGINE', 'POSTGRES', label='Execute SQL & ORM', dir='both', color='#f59e0b')
    dot.edge('MEMORY', 'SQLITE', label='Persist Data', dir='both', color='#f59e0b', style='dashed')

    # Output
    dot.render('architecture', format='png', cleanup=True)
    print("✅ Architecture diagram saved as 'architecture.png'")

if __name__ == "__main__":
    create_architecture_diagram()