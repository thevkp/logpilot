
import re

LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(DEBUG|INFO|WARNING|ERROR|CRITICAL) "
    r"(.+)$"
)


def parse_log_line(
    line: str,
    line_number: int,
) -> dict[str, str | int] | None:
    line = line.strip()
    match = LOG_PATTERN.match(line)

    if match is None:
        return None

    timestamp, level, message = match.groups()

    return {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "line_number": line_number,
    }
