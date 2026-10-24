from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.analysis import LogAnalysisResponse
from app.services import llm_analyzer
from app.services.llm_analyzer import (
    LLMAnalysisError,
    LLMConfigurationError,
    analyze_log_entries,
    select_log_entries,
)


def make_entry(
    line_number: int,
    message: str = "Request failed",
) -> dict[str, str | int]:
    return {
        "line_number": line_number,
        "timestamp": "2026-10-24T10:00:00",
        "level": "ERROR",
        "message": message,
    }


def valid_json_response(line_number: int = 1) -> str:
    return LogAnalysisResponse(
        summary="The request failed.",
        likely_causes=["A downstream dependency may be unavailable."],
        evidence=[
            LogAnalysisResponse.model_fields["evidence"].annotation.__args__[0](
                line_number=line_number,
                message="Request failed",
            )
        ],
        recommended_steps=["Check dependency health and application logs."],
        confidence="medium",
        limitations=["Only a limited set of log entries was inspected."],
    ).model_dump_json()


def make_mock_client(content: str):
    client = SimpleNamespace()
    client.chat = SimpleNamespace()
    client.chat.completions = SimpleNamespace()
    client.chat.completions.create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content)
                )
            ]
        )
    )
    client.close = AsyncMock()
    return client


def test_select_log_entries_respects_entry_limit():
    entries = [make_entry(number) for number in range(1, 150)]

    selected = select_log_entries(entries)

    assert len(selected) == llm_analyzer.MAX_ANALYSIS_ENTRIES
    assert selected[0]["line_number"] == 1
    assert selected[-1]["line_number"] == 100


def test_select_log_entries_respects_character_limit():
    entries = [
        make_entry(number, "x" * 1000)
        for number in range(1, 50)
    ]

    selected = select_log_entries(entries)

    assert len(selected) < len(entries)
    assert sum(
        len(__import__("json").dumps(entry, ensure_ascii=False))
        for entry in selected
    ) <= llm_analyzer.MAX_ANALYSIS_CHARS


@pytest.mark.asyncio
async def test_analyze_log_entries_validates_mocked_response(monkeypatch):
    client = make_mock_client(valid_json_response())
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    monkeypatch.setattr(llm_analyzer, "get_groq_client", lambda: client)

    result = await analyze_log_entries([make_entry(1)])

    assert result.summary == "The request failed."
    assert result.confidence == "medium"
    assert result.evidence[0].line_number == 1
    client.chat.completions.create.assert_awaited_once()
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_log_entries_rejects_evidence_for_unknown_line(
    monkeypatch,
):
    client = make_mock_client(valid_json_response(line_number=999))
    monkeypatch.setattr(llm_analyzer, "get_groq_client", lambda: client)

    with pytest.raises(LLMAnalysisError, match="line"):
        await analyze_log_entries([make_entry(1)])

    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_log_entries_rejects_invalid_json(monkeypatch):
    client = make_mock_client("not json")
    monkeypatch.setattr(llm_analyzer, "get_groq_client", lambda: client)

    with pytest.raises(LLMAnalysisError, match="schema"):
        await analyze_log_entries([make_entry(1)])


@pytest.mark.asyncio
async def test_analyze_log_entries_handles_provider_failure(monkeypatch):
    client = make_mock_client("{}")
    client.chat.completions.create.side_effect = RuntimeError("provider down")
    monkeypatch.setattr(llm_analyzer, "get_groq_client", lambda: client)

    with pytest.raises(LLMAnalysisError, match="failed"):
        await analyze_log_entries([make_entry(1)])

    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_api_key_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError):
        llm_analyzer.get_groq_client()


@pytest.mark.asyncio
async def test_empty_entries_do_not_call_provider(monkeypatch):
    def unexpected_client():
        pytest.fail("The provider should not be called for empty input.")

    monkeypatch.setattr(llm_analyzer, "get_groq_client", unexpected_client)

    result = await analyze_log_entries([])

    assert result.confidence == "low"
    assert result.evidence == []