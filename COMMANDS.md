# Code-RAG Commands Reference

Quick reference for all commands needed to run and manage Code-RAG.

## Prerequisites

```bash
# Install Redis (macOS)
brew install redis

# Install Python dependencies
cd server
pip install -r requirements.txt

# Install Node dependencies
cd client
npm install
```

---

## Starting Services

### 1. Start Redis
```bash
# Start Redis server
redis-server

# Or run in background
brew services start redis
```

### 2. Start FastAPI Server
```bash
cd server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Celery Worker (for async indexing)
```bash
cd server
celery -A app.core.celery_app worker --loglevel=info
```

### 4. Start React Client
```bash
cd client
npm run dev
```

---

## Stopping Services

### Kill FastAPI Server (port 8000)
```bash
lsof -ti:8000 | xargs kill -9
```

### Kill React Dev Server (port 5173)
```bash
lsof -ti:5173 | xargs kill -9
```

### Kill Celery Workers
```bash
pkill -f "celery"
```

### Stop Redis
```bash
# If running as service
brew services stop redis

# If running in foreground, just Ctrl+C
```

### Kill Any Port
```bash
# Replace PORT with the port number
lsof -ti:PORT | xargs kill -9
```

---

## Redis Management

### Flush Redis (clear all data)
```bash
redis-cli FLUSHALL
```

### Check Redis Status
```bash
redis-cli ping
# Should return: PONG
```

### View Redis Keys
```bash
redis-cli KEYS "*"
```

### Clear Celery Task Queue
```bash
redis-cli FLUSHDB
```

---

## ChromaDB Management

### Clear All Indexed Data
```bash
rm -rf server/data/chroma
```

### Check ChromaDB Size
```bash
du -sh server/data/chroma
```

---

## Troubleshooting

### Celery Worker Crashes on macOS
If you see `objc[PID]: +[NSNumber initialize]` errors:
```bash
# The celery_app.py already handles this, but if needed:
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
celery -A app.core.celery_app worker --loglevel=info
```

### Server Not Reloading Changes
```bash
# Kill and restart with --reload flag
lsof -ti:8000 | xargs kill -9
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Not Picking Up Code Changes
Celery workers don't auto-reload. Restart the worker:
```bash
pkill -f "celery"
celery -A app.core.celery_app worker --loglevel=info
```

### Embedding Dimension Mismatch Error
If switching between OpenAI and HuggingFace embeddings:
```bash
# Clear ChromaDB and re-index
rm -rf server/data/chroma
```

### Check What's Running on a Port
```bash
lsof -i:8000
lsof -i:5173
lsof -i:6379  # Redis
```

---

## Quick Start (All-in-One)

Open 4 terminal tabs and run:

**Tab 1 - Redis:**
```bash
redis-server
```

**Tab 2 - FastAPI Server:**
```bash
cd /Users/rachit/Documents/Code/code-RAG/server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Tab 3 - Celery Worker:**
```bash
cd /Users/rachit/Documents/Code/code-RAG/server
celery -A app.core.celery_app worker --loglevel=info
```

**Tab 4 - React Client:**
```bash
cd /Users/rachit/Documents/Code/code-RAG/client
npm run dev
```

Then open: http://localhost:5173

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/codebase/index` | POST | Index a codebase |
| `/api/codebase/query` | POST | Query indexed codebase |
| `/api/codebase/projects` | GET | List all indexed projects |
| `/api/codebase/projects/{name}` | DELETE | Delete a project |
| `/api/codebase/task/{task_id}` | GET | Check async task status |
| `/api/health` | GET | Health check |

---

## Environment Variables

Copy `server/env.sample` to `server/.env` and configure:

```bash
cp server/env.sample server/.env
```

Key variables:
- `OPENAI_API_KEY` - Required for OpenAI embeddings/LLM
- `EMBEDDING_PROVIDER` - `openai` or `huggingface`
- `CELERY_BROKER_URL` - Redis URL (default: `redis://localhost:6379/0`)
