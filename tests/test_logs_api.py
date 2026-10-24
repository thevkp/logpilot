
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


def test_parse_logs_supports_pagination():
    content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:00:01 ERROR Database failed\n"
        "2026-10-24 10:00:02 WARNING Slow request\n"
        "2026-10-24 10:00:03 ERROR Request failed\n"
    )

    response = client.post(
        "/logs/parse?limit=2&offset=1",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 4
    assert [entry["level"] for entry in data["logs"]] == [
        "ERROR",
        "WARNING",
    ]
    assert data["by_severity"]["ERROR"] == 2
    assert data["by_severity"]["INFO"] == 1


def test_parse_logs_pagination_returns_empty_page_past_end():
    content = (
        "2026-10-24 10:00:00 INFO Server started\n"
        "2026-10-24 10:00:01 ERROR Database failed\n"
    )

    response = client.post(
        "/logs/parse?limit=2&offset=10",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200
    assert response.json()["logs"] == []
    assert response.json()["total"] == 2


def test_parse_logs_rejects_invalid_pagination_parameters():
    content = "2026-10-24 10:00:00 INFO Server started\n"

    for query in ("limit=0", "limit=1001", "offset=-1"):
        response = client.post(
            f"/logs/parse?{query}",
            files={
                "file": ("sample.log", content, "text/plain"),
            },
        )
        assert response.status_code == 422



def test_parse_logs_searches_messages_case_insensitively():
    content = (
        "2026-10-24 10:00:00 INFO Database connected\n"
        "2026-10-24 10:00:01 ERROR Database connection failed\n"
        "2026-10-24 10:00:02 ERROR Request timed out\n"
        "2026-10-24 10:00:03 WARNING DATABASE is slow\n"
    )

    response = client.post(
        "/logs/parse?search=database",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 3
    assert [entry["level"] for entry in data["logs"]] == [
        "INFO",
        "ERROR",
        "WARNING",
    ]
    assert data["by_severity"]["INFO"] == 1
    assert data["by_severity"]["ERROR"] == 1
    assert data["by_severity"]["WARNING"] == 1


def test_parse_logs_combines_search_severity_and_pagination():
    content = (
        "2026-10-24 10:00:00 ERROR Database unavailable\n"
        "2026-10-24 10:00:01 ERROR Database connection failed\n"
        "2026-10-24 10:00:02 WARNING Database is slow\n"
        "2026-10-24 10:00:03 ERROR Request timed out\n"
    )

    response = client.post(
        "/logs/parse?search=database&severity=ERROR&limit=1&offset=1",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert len(data["logs"]) == 1
    assert data["logs"][0]["message"] == "Database connection failed"
    assert data["by_severity"]["ERROR"] == 2
    assert data["by_severity"]["WARNING"] == 0


def test_parse_logs_search_returns_empty_results_when_no_match():
    content = "2026-10-24 10:00:00 INFO Server started\n"

    response = client.post(
        "/logs/parse?search=database",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 200
    assert response.json()["logs"] == []
    assert response.json()["total"] == 0
    assert all(
        count == 0
        for count in response.json()["by_severity"].values()
    )


def test_parse_logs_rejects_empty_search_parameter():
    content = "2026-10-24 10:00:00 INFO Server started\n"

    response = client.post(
        "/logs/parse?search=",
        files={
            "file": ("sample.log", content, "text/plain"),
        },
    )

    assert response.status_code == 422