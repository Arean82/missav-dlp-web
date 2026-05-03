FROM python:3.10-slim

# 1. Install system dependencies
# gcc and libcurl are required for curl_cffi
# ffmpeg is required for video merging
RUN apt-get update && \
    apt-get install -y ffmpeg curl bash gcc libcurl4-openssl-dev python3-tk && \
    rm -rf /var/lib/apt/lists/*

# 2. Install SpoofDPI (Linux version)
RUN curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash -s linux-amd64
ENV PATH="/root/.spoofdpi/bin:${PATH}"

WORKDIR /app

# 3. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Create necessary directories for persistence
RUN mkdir -p /app/downloads /app/logs

# 6. Set Environment Variables
ENV FLASK_HOST=0.0.0.0
ENV PORT=5000

# 7. Expose port
EXPOSE 5000

# 8. Start via main.py (handles Docker detection and SpoofDPI auto-start)
CMD ["python", "main.py"]