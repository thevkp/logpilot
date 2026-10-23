import pytest

from app.services.log_parser import (
    filter_logs,
    parse_log_file,
    parse_log_line,
    parse_logs,
)


def test_parse_valid_error_line():
    result = parse_log_line(
        "2026-10-22 10:15:03 ERROR Database connection failed",
        2,
    )

    assert result == {
        "timestamp": "2026-10-22 10:15:03",
        "level": "ERROR",
        "message": "Database connection failed",
        "line_number": 2,
    }


def test_parse_valid_info_line():
    result = parse_log_line(
        "2026-10-22 10:15:01 INFO Server started",
        1,
    )

    assert result is not None
    assert result["level"] == "INFO"
    assert result["message"] == "Server started"


def test_malformed_line_returns_none():
    result = parse_log_line(
        "This line does not follow the expected format",
        5,
    )

    assert result is None


def test_parse_multiple_lines_skips_malformed_lines():
    lines = [
        "2026-10-22 10:15:01 INFO Server started",
        "malformed line",
        "2026-10-22 10:15:03 ERROR Database connection failed",
    ]

    result = parse_logs(lines)

    assert len(result) == 2

    assert result[0]["level"] == "INFO"
    assert result[0]["line_number"] == 1

    assert result[1]["level"] == "ERROR"
    assert result[1]["line_number"] == 3



def test_parse_log_file_skips_malformed_lines(tmp_path):
    log_file = tmp_path / "application.log"

    log_file.write_text(
        "2026-10-22 10:15:01 INFO Server started\n"
        "malformed line\n"
        "2026-10-22 10:15:03 ERROR Database connection failed\n",
        encoding="utf-8",
    )

    result = list(parse_log_file(log_file))

    assert len(result) == 2
    assert result[0]["level"] == "INFO"
    assert result[0]["line_number"] == 1
    assert result[1]["level"] == "ERROR"
    assert result[1]["line_number"] == 3


def test_filter_logs_returns_only_exact_severity_matches():
    entries = [
        {"timestamp": "2026-10-22 10:15:01", "level": "INFO",
         "message": "Server started", "line_number": 1},
        {"timestamp": "2026-10-22 10:15:02", "level": "ERROR",
         "message": "Query failed", "line_number": 2},
        {"timestamp": "2026-10-22 10:15:03", "level": "CRITICAL",
         "message": "Database unavailable", "line_number": 3},
        {"timestamp": "2026-10-22 10:15:04", "level": "ERROR",
         "message": "Request failed", "line_number": 4},
    ]

    result = list(filter_logs(entries, "ERROR"))

    assert len(result) == 2
    assert all(entry["level"] == "ERROR" for entry in result)
    assert result[0]["message"] == "Query failed"
    assert result[1]["message"] == "Request failed"


def test_filter_logs_rejects_unknown_severity():
    with pytest.raises(ValueError):
        list(filter_logs([], "TRACE"))
