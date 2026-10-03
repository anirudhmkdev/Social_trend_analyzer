from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger


def create_app() -> FastAPI:
    application = FastAPI(
        title="Social Trend Analyzer API",
        version="0.1.0",
        description="NLP-based platform for detecting emerging topics, sentiment, and trends.",
    )

    cors_origins: List[str] = (
        settings.CORS_ORIGINS
        if isinstance(settings.CORS_ORIGINS, list)
        else [str(settings.CORS_ORIGINS)]
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application exception on %s: %s (status=%d)",
            request.url.path,
            exc.message,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )

    application.include_router(api_router)

    return application


app = create_app()
