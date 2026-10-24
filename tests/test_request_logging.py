
import logging

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_successful_request_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="logpilot.access"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any(
        "request_completed" in record.message
        and "method=GET" in record.message
        and "path=/health" in record.message
        and "status_code=200" in record.message
        and "duration_ms=" in record.message
        for record in caplog.records
    )


def test_not_found_request_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="logpilot.access"):
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert any(
        "path=/does-not-exist" in record.message
        and "status_code=404" in record.message
        for record in caplog.records
    )


def test_query_string_is_not_logged(caplog):
    with caplog.at_level(logging.INFO, logger="logpilot.access"):
        response = client.get("/health?token=secret-value")

    assert response.status_code == 200
    assert "secret-value" not in caplog.text
    assert any(
        "path=/health" in record.message
        for record in caplog.records
    )