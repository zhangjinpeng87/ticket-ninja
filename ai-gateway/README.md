# AI Gateway (FastAPI)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` – health check
- `POST /analyze` – analyze query and optional screenshot id

## Response shape

```json
{
  "answer": "string",
  "citations": [{ "title": "string", "url": "string", "source_type": "jira|confluence|other" }],
  "confidence": 0.0,
  "kb_suggestions": [{ "title": "string", "url": "string" }],
  "debug": {}
}
```

## Notes

- Service modules are stubs. Replace with real embeddings, vector DB, and LLM calls.
