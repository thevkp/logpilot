from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import LogAnalysisResponse
import app.main as main_module


client = TestClient(app)


def test_analyze_endpoint_returns_structured_result(monkeypatch):
    parsed_entries = [
        {
            "timestamp": "2026-10-24T10:00:00",
            "level": "ERROR",
            "message": "Database connection failed",
            "line_number": 1,
        },
        {
            "timestamp": "2026-10-24T10:01:00",
            "level": "INFO",
            "message": "Retry scheduled",
            "line_number": 2,
        },
    ]

    async def fake_analyze(entries):
        assert len(entries) == 2
        return LogAnalysisResponse(
            summary="A database connection failed before a retry was scheduled.",
            likely_causes=["The database may be unavailable."],
            evidence=[
                {
                    "line_number": 1,
                    "message": "Database connection failed",
                }
            ],
            recommended_steps=["Check database availability."],
            confidence="medium",
            limitations=["Only the uploaded log entries were inspected."],
        )

    monkeypatch.setattr(
        main_module,
        "parse_log_lines",
        lambda lines: iter(parsed_entries),
    )
    monkeypatch.setattr(main_module, "analyze_log_entries", fake_analyze)

    response = client.post(
        "/logs/analyze",
        files={"file": ("sample.log", b"placeholder log content", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"].startswith("A database connection failed")
    assert body["evidence"][0]["line_number"] == 1
    assert body["confidence"] == "medium"


def test_analyze_endpoint_filters_by_severity(monkeypatch):
    parsed_entries = [
        {
            "timestamp": "2026-10-24T10:00:00",
            "level": "ERROR",
            "message": "Database connection failed",
            "line_number": 1,
        },
        {
            "timestamp": "2026-10-24T10:01:00",
            "level": "INFO",
            "message": "Retry scheduled",
            "line_number": 2,
        },
    ]

    async def fake_analyze(entries):
        assert len(entries) == 1
        assert entries[0]["level"] == "ERROR"
        return LogAnalysisResponse(
            summary="An error was found.",
            likely_causes=[],
            evidence=[],
            recommended_steps=["Inspect the error."],
            confidence="low",
            limitations=["Only ERROR entries were selected."],
        )

    monkeypatch.setattr(
        main_module,
        "parse_log_lines",
        lambda lines: iter(parsed_entries),
    )
    monkeypatch.setattr(main_module, "analyze_log_entries", fake_analyze)

    response = client.post(
        "/logs/analyze?severity=ERROR",
        files={"file": ("sample.log", b"placeholder log content", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "An error was found."


def test_analyze_endpoint_returns_503_when_provider_is_unconfigured(
    monkeypatch,
):
    from app.services.llm_analyzer import LLMConfigurationError

    async def fake_analyze(entries):
        raise LLMConfigurationError("missing key")

    monkeypatch.setattr(
        main_module,
        "parse_log_lines",
        lambda lines: iter(
            [
                {
                    "timestamp": "2026-10-24T10:00:00",
                    "level": "ERROR",
                    "message": "Failure",
                    "line_number": 1,
                }
            ]
        ),
    )
    monkeypatch.setattr(main_module, "analyze_log_entries", fake_analyze)

    response = client.post(
        "/logs/analyze",
        files={"file": ("sample.log", b"placeholder", "text/plain")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Log analysis service is not configured."
    )