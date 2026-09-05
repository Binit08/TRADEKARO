import json
import logging
import uuid
from fastapi.testclient import TestClient

from app.api.server import app, request_id_var
from app.metrics.prometheus import KITE_RETRIES

def test_request_id_middleware_generates_id():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Verify it is a valid UUID
    request_id = response.headers["X-Request-ID"]
    uuid.UUID(request_id)

def test_request_id_middleware_propagates_passed_id():
    client = TestClient(app)
    passed_id = str(uuid.uuid4())
    response = client.get("/metrics", headers={"X-Request-ID": passed_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == passed_id

def test_json_logging_and_request_id_injection():
    # Set up a logger to capture records
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    
    # We will test that when request_id is set in the contextvar,
    # the RequestIDFilter injects it and CustomJsonFormatter outputs it in JSON.
    
    # Create our custom handler and formatter to capture output
    import io
    from app.api.server import CustomJsonFormatter, RequestIDFilter
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s %(request_id)s"))
    handler.addFilter(RequestIDFilter())
    logger.addHandler(handler)
    
    # Set request ID in contextvar
    test_id = "abc-123-xyz"
    token = request_id_var.set(test_id)
    try:
        logger.info("Test message for structured logging")
    finally:
        request_id_var.reset(token)
        
    handler.flush()
    log_output = stream.getvalue().strip()
    
    # Parse the output as JSON
    parsed = json.loads(log_output)
    assert parsed["message"] == "Test message for structured logging"
    assert parsed["request_id"] == test_id
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert "timestamp" in parsed

def test_metrics_endpoint_exposes_kite_retries():
    # Increment the custom counter
    KITE_RETRIES.labels(symbol="TEST_SYM").inc()
    
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "kite_retries_total" in response.text
    assert 'symbol="TEST_SYM"' in response.text
