
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