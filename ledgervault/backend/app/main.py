import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .db import Base, engine, SessionLocal
from .routers import (
    auth,
    users,
    profile,
    documents,
    comments,
    expenses,
    reports,
    admin,
    debug,
)

app = FastAPI(title="LedgerVault API", version="1.0.0")


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
    else:
        response = await call_next(request)
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "type": exc.__class__.__name__,
                "traceback": traceback.format_exc(),
            },
        )
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(documents.router)
app.include_router(comments.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(debug.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    if settings.SEED_ON_START:
        from .seed import run_seed

        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()
