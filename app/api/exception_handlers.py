"""
Exception Handlers - カスタム例外ハンドラー

アプリケーション固有の例外を適切なHTTPレスポンスに変換します。
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.exceptions import (
    JockeyNotFoundError,
    PickleDeserializeError,
    S3AccessError,
    SSMConfigError,
)

logger = get_logger(__name__)


async def jockey_not_found_handler(
    request: Request, exc: JockeyNotFoundError
) -> JSONResponse:
    """
    JockeyNotFoundError を 404 Not Found レスポンスに変換

    Args:
        request: HTTPリクエスト
        exc: JockeyNotFoundError例外

    Returns:
        404 HTTPレスポンス
    """
    logger.warning(
        "Jockey not found",
        extra={
            "jockey_id": exc.jockey_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "message": f"Jockey with ID '{exc.jockey_id}' not found",
            "jockey_id": exc.jockey_id,
        }
    )


async def s3_access_error_handler(
    request: Request, exc: S3AccessError
) -> JSONResponse:
    """
    S3AccessError を 500 Internal Server Error レスポンスに変換

    Args:
        request: HTTPリクエスト
        exc: S3AccessError例外

    Returns:
        500 HTTPレスポンス
    """
    logger.error(
        "S3 access error",
        extra={
            "bucket": exc.bucket,
            "key": exc.key,
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Failed to access S3 storage. Please try again later.",
        }
    )


async def pickle_deserialize_error_handler(
    request: Request, exc: PickleDeserializeError
) -> JSONResponse:
    """
    PickleDeserializeError を 500 Internal Server Error レスポンスに変換

    Args:
        request: HTTPリクエスト
        exc: PickleDeserializeError例外

    Returns:
        500 HTTPレスポンス
    """
    logger.error(
        "Pickle deserialization error",
        extra={
            "jockey_id": exc.jockey_id,
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Failed to process jockey data. Please try again later.",
        }
    )


async def ssm_config_error_handler(
    request: Request, exc: SSMConfigError
) -> JSONResponse:
    """
    SSMConfigError を 503 Service Unavailable レスポンスに変換

    Args:
        request: HTTPリクエスト
        exc: SSMConfigError例外

    Returns:
        503 HTTPレスポンス
    """
    logger.error(
        "SSM configuration error",
        extra={
            "parameter_name": exc.parameter_name,
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service Unavailable",
            "message": "Service configuration error. Please contact support.",
        }
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    予期しない例外を 500 Internal Server Error レスポンスに変換

    Args:
        request: HTTPリクエスト
        exc: Exception例外

    Returns:
        500 HTTPレスポンス
    """
    logger.error(
        "Unexpected error",
        extra={
            "error_type": type(exc).__name__,
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        }
    )
