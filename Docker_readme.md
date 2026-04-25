
### Step 1: Update `docker-compose.yml` for the Network Fix
Because we made `app.py` safe for your local PC (127.0.0.1) but Docker needs (0.0.0.0), add the environment variable to your compose file.

Replace your `docker-compose.yml` with this:

```yaml
services:
  missav-dlp-web:
    build: .
    container_name: missav-dlp-web
    ports:
      - '55000:5000'
    restart: unless-stopped
    environment:
      - FLASK_HOST=0.0.0.0  # Tells app.py to open to Docker network
    volumes:
      - /home/main/downloads:/app/downloads
      - /home/main/logs:/app/logs
```
*(Note: If you are testing Docker locally on your Windows PC right now, change `/home/main/downloads` to something like `C:\Users\user\Downloads\DockerTest` so you can easily find the files on your PC).*

---

### Step 2: Test Locally
Open your terminal in your project folder and run:

```bash
docker compose up --build
```
* Wait for it to say `MissAV Downloader Started`.
* Open your browser and go to: `http://localhost:55000`
* Try downloading a video to make sure it works.
* When done, press `Ctrl + C` in the terminal to stop it.

---

### Step 3: Setup GitHub Secrets for Publishing
Before GitHub can publish the image, it needs your Docker Hub password.

1. Go to [Docker Hub](https://hub.docker.com/) and log in.
2. Go to **Account Settings** -> **Security** -> **New Access Token**.
3. Name it "GitHub Actions", give it "Read & Write" permission, and generate it. **Copy the token.**
4. Go to your **GitHub Repository** page.
5. Go to **Settings** -> **Secrets and variables** -> **Actions**.
6. Click **New repository secret**.
7. Name: `DOCKERHUB_USERNAME` | Value: *your docker hub username*
8. Click **New repository secret**.
9. Name: `DOCKERHUB_TOKEN` | Value: *the token you just copied*
*(Note: You do NOT need to add a secret for GHCR. GitHub automatically provides `GITHUB_TOKEN` for free).*

---

### Step 4: Publish to GitHub
Once the secrets are saved, just commit your new Docker files and push them:

```bash
git add .
git commit -m "Add docker support and fix workflows"
git push origin main
```