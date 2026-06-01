# ContractIQ

A production-style REST API for contract management and AI-powered analysis. Built with FastAPI, SQLModel, and Groq (Llama 3.3 70B).

Built as a hands-on Day 1 learning project covering the core RedHold backend stack — the goal was to not just read the docs, but actually build something real with every concept.

---

## What it does

- User registration and login with JWT authentication
- Full contract CRUD — create, list, filter, update, delete
- Ownership enforcement — users can only access their own contracts
- AI-powered contract analysis — returns structured JSON with summary, parties, obligations, risk level, and risk reasons
- Bulk analysis — analyse multiple contracts concurrently using `asyncio.gather()`
- Background jobs — fire-and-forget analysis with a polling endpoint
- Request timing middleware — every response includes `X-Request-ID` and `X-Process-Time-Ms` headers
- Pydantic v2 validators — email format, password strength, cross-field validation

---

## Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Data validation | Pydantic v2 |
| Database ORM | SQLModel + SQLite |
| Authentication | JWT via python-jose |
| Password hashing | passlib + bcrypt |
| AI / LLM | Groq API (Llama 3.3 70B) |
| Testing | pytest + TestClient |

---

## Project structure

```
app/
├── main.py                  # App entry point, middleware, router mounting
├── config.py                # Settings from .env via pydantic-settings
├── database.py              # SQLModel engine and session dependency
├── dependencies.py          # Shared auth dependency (get_current_user)
├── models/
│   ├── contract.py          # Contract table + Pydantic schemas
│   └── user.py              # User table + schemas + validators
├── routers/
│   ├── users.py             # Register + login
│   ├── contracts.py         # CRUD endpoints
│   ├── analysis.py          # AI analysis
│   └── bulk.py              # Concurrent analysis + background jobs
└── services/
    ├── auth.py              # Password hashing + JWT
    └── llm.py               # Groq API integration
tests/
└── test_contracts.py        # pytest with in-memory DB and dependency overrides
```

---

## API endpoints

```
POST   /users/register              Register a new user
POST   /users/login                 Login, returns JWT token

POST   /contracts/                  Create a contract
GET    /contracts/                  List contracts (filter by status, paginate)
GET    /contracts/{id}              Get a single contract
PATCH  /contracts/{id}             Partial update
DELETE /contracts/{id}             Delete

POST   /analysis/{id}              AI analysis of a contract

POST   /bulk/analyse-all           Analyse all contracts concurrently
POST   /bulk/analyse-async/{id}    Start background analysis, returns job ID
GET    /bulk/job/{job_id}          Poll background job status

GET    /health                     Health check
```

---

## Run locally

**1. Clone and enter the project**

```bash
git clone https://github.com/yuvrraaj/contractiq.git
cd contractiq
```

**2. Create a virtual environment and install dependencies**

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn sqlmodel pydantic-settings python-jose passlib "bcrypt==4.0.1" httpx groq python-multipart
```

**3. Set up your .env file**

```bash
cp .env.example .env
# Fill in your GROQ_API_KEY and SECRET_KEY
```

**4. Start the server**

```bash
python -m uvicorn app.main:app --reload
```

**5. Open the interactive docs**

```
http://localhost:8000/docs
```

---

## Environment variables

```env
DATABASE_URL=sqlite:///./contractiq.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=your-groq-api-key-here
```

---

## Running tests

```bash
pytest tests/ -v
```

Tests run against an in-memory SQLite database — nothing touches the real DB.

---

## Key things learned building this

- FastAPI dependency injection and how the `yield` pattern works for DB sessions
- Pydantic v2 — field validators, model validators, serialization modes
- JWT authentication flow end to end — hashing, signing, decoding, ownership checks
- `asyncio.gather()` for concurrent LLM calls vs sequential awaits
- `asyncio.create_task()` for fire-and-forget background jobs
- pytest fixtures and dependency overrides for isolated testing
- Real Windows environment debugging — venv conflicts, bcrypt pinning, multipart deps