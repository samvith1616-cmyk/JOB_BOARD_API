from fastapi import FastAPI
import app.models
from app.users.router import user_router
from app.auth.router import router as auth_router
from app.companies.router import router as company_router
from app.jobs.router import router as job_router
from app.applications.router import router as application_router


app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(job_router)
app.include_router(application_router)

