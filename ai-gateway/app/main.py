from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import analyze, knowledge_base

app = FastAPI(title="Ticket Ninja AI Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True}

app.include_router(analyze.router)
app.include_router(knowledge_base.router)
