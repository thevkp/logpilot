from app.services.log_parser import parse_log_line


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
