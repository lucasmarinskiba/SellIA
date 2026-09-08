FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright's Chromium binary + its OS-level dependencies (fonts, libgbm,
# libnss3, etc.) -- the playwright pip package above is only the driver/API;
# app/domains/computer_use/browser_service.py's real browser-automation
# engine needs an actual browser installed to launch headless sessions.
# Installed to a shared path (not the installing (root) user's home) so
# it's still findable by appuser at runtime after USER switches below --
# PLAYWRIGHT_BROWSERS_PATH is an ENV, so it persists into the running
# container regardless of which user's $HOME it was set relative to.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium

COPY . .

# Don't run the app as root: if the process is ever compromised (a
# vulnerable dependency, a code-execution bug in a request handler), a
# root-owned container process gives an attacker root inside the
# container — an unnecessary extra privilege this app never needs.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /ms-playwright
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
