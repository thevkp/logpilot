from collections import Counter

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from app.services.log_parser import (
    VALID_LEVELS,
    filter_logs,
    parse_log_lines,
)

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024

app = FastAPI(title="LogPilot")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/logs/parse")
def parse_uploaded_logs(
    file: UploadFile = File(...),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[
    str,
    list[dict[str, str | int]] | int | dict[str, int],
]:
    if severity is not None and severity not in VALID_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported severity: {severity}",
        )

    if (
        file.size is not None
        and file.size > MAX_UPLOAD_SIZE_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 5 MiB size limit.",
        )

    logs: list[dict[str, str | int]] = []
    counts = Counter()
    total = 0

    try:
        with file.file as uploaded_file:
            lines = (
                line.decode("utf-8")
                for line in uploaded_file
            )

            for entry in parse_log_lines(lines):
                level = str(entry["level"])

                if severity is not None and level != severity:
                    continue

                counts[level] += 1

                if total >= offset and len(logs) < limit:
                    logs.append(entry)

                total += 1

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must contain valid UTF-8 text.",
        ) from None

    by_severity = {
        level: counts.get(level, 0)
        for level in VALID_LEVELS
    }

    return {
        "logs": logs,
        "total": total,
        "by_severity": by_severity,
    }


@app.post("/logs/summary")
def summarize_uploaded_logs(
    file: UploadFile = File(...),
    severity: str | None = Query(default=None),
) -> dict[str, int | dict[str, int]]:
    if severity is not None and severity not in VALID_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported severity: {severity}",
        )

    if (
        file.size is not None
        and file.size > MAX_UPLOAD_SIZE_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 5 MiB size limit.",
        )

    counts = Counter()
    total = 0

    try:
        with file.file as uploaded_file:
            lines = (
                line.decode("utf-8")
                for line in uploaded_file
            )

            for entry in parse_log_lines(lines):
                level = str(entry["level"])

                if severity is not None and level != severity:
                    continue

                total += 1
                counts[level] += 1

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must contain valid UTF-8 text.",
        ) from None

    by_severity = {
        level: counts.get(level, 0)
        for level in VALID_LEVELS
    }

    return {
        "total": total,
        "by_severity": by_severity,
    }