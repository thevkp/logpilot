
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_logs_endpoint():
    log_content = (
        "2026-10-23 10:00:00 INFO Application started\n"
        "2026-10-23 10:00:01 ERROR Database connection failed\n"
        "this is not a valid log line\n"
    )

    response = client.post(
        "/logs/parse",
        files={
            "file": (
                "app.log",
                log_content.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "logs": [
            {
                "timestamp": "2026-10-23 10:00:00",
                "level": "INFO",
                "message": "Application started",
                "line_number": 1,
            },
            {
                "timestamp": "2026-10-23 10:00:01",
                "level": "ERROR",
                "message": "Database connection failed",
                "line_number": 2,
            },
        ],
        "total": 2,
        "by_severity": {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 0,
            "ERROR": 1,
            "CRITICAL": 0,
        },
    }


def test_parse_logs_with_severity_filter():
    client = TestClient(app)

    log_content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:01:00 ERROR Database connection failed\n"
        "2026-10-24 10:02:00 WARNING High memory usage\n"
        "2026-10-24 10:03:00 ERROR Request failed\n"
    )

    response = client.post(
        "/logs/parse?severity=ERROR",
        files={
            "file": (
                "test.log",
                log_content.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert all(entry["level"] == "ERROR" for entry in data["logs"])




def test_parse_logs_with_invalid_severity():
    client = TestClient(app)

    log_content = "2026-10-24 10:00:00 ERROR Something failed\n"

    response = client.post(
        "/logs/parse?severity=BOGUS",
        files={
            "file": (
                "test.log",
                log_content.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Unsupported severity: BOGUS"


def test_parse_logs_returns_severity_summary():
    client = TestClient(app)

    log_content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:01:00 ERROR Database failed\n"
        "2026-10-24 10:02:00 INFO Request received\n"
        "2026-10-24 10:03:00 CRITICAL Service unavailable\n"
        "This is not a valid log line\n"
    )

    response = client.post(
        "/logs/parse",
        files={
            "file": (
                "test.log",
                log_content.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 4
    assert data["by_severity"] == {
        "DEBUG": 0,
        "INFO": 2,
        "WARNING": 0,
        "ERROR": 1,
        "CRITICAL": 1,
    }


def test_parse_logs_rejects_invalid_utf8():
    response = client.post(
        "/logs/parse",
        files={
            "file": (
                "invalid.log",
                b"2026-10-24 10:00:00 ERROR Bad byte: \xff\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Uploaded file must contain valid UTF-8 text."
    }


def test_parse_logs_rejects_oversized_file():
    from app.main import MAX_UPLOAD_SIZE_BYTES

    oversized_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    response = client.post(
        "/logs/parse",
        files={
            "file": (
                "large.log",
                oversized_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Uploaded file exceeds the 5 MiB size limit."
    }

def test_summary_returns_total_and_severity_counts():
    content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:00:01 ERROR Database failed\n"
        "2026-10-24 10:00:02 ERROR Request failed\n"
        "this is not a valid log line\n"
        "2026-10-24 10:00:03 WARNING Slow request\n"
    )

    response = client.post(
        "/logs/summary",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 4,
        "by_severity": {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 1,
            "ERROR": 2,
            "CRITICAL": 0,
        },
    }


def test_summary_can_filter_by_severity():
    content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:00:01 ERROR Database failed\n"
        "2026-10-24 10:00:02 ERROR Request failed\n"
    )

    response = client.post(
        "/logs/summary?severity=ERROR",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 2,
        "by_severity": {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 2,
            "CRITICAL": 0,
        },
    }


def test_summary_rejects_invalid_severity():
    response = client.post(
        "/logs/summary?severity=TRACE",
        files={
            "file": (
                "sample.log",
                "2026-10-24 10:00:00 INFO Server started\n",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Unsupported severity: TRACE",
    }


def test_summary_rejects_invalid_utf8():
    response = client.post(
        "/logs/summary",
        files={
            "file": (
                "invalid.log",
                b"2026-10-24 10:00:00 ERROR Bad byte: \xff\n",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Uploaded file must contain valid UTF-8 text.",
    }


def test_summary_rejects_oversized_file():
    from app.main import MAX_UPLOAD_SIZE_BYTES

    oversized_content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    response = client.post(
        "/logs/summary",
        files={
            "file": (
                "large.log",
                oversized_content,
                "text/plain",
            ),
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Uploaded file exceeds the 5 MiB size limit.",
    }