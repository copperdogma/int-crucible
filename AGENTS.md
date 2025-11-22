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

## AI-First Development Philosophy

**Critical**: This project operates on an AI-first development model. Understanding and following this philosophy is essential for all AI assistants working on this codebase.

### Role Division

**Human's Role:**
- Source of requirements and specifications
- Oversight and high-level direction
- Acceptance of completed work

**AI's Role:**
- **Everything else**, including:
  - Implementation of features
  - Code quality and testing
  - Documentation
  - Bug fixes and optimizations
  - **Critical: Self-verification of all work**

### Self-Verification Requirement

**MANDATORY**: The AI must **never** report that work is complete or done unless it has:

1. **Tested the implementation** - Verified that the code runs without errors
2. **Validated against requirements** - Confirmed that the implementation meets the stated requirements
3. **Checked against story acceptance criteria** - Ensured all acceptance criteria in the relevant user story are satisfied
4. **Verified integration** - Tested that new code works correctly with existing systems
5. **Run all relevant checks** - Executed linters, tests, migrations, and other verification steps

**Before presenting any work as complete**, the AI must:
- Execute the code and verify it works as intended
- Run tests (unit, integration, or manual verification as appropriate)
- Check that database migrations apply successfully (if applicable)
- Verify imports resolve correctly
- Ensure linting passes
- Confirm that functionality can be exercised and produces expected results
- Document the verification steps taken

The AI should not return to the human asking them to verify or test work - verification is the AI's responsibility, not the human's. The human's role is oversight, not execution or verification.

### AI-First Tools and Testing Pipeline

**PRIMARY MISSION**: AI agents must actively use the snapshot testing system and other AI-first tools for verification, debugging, and continuous improvement of the system.

**Snapshot Testing System:**
- **Use for regression testing** - Create snapshots before changes, test after changes
- **Use for debugging** - Replay snapshots to reproduce issues and validate fixes
- **Use for validation** - Run snapshot tests to verify system behavior hasn't regressed
- **Use for improvement** - Track metrics over time to identify performance trends

**When to Use Snapshot Testing:**
- Before making significant changes (create baseline snapshots)
- After implementing features (run snapshot tests to verify no regressions)
- When debugging issues (replay relevant snapshots to reproduce problems)
- During refactoring (ensure behavior is preserved)
- For continuous validation (run snapshot tests regularly)

**Commands:**
```bash
# Create snapshot before changes
crucible snapshot create --project-id <id> --name "Baseline" --tags test

# Run tests after changes
crucible snapshot test --all

# Replay specific snapshot for debugging
crucible snapshot replay <snapshot-id>
```

**AI agents should:**
- Automatically create snapshots when appropriate
- Run snapshot tests as part of verification workflows
- Use snapshot replay to debug issues
- Monitor test results and address failures proactively
- Treat snapshot test failures as blocking issues that must be resolved

The snapshot testing system is not optional - it is a core tool for AI agents to verify, debug, and improve the system autonomously.

### Verification Checklist

When completing any task, the AI must verify:
- ✅ Code compiles/runs without errors
- ✅ All imports resolve correctly
- ✅ Linter passes: `ruff check crucible/`
- ✅ Database migrations apply (if applicable): `alembic upgrade head`
- ✅ CRUD operations work (if applicable)
- ✅ New functionality can be exercised via tests or manual verification
- ✅ Implementation matches requirements and story acceptance criteria
- ✅ Integration with existing systems works correctly
- ✅ Snapshot tests pass (if applicable): `crucible snapshot test --all` or relevant snapshots

Only after all verification steps pass should work be presented as complete.

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
- `POST /projects/{project_id}/issues` - Create issue
- `GET /projects/{project_id}/issues` - List issues (with filters)
- `GET /issues/{issue_id}` - Get issue details
- `PATCH /issues/{issue_id}` - Update issue
- `POST /issues/{issue_id}/resolve` - Resolve issue with remediation action
- `POST /issues/{issue_id}/feedback` - Get feedback/remediation proposal

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

### Feedback Agent (`crucible/agents/feedback_agent.py`)

The Feedback Agent helps users understand and resolve issues they've flagged in the system.

**Purpose:**
- Analyzes user-flagged issues (problems with ProblemSpec, WorldModel, constraints, evaluators, scenarios)
- Asks clarifying questions to better understand the issue
- Proposes appropriate remediation actions based on issue severity

**Remediation Actions:**
- **Patch-and-rescore** (minor issues): Updates ProblemSpec/WorldModel, re-runs only evaluation and ranking phases
- **Partial rerun** (important issues): Updates ProblemSpec/WorldModel, re-runs evaluation and ranking phases, potentially creating a new `EVAL_ONLY` run
- **Full rerun** (catastrophic issues): Updates ProblemSpec/WorldModel, creates a new `FULL_SEARCH` or `SEEDED` run
- **Invalidate candidates**: Marks specific candidates as `REJECTED` due to catastrophic issues

**Usage:**
```python
from crucible.services.feedback_service import FeedbackService
from crucible.db.session import get_session

session = next(get_session())
feedback_service = FeedbackService(session)
result = feedback_service.propose_remediation(issue_id)
# Returns: {
#   "feedback_message": "...",
#   "clarifying_questions": [...],
#   "remediation_proposal": {...},
#   "needs_clarification": bool
# }
```

**API Endpoint:**
- `POST /issues/{issue_id}/feedback` - Get feedback and remediation proposal for an issue

**Integration:**
- Automatically triggered when an issue is created via the frontend
- Feedback is displayed in the chat interface
- Users can approve/reject remediation proposals

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

### Snapshot Testing

Int Crucible includes an AI-first snapshot testing system for regression testing of non-deterministic LLM-based systems. See `docs/snapshot-testing.md` for complete documentation.

**Quick Start:**
```bash
# Create a snapshot from a project
crucible snapshot create --project-id <id> --name "Baseline" --tags test

# List snapshots
crucible snapshot list

# Replay a snapshot
crucible snapshot replay <snapshot-id>

# Run snapshot tests
crucible snapshot test --all
```

**API Endpoints:**
- `POST /snapshots` - Create snapshot
- `GET /snapshots` - List snapshots (with filters)
- `GET /snapshots/{id}` - Get snapshot details
- `DELETE /snapshots/{id}` - Delete snapshot
- `POST /snapshots/{id}/replay` - Replay snapshot
- `POST /snapshots/run-tests` - Run snapshot tests

**For AI Agents:**
- Use JSON output format: `--format json` for CLI, or use API endpoints
- Snapshots capture ProblemSpec, WorldModel, and run configuration
- Invariants define expected behaviors (e.g., min_candidates, run_status)
- Test results include pass/fail status and cost tracking
- See `docs/snapshot-testing.md` for detailed usage patterns

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

**Completed:**
- ✅ Backend structure created
- ✅ FastAPI application with basic endpoints
- ✅ CLI interface with test commands
- ✅ Kosmos integration verified
- ✅ Configuration management
- ✅ Database connection
- ✅ Snapshot testing system (Story 018)
  - Snapshot creation, storage, retrieval
  - Snapshot replay with pipeline execution
  - Invariant validation
  - Test harness for automated regression testing

**Completed (Story 009):**
- ✅ Feedback Agent (`crucible/agents/feedback_agent.py`)
  - Issue clarification and remediation proposal
  - Tool-based system state querying
  - Integration with chat interface
- ✅ Issue Management System
  - Issue creation, listing, and resolution
  - API endpoints for issue operations
  - Frontend UI for flagging and viewing issues
- ✅ Remediation Actions
  - Patch-and-rescore for minor issues
  - Partial rerun for important issues
  - Full rerun for catastrophic issues
  - Candidate invalidation

**To Be Built (Future Stories):**
- ProblemSpec Agent
- WorldModeller
- Designers
- ScenarioGenerator
- Evaluators
- I-Ranker
- Provenance Tracker
- Frontend UI (partial - core features implemented)

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

