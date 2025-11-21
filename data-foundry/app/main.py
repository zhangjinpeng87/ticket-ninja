from fastapi import FastAPI
from .routers import ingest

app = FastAPI(
    title="Ticket Ninja Data Foundry",
    version="0.1.0",
    description="On-demand documentation ingestion service for the Ticket Ninja knowledge base.",
)


@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(ingest.router)

