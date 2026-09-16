from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routers import auth as auth_router
from app.routers import geo as geo_router
from app.routers import logistics as logistics_router
from app.routers import incidents as incidents_router
from app.routers import citizen_reports as citizen_reports_router
from app.routers import operations as operations_router
from app.routers import users as users_router
from app.routers import ws as ws_router

app = FastAPI(
    title="Samvahak API",
    description="AI-powered logistics and accessibility intelligence platform for North East India",
    version="0.1.0",
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://samvahak-frontend-epahqdulg-farhxnahmad.vercel.app/","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Secure, uniform error handling (never leak stack traces to the client) ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request data", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    # In production we never return exc's message directly — avoids leaking internals.
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "samvahak-api", "environment": settings.ENVIRONMENT}


app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(geo_router.router)
app.include_router(logistics_router.router)
app.include_router(incidents_router.router)
app.include_router(citizen_reports_router.router)
app.include_router(operations_router.router)
app.include_router(ws_router.router)

# Phase 3 note: no backend work remains outstanding here — the Next.js
# frontend is the next build phase and consumes everything registered above.
