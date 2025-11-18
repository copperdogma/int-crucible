# Kosmos Troubleshooting Guide

**Version:** 0.10.0
**Last Updated:** 2025-01-15

This guide helps resolve common issues when using Kosmos.

## Quick Diagnostics

Always start with:

```bash
kosmos doctor
```

This checks:
- Python version
- Required packages
- API key configuration
- Cache directory
- Database connectivity

---

## Installation Issues

### Issue: ModuleNotFoundError: No module named 'kosmos'

**Symptoms:**
```
ModuleNotFoundError: No module named 'kosmos'
```

**Causes:**
- Kosmos not installed
- Wrong Python environment
- Installation failed silently

**Solutions:**

1. **Verify virtual environment:**
   ```bash
   which python
   # Should show venv path, not system Python
   ```

2. **Reinstall in editable mode:**
   ```bash
   pip install -e .
   
   # Verify installation
   pip show kosmos
   ```

3. **Check Python path:**
   ```python
   import sys
   print(sys.path)
   # Should include /path/to/kosmos
   ```

### Issue: Package dependency conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solutions:**

1. **Use fresh virtual environment:**
   ```bash
   # Remove old venv
   rm -rf venv
   
   # Create fresh
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install
   pip install --upgrade pip
   pip install -e .
   ```

2. **Install specific versions:**
   ```bash
   pip install anthropic==0.18.0
   pip install typer==0.9.0
   pip install rich==13.7.0
   ```

---

## Configuration Issues

### Issue: ANTHROPIC_API_KEY not found

**Symptoms:**
```
Error: ANTHROPIC_API_KEY environment variable not set
```

**Solutions:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   # Should exist in project root
   ```

2. **Check .env contents:**
   ```bash
   cat .env | grep ANTHROPIC_API_KEY
   # Should show: ANTHROPIC_API_KEY=sk-ant-... or 999...
   ```

3. **Load environment variables:**
   ```bash
   # Bash/Zsh
   export $(cat .env | grep -v '^#' | xargs)
   
   # Or source if using direnv
   direnv allow
   ```

4. **Verify loaded:**
   ```bash
   echo $ANTHROPIC_API_KEY
   # Should print your key
   ```

### Issue: API key invalid

**Symptoms:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solutions:**

1. **For API mode:** Get new key from console.anthropic.com
2. **For CLI mode:** Ensure using 50 nines: `999...999`
3. **Verify Claude CLI authenticated:**
   ```bash
   claude auth
   ```

---

## Runtime Issues

### Issue: Research hangs or times out

**Symptoms:**
- Research runs for hours without completing
- No progress updates
- Process appears frozen

**Solutions:**

1. **Check iteration count:**
   ```bash
   # Reduce iterations
   kosmos run "question" --max-iterations 3
   ```

2. **Enable watch mode in separate terminal:**
   ```bash
   kosmos status <run_id> --watch
   # See if progress is actually happening
   ```

3. **Check logs:**
   ```bash
   tail -f ~/.kosmos/logs/kosmos.log
   ```

4. **Set timeout:**
   ```python
   # In .env
   MAX_EXPERIMENT_EXECUTION_TIME=600  # 10 minutes
   ```

### Issue: Out of memory errors

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Reduce cache size:**
   ```python
   # In .env
   CACHE_MAX_MEMORY_MB=256  # Reduce from 512
   ```

2. **Clear cache:**
   ```bash
   kosmos cache --clear
   ```

3. **Increase system swap:**
   ```bash
   # Linux
   sudo fallocate -l 4G /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## Database Issues

### Issue: Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Check for other Kosmos processes:**
   ```bash
   ps aux | grep kosmos
   # Kill if necessary: kill -9 <PID>
   ```

2. **Use PostgreSQL instead of SQLite:**
   ```python
   # In .env
   DATABASE_URL=postgresql://user:pass@localhost/kosmos
   ```

3. **Delete and recreate database:**
   ```bash
   rm kosmos.db
   kosmos doctor  # Recreates DB
   ```

### Issue: Missing tables

**Symptoms:**
```
sqlalchemy.exc.OperationalError: no such table: research_runs
```

**Solutions:**

1. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Recreate database:**
   ```bash
   rm kosmos.db
   python -c "from kosmos.db import init_db; init_db()"
   ```

---

## API and Network Issues

### Issue: Rate limit exceeded

**Symptoms:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solutions:**

1. **Enable caching:**
   ```python
   # In .env
   CACHE_ENABLED=true
   ```

2. **Reduce parallel requests:**
   ```python
   # Disable parallel execution
   parallel_execution = False
   ```

3. **Add delays between requests:**
   ```python
   import time
   time.sleep(1)  # 1 second delay
   ```

4. **Switch to Claude CLI mode** (unlimited):
   ```python
   ANTHROPIC_API_KEY=99999999999999999999999999999999999999999999999999
   ```

### Issue: Connection timeouts

**Symptoms:**
```
httpx.ConnectTimeout: timed out
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping api.anthropic.com
   ```

2. **Increase timeout:**
   ```python
   # In code
   client = httpx.Client(timeout=60.0)  # 60 seconds
   ```

3. **Check firewall/proxy:**
   ```bash
   # Test direct connection
   curl -I https://api.anthropic.com
   ```

---

## CLI Issues

### Issue: Command not found

**Symptoms:**
```bash
kosmos: command not found
```

**Solutions:**

1. **Verify installation:**
   ```bash
   pip show kosmos
   ```

2. **Check PATH:**
   ```bash
   which kosmos
   # Should show: /path/to/venv/bin/kosmos
   ```

3. **Use python -m:**
   ```bash
   python -m kosmos.cli.main run "question"
   ```

4. **Reinstall with entry points:**
   ```bash
   pip install --force-reinstall -e .
   ```

### Issue: Rich formatting not working

**Symptoms:**
- No colors in terminal
- Tables not rendering
- Progress bars broken

**Solutions:**

1. **Check terminal supports ANSI:**
   ```bash
   echo $TERM
   # Should be: xterm-256color or similar
   ```

2. **Force color output:**
   ```bash
   export FORCE_COLOR=1
   kosmos run "question"
   ```

3. **Use plain output:**
   ```bash
   kosmos run "question" --no-color
   ```

---

## Cache Issues

### Issue: Cache not saving costs

**Symptoms:**
- Cache hit rate is 0%
- No cost savings
- Every request hits API

**Solutions:**

1. **Verify cache enabled:**
   ```bash
   kosmos cache --stats
   # Check if cache is enabled
   ```

2. **Check cache directory:**
   ```bash
   ls -la ~/.kosmos/cache
   # Should have files
   ```

3. **Clear and rebuild:**
   ```bash
   kosmos cache --clear
   kosmos cache --optimize
   ```

### Issue: Cache corruption

**Symptoms:**
```
pickle.UnpicklingError: invalid load key
```

**Solutions:**

1. **Clear all caches:**
   ```bash
   kosmos cache --clear
   ```

2. **Delete cache directory:**
   ```bash
   rm -rf ~/.kosmos/cache
   mkdir -p ~/.kosmos/cache
   ```

---

## Domain-Specific Issues

### Biology: KEGG API not responding

**Solutions:**
1. Check KEGG status: https://www.kegg.jp/
2. Use local cache if available
3. Try alternative endpoints

### Neuroscience: FlyWire authentication

**Solutions:**
1. Get API token from flywire.ai
2. Set in environment: `FLYWIRE_TOKEN=your_token`
3. Check token expiration

### Materials: Materials Project key

**Solutions:**
1. Get key from materialsproject.org
2. Set in .env: `MP_API_KEY=your_key`
3. Check usage limits

---

## Performance Issues

### Issue: Research too slow

**Symptoms:**
- Taking hours to complete
- High API costs
- Low throughput

**Solutions:**

1. **Enable caching:**
   ```bash
   kosmos cache --stats
   # Verify enabled and working
   ```

2. **Use Haiku for simple tasks:**
   ```python
   # Auto model selection
   AUTO_MODEL_SELECTION=true
   ```

3. **Reduce iterations:**
   ```bash
   kosmos run "question" --max-iterations 5
   ```

4. **Use Claude CLI mode:**
   ```python
   ANTHROPIC_API_KEY=99999999999999999999999999999999999999999999999999
   ```

---

## Getting More Help

If issues persist:

1. **Check logs:**
   ```bash
   tail -100 ~/.kosmos/logs/kosmos.log
   ```

2. **Enable debug mode:**
   ```bash
   kosmos --debug run "question"
   ```

3. **Run diagnostics:**
   ```bash
   kosmos doctor > diagnostics.txt
   ```

4. **Report issue:**
   - GitHub: https://github.com/your-org/kosmos/issues
   - Include: OS, Python version, error message, logs
   - Attach: diagnostics.txt

5. **Community:**
   - Discussions: https://github.com/your-org/kosmos/discussions
   - Discord: https://github.com/jimmc414/Kosmos/discussions

---

## Common Error Messages

### "No module named 'anthropic'"
**Fix:** `pip install anthropic`

### "Database migration required"
**Fix:** `alembic upgrade head`

### "Permission denied: ~/.kosmos/cache"
**Fix:** `chmod 755 ~/.kosmos/cache`

### "JSON decode error"
**Fix:** Clear cache, check API responses

### "Hypothesis generation failed"
**Fix:** Check API key, retry with different question

---

*For more help, see [User Guide](user_guide.md) or [Developer Guide](developer_guide.md)*
