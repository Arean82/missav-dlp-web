# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 4.0.x   | :white_check_mark: |
| 3.x.x   | :x:                |
| < 3.0   | :x:                |

## Security Overview

The MissAV Downloader is designed with a focus on user privacy and local-first data management.

### 🛡️ Data Privacy
- **Local Storage**: All download history and settings are stored locally in an `tasks.db` (SQLite) and `.settings.json` file. No data is sent to external servers other than the video sources themselves.
- **No Analytics**: This application does not contain any tracking, telemetry, or analytics scripts.

### 🌐 Network Security
- **Bypass Proxies**: The application uses **SpoofDPI** to bypass SNI-based ISP blocking.
- **Modular Control**: Users can toggle the proxy specifically for Metadata fetching and Crawling via the "Global Proxy Bypass" setting.
- **SSL/TLS**: All connections to MissAV and metadata sites are encrypted via HTTPS.
- **Impersonation**: The app uses `curl_cffi` to impersonate a legitimate browser (Chrome) to prevent Cloudflare blocks.

### ⚠️ Recommendations
- **VPN Usage**: It is highly recommended to run this application behind a VPN (e.g., Gluetun in Docker) to hide your IP address from video providers.
- **Internal Access**: Do not expose the web interface (Port 5000/55000) directly to the public internet without a reverse proxy (like Nginx) and password protection (Basic Auth).

## Reporting a Vulnerability

If you discover a security vulnerability, please open an issue on the GitHub repository or contact the maintainers directly. We aim to respond to all security reports within 48 hours.
