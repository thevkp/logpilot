
from collections.abc import Iterator
from typing import BinaryIO

from fastapi import HTTPException, UploadFile

from app.services.log_parser import VALID_LEVELS

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


def validate_severity(severity: str | None) -> None:
    if severity is not None and severity not in VALID_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported severity: {severity}",
        )


def validate_upload_size(file: UploadFile) -> None:
    size = file.size

    # Fall back to measuring the underlying file if size is unknown.
    if size is None:
        current_position = file.file.tell()
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(current_position)

    if size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 5 MiB size limit.",
        )

def decode_uploaded_lines(
    uploaded_file: BinaryIO,
) -> Iterator[str]:
    try:
        for line in uploaded_file:
            yield line.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must contain valid UTF-8 text.",
        ) from None