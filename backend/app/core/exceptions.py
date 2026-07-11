from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, resource_id):
        self.resource_id = resource_id
        super().__init__(f"Resource {resource_id} not found")


class ConflictError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.detail})
