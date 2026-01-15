# Code-RAG API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently, the API does not require authentication. In production, you should implement appropriate auth mechanisms.

---

## Codebase API

### Index Codebase

Indexes a codebase for RAG queries.

```http
POST /codebase/index
```

**Request Body:**
```json
{
  "path": "/path/to/codebase",
  "include_patterns": ["*.py", "*.ts"],
  "exclude_patterns": ["node_modules", ".git", "__pycache__"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Codebase indexed successfully",
  "data": {
    "files_indexed": 150,
    "chunks_created": 450,
    "path": "/path/to/codebase"
  }
}
```

### Query Codebase

Ask questions about the indexed codebase.

```http
POST /codebase/query
```

**Request Body:**
```json
{
  "question": "How does the authentication work?",
  "context_limit": 5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Query processed successfully",
  "data": {
    "answer": "The authentication in this codebase uses JWT tokens...",
    "sources": [
      {
        "file": "src/auth/jwt.py",
        "snippet": "def verify_token(token: str)..."
      }
    ]
  }
}
```

### Explain Code

Get an explanation of a specific file or directory.

```http
POST /codebase/explain
```

**Request Body:**
```json
{
  "path": "/path/to/file.py",
  "detail_level": "detailed"
}
```

### Get Structure

Get directory structure of a codebase.

```http
GET /codebase/structure/{path}
```

---

## Architecture API

### Analyze Architecture

Perform full architecture analysis.

```http
POST /architecture/analyze
```

**Request Body:**
```json
{
  "path": "/path/to/codebase",
  "analysis_type": "full"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Architecture analyzed successfully",
  "data": {
    "modules": [...],
    "layers": [...],
    "patterns": [...],
    "summary": "..."
  }
}
```

### Get Modules

List all modules with their responsibilities.

```http
GET /architecture/modules/{path}
```

### Get Layers

Identify architectural layers.

```http
GET /architecture/layers/{path}
```

### Detect Patterns

Detect design patterns in the codebase.

```http
GET /architecture/patterns/{path}
```

---

## Terraform API

### Analyze Terraform

Analyze Terraform configuration.

```http
POST /terraform/analyze
```

**Request Body:**
```json
{
  "path": "/path/to/terraform",
  "include_modules": true
}
```

### Get Resources

List all Terraform resources.

```http
GET /terraform/resources/{path}
```

### Get Application Links

Map Terraform to application components.

```http
POST /terraform/app-links
```

### Explain Infrastructure

Get human-readable infrastructure summary.

```http
POST /terraform/explain
```

---

## Graph API

### Generate Graph

Generate a dependency or integration graph.

```http
POST /graph/generate
```

**Request Body:**
```json
{
  "path": "/path/to/codebase",
  "graph_type": "full",
  "output_format": "json"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Graph generated successfully",
  "data": {
    "nodes": [
      {
        "id": "src/main.py",
        "label": "main.py",
        "type": "python"
      }
    ],
    "edges": [
      {
        "source": "src/main.py",
        "target": "src/utils.py",
        "relationship": "imports"
      }
    ],
    "stats": {
      "total_nodes": 50,
      "total_edges": 75
    }
  }
}
```

### Export as Mermaid

Export graph as Mermaid diagram syntax.

```http
POST /graph/export/mermaid
```

### Export as SVG

Export graph as SVG image.

```http
POST /graph/export/svg
```

### Get Summary

Get a readable summary of graph relationships.

```http
POST /graph/summary
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (path doesn't exist)
- `500` - Internal Server Error

