# Testing Story 003: ProblemSpec Agent and Flow

This guide explains how to test the ProblemSpec agent implementation.

## Prerequisites

### 1. LLM Provider Configuration

The ProblemSpec agent requires an LLM provider to be configured. You need to set up at least one of:

#### Option A: Anthropic (Claude) - Recommended
```bash
# Create or edit .env file in project root
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
echo "LLM_PROVIDER=anthropic" >> .env
# Optional: customize model
echo "CLAUDE_MODEL=claude-3-5-sonnet-20241022" >> .env
```

Get your API key from: https://console.anthropic.com/

#### Option B: OpenAI
```bash
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
echo "OPENAI_MODEL=gpt-4-turbo" >> .env
```

Get your API key from: https://platform.openai.com/api-keys

#### Option C: Local Ollama (Free, No API Key Needed)
```bash
# 1. Install Ollama: https://ollama.com/download
# 2. Start Ollama: ollama serve
# 3. Pull a model: ollama pull llama3.1:70b

# Then configure:
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=ollama" >> .env
echo "OPENAI_BASE_URL=http://localhost:11434/v1" >> .env
echo "OPENAI_MODEL=llama3.1:70b" >> .env
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Ensure Database is Initialized

The test script will initialize the database, but you can also do it manually:

```bash
# Verify database initialization
python -c "from crucible.db.session import init_from_config; init_from_config(); print('Database initialized')"
```

---

## Testing Methods

### Method 1: Test Script (Easiest)

This script demonstrates the complete end-to-end flow:

```bash
source venv/bin/activate
python scripts/test_problemspec_flow.py
```

**What it does:**
1. Creates a test project ("Improve API Response Time")
2. Creates a chat session
3. Adds sample chat messages (user describing problem, agent asking questions)
4. Calls the ProblemSpec agent to refine the spec
5. Shows the resulting ProblemSpec with constraints, goals, and follow-up questions
6. Displays the ProblemSpec as stored in the database

**Expected Output:**
```
2025-01-17 22:30:00 - INFO - Initializing database...
2025-01-17 22:30:01 - INFO - Creating test project...
2025-01-17 22:30:01 - INFO - Created project: <uuid> - Test Problem: Improve API Response Time
...
================================================================================
PROBLEMSPEC REFINEMENT RESULT
================================================================================

Updated Spec:
{
  "constraints": [
    {"name": "Database Schema", "description": "Cannot change without migration window", "weight": 80},
    {"name": "Infrastructure Changes", "description": "Avoid major infrastructure changes", "weight": 60},
    ...
  ],
  "goals": ["Reduce response time to under 500ms", "Target 200ms for common endpoints"],
  "resolution": "medium",
  "mode": "full_search"
}

Follow-up Questions:
1. What specific endpoints are causing the slowest performance?
2. Have you identified any bottlenecks in the current implementation?
...

Ready to run: false
Applied to database: true
```

### Method 2: API Testing

Start the API server and test via HTTP endpoints:

#### Step 1: Start the Server

```bash
source venv/bin/activate
./start_server.sh
# Or manually:
python -m crucible.api.main
```

Server will run on `http://127.0.0.1:8000`

#### Step 2: Create Test Data

You can use the test script first to create data, or use the API:

```bash
# Create a project (you'll need to implement this endpoint or use SQL directly)
# For now, use the test script to create data, then use these endpoints:
```

#### Step 3: Test Endpoints

**Get ProblemSpec:**
```bash
curl http://127.0.0.1:8000/projects/{project_id}/problem-spec
```

**Refine ProblemSpec:**
```bash
curl -X POST http://127.0.0.1:8000/projects/{project_id}/problem-spec/refine \
  -H "Content-Type: application/json" \
  -d '{
    "chat_session_id": "{chat_session_id}",
    "message_limit": 20
  }'
```

**View API Documentation:**
Open http://127.0.0.1:8000/docs in your browser for interactive API testing.

#### Step 4: Test with Python Requests

```python
import requests

# Refine ProblemSpec
response = requests.post(
    "http://127.0.0.1:8000/projects/{project_id}/problem-spec/refine",
    json={
        "chat_session_id": "{chat_session_id}",
        "message_limit": 20
    }
)

result = response.json()
print("Updated Spec:", result["updated_spec"])
print("Follow-up Questions:", result["follow_up_questions"])
print("Reasoning:", result["reasoning"])
print("Ready to run:", result["ready_to_run"])
```

### Method 3: Direct Service Testing

Test the service layer directly:

```python
from crucible.db.session import get_session, init_from_config
from crucible.services.problemspec_service import ProblemSpecService
from crucible.db.repositories import (
    create_project,
    create_chat_session,
    create_message
)

# Initialize
init_from_config()

with get_session() as session:
    # Create test data
    project = create_project(session, "Test Project", "Test description")
    chat = create_chat_session(session, project.id, "Test Chat")
    create_message(session, chat.id, "user", "I need to improve performance")
    
    # Test service
    service = ProblemSpecService(session)
    result = service.refine_problem_spec(project.id, chat.id)
    
    print("Result:", result)
```

---

## What to Expect

### Successful Test Results

1. **Agent Execution:**
   - Agent successfully reads chat messages
   - LLM processes the context and generates structured ProblemSpec
   - Response includes constraints, goals, resolution, and mode

2. **Database Updates:**
   - ProblemSpec is created or updated in database
   - All fields are properly stored
   - Enum values (resolution, mode) are correctly converted

3. **Follow-up Questions:**
   - Agent generates 0-3 relevant follow-up questions
   - Questions help refine the spec further

4. **Ready to Run Flag:**
   - Initially `false` (spec needs more detail)
   - Can become `true` after sufficient refinement

### Troubleshooting

**Error: "ANTHROPIC_API_KEY not set"**
- Ensure `.env` file exists in project root
- Check that `ANTHROPIC_API_KEY` is set correctly
- Verify no extra spaces or quotes around the key

**Error: "ModuleNotFoundError: No module named 'kosmos'"**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall Kosmos: `pip install -e vendor/kosmos`

**Error: "Database not initialized"**
- Run: `python -c "from crucible.db.session import init_from_config; init_from_config()"`

**Agent returns empty or invalid JSON:**
- Check LLM provider is working: `crucible kosmos-test`
- Try a different provider or model
- Increase `max_tokens` in agent if response is truncated

**No follow-up questions generated:**
- Agent may determine spec is complete
- Check `ready_to_run` flag
- Try adding more context in chat messages

---

## Next Steps

After successful testing:

1. **Review the ProblemSpec:**
   - Check constraints have appropriate weights (0-100)
   - Verify goals are clear and actionable
   - Ensure resolution and mode are appropriate

2. **Iterate:**
   - Add more chat messages
   - Call refine endpoint again
   - See how spec evolves with more context

3. **Test Edge Cases:**
   - Empty chat session
   - Very long conversation
   - Conflicting constraints
   - Incomplete problem description

4. **User Sign-off:**
   - Once satisfied with functionality, mark story as complete
   - Test with real-world problem scenarios

---

## Example Test Scenarios

### Scenario 1: Simple Problem
```
User: "I need to reduce server costs by 30%"
Agent: [Asks about current setup, constraints, timeline]
Result: Constraints with cost focus, goals about 30% reduction
```

### Scenario 2: Complex Problem
```
User: "We have performance issues and budget constraints and can't change the database"
Agent: [Asks clarifying questions about each constraint]
Result: Multiple constraints with different weights, clear goals
```

### Scenario 3: Incremental Refinement
```
Turn 1: User provides initial problem
Turn 2: Agent asks follow-up questions
Turn 3: User answers, agent refines spec
Turn 4: Spec becomes ready_to_run=true
```

