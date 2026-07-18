from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from research_os.config import get_settings
from research_os.db import init_db
from research_os.domain.errors import ConflictError, ExternalServiceError, NotFoundError, ValidationError

from .router import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if get_settings().environment == "development":
        init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Research OS API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router)

    @app.get("/health", tags=["operations"])
    def health():
        return {"status": "ok"}

    @app.exception_handler(NotFoundError)
    async def not_found(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": str(exc)}})

    @app.exception_handler(ConflictError)
    async def conflict(_request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"error": {"code": "conflict", "message": str(exc)}})

    @app.exception_handler(ValidationError)
    async def invalid(_request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422, content={"error": {"code": "domain_validation", "message": str(exc)}}
        )

    @app.exception_handler(ExternalServiceError)
    async def upstream_failure(_request: Request, exc: ExternalServiceError):
        return JSONResponse(
            status_code=502, content={"error": {"code": "upstream_failure", "message": str(exc)}}
        )

    return app


app = create_app()
