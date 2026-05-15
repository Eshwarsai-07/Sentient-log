from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Configure structured root logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from app.api import health, ingest, query
from app.ingestion.worker import worker
from app.clickhouse.client import run_migrations, close_client

# OpenTelemetry setup
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await run_migrations()
    worker.start()
    yield
    # Shutdown
    await worker.stop()
    await close_client()

app = FastAPI(
    title="SentientLog",
    description="AI-powered observability analytics platform",
    version="1.0.0",
    lifespan=lifespan
)

# Register Root-level Kubernetes Probes
app.include_router(health.router)

# Register API v1 Endpoints
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")

FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=3100, reload=True)
