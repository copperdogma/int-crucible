# Migration Guide: Multi-Provider LLM Support

## TL;DR

**Nothing breaks. Your existing setup continues to work exactly as before.**

If you're currently using Anthropic/Claude, no action needed. The system defaults to Anthropic and respects all your existing configuration.

---

## For Existing Users

### What Changed?

Kosmos v0.2.0 adds support for multiple LLM providers (OpenAI, Ollama, etc.) while maintaining 100% backward compatibility with existing Claude/Anthropic setups.

### What Stays the Same?

**Everything in your current setup:**

- Your `.env` file works unchanged
- `ANTHROPIC_API_KEY` still works
- `CLAUDE_MODEL` still works
- `CLAUDE_*` environment variables still work
- Claude Code CLI routing still works (all 9s API key)
- All your existing code continues to work
- Default provider is still Anthropic

### Do I Need to Update Anything?

**No.** Your existing configuration continues to work:

```bash
# Your current .env - STILL WORKS PERFECTLY
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
CLAUDE_ENABLE_CACHE=true

# No need to add LLM_PROVIDER=anthropic
# (it's the default!)
```

---

## Optional: Switch to New Providers

### If You Want to Try OpenAI

Add these to your `.env`:

```bash
# Tell Kosmos to use OpenAI
LLM_PROVIDER=openai

# OpenAI configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
```

### If You Want to Try Local Models (Free)

```bash
# 1. Install Ollama: https://ollama.com/download
# 2. Pull a model: ollama pull llama3.1:70b
# 3. Start Ollama: ollama serve

# Then configure Kosmos:
LLM_PROVIDER=openai
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:70b
```

---

## Configuration Reference

### Old Configuration (Still Works)

```bash
# This configuration continues to work exactly as before
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
CLAUDE_ENABLE_CACHE=true
```

### New Configuration (Optional)

If you want to be explicit or use the new naming:

```bash
# Explicitly set provider (optional, defaults to anthropic)
LLM_PROVIDER=anthropic

# All your existing settings work
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

---

## FAQ

### Q: Will my existing research runs still work?

**A:** Yes, 100%. The system defaults to Anthropic and all your existing configuration is respected.

### Q: Do I need to change my code?

**A:** No. All existing code using `get_client()` continues to work.

### Q: Will my costs change?

**A:** No, unless you explicitly switch providers. Anthropic remains the default with the same pricing.

### Q: What about Claude Code CLI (all 9s API key)?

**A:** Still works perfectly. No changes needed.

### Q: Can I switch back to Claude after trying OpenAI?

**A:** Yes! Just remove `LLM_PROVIDER=openai` or set it to `anthropic`. Or delete the OpenAI config lines.

### Q: Will my cached responses still work?

**A:** Yes. Existing Anthropic caches continue to work.

### Q: Do I need to reinstall or update dependencies?

**A:** Only if you want to use OpenAI. For existing Anthropic users, no update needed. If you want OpenAI support: `pip install --upgrade kosmos-ai-scientist` (includes `openai` package).

### Q: What if I have multiple `.env` files or environments?

**A:** Each environment can use a different provider. Dev could use Ollama (free), staging could use GPT-3.5 (cheap), production could use Claude (high quality).

---

## Code Compatibility

### Existing Code (Works Unchanged)

```python
# Your existing code - STILL WORKS
from kosmos.core.llm import get_client

client = get_client()
response = client.generate("Your prompt")
```

### New Code (Optional)

If you want to use the new provider-agnostic API:

```python
# New recommended API (works with any provider)
from kosmos.core.llm import get_provider

provider = get_provider()  # Auto-detects from config
response = provider.generate("Your prompt")
print(response.content)  # Unified response format
```

Both work! Use whichever you prefer.

---

## Troubleshooting

### "My setup stopped working after updating"

This shouldn't happen, but if it does:

1. **Check your `.env` file exists** - Must be in project root
2. **Verify `ANTHROPIC_API_KEY` is set** - Not changed or removed
3. **Check for typos in environment variables**
4. **Try explicitly setting:** `LLM_PROVIDER=anthropic`
5. **Open an issue** if problems persist: [GitHub Issues](https://github.com/jimmc414/Kosmos/issues)

### "I want to revert to the old version"

```bash
pip install kosmos-ai-scientist==0.1.0
```

But this shouldn't be necessary - v0.2.0 is fully backward compatible.

---

## Testing the Update

Want to verify everything still works before fully updating?

```bash
# 1. Create a test environment
python3 -m venv test_env
source test_env/bin/activate

# 2. Install the new version
pip install --upgrade kosmos-ai-scientist

# 3. Copy your .env file
cp .env .env.backup

# 4. Run a simple test
kosmos run --question "Test: What is 2+2?" --quick

# 5. Check it used your configured provider
# (Should show "Anthropic" in output)

# 6. If all looks good, you're done!
# If not, restore: mv .env.backup .env
```

---

## Benefits of Multi-Provider Support

Even if you don't switch immediately, the new architecture provides:

### 1. Cost Savings Options
- Mix providers: GPT-3.5 for simple tasks ($0.50/M tokens), Claude for complex
- Use free local models for development/testing
- Switch to cheaper providers during high-volume periods

### 2. Privacy & Security
- Run sensitive research entirely locally (Ollama, LM Studio)
- No data leaves your machine
- Useful for proprietary or confidential research

### 3. Reliability & Redundancy
- Automatic fallback if one provider has issues
- Bypass rate limits by switching providers
- No single point of failure

### 4. Flexibility
- Try different models for different domains
- Compare results across providers
- Access specialized models (coding, math, etc.)

---

## When to Consider Switching

### Stay with Anthropic/Claude if:
- You value highest quality structured output
- You use prompt caching (30%+ cost savings)
- Your research needs Claude's reasoning capabilities
- You're using Claude Code CLI (Max subscription)

### Try OpenAI if:
- You need O1 reasoning models
- You want GPT-3.5's speed and low cost
- Your team is already on OpenAI
- You want wider ecosystem integration

### Try Local Models (Ollama) if:
- You want completely free usage
- Privacy is critical (sensitive research)
- You need offline capability
- You're experimenting or learning
- You have powerful hardware (32GB+ RAM)

### Try OpenRouter if:
- You want access to 100+ models
- You want to compare providers
- You want single API key for everything
- You want potentially lower costs

---

## Support

- **Full Provider Guide:** [docs/providers/README.md](providers/README.md)
- **Issues:** [GitHub Issues](https://github.com/jimmc414/Kosmos/issues)
- **Feature Discussion:** [Issue #3](https://github.com/jimmc414/Kosmos/issues/3)

---

## Summary

**For 99% of existing users: Do nothing. Everything continues to work.**

The multi-provider feature is opt-in. Your existing Anthropic/Claude setup is the default and requires zero changes. The new capabilities are there when you need them.
