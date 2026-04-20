# EduChat Deployment Guide

This guide covers deploying EduChat using **Vercel** (frontend) + **Render** (backend + PostgreSQL).

---

## Architecture

```
Browser → Vercel CDN → Render Backend → PostgreSQL
```

---

## Step 1: Push to GitHub

Make sure your code is pushed to GitHub. Both Vercel and Render will connect to the same repo.

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

---

## Step 2: Deploy Backend to Render

### 2.1 Create PostgreSQL Database

1. Go to [render.com](https://render.com) and sign up
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `educhat-db`
   - **Database**: `educhat`
   - **User**: (leave default)
4. Click **"Create Database"**
5. Wait for provisioning (~2 minutes)
6. Copy the **"Internal Connection String"** (format: `postgres://...`)

### 2.2 Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `educhat-api`
   - **Region**: (choose closest to users)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
4. Settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `web: python -m uvicorn api.index:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (click **"Add Environment Variable"**):
   ```
   DATABASE_URL = (paste your PostgreSQL connection string)
   GEMINI_API_KEY = (your Gemini API key)
   GROQ_API_KEY = (your Groq API key)
   ```
6. Click **"Create Web Service"**
7. Wait for deployment (~3-5 minutes)
8. Copy your backend URL (e.g., `https://educhat-api.onrender.com`)

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Update Vercel Configuration

Before deploying, update `vercel.json` with your Render backend URL:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://YOUR-APP-NAME.onrender.com/api/:path*"
    }
  ]
}
```

Replace `YOUR-APP-NAME` with your actual Render web service name.

### 3.2 Deploy

1. Go to [vercel.com](https://vercel.com) and sign up
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repo
4. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: (leave as `.`)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variable:
   ```
   VITE_API_URL = https://YOUR-APP-NAME.onrender.com
   ```
6. Click **"Deploy"**

---

## Step 4: Verify Deployment

1. Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
2. You should see the EduChat login page
3. Log in and test:
   - Send a message
   - Upload a file (max 50MB)

---

## Environment Variables Reference

### Render Backend
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GROQ_API_KEY` | Yes | Groq API key |
| `OPENAI_API_KEY` | No | OpenAI API key (optional) |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (optional) |

### Vercel Frontend
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Your Render backend URL |

---

## File Upload Limits

- **Max file size**: 50MB
- **Supported formats**: PDF, DOC, DOCX, PPT, PPTX, TXT, PNG, JPG, MP3, WAV, MP4

---

## Troubleshooting

### Backend Issues

**CORS errors:**
- Verify CORS is set to allow your Vercel domain
- Check browser console for specific errors

**Database connection failed:**
- Verify `DATABASE_URL` is correct
- Check Render logs for PostgreSQL errors

**API not responding:**
- Check Render web service status
- Verify environment variables are set
- Check "Free" tier sleep: Render spins down after 15 min inactivity

### Frontend Issues

**API calls failing:**
- Verify `VITE_API_URL` is set correctly (include `https://`)
- Check that `vercel.json` rewrites point to correct backend

**Static assets not loading:**
- Rebuild: Vercel Dashboard → Your Project → Redeploy

---

## Cost Summary

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Vercel | Hobby | $0 |
| Render Web Service | Free | $0 |
| Render PostgreSQL | Free | $0 |
| **Total** | | **$0** |

### Free Tier Limitations

- **Render**: Spins down after 15 min inactivity (cold start ~30s)
- **PostgreSQL**: 1GB storage, 250MB RAM

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Start backend
npm run server

# Start frontend (new terminal)
npm run dev
```

---

## Quick Deploy Commands

```bash
# Update and push
git add .
git commit -m "Update code"
git push

# Both platforms auto-deploy on push to main branch
```
