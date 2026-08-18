FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

# Create an unprivileged user
RUN useradd --create-home --shell /bin/bash appuser

# Copy application files and give ownership to appuser
COPY --chown=appuser:appuser . .

# Run everything after this point as appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]