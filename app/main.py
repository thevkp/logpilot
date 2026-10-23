from fastapi import FastAPI, File, UploadFile

from app.services.log_parser import parse_log_lines

app = FastAPI(title="LogPilot")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/logs/parse")
def parse_uploaded_logs(
    file: UploadFile = File(...),
) -> dict[str, list[dict[str, str | int]] | int]:
    with file.file as uploaded_file:
        logs = list(
            parse_log_lines(
                line.decode("utf-8")
                for line in uploaded_file
            )
        )

    return {
        "logs": logs,
        "total": len(logs),
    }
