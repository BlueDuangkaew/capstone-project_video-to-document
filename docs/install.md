# Installation guide

This project requires a few external binaries for full pipeline functionality:

- ffmpeg — for trimming and frame extraction
- gifski — for high-quality GIF generation

Below are quick install notes for common platforms and an example Dockerfile snippet for building a container that includes gifski.

## Linux (Debian / Ubuntu)

Try installing from the package manager first:

```bash
sudo apt update
sudo apt install -y ffmpeg gifski
```

If your distribution doesn't provide a `gifski` package you can install via Rust's cargo (requires Rust toolchain):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
cargo install gifski-cli
```

## macOS (Homebrew)

```bash
brew install ffmpeg gifski
```

## Windows (Scoop or Chocolatey)

Scoop (recommended):

```powershell
scoop install ffmpeg gifski
```

Chocolatey:

```powershell
choco install ffmpeg
# gifski may need to be installed via prebuilt binaries or cargo
```

## Example Dockerfile (minimal)

Below is a small example Dockerfile (Ubuntu-based) that installs system dependencies and the `gifski` binary when available, falling back to a `cargo install` if necessary.

```dockerfile
FROM python:3.10-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Attempt to install gifski via apt; if not present, install Rust and build gifski via cargo
RUN if apt-cache show gifski >/dev/null 2>&1; then \
        apt-get update && apt-get install -y gifski && rm -rf /var/lib/apt/lists/*; \
    else \
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
        /root/.cargo/bin/cargo install gifski-cli; \
    fi

# Copy app
WORKDIR /app
COPY . /app

# Install Python deps
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "-m", "src.main"]
```

Notes:
- Use a multi-stage build and a smaller final image if you want a production-ready container.
- For production it's recommended to use pre-built gifski packages if your base image provides them to reduce image size.

*** End Patch