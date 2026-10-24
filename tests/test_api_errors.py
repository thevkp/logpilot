
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services.api_errors import (
    MAX_UPLOAD_SIZE_BYTES,
    decode_uploaded_lines,
    validate_severity,
    validate_upload_size,
)


def test_validate_severity_accepts_valid_severity():
    validate_severity("ERROR")


def test_validate_severity_accepts_none():
    validate_severity(None)


def test_validate_severity_rejects_invalid_severity():
    with pytest.raises(HTTPException) as exc_info:
        validate_severity("TRACE")

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Unsupported severity: TRACE"


def test_validate_upload_size_rejects_oversized_file():
    upload = UploadFile(
        file=BytesIO(b"x"),
        size=MAX_UPLOAD_SIZE_BYTES + 1,
        filename="large.log",
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_upload_size(upload)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == (
        "Uploaded file exceeds the 5 MiB size limit."
    )


def test_decode_uploaded_lines_returns_utf8_text():
    lines = list(decode_uploaded_lines(BytesIO(b"INFO started\nERROR failed\n")))

    assert lines == ["INFO started\n", "ERROR failed\n"]


def test_decode_uploaded_lines_rejects_invalid_utf8():
    with pytest.raises(HTTPException) as exc_info:
        list(decode_uploaded_lines(BytesIO(b"valid line\ninvalid \xff\n")))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "Uploaded file must contain valid UTF-8 text."
    )
