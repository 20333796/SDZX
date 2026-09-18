from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.observability import MetricsMiddleware, metrics_response
from app.rate_limit import AnonymousChatRateLimitMiddleware
from app.routers import admin, chat, geo_data, knowledge, knowledge_graph, learning, portal, resources, well_log
from app.services.resources import seed_resources
from app.services.learning import seed_learning_tasks, seed_demo_submissions
from app.services.geo_data import seed_geo_datasets

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_resources(session)
        seed_learning_tasks(session)
        seed_demo_submissions(session)
        seed_geo_datasets(session)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(AnonymousChatRateLimitMiddleware)
app.add_middleware(MetricsMiddleware)

app.include_router(resources.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(well_log.router, prefix="/api/v1")
app.include_router(geo_data.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(knowledge_graph.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")
app.include_router(portal.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/healthz", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/readyz", tags=["health"])
def readiness() -> dict[str, str]:
    """Confirm the API can reach its required relational data store."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error
    return {"status": "ready", "database": "available"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()
