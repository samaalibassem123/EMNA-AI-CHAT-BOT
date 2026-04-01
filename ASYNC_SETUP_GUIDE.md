# 🚀 Async Agent Setup Guide

## Overview

The EMNA Chat Bot is now fully asynchronous, enabling concurrent database queries, non-blocking I/O, and efficient streaming responses.

## Architecture

### Full Async Stack

```
┌─────────────────┐
│   Streamlit UI  │ (main.py)
│  (Async Runner) │
└────────┬────────┘
         │ asyncio.run_until_complete()
         ▼
┌──────────────────────────────────┐
│     LangGraph State Machine      │ (graph.py)
│                                  │
│ ┌──────────────────────────────┐ │
│ │  Intent Classification       │ │ → Chat or Database?
│ └──────────┬───────────────────┘ │
│            ▼                      │
│ ┌──────────────────────────────┐ │
│ │  Schema Inspector (Async DB) │ │ → AsyncSession
│ └──────────┬───────────────────┘ │
│            ▼                      │
│ ┌──────────────────────────────┐ │
│ │  Query Generator (LLM)       │ │ → Generate SQL
│ └──────────┬───────────────────┘ │
│            ▼                      │
│ ┌──────────────────────────────┐ │
│ │  Validate Query              │ │ → Safety Check
│ └──────────┬─────────┬──────────┘ │
│            │         │            │
│       (Safe)     (Unsafe)         │
│        ▼         ▼                │
│ ┌──────────┐ ┌────────────────┐   │
│ │Execute   │ │Handle Error    │   │
│ │Query     │ └────────┬───────┘   │
│ └──────┬───┘          │           │
│        ├──────────────┤           │
│        ▼              ▼           │
│ ┌──────────────────────────────┐ │
│ │  Generate Response (LLM)     │ │ → Markdown Report
│ └──────────┬───────────────────┘ │
│            ▼                      │
└─────────────────────────────────┘
         │
         │ Stream: steps, tokens, errors
         ▼
┌─────────────────────────────────┐
│  Streamlit Chat Message Display │
└─────────────────────────────────┘
```

### Async Components

**Database** (SQLAlchemy AsyncSession)

- PostgreSQL with asyncpg driver
- Non-blocking queries via `await session.execute()`
- Connection pooling for efficiency

**LLM** (LangChain with async support)

- Uses `.ainvoke()` for non-blocking model calls
- Streams tokens for real-time UX
- Supports Gemini, Ollama, and other providers

**Graph** (LanGraph with memory checkpointing)

- Compiled with `MemorySaver` for session persistence
- `astream_events()` for real-time progress streaming
- Conditional edges with async routing

## Environment Setup

### Requirements

- Python ≥ 3.12
- PostgreSQL database with asyncpg driver
- Ollama or Gemini API key (see `.env`)

### Installation

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# 2. Install dependencies (already listed in pyproject.toml)
# If using uv:
uv pip install -e .

# If using pip:
pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env with your database and API credentials
```

### `.env` Configuration

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/emna_hrassistant_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=emna_hrassistant_db
DB_DRIVER=postgresql

# LLM API Keys
OLLAMA_API_KEY=your_ollama_key
GOOGLE_AI_KEY=your_google_gemini_key
```

## Running the Application

### Method 1: Streamlit (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Streamlit app
streamlit run main.py

# The app will open at http://localhost:8501
```

### Method 2: Development Testing

```bash
# Test async functions directly
python -c "
import asyncio
from core.database.async_db import async_session
from rh_agent.graph import generate_stream

async def test():
    thread_id = 'test-thread'
    user_input = 'Show me all employees'
    async with async_session() as session:
        async for event in generate_stream(user_input, thread_id, session):
            print(event)

asyncio.run(test())
"
```

## Key Async Features

### 1. Non-Blocking Database Operations

```python
# All database queries are async
async with async_session() as session:
    result = await session.execute(text("SELECT * FROM employees"))
    rows = result.fetchall()
```

### 2. Streaming Responses

```python
# Real-time token streaming from LLM
async for event in generate_stream(user_input, thread_id, session):
    # Events include: steps, tokens, errors
    print(event)
```

### 3. Session State Management

- Thread ID tracks conversation history
- LangGraph's MemorySaver for persistence
- Asyncio event loop for Streamlit integration

## Performance Benefits

✅ **Concurrent Requests** - Handle multiple user queries simultaneously  
✅ **Non-Blocking I/O** - Database queries don't block the event loop  
✅ **Responsive UI** - Token streaming for real-time feedback  
✅ **Efficient Resource Usage** - Single event loop manages all async operations  
✅ **Scalability** - Ready for production deployment with async frameworks (FastAPI, etc.)

## Troubleshooting

### Issue: "RuntimeError: no running event loop"

**Solution**: The `asyncio.run_until_complete()` in main.py handles this.

### Issue: Database connection errors

**Check**:

- PostgreSQL is running
- `.env` credentials are correct
- `DATABASE_URL` uses `postgresql+asyncpg://` scheme

### Issue: LLM API key errors

**Check**:

- `OLLAMA_API_KEY` or `GOOGLE_AI_KEY` are set in `.env`
- API service is accessible from your network

## Project Structure

```
EMNA-AI-CHAT-BOT/
├── main.py                     # Streamlit app (async runner)
├── pyproject.toml             # Dependencies
├── .env                        # Configuration
│
├── core/
│   ├── config.py              # Settings
│   └── database/
│       ├── async_db.py        # AsyncSession setup
│       └── models/
│           ├── Base.py        # SQLAlchemy base
│           └── models.py      # DB models
│
├── llms/
│   └── models.py              # LLM configurations
│
└── rh_agent/
    ├── graph.py               # Main agent graph (async)
    └── utils/
        ├── nodes.py           # Agent nodes (all async)
        ├── routes.py          # Conditional routing (async)
        ├── states.py          # State schema
        ├── agent.py           # LLM agent setup
        └── contexts.py        # DB context (async)
```

## Next Steps

### For Production Deployment:

1. **Replace Streamlit with FastAPI** for true async HTTP serving
2. **Add connection pooling** for more concurrent users
3. **Implement rate limiting** and authentication
4. **Set up monitoring** with async logging

### Adding New Async Features:

1. All new database operations should use `await` with `AsyncSession`
2. All new LLM calls should use `.ainvoke()` instead of `.invoke()`
3. Maintain async/await patterns throughout the codebase

## Documentation

- [LangChain Async](https://python.langchain.com/docs/guides/async)
- [LanGraph](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Streamlit Async](https://docs.streamlit.io/library/api-reference/performance)

---

**Last Updated**: April 1, 2026  
**Status**: ✅ Fully Async
