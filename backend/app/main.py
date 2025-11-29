"""FastAPI entrypoint for show-me-the-money."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from .api import api_router
from .core.config import get_settings
from .core.logger import configure_tracing, logger

app = FastAPI(title="show-me-the-money API")
app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    configure_tracing(settings.application_insights_connection_string, settings.app_name)
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    logger.info("show-me-the-money API started")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
