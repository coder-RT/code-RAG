# Code-RAG Architecture

## Overview

Code-RAG is a Retrieval-Augmented Generation (RAG) powered **coding agent** that helps developers understand codebases, architecture, and infrastructure. It uses an agentic architecture where an orchestrator coordinates multiple tools to answer complex questions.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Client)                               │
│  ┌────────────┬────────────┬────────────┬────────────┬────────────────────┐ │
│  │ Dashboard  │  Explorer  │Architecture│  Infra     │   Graph View       │ │
│  │            │            │   View     │   View     │                    │ │
│  └────────────┴────────────┴────────────┴────────────┴────────────────────┘ │
│                                    │                                         │
│                         React Query + Axios                                  │
│                                    │                                         │
│                              REST API Calls                                  │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (Server)                                │
│                                                                              │
│  ┌───────────────────────────── API Layer ─────────────────────────────────┐│
│  │  /api/agent    /api/codebase   /api/architecture   /api/terraform       ││
│  │  /api/graph                                                              ││
│  └──────────────────────────────────┬───────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────── Agent Layer ─────────────────────────────────┐│
│  │                                                                          ││
│  │   ┌──────────────────────────────────────────────────────────────────┐  ││
│  │   │                        ORCHESTRATOR                               │  ││
│  │   │   • Receives user queries                                         │  ││
│  │   │   • Plans execution steps                                         │  ││
│  │   │   • Selects & calls tools                                         │  ││
│  │   │   • Synthesizes final response                                    │  ││
│  │   └───────────────────────────────┬──────────────────────────────────┘  ││
│  │                                   │                                      ││
│  │         ┌─────────────────────────┼─────────────────────────┐           ││
│  │         ▼                         ▼                         ▼           ││
│  │   ┌──────────┐            ┌──────────────┐           ┌──────────┐       ││
│  │   │  MEMORY  │            │    TOOLS     │           │ PROMPTS  │       ││
│  │   │          │            │   Registry   │           │          │       ││
│  │   │ • Conv.  │            │              │           │ • System │       ││
│  │   │   History│            │ • 6 tools    │           │ • Planning│      ││
│  │   │ • Working│            │   registered │           │ • Synthesis│     ││
│  │   │   Memory │            │              │           │          │       ││
│  │   └──────────┘            └──────┬───────┘           └──────────┘       ││
│  │                                  │                                       ││
│  └──────────────────────────────────┼───────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────Services Layer ─────────────────────────────────┐│
│  │                                                                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     ││
│  │  │ RAG Engine  │  │    Code     │  │Architecture │  │  Terraform  │     ││
│  │  │             │  │  Analyzer   │  │  Analyzer   │  │  Analyzer   │     ││
│  │  │ • Index     │  │             │  │             │  │             │     ││
│  │  │ • Query     │  │ • Explain   │  │ • Modules   │  │ • Resources │     ││
│  │  │ • Embed     │  │ • Structure │  │ • Layers    │  │ • Variables │     ││
│  │  │             │  │             │  │ • Patterns  │  │ • Outputs   │     ││
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘  └─────────────┘     ││
│  │         │                                                                ││
│  │         │         ┌─────────────┐                                        ││
│  │         │         │   Graph     │                                        ││
│  │         │         │  Generator  │                                        ││
│  │         │         │             │                                        ││
│  │         │         │ • Deps      │                                        ││
│  │         │         │ • Mermaid   │                                        ││
│  │         │         │ • SVG       │                                        ││
│  │         │         └─────────────┘                                        ││
│  └─────────┼────────────────────────────────────────────────────────────────┘│
│            │                                                                 │
└────────────┼─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                 │
│                                                                             │
│    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐            │
│    │   ChromaDB   │      │   OpenAI     │      │  Filesystem  │            │
│    │   (Vectors)  │      │   LLM API    │      │  (Codebase)  │            │
│    │              │      │              │      │              │            │
│    │ • Embeddings │      │ • GPT-4o     │      │ • Source     │            │
│    │ • Similarity │      │ • Embeddings │      │   files      │            │
│    │   search     │      │              │      │ • .tf files  │            │
│    └──────────────┘      └──────────────┘      └──────────────┘            │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (Client)

**Tech Stack:** Vite + React 19 + TypeScript + Tailwind CSS

| Component | Description |
|-----------|-------------|
| `Dashboard` | Main entry with codebase indexing and chat interface |
| `CodeExplorer` | File tree navigation with AI explanations |
| `ArchitectureView` | Module, layer, and pattern visualization |
| `InfrastructureView` | Terraform resource analysis |
| `GraphView` | Interactive Mermaid dependency graphs |
| `ChatInterface` | Conversational UI for agent interaction |

**State Management:** TanStack Query (React Query)

---

### 2. API Layer

REST endpoints organized by domain:

| Route | Purpose |
|-------|---------|
| `/api/agent/*` | Agent chat, history, planning |
| `/api/codebase/*` | Index, query, explain code |
| `/api/architecture/*` | Module/layer/pattern analysis |
| `/api/terraform/*` | Infrastructure parsing |
| `/api/graph/*` | Dependency graph generation |

---

### 3. Agent Layer (Orchestration)

The **brain** of Code-RAG. Coordinates tools to answer complex questions.

```
server/app/agent/
├── orchestrator.py    # Main agent loop
├── tools.py           # Tool registry & execution
├── memory.py          # Conversation & working memory
└── prompts.py         # System prompts & templates
```

#### Orchestrator (`orchestrator.py`)

```python
class CodeRAGAgent:
    """Main agent that coordinates everything"""
    
    async def chat(message) -> response
        # 1. Add to conversation memory
        # 2. Run agent loop (may call tools)
        # 3. Return synthesized response
    
    async def _run_agent_loop():
        # LLM decides which tools to call
        # Execute tools, collect results
        # Repeat until final answer ready
```

#### Tools (`tools.py`)

6 tools registered for the agent to use:

| Tool | Service | Purpose |
|------|---------|---------|
| `query_codebase` | RAGEngine | Search code with RAG |
| `explain_code` | CodeAnalyzer | Explain files/dirs |
| `analyze_architecture` | ArchitectureAnalyzer | Find modules/patterns |
| `analyze_terraform` | TerraformAnalyzer | Parse .tf files |
| `generate_graph` | GraphGenerator | Create dep graphs |
| `get_structure` | CodeAnalyzer | Directory tree |

#### Memory (`memory.py`)

```python
ConversationMemory:
    - Message history (user, assistant, tool)
    - Tool call records
    - Session metadata

WorkingMemory:
    - Current goal
    - Execution plan
    - Observations from tools
    - Scratchpad for intermediate data
```

---

### 4. Services Layer

Individual capabilities the agent can use as tools:

| Service | Responsibility |
|---------|----------------|
| `RAGEngine` | Vector indexing, similarity search, LLM Q&A |
| `CodeAnalyzer` | File/directory explanation, structure |
| `ArchitectureAnalyzer` | Module, layer, pattern detection |
| `TerraformAnalyzer` | .tf parsing, resource mapping |
| `GraphGenerator` | NetworkX graphs, Mermaid export |

---

### 5. External Services

| Service | Purpose |
|---------|---------|
| **ChromaDB** | Vector database for code embeddings |
| **OpenAI API** | LLM (GPT-4o) + Embeddings |
| **Filesystem** | Source code access |

---

## Data Flows

### Agent Chat Flow

```
User Message
     │
     ▼
┌─────────────────┐
│   Orchestrator  │
│                 │
│ 1. Add to memory│
│ 2. Send to LLM  │◄────────────────────────┐
│    with tools   │                         │
└────────┬────────┘                         │
         │                                  │
         ▼                                  │
   ┌─────────────┐                          │
   │ LLM decides │                          │
   │             │                          │
   │ Tool call?  │                          │
   └──────┬──────┘                          │
          │                                 │
    ┌─────┴─────┐                          │
    │           │                          │
   Yes          No                         │
    │           │                          │
    ▼           ▼                          │
┌────────┐  ┌──────────┐                   │
│Execute │  │  Return  │                   │
│ Tool   │  │  Answer  │                   │
└───┬────┘  └──────────┘                   │
    │                                      │
    ▼                                      │
┌─────────────────┐                        │
│ Record result   │                        │
│ in memory       │────────────────────────┘
└─────────────────┘
      (loop until answer)
```

### RAG Indexing Flow

```
Codebase Path
     │
     ▼
┌─────────────────┐
│  Walk directory │
│  (filter files) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunk files    │
│  (1500 tokens)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate       │
│  embeddings     │──────► OpenAI API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store in       │
│  ChromaDB       │
└─────────────────┘
```

### RAG Query Flow

```
User Question
     │
     ▼
┌─────────────────┐
│ Embed question  │──────► OpenAI API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Similarity      │
│ search ChromaDB │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Top K chunks    │
│ as context      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM generates   │
│ answer          │──────► OpenAI API
└────────┬────────┘
         │
         ▼
    Answer + Sources
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `LLM_MODEL` | ❌ | `gpt-4o` | LLM model |
| `EMBEDDING_MODEL` | ❌ | `text-embedding-3-small` | Embedding model |
| `CHROMA_PERSIST_DIRECTORY` | ❌ | `./data/chroma` | Vector DB path |
| `PORT` | ❌ | `8000` | Server port |
| `CORS_ORIGINS` | ❌ | `localhost:5173` | Allowed origins |

---

## Directory Structure

```
code-RAG/
├── client/                      # Frontend
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Route pages
│   │   └── lib/api.ts           # API client
│   └── package.json
│
├── server/                      # Backend
│   ├── app/
│   │   ├── agent/               # 🧠 Orchestration
│   │   │   ├── orchestrator.py
│   │   │   ├── tools.py
│   │   │   ├── memory.py
│   │   │   └── prompts.py
│   │   ├── api/                 # REST endpoints
│   │   ├── services/            # 🔧 Individual tools
│   │   └── core/config.py
│   └── requirements.txt
│
├── shared/                      # Shared types & docs
│   ├── schemas/
│   └── docs/
│
└── docker-compose.yml
```

---

## Deployment

### Development

```bash
# Terminal 1: Backend
cd server && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd client && npm install && npm run dev
```

### Production

- Backend: Gunicorn/Uvicorn workers behind nginx
- Frontend: `npm run build` → serve static files
- ChromaDB: Persistent volume mount
- Secrets: Environment variables or secrets manager
