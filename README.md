# Love Concierge Backend

FastAPI backend for the Love Concierge MVP.

## 🚀 Features
- Upload dating convo screenshots
- Get AI-generated message advice (GPT-4)
- Stores history for each user

## 🛠️ Local Development
```bash
uvicorn main:app --reload
```

## 🌐 Deployment
Use Render, Railway, or Fly.io. Set environment variables:
- `OPENAI_API_KEY`
- `DATABASE_URL`
