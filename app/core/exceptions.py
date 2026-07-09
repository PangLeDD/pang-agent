from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.response import error_payload


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_payload(status_code, message),
    )


def register_exception_handlers(app: FastAPI) -> None:
    # 所有对外异常都收口成固定 JSON，避免 FastAPI 默认结构泄漏到客户端。
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        logger.warning("HTTP error: status={} detail={}", exc.status_code, exc.detail)
        return error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning("Validation error: path={} errors={}", request.url.path, exc.errors())
        return error_response(422, "Validation error")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: path={} error={}", request.url.path, exc)
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error")
