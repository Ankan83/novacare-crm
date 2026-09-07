# NovaCare CRM

NovaCare CRM is an AI-first healthcare relationship management workspace for
recording healthcare-professional (HCP) interactions, organizing follow-ups,
and turning conversation notes into structured CRM data.

## Highlights

- Conversational interaction capture with Nova AI
- Structured HCP and interaction records
- Natural-language date handling, including relative dates
- Follow-Up Copilot with due dates and next actions
- Interaction timeline, analytics, meeting preparation, and compliance checks
- Duplicate HCP detection
- Follow-up email drafts and optional SMTP delivery
- Calendar event export as `.ics`
- Voice input in supported browsers
- Offline message persistence with automatic retry after reconnecting

## Technology

- React and Vite frontend
- FastAPI backend
- LangGraph and LangChain
- Groq-hosted language model
- MySQL with SQLAlchemy

## Requirements

- Python 3.11+
- Node.js 18+
- MySQL 8+ or Docker Desktop
- A Groq API key

## Local setup

### 1. Configure the backend

```powershell
cd backend
Copy-Item .env.example .env
```

Open `backend/.env` and set `GROQ_API_KEY`. The default model is
`openai/gpt-oss-120b`.

### 2. Start MySQL

With Docker Desktop:

```powershell
docker compose up -d mysql
```

Alternatively, use an existing MySQL instance and update the database values
in `backend/.env`.

### 3. Install and start the API

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API and interactive documentation are available at:

- http://localhost:8000
- http://localhost:8000/docs

### 4. Install and start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL shown by Vite, usually http://localhost:5173.

## Optional email integration

NovaCare CRM can generate email drafts and open them in the local mail
application without any SMTP setup. For server-side delivery, add these
variables to `backend/.env`:

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-user
SMTP_PASSWORD=your-password
SMTP_FROM=crm@example.com
SMTP_USE_TLS=true
```

## Security

Never commit `backend/.env`, API keys, SMTP credentials, virtual environments,
dependency folders, or build output. The repository `.gitignore` excludes
these files by default. Use `backend/.env.example` as the safe configuration
template.

## Validation

```powershell
cd frontend
npm run build
```

For backend syntax validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
```

## Production deployment

The frontend can be deployed on Vercel with `frontend/` as the project root.
Set `VITE_API_URL` to the deployed API URL followed by `/api`.

The FastAPI service is configured for Railway in `backend/railway.toml`.
Railway is recommended here because it supports Python services and managed
MySQL in the same deployment platform. Configure the backend variables from
`backend/.env.example`, then set the frontend's `VITE_API_URL` to the Railway
service URL.
