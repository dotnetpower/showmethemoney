"""Logging configuration that can ship telemetry to Application Insights."""

import logging
from typing import Literal

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(format=_LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger("show-me-the-money")


def configure_tracing(connection_string: str | None, service_name: str) -> None:
    """Attach Azure Monitor exporter when a connection string is configured."""
    if not connection_string:
        logger.info("Application Insights connection string not provided; tracing disabled")
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = AzureMonitorTraceExporter.from_connection_string(connection_string)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    logger.info("Application Insights exporter configured")
