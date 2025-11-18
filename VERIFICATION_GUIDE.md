# Int Crucible Setup Verification Guide

This guide helps you verify that the Int Crucible backend is set up correctly, even if you're not familiar with Kosmos.

## Quick Verification (Automated)

The easiest way to verify everything works:

```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

This script will:
- Check if the virtual environment exists (create it if needed)
- Test that Python and all packages are installed
- Verify CLI commands work
- Test Kosmos integration
- Test the FastAPI application

**Expected output:** All checks should show ✓ (green checkmarks)

## Manual Verification Steps

If you prefer to verify step-by-step, or if the automated script fails:

### Step 1: Check Python Environment

```bash
# Check Python version (should be 3.11 or higher)
python3 --version

# Should show something like: Python 3.11.x or Python 3.14.x
```

### Step 2: Run Setup (if not done already)

```bash
# This creates the virtual environment and installs everything
./setup_backend.sh
```

**What to look for:**
- Script should complete without errors
- You should see "✓ Kosmos installed" and "✓ Int Crucible backend installed"

### Step 3: Activate Virtual Environment

```bash
source venv/bin/activate

# Your prompt should now show (venv) at the beginning
```

### Step 4: Test Basic Commands

```bash
# Test 1: Version command
crucible version

# Expected output:
# Int Crucible v0.1.0
# A general multi-agent reasoning system

# Test 2: Configuration
crucible config

# Expected output: A table showing database URL, log level, API host/port
```

**What this means:** If these commands work, the CLI is installed correctly.

### Step 5: Test Kosmos Integration

```bash
# This is the key test - it verifies Kosmos is working
crucible kosmos-test
```

**Expected output:**
```
Testing Kosmos Integration

1. Testing Kosmos configuration...
   ✓ Kosmos config loaded
2. Testing database connection...
   ✓ Database initialized
3. Testing agent registry...
   ✓ Found X agent(s) in registry

✓ All tests passed! Kosmos integration is working.
```

**What this means:**
- ✓ Kosmos is installed and can be imported
- ✓ Database connection works (SQLite file will be created)
- ✓ Kosmos agent system is accessible

**If this fails:**
- Make sure `vendor/kosmos` directory exists
- Try running `./setup_backend.sh` again
- Check that you have Python 3.11 or higher

### Step 6: Start and Test the API Server

**Important:** The verification script doesn't start the server - it only checks that the code works. You need to start the server separately.

**Option 1: Use the start script (Easiest)**
```bash
./start_server.sh
```

**Option 2: Start manually**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server
python -m crucible.api.main
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

**Then test it (in another terminal or browser):**

```bash
# Test the health endpoint
curl http://127.0.0.1:8000/health

# Expected output: {"status":"healthy","service":"int-crucible"}

# Or visit in browser:
# http://127.0.0.1:8000/docs
```

**What this means:** The FastAPI server is running and responding to requests.

**Note:** Keep the server running in one terminal. Use another terminal or your browser to test the endpoints.

## Understanding What Each Test Means

### ✓ Kosmos Integration Test
This test verifies that:
- Kosmos (the underlying AI system) is properly installed
- The database connection works
- The agent system is accessible

**You don't need to understand Kosmos** - you just need to see all three checks pass.

### ✓ CLI Commands
These verify that:
- The command-line interface is installed
- You can interact with the system from the terminal

### ✓ API Server
This verifies that:
- The web API is working
- You can make HTTP requests to the system
- The server starts without errors

## Common Issues and Solutions

### "ModuleNotFoundError: No module named 'kosmos'"
**Solution:** Run `./setup_backend.sh` again. Make sure `vendor/kosmos` exists.

### "Error: Python 3.11+ is required"
**Solution:** Install Python 3.11 or higher. Check with `python3 --version`.

### "chromadb dependency conflict"
**Solution:** The setup script should handle this automatically. If it doesn't, the script will show a workaround message.

### "Database initialization skipped"
**This is OK!** The database will be created automatically when first used. You can ignore this warning.

## What Success Looks Like

When everything is working, you should be able to:

1. ✅ Run `crucible version` and see version info
2. ✅ Run `crucible kosmos-test` and see all checks pass
3. ✅ Start the API server (using `./start_server.sh` or `python -m crucible.api.main`)
4. ✅ See server running message: "Uvicorn running on http://127.0.0.1:8000"
5. ✅ Visit http://127.0.0.1:8000/docs in your browser and see API documentation
6. ✅ Visit http://127.0.0.1:8000/health and see `{"status":"healthy"}`

**Important:** The verification script (`./verify_setup.sh`) checks that everything is *installed correctly*, but it doesn't start the server. You need to start the server separately using `./start_server.sh` or the manual command.

## Next Steps After Verification

Once verification passes:

1. **Configure API keys** (optional, for LLM features):
   - Edit `.env` file
   - Add your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` if you want to use AI features
   - For now, basic functionality works without API keys

2. **Explore the API:**
   - Visit http://127.0.0.1:8000/docs
   - Try the `/health` endpoint
   - Try the `/kosmos/agents` endpoint

3. **Ready for development:**
   - The backend is ready for the next stories
   - You can start building Crucible-specific features on top of this foundation

## Still Having Issues?

If verification fails:
1. Check the error message carefully
2. Make sure `vendor/kosmos` directory exists (it should, if you followed the setup)
3. Try deleting `venv` and running `./setup_backend.sh` again
4. Check Python version: `python3 --version` (needs 3.11+)

The most common issue is the virtual environment not being activated. Make sure you run `source venv/bin/activate` before testing commands.

