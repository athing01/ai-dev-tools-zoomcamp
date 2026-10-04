from __future__ import annotations

import atexit
import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


_LOGGER = logging.getLogger(__name__)
_CONFIGURED = False

TRACE_PROVIDER: TracerProvider | None = None
METER_PROVIDER: MeterProvider | None = None
LOGGER_PROVIDER: LoggerProvider | None = None

TRACER = trace.get_tracer("taskflow-backend")
METER = metrics.get_meter("taskflow-backend")

TASKS_LIST_REQUESTS = METER.create_counter(
    "taskflow.api.tasks.list.requests",
    description="Number of GET /api/tasks requests.",
)

TASKS_LIST_ERRORS = METER.create_counter(
    "taskflow.api.tasks.list.errors",
    description="Number of GET /api/tasks requests that failed.",
)

TASKS_LIST_DURATION = METER.create_histogram(
    "taskflow.api.tasks.list.duration",
    unit="ms",
    description="Duration of GET /api/tasks requests.",
)


def _enabled() -> bool:
    return os.getenv("TASKFLOW_OBSERVABILITY_ENABLED", "false").lower() == "true"


def configure_observability(app) -> None:
    global _CONFIGURED, TRACE_PROVIDER, METER_PROVIDER, LOGGER_PROVIDER

    if _CONFIGURED or not _enabled():
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "taskflow-backend")
    environment = os.getenv("TASKFLOW_ENVIRONMENT", "unknown")
    release = os.getenv("TASKFLOW_RELEASE_SHA", "unknown")

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": release,
            "deployment.environment.name": environment,
        }
    )

    TRACE_PROVIDER = TracerProvider(resource=resource)
    TRACE_PROVIDER.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter())
    )
    trace.set_tracer_provider(TRACE_PROVIDER)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter()
    )
    METER_PROVIDER = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(METER_PROVIDER)

    LOGGER_PROVIDER = LoggerProvider(resource=resource)
    LOGGER_PROVIDER.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter())
    )

    trace_logging_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=LOGGER_PROVIDER,
    )

    application_logger = logging.getLogger("taskflow_backend")
    application_logger.setLevel(logging.INFO)
    application_logger.addHandler(trace_logging_handler)

    LoggingInstrumentor().instrument(
        set_logging_format=False,
        inject_trace_context=True,
        enable_log_auto_instrumentation=False,
    )
    FastAPIInstrumentor.instrument_app(app)

    _CONFIGURED = True

    _LOGGER.info(
        "TaskFlow observability configured",
        extra={
            "operation": "observability.bootstrap",
            "taskflow_environment": environment,
            "taskflow_release": release,
        },
    )

    atexit.register(_shutdown)


def _shutdown() -> None:
    if LOGGER_PROVIDER is not None:
        LOGGER_PROVIDER.shutdown()
    if METER_PROVIDER is not None:
        METER_PROVIDER.shutdown()
    if TRACE_PROVIDER is not None:
        TRACE_PROVIDER.shutdown()
