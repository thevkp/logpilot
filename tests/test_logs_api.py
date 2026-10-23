
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
