# Example Dockerfile for local testing and development
# Installs system deps (ffmpeg) and tries to ensure gifski is available.

FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install gifski via apt if available, otherwise use cargo
RUN if apt-cache show gifski >/dev/null 2>&1; then \
      apt-get update && apt-get install -y gifski && rm -rf /var/lib/apt/lists/*; \
    else \
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
      /root/.cargo/bin/cargo install gifski-cli; \
    fi

# Copy project files
WORKDIR /app
COPY . /app

# Install Python requirements
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "-m", "src.main"]
