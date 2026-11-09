# ---------- Stage 1: base (shared by test and final) ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .

# ---------- Stage 2: test (Jenkins builds this with --target test) ----------
# If any test fails, "docker build" fails, so the pipeline stops.
FROM base AS test
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY tests/ ./tests/
RUN python -m pytest -v tests

# ---------- Stage 3: final (small production image) ----------
FROM base AS final
ARG BUILD_NUMBER=local
ENV APP_VERSION=${BUILD_NUMBER}
RUN useradd --create-home appuser
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
