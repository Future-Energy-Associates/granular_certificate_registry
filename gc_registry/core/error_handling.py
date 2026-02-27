import datetime
import logging
import traceback
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from gc_registry.logging_config import log_context
from gc_registry.settings import settings

logger = logging.getLogger(__name__)


class ErrorResponse(Exception):
    """Standardised error response format for API errors.

    Attributes:
        timestamp: When the error occurred.
        status_code: HTTP status code.
        message: Human-readable error message.
        error_type: Category of error (validation_error, http_error, server_error).
        details: Additional context about the error.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        request: Request | None = None,
        details: dict[str, Any] | None = None,
        error_type: str = "error",
        exc: Exception | None = None,
        include_stack: bool = False,
    ) -> None:
        """Initialize an ErrorResponse.

        Args:
            status_code: HTTP status code for the error.
            message: Human-readable error message.
            request: Optional FastAPI request object for context extraction.
            details: Optional dictionary of additional error details.
            error_type: Category of error (default: "error").
            exc: Optional original exception for stack trace extraction.
            include_stack: Whether to include stack trace in details.
        """
        self.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.status_code = status_code
        self.message = message
        self.error_type = error_type
        self.details = details or {}

        # Extract request context
        if request:
            self.details.update(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "endpoint": (
                        f"{request.scope['endpoint'].__module__}."
                        f"{request.scope['endpoint'].__name__}"
                        if request.scope.get("endpoint")
                        else None
                    ),
                }
            )

        # Add stack trace only when explicitly requested and we have a real
        # exception object with a traceback.
        if include_stack and exc and exc.__traceback__:
            tb_exc = traceback.TracebackException.from_exception(exc)
            stack_frames = tb_exc.stack

            if stack_frames:
                last = stack_frames[-1]
                self.details["source_location"] = {
                    "file": last.filename,
                    "line": last.lineno,
                    "function": last.name,
                }

            self.details["stack"] = list(tb_exc.format())

    def to_dict(self) -> dict[str, Any]:
        """Convert the error response to a dictionary for JSON serialization.

        Returns:
            Dictionary with status_code, error_type, error_message, and details.
        """
        return {
            "status_code": self.status_code,
            "error_type": self.error_type,
            "error_message": self.message,
            "details": self.details,
        }


def _extract_value(body: Any, path: tuple[Any, ...]) -> Any:
    """Walk the request body using the error location to fetch the offending value.

    Args:
        body: The request body to traverse.
        path: Tuple representing the path to the value (e.g., ('body', 'foo', 0, 'bar')).

    Returns:
        The value at the specified path, or None if not found.

    Example:
        ('body', 'foo', 0, 'bar') → body['foo'][0]['bar']
    """
    try:
        cur = body
        for part in path[1:]:
            if isinstance(cur, dict):
                cur = cur.get(part)
            elif isinstance(cur, list):
                cur = cur[part]
            else:
                return None
        return cur
    except Exception:
        return None


def _truncate_value(value: Any, max_length: int = 100) -> Any:
    """Truncate a value for display if it's too long.

    Args:
        value: The value to potentially truncate.
        max_length: Maximum length before truncation.

    Returns:
        The original value or a truncated string representation.
    """
    if value is None:
        return None
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[: max_length - 3] + "..."
    return value


def format_validation_error(
    exc: RequestValidationError,
    request: Request,
) -> ErrorResponse:
    """Format a Pydantic/FastAPI validation error into a standardized ErrorResponse.

    Args:
        exc: The RequestValidationError from FastAPI/Pydantic.
        request: The FastAPI request object.

    Returns:
        An ErrorResponse with enriched field-level error details.
    """
    body = exc.body
    enriched: list[dict[str, Any]] = []

    for err in exc.errors():
        loc_tuple: tuple[Any, ...] = err["loc"]
        # Ensure ctx is JSON-serializable (no raw Error types)
        ctx = err.get("ctx", {})
        if ctx and isinstance(ctx, dict):
            ctx = {
                k: (str(v) if isinstance(v, BaseException) else v)
                for k, v in ctx.items()
            }

        # Extract and truncate the invalid value for display
        invalid_value = _extract_value(body, loc_tuple)
        display_value = _truncate_value(invalid_value)

        enriched.append(
            {
                "location": " -> ".join(str(x) for x in loc_tuple),
                "field": str(loc_tuple[-1]) if len(loc_tuple) > 0 else None,
                "invalid_value": display_value,
                "message": err["msg"],
                "type": err["type"],
                "ctx": ctx if ctx else {},
            }
        )

    return ErrorResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error",
        request=request,
        details={"errors": enriched},
        error_type="validation_error",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI validation errors.

    Args:
        request: The FastAPI request object.
        exc: The RequestValidationError.

    Returns:
        JSONResponse with structured validation error details.
    """
    error_response = format_validation_error(exc, request)

    # Log with structured context
    with log_context(
        error_type="validation_error",
        path=request.url.path,
        method=request.method,
    ):
        logger.warning(
            "Validation error",
            extra={
                "error_count": len(error_response.details.get("errors", [])),
                "errors": error_response.details.get("errors", []),
            },
        )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions raised by the application.

    Args:
        request: The FastAPI request object.
        exc: The HTTPException.

    Returns:
        JSONResponse with structured error details.
    """
    # Don't include request context in the response details for HTTP errors
    # to maintain backward compatibility with existing API consumers
    error_response = ErrorResponse(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_type="http_error",
    )

    # Log with structured context (request info goes to logs, not response)
    with log_context(
        error_type="http_error",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
    ):
        logger.warning("HTTP error", extra={"detail": str(exc.detail)})

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions.

    Args:
        request: The FastAPI request object.
        exc: The unhandled exception.

    Returns:
        JSONResponse with structured error details (stack trace only in non-PROD).
    """
    # Only expose the stack trace outside PROD
    show_stack = settings.ENVIRONMENT != "PROD"

    error_response = ErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=str(exc) if show_stack else "An internal server error occurred",
        request=request,
        details={"exception_type": type(exc).__name__},
        error_type="server_error",
        exc=exc,
        include_stack=show_stack,
    )

    # Log with structured context
    with log_context(
        error_type="server_error",
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    ):
        logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={"exception_message": str(exc)},
        )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict(),
    )
