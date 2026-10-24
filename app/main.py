import logging
from time import perf_counter
from collections import Counter

from fastapi import FastAPI, File, Query, UploadFile

from app.schemas.logs import LogParseResponse, LogSummaryResponse
from app.services.api_errors import (
    MAX_UPLOAD_SIZE_BYTES,
    decode_uploaded_lines,
    validate_severity,
    validate_upload_size,
)
from app.services.log_parser import VALID_LEVELS, parse_log_lines

app = FastAPI(title="LogPilot")
access_logger = logging.getLogger("logpilot.access")


@app.middleware("http")
async def log_requests(request, call_next):
    start_time = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - start_time) * 1000

        access_logger.exception(
            "request_failed method=%s path=%s status_code=500 duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - start_time) * 1000

    access_logger.info(
        "request_completed method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response



@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/logs/parse", response_model=LogParseResponse)
def parse_uploaded_logs(
    file: UploadFile = File(...),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1),
) -> LogParseResponse:
    validate_severity(severity)
    validate_upload_size(file)

    search_term = search.strip().casefold() if search else None

    logs: list[dict[str, str | int]] = []
    counts = Counter()
    total = 0

    with file.file as uploaded_file:
        lines = decode_uploaded_lines(uploaded_file)

        for entry in parse_log_lines(lines):
            level = str(entry["level"])
            message = str(entry["message"])

            if severity is not None and level != severity:
                continue

            if (
                search_term is not None
                and search_term not in message.casefold()
            ):
                continue

            counts[level] += 1

            if total >= offset and len(logs) < limit:
                logs.append(entry)

            total += 1

    by_severity = {
        level: counts.get(level, 0)
        for level in sorted(VALID_LEVELS)
    }

    return LogParseResponse(
        logs=logs,
        total=total,
        by_severity=by_severity,
    )


@app.post("/logs/summary", response_model=LogSummaryResponse)
def summarize_uploaded_logs(
    file: UploadFile = File(...),
    severity: str | None = Query(default=None),
) -> LogSummaryResponse:
    validate_severity(severity)
    validate_upload_size(file)

    counts = Counter()
    total = 0

    with file.file as uploaded_file:
        lines = decode_uploaded_lines(uploaded_file)

        for entry in parse_log_lines(lines):
            level = str(entry["level"])

            if severity is not None and level != severity:
                continue

            total += 1
            counts[level] += 1

    by_severity = {
        level: counts.get(level, 0)
        for level in sorted(VALID_LEVELS)
    }

    return LogSummaryResponse(
        total=total,
        by_severity=by_severity,
    )
