from fastapi import FastAPI

app = FastAPI(title="LogPilot")

@app.get("/health", status_code=200)
def health_check() -> dict[str, str]:
    return {"status": "ok"}