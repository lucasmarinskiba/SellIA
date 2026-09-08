# SellIA Backend - Production Dockerfile

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright's Chromium binary + its OS-level dependencies (fonts, libgbm,
# libnss3, etc.) -- the playwright pip package above is only the driver/API;
# app/domains/computer_use/browser_service.py's real browser-automation
# engine needs an actual browser installed to launch headless sessions.
# Installed to a shared path (not root's home, since this image runs as
# root throughout -- no USER switch here, unlike backend/Dockerfile) so it
# stays predictable regardless of that.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium

# App code
COPY backend/ .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/ping')"

# Run entrypoint (migrations + FastAPI)
CMD ["./entrypoint.sh"]
