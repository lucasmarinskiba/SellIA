# SellIA Backend - Production Dockerfile

# Pinned to bookworm (Debian 12) rather than the floating `python:3.11-slim`
# tag: that tag rolled forward to trixie (Debian 13) at some point, and
# Playwright's `--with-deps` (below) doesn't recognize trixie -- it falls
# back to an ubuntu20.04-x64 package list whose font package names
# (ttf-unifont, ttf-ubuntu-font-family) don't exist in trixie's repos,
# failing the whole build with "Package 'ttf-unifont' has no installation
# candidate". bookworm is Debian's current stable release and one of
# Playwright's officially supported base OSes.
FROM python:3.11-slim-bookworm

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
