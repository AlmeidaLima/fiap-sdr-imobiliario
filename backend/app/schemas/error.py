from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str | list[dict[str, Any]]