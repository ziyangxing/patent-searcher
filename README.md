# Patent Searcher

AI-powered global patent search tool. Search, download, and analyze patents worldwide.

## Features

| Feature | Description |
|---------|-------------|
| **F1 Smart Search** | Natural language patent search via Google Patents (SerpAPI), returns real global patents |
| **F2 Number Lookup** | Precise patent number search with multi-format support (CN/US/EP/WO/JP/KR/DE/GB/FR/TW/IN) |
| **F3 Similarity Search** | Upload a patent document (PDF/TXT), AI extracts features and finds similar patents |
| **Real-time Streaming** | SSE streaming for live search progress and AI analysis |
| **PDF Download** | Download real patent PDFs directly from Google Patents |
| **AI Chat** | Ask questions about specific patents, AI answers based on patent content |
| **Multi-source** | Google Patents (global) + local FAISS semantic index |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- [SerpAPI key](https://serpapi.com) (free, 100 searches/month)

### 1. Clone & Install

```bash
git clone https://github.com/ziyangxing/patent-searcher.git
cd patent-searcher

# Backend
cd backend
pip install -r requirements.txt
python -m app.services.data_importer   # Build FAISS index

# Frontend
cd ../frontend
npm install
```

### 2. Configure

```bash
cp .env.example backend/.env
# Edit backend/.env, add your SerpAPI key:
#   SERPAPI_KEY=your_key_here
# Optional: add OpenAI key for AI analysis:
#   OPENAI_API_KEY=sk-your-key
```

### 3. Start

```bash
# Terminal 1: Backend
cd backend
python run_server.py
# → http://localhost:8766/docs

# Terminal 2: Frontend
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8766/api" > .env.local
npm run dev
# → http://localhost:3000
```

Open http://localhost:3000/search and search for any technology.

## API Endpoints

```
POST /api/search/intent          F1: Smart patent search
POST /api/search/intent/stream   F1: Search with SSE streaming
POST /api/search/similar         F3: Similar patent search
POST /api/search/similar/stream  F3: Similar search SSE streaming
GET  /api/patent/{number}        F2: Patent number lookup
POST /api/patent/batch            F2: Batch patent lookup
POST /api/upload/patent           Upload patent document (PDF/TXT)
POST /api/chat/patent/{id}        AI chat about a patent (SSE)
GET  /api/health                  Health check
```

Full Swagger docs: http://localhost:8766/docs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python FastAPI + Uvicorn |
| Frontend | Next.js 16 + React 19 + Tailwind CSS 4 |
| Search | Google Patents (SerpAPI) + FAISS semantic |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| LLM | LiteLLM (OpenAI / Anthropic / Ollama) |
| Database | PostgreSQL + pgvector (optional) |
| Cache | Redis (optional) |
| Search Engine | Elasticsearch (optional) |

## Architecture

```
User Query → Search Agent
              ├── Google Patents (SerpAPI) → Real global patents
              ├── FAISS Semantic Search → Local vector similarity
              └── LLM Analysis → AI-powered insights
```

## Docker (Full Stack)

```bash
docker-compose up -d
# Starts: PostgreSQL + Elasticsearch + Redis + Backend + Frontend
```

## Download Patents

The `play_patents/` directory contains 14 sample patent PDFs downloaded from Google Patents covering coaxial drone technology from CN/US/EP/WO/KR/JP/HK.

To download patents via API:

```bash
curl -X POST http://localhost:8766/api/search/intent \
  -H "Content-Type: application/json" \
  -d '{"query":"quantum computing error correction","top_k":5}'
# Each result includes a google_url link for direct PDF download
```

## License

MIT
