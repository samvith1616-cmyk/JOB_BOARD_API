from fastapi import FastAPI, Request
import app.models
from app.users.router import user_router
from app.auth.router import router as auth_router
from app.companies.router import router as company_router
from app.jobs.router import router as job_router
from app.applications.router import router as application_router
from app.uploads.router import router as upload_router
from loguru import logger
import time


app = FastAPI(
    title="Job Board API",
    description="A production-pattern job board REST API",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    log_message = (
        f"{request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration:.2f}ms"
    )

    if response.status_code >= 500:
        logger.error(log_message)
    elif response.status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)

    return response

@app.on_event("startup")
async def startup_event():
    logger.info("Job Board API started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.warning("Job Board API shutting down")
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(upload_router)

