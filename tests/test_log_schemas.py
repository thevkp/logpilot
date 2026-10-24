
import pytest
from pydantic import ValidationError

from app.schemas.logs import (
    LogEntry,
    LogParseResponse,
    LogSummaryResponse,
)


def test_log_entry_accepts_valid_data():
    entry = LogEntry(
        timestamp="2026-10-24 10:30:00",
        level="ERROR",
        message="Database connection failed",
        line_number=4,
    )

    assert entry.level == "ERROR"
    assert entry.line_number == 4


def test_log_entry_rejects_unsupported_level():
    with pytest.raises(ValidationError):
        LogEntry(
            timestamp="2026-10-24 10:30:00",
            level="TRACE",
            message="Unexpected level",
            line_number=1,
        )


def test_log_entry_rejects_line_number_zero():
    with pytest.raises(ValidationError):
        LogEntry(
            timestamp="2026-10-24 10:30:00",
            level="INFO",
            message="Application started",
            line_number=0,
        )


def test_log_parse_response_validates_response_structure():
    response = LogParseResponse(
        logs=[
            {
                "timestamp": "2026-10-24 10:30:00",
                "level": "ERROR",
                "message": "Database connection failed",
                "line_number": 4,
            }
        ],
        total=1,
        by_severity={
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 1,
            "CRITICAL": 0,
        },
    )

    assert response.total == 1
    assert response.logs[0].message == "Database connection failed"
    assert response.by_severity.ERROR == 1


def test_log_summary_response_rejects_missing_severity():
    with pytest.raises(ValidationError):
        LogSummaryResponse(
            total=1,
            by_severity={
                "DEBUG": 0,
                "INFO": 1,
                "WARNING": 0,
                "ERROR": 0,
            },
        )
