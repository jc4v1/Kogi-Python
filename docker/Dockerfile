# Multi-stage build: build wheels in a builder stage, copy only installed packages
# and application files to a small runtime image.

### Builder stage: fetch source, build wheels
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1

# Install build tools and git in the builder only
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Clone the repo (keeps build reproducible without sending context)
RUN git clone https://github.com/jc4v1/Kogi-Python.git .

# Upgrade pip and build wheels for all requirements
RUN pip install --upgrade pip setuptools wheel \
    && if [ -f requirements.txt ]; then pip wheel --no-cache-dir -r requirements.txt -w /wheels; fi


### Runtime stage: minimal image with only the runtime dependencies
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application and pre-built wheels from builder
COPY --from=builder /src /app
COPY --from=builder /wheels /wheels

# Install from wheels (no build deps needed in final image)
RUN if [ -d /wheels ]; then pip install --no-cache-dir /wheels/*; fi \
    && rm -rf /wheels /root/.cache

EXPOSE 8866

# Start voila (bind to all interfaces inside container)
CMD ["voila", "--no-browser", "--port=8866", "KogiApp.ipynb", "--Voila.ip=0.0.0.0"]
