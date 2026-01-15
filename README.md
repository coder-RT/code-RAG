# Code-RAG

<div align="center">

![Code-RAG](https://img.shields.io/badge/Code--RAG-AI%20Powered-cyan?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)

**An intelligent coding agent powered by RAG for understanding codebases, architecture, and infrastructure**

</div>

---

## 🎯 Features

- **🔍 Codebase Understanding**: Ask natural language questions about any codebase
- **🏗️ Architecture Analysis**: Automatically detect modules, layers, and design patterns
- **☁️ Infrastructure Mapping**: Parse Terraform configs and map to application components
- **📊 Dependency Graphs**: Visualize how everything connects with interactive diagrams
- **💬 AI Chat Interface**: Conversational interface for exploring codebases

## 📁 Project Structure

```
code-RAG/
├── server/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Configuration
│   │   └── services/      # Business logic
│   ├── requirements.txt
│   └── .env.example
│
├── client/                 # Vite + React Frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route pages
│   │   └── lib/           # Utilities & API client
│   ├── package.json
│   └── tailwind.config.js
│
├── shared/                 # Shared types & documentation
│   ├── schemas/           # TypeScript interfaces
│   └── docs/              # Architecture docs
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key

### Backend Setup

```bash
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:5173 to access the app.

## 🎨 User Interface

### Dashboard
Index codebases and chat with the AI about your code.

### Code Explorer
Browse directory structure and get AI-powered explanations.

### Architecture View
Visualize modules, layers, and detected design patterns.

### Infrastructure View
Analyze Terraform configurations and understand cloud resources.

### Graph View
Generate and explore dependency graphs with Mermaid diagrams.

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/codebase/index` | POST | Index a codebase |
| `/api/codebase/query` | POST | Ask questions about code |
| `/api/codebase/explain` | POST | Get file/directory explanations |
| `/api/architecture/analyze` | POST | Analyze system architecture |
| `/api/terraform/analyze` | POST | Parse Terraform configs |
| `/api/graph/generate` | POST | Generate dependency graphs |

See [API Documentation](./shared/docs/API.md) for full details.

## 🧠 How It Works

### RAG Pipeline

1. **Indexing**: Files are parsed, chunked, and embedded using OpenAI
2. **Storage**: Embeddings stored in ChromaDB vector database
3. **Retrieval**: Questions trigger similarity search for relevant code
4. **Generation**: LLM generates answers using retrieved context

### Architecture Detection

The system identifies:
- **Modules**: Based on package indicators (`__init__.py`, `package.json`, etc.)
- **Layers**: Presentation, business, data, infrastructure
- **Patterns**: MVC, Repository, Factory, and more

### Graph Generation

Uses NetworkX to:
- Parse import statements across languages
- Resolve dependencies to actual files
- Export as Mermaid diagrams or SVG

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | Your OpenAI API key |
| `LLM_MODEL` | ❌ | `gpt-4o` | LLM model to use |
| `EMBEDDING_MODEL` | ❌ | `text-embedding-3-small` | Embedding model |
| `CHROMA_PERSIST_DIRECTORY` | ❌ | `./data/chroma` | Vector DB storage |
| `PORT` | ❌ | `8000` | Server port |

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration
- **ChromaDB** - Vector database
- **NetworkX** - Graph algorithms
- **OpenAI** - LLM and embeddings

### Frontend
- **Vite** - Fast build tool
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Mermaid.js** - Diagram rendering
- **TanStack Query** - Data fetching

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details.

---

<div align="center">

**Built with ❤️ using RAG technology**

</div>

