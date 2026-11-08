# AgentX architecture

## Functional areas

1. **Voice Assistant** — the VAZ browser assistant in `agentx-frontend/src/pages/Dashboard.jsx` and the protected Gemini Live Agent service in `modules/gemini_live_agent/`.
2. **Gmail and Google Calendar Automation** — the protected OAuth/classification/calendar workflow in `backend/main.py`, its FastAPI adapter in `backend/api.py`, and `agentx-frontend/src/pages/EmailIntelligence.jsx`.
3. **Knowledge Hub** — document ingestion, extraction/OCR hooks, chunk indexing, semantic source search and durable storage in `backend/institutional_platform.py`.
4. **Institutional AI Study Buddy** — the unified faculty, student and admin UI in `agentx-frontend/src/pages/InstitutionalPlatform.jsx`, with canonical answers, approvals, submissions and evaluation exposed by `/institutional/*`.

## Protected files

The following are intentionally retained and must not be rewritten or removed:

- `backend/main.py`
- `backend/api.py` Gmail helpers and `/scan-emails` route
- `agentx-frontend/src/pages/Dashboard.jsx`
- `agentx-frontend/src/pages/EmailIntelligence.jsx`
- `agentx-frontend/src/services/api.js`
- `modules/gemini_live_agent/`
- `backend/meeting_summarizer.py` and `backend/knowledge_hub.py` (imported by the preserved Gmail/meeting workflow)
- `requirements.txt` Google, FastAPI, multipart and AI dependencies
- `agentx-frontend/vite.config.js` `/api` proxy

## New structure

```text
backend/
  institutional_platform.py
  institutional_data/       # runtime documents and state, ignored by git
agentx-frontend/src/
  pages/InstitutionalPlatform.jsx
  pages/Dashboard.jsx        # protected voice assistant
  pages/EmailIntelligence.jsx # protected Gmail/Calendar UI
modules/gemini_live_agent/  # protected standalone voice service
```

The former organization-knowledge implementation and unrelated legacy frontend pages were removed. The preserved backend modules remain available to avoid changing their imports or runtime behavior.
