# Story: Fix SQLAlchemy Metadata Cache Issue for chat_session_id Column

**Status**: Done ✅

**Priority**: Medium (Blocks Story 010 completion) - **RESOLVED**

---

## Problem Summary

After adding the `chat_session_id` column to the `crucible_runs` table via Alembic migration, SQLAlchemy queries fail with `OperationalError: no such column: crucible_runs.chat_session_id`, even though the column exists in the database.

This blocks the Run History feature in Story 010 from working correctly.

## Related Stories

- **Story 010** - Multiple chats and runs per project (blocked by this issue)

## Current State

### What Works ✅
- Database migration applied successfully (`e900a34872ac_add_chat_session_id_to_runs`)
- Column exists in database (verified via `PRAGMA table_info` and `sqlite_master`)
- Column appears in SQLAlchemy model definition (`crucible/db/models.py`)
- Alembic shows migration at head: `e900a34872ac (head)`
- Direct SQL queries work: `SELECT chat_session_id FROM crucible_runs LIMIT 1` succeeds
- SQLAlchemy inspector can see the column: `inspector.get_columns('crucible_runs')` includes `chat_session_id`

### What's Broken ❌
- SQLAlchemy ORM queries fail when accessing `Run` model attributes
- Error: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: crucible_runs.chat_session_id`
- Error occurs even when querying just `Run.id` (SQLAlchemy tries to load all columns including `chat_session_id`)
- Endpoint `/projects/{project_id}/runs/summary` returns 500 error
- CORS headers not added to error responses (secondary issue)

## Error Details

### Error Message
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: crucible_runs.chat_session_id
[SQL: SELECT count(*) AS count_1 
FROM (SELECT crucible_runs.id AS crucible_runs_id, crucible_runs.project_id AS crucible_runs_project_id, 
      crucible_runs.mode AS crucible_runs_mode, crucible_runs.config AS crucible_runs_config, 
      crucible_runs.recommended_message_id AS crucible_runs_recommended_message_id, 
      crucible_runs.recommended_config_snapshot AS crucible_runs_recommended_config_snapshot, 
      crucible_runs.ui_trigger_id AS crucible_runs_ui_trigger_id, 
      crucible_runs.ui_trigger_source AS crucible_runs_ui_trigger_source, 
      crucible_runs.ui_trigger_metadata AS crucible_runs_ui_trigger_metadata, 
      crucible_runs.ui_triggered_at AS crucible_runs_ui_triggered_at, 
      crucible_runs.run_summary_message_id AS crucible_runs_run_summary_message_id, 
      crucible_runs.chat_session_id AS crucible_runs_chat_session_id,  <-- This column
      crucible_runs.status AS crucible_runs_status, 
      crucible_runs.created_at AS crucible_runs_created_at, 
      crucible_runs.started_at AS crucible_runs_started_at, 
      crucible_runs.completed_at AS crucible_runs_completed_at, 
      crucible_runs.duration_seconds AS crucible_runs_duration_seconds, 
      crucible_runs.candidate_count AS crucible_runs_candidate_count, 
      crucible_runs.scenario_count AS crucible_runs_scenario_count, 
      crucible_runs.evaluation_count AS crucible_runs_evaluation_count, 
      crucible_runs.metrics AS crucible_runs_metrics, 
      crucible_runs.llm_usage AS crucible_runs_llm_usage, 
      crucible_runs.error_summary AS crucible_runs_error_summary 
FROM crucible_runs 
WHERE crucible_runs.project_id = ?) AS anon_1]
```

### Database Verification

**Column exists:**
```bash
$ sqlite3 crucible.db "PRAGMA table_info(crucible_runs);" | grep chat_session_id
22|chat_session_id|VARCHAR|0||0

$ sqlite3 crucible.db "SELECT sql FROM sqlite_master WHERE type='table' AND name='crucible_runs';" | grep chat_session_id
chat_session_id VARCHAR
```

**SQLAlchemy inspector sees it:**
```python
from sqlalchemy import create_engine, inspect
from crucible.config import get_config
config = get_config()
engine = create_engine(config.database_url)
inspector = inspect(engine)
cols = [c['name'] for c in inspector.get_columns('crucible_runs')]
# Result: 'chat_session_id' in cols == True
```

## What Has Been Tried

### 1. Raw SQL Queries ✅ (Partial Success)
**Attempt:** Rewrote `/projects/{project_id}/runs/summary` endpoint to use raw SQL instead of ORM.

**Code Location:** `crucible/api/main.py` lines 1454-1541

**Result:** Code written but not executed - server still using old code path. The raw SQL approach should work but needs proper server restart.

**Implementation:**
- Uses `text()` for raw SQL queries
- Builds WHERE clauses with parameterized queries
- Creates `RunProxy` objects to avoid ORM lazy loading
- Excludes `chat_session_id` from SELECT until metadata issue resolved

### 2. Exception Handlers with CORS ✅ (Implemented)
**Attempt:** Added exception handlers to ensure CORS headers are added to error responses.

**Code Location:** `crucible/api/main.py` lines 91-130

**Result:** Handlers added but not being called - FastAPI's default error handler intercepts first.

**Implementation:**
- `@app.exception_handler(SQLAlchemyError)` - handles database errors
- `@app.exception_handler(StarletteHTTPException)` - handles HTTP exceptions
- `@app.exception_handler(RequestValidationError)` - handles validation errors
- `@app.exception_handler(Exception)` - catches all other exceptions
- All handlers add CORS headers to responses

### 3. Server Restarts 🔄 (Multiple Attempts)
**Attempt:** Killed and restarted server processes multiple times.

**Commands Used:**
```bash
pkill -9 -f "crucible.api.main"
pkill -9 -f "uvicorn"
python -m crucible.api.main > /tmp/crucible_api.log 2>&1 &
```

**Result:** Server restarts but error persists. Suggests the issue is not just a process cache problem.

### 4. Metadata Refresh Attempts ❌ (Failed)
**Attempt:** Tried to force SQLAlchemy to refresh metadata.

**Attempted Methods:**
- `Run.__table__.create(checkfirst=True)` - TypeError: missing bind
- `Run.__table__.reflect(bind=engine)` - AttributeError: no reflect method
- `Base.metadata.reflect(bind=engine)` - Didn't resolve issue

**Result:** SQLAlchemy doesn't provide easy way to refresh table metadata for existing models.

### 5. Defensive Attribute Access ✅ (Implemented)
**Attempt:** Modified `_serialize_run` to use `getattr()` for `chat_session_id`.

**Code Location:** `crucible/api/main.py` line 397

**Result:** Helps but doesn't fix root cause - SQLAlchemy still tries to load the column when querying.

## Root Cause Analysis

### Hypothesis 1: SQLAlchemy Metadata Cache
**Theory:** SQLAlchemy's `Base.metadata` is cached at import time and doesn't reflect database schema changes.

**Evidence:**
- Column exists in database
- Column exists in model definition
- Direct SQL works
- ORM queries fail

**Why This Happens:**
- SQLAlchemy builds table metadata when models are imported
- Metadata is shared across all instances (singleton pattern)
- Adding columns via migration doesn't automatically update metadata
- Need to explicitly refresh or recreate metadata

### Hypothesis 2: Connection Pool Cache
**Theory:** Database connection pool has cached schema information.

**Evidence:**
- Multiple server restarts didn't help
- Direct SQL queries work (new connections?)

**Why This Happens:**
- Connection pools may cache schema metadata
- Old connections might have stale schema info
- New connections should see updated schema

### Hypothesis 3: Model Import Order
**Theory:** Models are imported before database is initialized, causing metadata to be built incorrectly.

**Evidence:**
- Models import `Base` from `kosmos.db.models`
- Database initialization happens in `lifespan` context manager
- Models might be imported before `init_from_config()` runs

## Files Involved

### Database Schema
- `crucible/db/models.py` - `Run` model definition (line 262: `chat_session_id = Column(...)`)
- `alembic/versions/e900a34872ac_add_chat_session_id_to_runs.py` - Migration script

### API Endpoints
- `crucible/api/main.py`:
  - Line 1441: `get_project_run_summary` endpoint
  - Line 1454-1541: Raw SQL implementation (not active)
  - Line 394-423: `_serialize_run` function
  - Line 91-130: Exception handlers

### Database Session
- `crucible/db/session.py` - Session management (uses Kosmos session)

## Potential Solutions

### Solution 1: Force Metadata Refresh on Startup ⭐ (Recommended)
**Approach:** Refresh SQLAlchemy metadata after database initialization.

**Implementation:**
```python
# In crucible/api/main.py lifespan() or crucible/db/session.py init_from_config()
from crucible.db.models import Base, Run
from sqlalchemy import inspect

# After database init
engine = get_engine()  # Get from Kosmos
inspector = inspect(engine)
Base.metadata.reflect(bind=engine)
# Or recreate table metadata
Run.__table__.create(bind=engine, checkfirst=True)
```

**Pros:** Fixes root cause, works for all queries
**Cons:** May have performance impact on startup

### Solution 2: Use Raw SQL Queries (Temporary Workaround)
**Approach:** Continue using raw SQL in `get_project_run_summary` endpoint.

**Implementation:** Already implemented in code (lines 1454-1541), just needs server restart.

**Pros:** Works immediately, bypasses ORM
**Cons:** Not a permanent fix, loses ORM benefits

### Solution 3: Drop and Recreate Metadata
**Approach:** Clear SQLAlchemy metadata and rebuild from database.

**Implementation:**
```python
# Clear existing metadata
Base.metadata.clear()
# Rebuild from database
Base.metadata.reflect(bind=engine)
```

**Pros:** Forces fresh metadata
**Cons:** May break if models don't match database exactly

### Solution 4: Use Declarative Base with Auto-reflect
**Approach:** Configure SQLAlchemy to auto-reflect tables from database.

**Implementation:**
```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Use autoload_with in Column definitions
chat_session_id = Column(String, ForeignKey(...), autoload_with=engine)
```

**Pros:** Always in sync with database
**Cons:** Requires significant refactoring

### Solution 5: Separate Database Connection for Schema Queries
**Approach:** Use a separate connection that always reflects current schema.

**Implementation:**
```python
# Create fresh engine for schema queries
fresh_engine = create_engine(database_url, echo=False)
inspector = inspect(fresh_engine)
# Use this for queries that need current schema
```

**Pros:** Guaranteed fresh schema view
**Cons:** Adds complexity, multiple connections

## Acceptance Criteria

- [x] SQLAlchemy ORM queries work correctly with `chat_session_id` column ✅
- [x] `/projects/{project_id}/runs/summary` endpoint returns runs without errors ✅
- [x] Run History panel in frontend loads and displays runs ✅
- [x] CORS headers are present on all responses (including errors) ✅
- [x] No regression in other database queries ✅
- [x] Solution doesn't require manual intervention after server restarts ✅

**Status: COMPLETE** - All acceptance criteria met. Metadata refresh implemented and verified working.

## Testing Plan

1. **Verify Database State:**
   ```bash
   sqlite3 crucible.db "PRAGMA table_info(crucible_runs);" | grep chat_session_id
   alembic current
   ```

2. **Test ORM Query:**
   ```python
   from crucible.db.models import Run
   from crucible.db.session import get_session
   with get_session() as db:
       runs = db.query(Run).limit(1).all()
       print(f"Found {len(runs)} runs")
       if runs:
           print(f"chat_session_id: {runs[0].chat_session_id}")
   ```

3. **Test API Endpoint:**
   ```bash
   curl "http://127.0.0.1:8000/projects/{project_id}/runs/summary?limit=20&offset=0" \
        -H "Origin: http://localhost:3000"
   ```

4. **Test Frontend:**
   - Open Run History panel
   - Verify runs load without errors
   - Check browser console for CORS errors

## Notes

- The raw SQL implementation in `crucible/api/main.py` (lines 1454-1541) is a working workaround but not a permanent fix
- Exception handlers are in place but not being triggered (FastAPI default handler intercepts first)
- The issue appears to be specific to SQLAlchemy's metadata caching, not the database itself
- Multiple server restarts didn't resolve the issue, suggesting it's not just a process-level cache

## Related Issues

- Story 010 completion blocked
- CORS errors in browser console (secondary to 500 errors)
- Run History UI shows "No runs recorded yet" even when runs exist

## Next Steps for Implementer

1. **Start with Solution 1** - Try forcing metadata refresh on startup ✅ **COMPLETED**
2. **If that fails, try Solution 3** - Drop and recreate metadata (not needed)
3. **As temporary workaround, activate Solution 2** - Use the raw SQL code already written ✅ **COMPLETED**
4. **Test thoroughly** - Ensure all database queries still work ✅ **VERIFIED**
5. **Update Story 010** - Mark as complete once this is fixed ✅ **COMPLETED**

## Implementation Summary

**Solution Implemented:** Combination of Solution 1 (metadata refresh) and Solution 2 (raw SQL workaround)

**Key Changes:**
1. **Metadata Refresh** (`crucible/db/session.py` lines 42-93):
   - Detects missing columns by comparing database schema with model metadata
   - Uses SQLAlchemy Table reflection to refresh table metadata from database
   - Updates `Run.__table__` to use reflected version
   - Runs automatically on server startup

2. **Raw SQL Workaround** (`crucible/api/main.py` lines 1463-1575):
   - Uses SQLAlchemy 2.0 named parameters (`:param_name`)
   - Includes `RunProxy` class with datetime and JSON parsing
   - Handles all edge cases for data type conversion

3. **CORS Exception Handlers** (`crucible/api/main.py` lines 100-151):
   - Ensures CORS headers on all error responses
   - Handles all exception types

**Verification:**
- ✅ ORM queries work with `chat_session_id`
- ✅ Endpoint returns runs without errors
- ✅ Run History UI loads correctly
- ✅ No regression in other queries
- ✅ Automatic on server startup

