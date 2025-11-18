# Int Crucible - AI Agent Documentation

This document provides AI assistants with essential information about Int Crucible's architecture, components, and usage patterns.

## System Overview

Int Crucible is a general multi-agent reasoning system that:
- Builds structured world models from problem descriptions
- Generates diverse solution candidates
- Stress-tests candidates with scenario suites
- Evaluates candidates using constraint-weighted scoring
- Ranks candidates using the intelligence metric: **I = P / R** (Prediction quality / Resource cost)

The system is domain-agnostic and designed for iterative improvement of complex systems and designs.

## Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Int Crucible System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Frontend   │◄─────►│  Backend API │                    │
│  │   (Future)   │      │   (FastAPI)   │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                                │                             │
│                        ┌───────▼────────┐                    │
│                        │  Crucible Core │                    │
│                        │   (Agents)     │                    │
│                        └───────┬────────┘                    │
│                                │                             │
│                        ┌───────▼────────┐                    │
│                        │  Kosmos Layer  │                    │
│                        │ (Infrastructure)│                    │
│                        └───────┬────────┘                    │
│                                │                             │
│                        ┌───────▼────────┐                    │
│                        │   Database     │                    │
│                        │  (PostgreSQL/  │                    │
│                        │    SQLite)      │                    │
│                        └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Layers

1. **Backend API Layer** (`crucible/api/`)
   - FastAPI application
   - HTTP endpoints for system interaction
   - RESTful API interface

2. **Crucible Core** (`crucible/` - to be built)
   - ProblemSpec Agent
   - WorldModeller
   - Designers
   - ScenarioGenerator
   - Evaluators
   - I-Ranker
   - Provenance Tracker
   - Feedback Agent

3. **Kosmos Integration Layer** (`vendor/kosmos/`)
   - Database management
   - LLM provider abstraction
   - Agent framework infrastructure
   - Configuration management
   - Logging and monitoring

4. **Persistence Layer**
   - Shared database (PostgreSQL or SQLite)
   - Stores projects, runs, candidates, scores, provenance

## Key Components

### Backend API (`crucible/api/main.py`)

FastAPI application providing HTTP endpoints:

- `GET /` - Root endpoint (system info)
- `GET /health` - Health check
- `GET /kosmos/agents` - List available Kosmos agents
- `POST /kosmos/test` - Test Kosmos integration

**Usage:**
```bash
# Start server
./start_server.sh
# or
python -m crucible.api.main

# Server runs on http://127.0.0.1:8000
# API docs at http://127.0.0.1:8000/docs
```

### CLI Interface (`crucible/cli/main.py`)

Command-line interface using Typer:

- `crucible version` - Show version information
- `crucible config` - Display current configuration
- `crucible kosmos-agents` - List available Kosmos agents
- `crucible kosmos-test` - Test Kosmos integration

**Usage:**
```bash
source venv/bin/activate
crucible version
crucible kosmos-test
```

### Configuration (`crucible/config.py`)

Pydantic-based configuration management:
- Loads from environment variables and `.env` file
- Validates settings
- Provides typed configuration access

**Key settings:**
- `DATABASE_URL` - Database connection string
- `LOG_LEVEL` - Logging verbosity
- `API_HOST` / `API_PORT` - Server settings
- LLM provider settings (passed through to Kosmos)

### Kosmos Integration

Kosmos provides infrastructure that Int Crucible builds upon:

**What Kosmos provides:**
- Multi-provider LLM support (Anthropic, OpenAI, local models)
- Database abstraction and migrations
- Agent framework base classes
- Configuration management
- Logging infrastructure

**How Int Crucible uses it:**
- Imports Kosmos as a dependency (`vendor/kosmos`)
- Uses Kosmos database for persistence
- Leverages Kosmos agent framework for Crucible agents
- Shares configuration system

**Key imports:**
```python
from kosmos.config import get_config
from kosmos.db import init_from_config, get_session
from kosmos.agents.base import BaseAgent
from kosmos.agents.registry import AgentRegistry
```

## File Structure

```
int-crucible/
├── crucible/              # Int Crucible backend package
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── api/               # FastAPI application
│   │   └── main.py        # API endpoints
│   └── cli/               # CLI interface
│       └── main.py        # CLI commands
├── vendor/kosmos/         # Kosmos (vendored dependency)
│   └── kosmos/            # Kosmos package
├── docs/                  # Documentation
│   ├── architecture.md    # System architecture
│   ├── design.md          # Design decisions
│   ├── requirements.md    # Requirements
│   └── stories/           # User stories
├── pyproject.toml         # Python project config
├── setup_backend.sh       # Setup script
├── start_server.sh        # Server startup script
├── verify_setup.sh        # Verification script
├── AGENTS.md              # This file
└── README.md              # User-facing README
```

## Common Workflows

### 1. Setting Up the System

```bash
# Initial setup
./setup_backend.sh

# Verify installation
./verify_setup.sh

# Start server
./start_server.sh
```

### 2. Testing Integration

```bash
source venv/bin/activate

# Test CLI
crucible version
crucible config

# Test Kosmos integration
crucible kosmos-test

# Test API (server must be running)
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/kosmos/agents
```

### 3. Development Workflow

```bash
# Activate environment
source venv/bin/activate

# Make changes to code
# ...

# Test changes
crucible kosmos-test

# Start server to test API changes
python -m crucible.api.main
```

## Database Schema

The system uses a shared database (SQLite by default, PostgreSQL for production):

**Kosmos tables** (managed by Kosmos):
- Research runs, hypotheses, experiments, results
- Knowledge graph entities
- Agent state

**Int Crucible tables** (to be created in future stories):
- Projects
- ProblemSpecs
- WorldModels
- Runs
- Candidates
- Evaluations
- Provenance logs

**Database initialization:**
```python
from kosmos.db import init_from_config
init_from_config()  # Creates all tables
```

## Agent Framework

### Base Agent Structure

Int Crucible agents will inherit from Kosmos base classes:

```python
from kosmos.agents.base import BaseAgent

class ProblemSpecAgent(BaseAgent):
    """Agent that structures problem descriptions."""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Agent logic here
        pass
```

### Agent Communication

Agents communicate through:
- Message passing (Kosmos framework)
- Shared database state
- Structured data exchange

## Configuration Management

### Environment Variables

Configuration is loaded from:
1. Environment variables
2. `.env` file (if present)
3. Default values (in code)

**Key variables:**
```bash
# Database
DATABASE_URL=sqlite:///crucible.db

# Logging
LOG_LEVEL=INFO

# API
API_HOST=127.0.0.1
API_PORT=8000

# LLM Provider (for Kosmos)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
```

### Accessing Configuration

```python
from crucible.config import get_config

config = get_config()
print(config.database_url)
print(config.log_level)
```

## Extension Points

### Adding New CLI Commands

Edit `crucible/cli/main.py`:

```python
@app.command()
def my_new_command():
    """Description of new command."""
    console.print("New command output")
```

### Adding New API Endpoints

Edit `crucible/api/main.py`:

```python
@app.get("/my-endpoint")
async def my_endpoint() -> Dict[str, Any]:
    """New endpoint."""
    return {"status": "ok"}
```

### Creating New Agents

1. Create agent class in `crucible/agents/` (to be created)
2. Inherit from `BaseAgent` (from Kosmos)
3. Implement `execute()` method
4. Register in agent registry

## Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `typer` - CLI framework
- `rich` - Terminal formatting
- `pydantic` - Data validation
- `pydantic-settings` - Configuration

### Kosmos Dependencies
- Installed from `vendor/kosmos`
- Includes LLM clients, database tools, agent framework
- See `vendor/kosmos/pyproject.toml` for full list

## Testing

### Verification Script
```bash
./verify_setup.sh
```

Tests:
- Python environment
- Package installation
- CLI commands
- Kosmos integration
- FastAPI app structure

### Manual Testing
```bash
# CLI tests
crucible version
crucible kosmos-test

# API tests (server must be running)
curl http://127.0.0.1:8000/health
```

## Common Tasks for AI Assistants

### 1. Understanding the System
- Read this file (AGENTS.md)
- Review `docs/architecture.md` for detailed architecture
- Review `docs/design.md` for design decisions
- Check `docs/stories/` for feature requirements

### 2. Making Changes
- Backend code: `crucible/` directory
- API endpoints: `crucible/api/main.py`
- CLI commands: `crucible/cli/main.py`
- Configuration: `crucible/config.py`

### 3. Testing Changes
- Run `./verify_setup.sh` to verify installation
- Run `crucible kosmos-test` to test integration
- Start server and test API endpoints
- Check linting: `ruff check crucible/`

**IMPORTANT**: Before presenting any work to the user, you MUST verify:
- All code changes compile/run without errors
- Database migrations apply successfully (if applicable): `alembic upgrade head`
- CRUD operations work correctly (if applicable): test create, read, update operations
- Imports resolve correctly: `python -c "from crucible.db import ..."`
- Linter passes: `ruff check crucible/`
- Any new functionality can be exercised via tests or manual verification
- Document verification steps in work logs or commit messages

### 4. Adding Features
- Follow existing patterns in codebase
- Update relevant documentation
- Add tests if applicable
- Update this file if architecture changes
- **VERIFY BEFORE PRESENTING**: All changes must be tested and verified before being shown to the user

## Key Design Principles

1. **Domain-Agnostic**: System works across problem domains
2. **Transparency**: Full provenance tracking for all outputs
3. **Composability**: Agents are modular and replaceable
4. **Resource Awareness**: Explicit tracking of costs/resources
5. **MVP-First**: Simple, end-to-end usable loop prioritized

## Current Status

**Completed (Story 001):**
- ✅ Backend structure created
- ✅ FastAPI application with basic endpoints
- ✅ CLI interface with test commands
- ✅ Kosmos integration verified
- ✅ Configuration management
- ✅ Database connection

**To Be Built (Future Stories):**
- ProblemSpec Agent
- WorldModeller
- Designers
- ScenarioGenerator
- Evaluators
- I-Ranker
- Provenance Tracker
- Frontend UI

## Quick Reference

**Start server:**
```bash
./start_server.sh
```

**Test integration:**
```bash
crucible kosmos-test
```

**View API docs:**
http://127.0.0.1:8000/docs

**Check configuration:**
```bash
crucible config
```

**Verify setup:**
```bash
./verify_setup.sh
```

## Additional Resources

- `README.md` - User-facing documentation
- `VERIFICATION_GUIDE.md` - Step-by-step verification guide
- `docs/architecture.md` - Detailed architecture
- `docs/design.md` - Design decisions
- `docs/requirements.md` - System requirements
- `docs/stories/` - User stories and implementation plans

