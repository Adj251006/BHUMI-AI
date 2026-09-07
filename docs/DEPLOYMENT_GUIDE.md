# 🌐 BHUMI-AI Deployment Guide (Vercel & Cloud Hosting)

This guide explains how to deploy **BHUMI-AI** to **Vercel** and live cloud infrastructure in under 2 minutes so anyone can access it directly via a public URL.

---

## ⚡ Method 1: Deploy Frontend to Vercel (Recommended)

### Step 1: Push Code to GitHub
Ensure your repository is pushed to your GitHub account:
```bash
git push origin main
```

### Step 2: Import into Vercel
1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Connect your GitHub account and select the **BHUMI-AI** repository (`Adj251006/BHUMI-AI`).
3. Vercel will automatically detect the configuration from the included `vercel.json`:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `./` (or select `frontend` if deploying frontend only)
   - **Build Command**: `cd frontend && npm install && npm run build` (or `npm run build` if root is `frontend`)
   - **Output Directory**: `frontend/dist` (or `dist` if root is `frontend`)
4. In **Environment Variables**, optionally set:
   - `VITE_API_URL`: Your backend URL (e.g., `https://bhumi-ai-backend.onrender.com` or leave empty if using local/tunnel).
5. Click **Deploy**.

> 💡 **SPA Routing Included**: The repository contains `frontend/vercel.json` and root `vercel.json` with rewrite rules so that reloading on routes like `/dashboard`, `/projects`, or `/workflow` works seamlessly without 404 errors.

---

## 🚀 Method 2: Deploy Backend (1-Click on Render or Railway)

Since the backend is an asynchronous FastAPI app using PostGIS, it can be deployed on Render, Railway, or Fly.io with the included configuration:

### Option A — Render.com (1-Click Blueprint)
1. Go to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** → **Blueprint**.
3. Select your repository `BHUMI-AI`. Render will detect `render.yaml` and automatically deploy the FastAPI web service with Python 3.12 and all PostGIS dependencies!
4. Copy the assigned URL (e.g., `https://bhumi-ai-backend.onrender.com`) and paste it into your Vercel `VITE_API_URL` environment variable.

### Option B — Railway.app
1. Go to [railway.app/new](https://railway.app/new).
2. Deploy from GitHub Repo → `BHUMI-AI`.
3. Set the Root Directory to `backend` and start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Add the environment variable `DATABASE_URL` with your PostgreSQL/PostGIS connection string.

---

## 🐳 Method 3: Run with Docker Compose on Any Server (AWS / DigitalOcean / GCP)

If you have a Linux VM (EC2, Droplet, or Compute Engine):
```bash
git clone https://github.com/Adj251006/BHUMI-AI.git
cd BHUMI-AI
docker compose up -d
```
The application will be live at `http://your-server-ip:5173`.
