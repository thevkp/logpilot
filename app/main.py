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

    try:
        with file.file as uploaded_file:
            logs = list(
                parse_log_lines(
                    line.decode("utf-8")
                    for line in uploaded_file
                )
            )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must contain valid UTF-8 text.",
        ) from None

    if severity is not None:
        logs = list(filter_logs(logs, severity))

    severity_counts = Counter(
        str(entry["level"]) for entry in logs
    )

    by_severity = {
        level: severity_counts.get(level, 0)
        for level in VALID_LEVELS
    }

    return {
        "logs": logs,
        "total": len(logs),
        "by_severity": by_severity,
    }
