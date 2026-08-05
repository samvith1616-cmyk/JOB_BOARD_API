# Job Board API

A production-pattern REST API for a job board platform built with FastAPI and PostgreSQL. Implements multi-role authentication, full CRUD operations, real-time search, caching, file uploads, and async background tasks.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (access + refresh tokens) |
| Cache / Broker | Redis 7 |
| Task Queue | Celery |
| File Storage | MinIO (S3-compatible) |
| Containerization | Docker + Docker Compose |

## Features

- **JWT Authentication** — access tokens (15 min) + refresh tokens (7 days) with rotation and Redis-based blacklisting on logout
- **Role-Based Access Control (RBAC)** — three roles: `job_seeker`, `employer`, `admin` with endpoint-level enforcement
- **Full CRUD** — users, companies, jobs, applications with ownership-based authorization
- **PostgreSQL Full-Text Search** — `tsvector` + GIN index + database trigger for auto-updating search vectors, relevance ranking via `ts_rank`
- **Redis Caching** — cache-aside pattern with TTL and automatic invalidation on data mutations
- **PDF Resume Upload** — MinIO object storage with file type/size validation
- **Async Email** — Celery task queue sends application confirmation emails without blocking API responses
- **Pagination** — offset/limit pagination with metadata (`total`, `total_pages`, `has_next`, `has_previous`)
- **Duplicate Prevention** — PostgreSQL `UniqueConstraint` on `(user_id, job_id)` prevents duplicate applications

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git

### 1. Clone the repository

```bash
git clone https://github.com/samvith1616-cmyk/JOB_BOARD_API.git
cd JOB_BOARD_API
```

### 2. Create your `.env` file

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

This starts all services:

- **FastAPI** at `http://localhost:8000`
- **PostgreSQL** at `localhost:5432`
- **Redis** at `localhost:6379`
- **MinIO** at `http://localhost:9000` (API) / `http://localhost:9001` (Console)
- **Celery worker** (background)

Migrations run automatically on startup.

### 4. Access the API

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **MinIO Console:** `http://localhost:9001` (`minioadmin` / `minioadmin`)

## API Endpoints

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/login` | No | Login, returns access + refresh tokens |
| POST | `/logout` | Yes | Logout, blacklists refresh token |
| POST | `/refresh` | No | Get new access token using refresh token |

### Users

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/users` | No | Register new user |
| GET | `/users/{id}` | Yes | Get user by ID |

### Companies

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/company` | Yes | Employer | Create company |
| GET | `/companies` | No | Any | List all companies |
| GET | `/company/{id}` | No | Any | Get company by ID |
| PATCH | `/company/{id}` | Yes | Employer (owner) | Update company |
| DELETE | `/company/{id}` | Yes | Employer (owner) | Delete company |

### Jobs

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/job` | Yes | Employer | Create job posting |
| GET | `/job` | No | Any | List all jobs (paginated) |
| GET | `/job/{id}` | No | Any | Get job by ID |
| GET | `/jobs/search` | No | Any | Full-text search (paginated) |
| PATCH | `/job/{id}` | Yes | Employer (owner) | Update job |
| DELETE | `/job/{id}` | Yes | Employer (owner) | Delete job |

### Applications

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/application` | Yes | Job Seeker | Apply for a job |
| GET | `/application/me` | Yes | Job Seeker | My applications |
| GET | `/application/me/{id}` | Yes | Job Seeker | Get specific application |
| GET | `/job/{id}/applications` | Yes | Employer (owner) | Applications for a job |
| DELETE | `/application/{id}` | Yes | Job Seeker (owner) | Delete application |
| PATCH | `/application/{id}` | Yes | Employer (owner) | Update application status |

### Uploads

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/upload/resume` | Yes | Job Seeker | Upload PDF resume |
| GET | `/download/resume/{filename}` | Yes | Any | Download resume |

## Key Design Decisions

**Why PostgreSQL over MySQL:** Native UUID support, built-in full-text search, robust enum types — all used directly in this project.

**Why feature-based folder structure:** Each domain (users, companies, jobs, applications) is self-contained. Scales better than type-based grouping as the project grows.

**Why separate access and refresh tokens:** Access tokens are short-lived (15 min), limiting damage if stolen. Refresh tokens are long-lived (7 days) with Redis blacklisting, making them revocable on logout.

**Why Redis for caching:** Sub-millisecond reads compared to PostgreSQL. Redis is already used for token blacklisting, so no additional infrastructure is required.

**Why PostgreSQL FTS over Elasticsearch:** No additional infrastructure, always synchronized with application data, and more than sufficient for a job board of this scale.

**Why Celery over FastAPI BackgroundTasks:** Tasks survive server crashes, support retries for transient failures, and workers can be scaled independently.

**Why MinIO:** S3-compatible object storage. Migrating to AWS S3 only requires changing configuration, making local development free and production migration seamless.

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT signing key (keep secret) | 64-character random string |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRY_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRY_DAYS` | Refresh token lifetime | `7` |
| `REDIS_HOST` | Redis hostname | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `CELERY_BROKER_URL` | Celery task broker | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/2` |
| `MAIL_USERNAME` | SMTP username | Mailtrap username |
| `MAIL_PASSWORD` | SMTP password | Mailtrap password |
| `MAIL_FROM` | Sender email address | `noreply@jobboard.com` |
| `MAIL_PORT` | SMTP port | `2525` |
| `MAIL_SERVER` | SMTP server | `sandbox.smtp.mailtrap.io` |
| `MINIO_ENDPOINT` | MinIO endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `MINIO_BUCKET_NAME` | Bucket name | `resumes` |

## License

MIT