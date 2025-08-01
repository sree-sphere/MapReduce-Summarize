from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import os
from dotenv import load_dotenv

load_dotenv()

resource = Resource(attributes={"service.name": os.getenv("APP_NAME", "summarizer")})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Only set up OTLP exporter if endpoint is configured
otel_endpoint = os.getenv("OTEL_EXPORTER")
if otel_endpoint:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        
        # Configure for insecure connection (no TLS)
        otlp_exporter = OTLPSpanExporter(
            endpoint=otel_endpoint,
            insecure=True
        )
        
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        print(f"OTLP exporter configured for {otel_endpoint}")
    except Exception as e:
        print(f"Failed to configure OTLP exporter: {e}")