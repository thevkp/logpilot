# logpilot
## AI-Powered Log Analysis

LogPilot uses the Groq API to analyze parsed application logs and return structured, evidence-based debugging suggestions. Instead of manually scanning log entries, developers can get a summary of observed failures, plausible causes, supporting evidence, and recommended diagnostic steps.

### Features

- **Automated log analysis:** Summarizes patterns and failures in uploaded logs.
- **Evidence-backed findings:** Links observations to original log line numbers.
- **Actionable recommendations:** Suggests practical debugging and investigation steps.
- **Confidence and limitations:** Communicates uncertainty instead of claiming an unverified root cause.
- **Bounded input:** Limits the analysis input to at most 100 entries and 12,000 serialized characters.
- **Validated responses:** Uses Pydantic to validate the structured output returned by the LLM.
- **Configurable provider:** Uses environment variables for Groq credentials, model selection, and timeout configuration.

### Setup

**Requirements:** Python 3.12 and a Groq API key for AI-powered analysis.

Clone the repository and enter the project directory:

```bash
git clone https://github.com/thevkp/logpilot.git
cd logpilot
```

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies and create your local configuration file:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace the placeholder `GROQ_API_KEY` with your own key. The model and timeout have defaults in `.env.example`.

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### Configuration

Configure the following environment variables in `.env`:

| Variable               | Description                                          |
| ---------------------- | ---------------------------------------------------- |
| `GROQ_API_KEY`         | Your Groq API key. Required for AI-powered analysis. |
| `GROQ_MODEL`           | Groq model identifier used for analysis.             |
| `GROQ_TIMEOUT_SECONDS` | Timeout for provider requests, in seconds.           |

Example:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=30
```

**Security:** Never commit your real `.env` file or expose your API key. Use `.env.example` as the configuration template.

### API Usage

**Endpoint:** `POST /logs/analyze`

**Content type:** `multipart/form-data`

| Parameter  | Type            | Required | Description                                |
| ---------- | --------------- | -------- | ------------------------------------------ |
| `file`     | File            | Yes      | Log file to analyze                        |
| `severity` | Query parameter | No       | Filter entries by severity before analysis |

Example request using `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/logs/analyze" \
  -F "file=@application.log"
```

To analyze only error-level entries:

```bash
curl -X POST \
  "http://127.0.0.1:8000/logs/analyze?severity=ERROR" \
  -F "file=@application.log"
```

### Example Response

```json
{
  "summary": "The server encounters a database failure followed by a request failure and a slow-request warning.",
  "likely_causes": [
    "Database connectivity or availability issue causing request failures and performance degradation"
  ],
  "evidence": [
    {
      "line_number": 2,
      "message": "Database failed"
    },
    {
      "line_number": 3,
      "message": "Request failed"
    },
    {
      "line_number": 4,
      "message": "Slow request"
    }
  ],
  "recommended_steps": [
    "Verify database service status and network connectivity",
    "Check database logs for connection errors or timeouts",
    "Review database credentials and connection pool settings",
    "Monitor request latency after investigating the database issue"
  ],
  "confidence": "medium",
  "limitations": [
    "Only four log entries are available, so the root cause cannot be confirmed."
  ]
}
```

*The response above is an illustrative example. Actual results depend on the uploaded logs and the model's analysis.*

### Error Handling

The API uses HTTP status codes to distinguish invalid input from analysis-service failures:

- `400 Bad Request` — uploaded file contains invalid UTF-8 text.
- `413 Request Entity Too Large` — uploaded file exceeds the configured 5 MiB limit.
- `422 Unprocessable Entity` — unsupported severity values or other request-validation errors.
- `502 Bad Gateway` — the LLM provider request fails or its response cannot be used.
- `503 Service Unavailable` — the LLM analysis service is not configured.

Error responses include a `detail` field explaining the failure. Internal provider details should remain in server-side logs rather than being exposed to API clients.

### Testing

Run the complete test suite:

```bash
python -m pytest -q
```
The test suite covers API endpoints, log parsing, request validation, LLM analysis, and request logging.