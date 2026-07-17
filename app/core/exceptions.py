from fastapi import HTTPException, status


class AppError(Exception):
    """Base application exception for predictable business errors."""


class InvalidUploadError(AppError):
    pass


class IngestionError(AppError):
    pass


class LLMConfigurationError(AppError):
    pass


class LLMRateLimitError(AppError):
    pass


class LLMTransientError(AppError):
    pass


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def too_many_requests(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)


def service_unavailable(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=message,
    )
