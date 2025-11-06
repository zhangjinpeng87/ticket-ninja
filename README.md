# Ticket Ninja – Jira AI Assistant (Forge + FastAPI)

This monorepo contains an Atlassian Forge app for Jira and an external AI Gateway (FastAPI) that together enable an AI assistant to analyze error logs or screenshots, retrieve similar resolved tickets or knowledge base articles, and synthesize grounded answers with citations and confidence scores.

![Ticket-Ninja](resources/ticket-ninja.png)

## Structure

- `forge-app/` – Forge app (TypeScript)
  - UI (Custom UI with React) for the "AI Assistant" panel
  - Resolver functions to call Jira/Confluence and the AI Gateway
- `ai-gateway/` – External AI Gateway (FastAPI)
  - Endpoints and service stubs for Intent → Retriever → RAG → LLM
  - Screenshot parsing service that calls OCR service
- `ocr-service/` – OCR Service (FastAPI)
  - Standalone service for extracting error logs from screenshots
  - Uses EasyOCR for text recognition and error pattern detection
- `docker/` – Dockerfiles

## Features

- Input: text question and/or screenshot upload (Forge Media API placeholder)
- Backend: Jira/Confluence API integration (stubs), proxy to AI Gateway
- Gateway: Intent classification, retrieval, RAG, answer synthesis stubs
- Response: AI answer, citations, confidence, KB suggestions

## Quick Start

1) Prerequisites
- Node 18+
- Python 3.10+
- Atlassian Forge CLI (`npm i -g @forge/cli`)

2) Configure environment
- Copy `ai-gateway/.env.example` to `ai-gateway/.env` and adjust as needed

3) Run OCR Service (required for screenshot processing)

**Option A: Direct Python**
```bash
cd ocr-service
pip install -r requirements.txt
python main.py
# Or use the startup script:
# ./start.sh
```

**Option B: Using Docker**
```bash
# Build and run from project root:
docker build -f docker/Dockerfile.ocr-service -t ticket-ninja-ocr-service .
docker run -p 8001:8001 ticket-ninja-ocr-service

# Or use docker-compose (runs both services):
cd docker
docker-compose up
```

The OCR service runs on port 8001 by default. Note: EasyOCR will download model files (~100MB) on first run.

4) Run AI Gateway (local)
```bash
cd ai-gateway
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OCR_SERVICE_URL=http://localhost:8001  # Point to OCR service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5) Deploy Forge app
```bash
cd forge-app
npm install
# Login and register app if first time
forge login
forge register
# Deploy and install to your Jira site
forge deploy
forge install
```

6) Configure allowed outbound links
- In `forge-app/manifest.yml`, ensure the AI Gateway URL is listed under `permissions.external.fetch`.

## Development Notes

- UI is a minimal Custom UI React app using `@forge/bridge` to call resolver.
- Resolver proxies to the AI Gateway `/analyze` endpoint and will later add Jira/Confluence lookups.
- AI Gateway returns structured JSON: `answer`, `citations`, `confidence`, `kb_suggestions`, `debug`.
- OCR Service extracts text from screenshots and identifies error log patterns using EasyOCR.

## Roadmap

- Implement real Media API upload and secure storage
- Implement Jira/Confluence retrieval and vector index (Milvus/Weaviate)
- Replace stubs with real models: miniLM/DistilBERT, embeddings, LLM
- Add authentication between Forge app and Gateway
- Observability and rate limiting
