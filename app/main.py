from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import create_db_and_tables
from app.routers import contracts, users, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup
    create_db_and_tables()
    yield
    # Runs on shutdown (add cleanup here if needed)


app = FastAPI(
    title="ContractIQ",
    description="AI-powered contract analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(contracts.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}