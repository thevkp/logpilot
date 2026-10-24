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

### Configuration

Set the following variables in your local `.env` file:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=30
```

Install the project's dependencies and start the FastAPI application using the existing development instructions in this repository.

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

The endpoint returns appropriate HTTP errors for common failure scenarios:

- `400 Bad Request` — invalid request parameters or uploaded content, where applicable.
- `413 Request Entity Too Large` — upload exceeds the configured size limit.
- `503 Service Unavailable` — the LLM provider is not configured.
- `502 Bad Gateway` — the provider request fails or its response cannot be used.

### Testing

Run the complete test suite:

```bash
python -m pytest -q
```

The feature was verified with **51 passing tests** after merging into `main`.
