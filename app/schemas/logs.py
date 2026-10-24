
from typing import Literal

from pydantic import BaseModel, Field


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogEntry(BaseModel):
    timestamp: str
    level: LogLevel
    message: str
    line_number: int = Field(ge=1)


class SeverityCounts(BaseModel):
    DEBUG: int = Field(ge=0)
    INFO: int = Field(ge=0)
    WARNING: int = Field(ge=0)
    ERROR: int = Field(ge=0)
    CRITICAL: int = Field(ge=0)


class LogParseResponse(BaseModel):
    logs: list[LogEntry]
    total: int = Field(ge=0)
    by_severity: SeverityCounts


class LogSummaryResponse(BaseModel):
    total: int = Field(ge=0)
    by_severity: SeverityCounts