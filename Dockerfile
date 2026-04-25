FROM python:3.10-slim

# 1. Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Install required packages (added gcc & libcurl for curl_cffi)
RUN apt-get update && \
    apt-get install -y ffmpeg curl bash gcc libcurl4-openssl-dev && \
    rm -rf /var/lib/apt/lists/*

# 3. Install SpoofDPI
RUN curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash -s linux-amd64

WORKDIR /app

# 4. Fast installation of Python packages
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 5. Copy application
COPY . .

# 6. Create folders and expose port
RUN mkdir -p /app/downloads /app/logs
EXPOSE 5000

# 7. Run Python directly (SpoofDPI is started by app.py automatically)
CMD ["python", "app.py"]