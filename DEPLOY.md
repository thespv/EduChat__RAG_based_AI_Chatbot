# EduChat Deployment Guide

This guide covers deploying EduChat on **Render** (full stack - frontend + backend + PostgreSQL).

---

## Architecture

```
Browser → Render Web Service (Frontend + API) → PostgreSQL
```

---

## Step 1: Push to GitHub

Make sure your code is pushed to GitHub.

```bash
git add .
git commit -m "Update code"
git push origin main
```

---

## Step 2: Create PostgreSQL Database

1. Go to [render.com](https://render.com) and sign up
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `educhat-db`
   - **Database**: `educhat`
   - **User**: (leave default)
4. Click **Create Database**
5. Wait for provisioning (~2 minutes)
6. Copy the **Internal Connection String** (format: `postgres://...`)

---

## Step 3: Deploy to Render

### 3.1 Create Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `educhat`
   - **Branch**: `main`
   - **Build Command**: `./build.sh`
   - **Start Command**: `python -m uvicorn api.index:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: `3.12`

### 3.2 Add Environment Variables

Click **Add Environment Variable**:
```
DATABASE_URL = (paste your PostgreSQL connection string)
GEMINI_API_KEY = (your Google Gemini API key)
```

Optional (for fallback):
```
GROQ_API_KEY = (your Groq API key)
OPENAI_API_KEY = (your OpenAI API key)
ANTHROPIC_API_KEY = (your Anthropic API key)
```

### 3.3 Deploy

Click **Create Web Service**
Wait for deployment (~3-5 minutes)

---

## Step 4: Verify Deployment

1. Visit your Render URL (e.g., `https://educhat.onrender.com`)
2. You should see the EduChat login page
3. Log in and test:
   - Send a message
   - Upload a file (max 50MB)

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GROQ_API_KEY` | No | Groq API key (fallback) |
| `OPENAI_API_KEY` | No | OpenAI API key (fallback) |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (fallback) |

---

## API Fallback System

When Gemini API quota is exhausted, the system automatically tries these providers in order:
1. Gemini (with key rotation)
2. Groq
3. OpenRouter
4. OpenAI
5. Anthropic

Set multiple API keys for better reliability.

---

## File Upload Limits

- **Max file size**: 50MB
- **Supported formats**: PDF, DOC, DOCX, PPT, PPTX, TXT, PNG, JPG, MP3, WAV

---

## Troubleshooting

### Service not responding
- Check Render web service status
- Verify environment variables are set
- Render free tier spins down after 15 min inactivity (cold start ~30s)

### Database connection failed
- Verify `DATABASE_URL` is correct
- Check Render logs for PostgreSQL errors

### API errors
- Verify `GEMINI_API_KEY` is set correctly
- Check Render logs for error messages

---

## Cost Summary

| Service | Tier | Monthly Cost |
|---------|------|--------------|
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
python -m uvicorn api.index:app --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
npm run dev
```

---

## Quick Deploy Commands

```bash
# Update and push
git add .
git commit -m "Update code"
git push origin main

# Render auto-deploys on push to main branch
```