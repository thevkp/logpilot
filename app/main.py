from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from app.services.log_parser import (
    VALID_LEVELS,
    filter_logs,
    parse_log_lines,
)

app = FastAPI(title="LogPilot")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/logs/parse")
def parse_uploaded_logs(
    file: UploadFile = File(...),
    severity: str | None = Query(default=None),
) -> dict[str, list[dict[str, str | int]] | int]:
    if severity is not None and severity not in VALID_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported severity: {severity}",
        )

    with file.file as uploaded_file:
        logs = list(
            parse_log_lines(
                line.decode("utf-8")
                for line in uploaded_file
            )
        )

    if severity is not None:
        logs = list(filter_logs(logs, severity))

    return {
        "logs": logs,
        "total": len(logs),
    }