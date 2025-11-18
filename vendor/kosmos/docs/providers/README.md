# Multi-Provider LLM Support

Kosmos AI Scientist supports multiple LLM providers, giving you flexibility in cost, privacy, and model selection.

## Supported Providers

| Provider | Type | Models | Cost | Privacy | Setup Difficulty |
|----------|------|--------|------|---------|------------------|
| **Anthropic (Claude)** | Cloud API | Claude 3.5 Sonnet, Opus, Haiku | $$ | Cloud | Easy |
| **OpenAI** | Cloud API | GPT-4 Turbo, GPT-4, GPT-3.5, O1 | $$$ | Cloud | Easy |
| **Ollama** | Local | Llama 3.1, Mistral, Mixtral, etc. | Free | Local | Medium |
| **OpenRouter** | Aggregator | 100+ models | Varies | Cloud | Easy |
| **LM Studio** | Local | Any GGUF model | Free | Local | Easy |
| **Together AI** | Cloud API | 50+ open models | $ | Cloud | Easy |

---

## Quick Start

### Default: Anthropic (Claude)

No configuration changes needed. Kosmos defaults to Anthropic:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
# That's it! Uses Claude 3.5 Sonnet by default
```

---

## Provider Setup Guides

### 1. Anthropic (Claude)

**Best for:** Production research, high-quality reasoning, structured output

#### API Mode (Pay-per-use)

1. Get API key from [console.anthropic.com](https://console.anthropic.com/)
2. Configure `.env`:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
CLAUDE_ENABLE_CACHE=true
```

#### CLI Mode (Claude Max Subscription)

If you have a Claude Max subscription, route to Claude Code CLI:

1. Install router: `pip install git+https://github.com/jimmc414/claude_n_codex_api_proxy.git`
2. Authenticate Claude CLI: `claude auth`
3. Configure `.env`:

```bash
LLM_PROVIDER=anthropic
# Set API key to all 9s for CLI routing
ANTHROPIC_API_KEY=999999999999999999999999999999999999999999999999
```

**Pricing:** Input: $3/M tokens, Output: $15/M tokens

---

### 2. OpenAI

**Best for:** GPT-4 users, O1 reasoning models, wide adoption

#### Setup

1. Get API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Configure `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7
```

#### Model Options

```bash
# GPT-4 Turbo (128k context, $10/$30 per M tokens)
OPENAI_MODEL=gpt-4-turbo-2024-04-09

# GPT-4 (8k context, $30/$60 per M tokens)
OPENAI_MODEL=gpt-4

# GPT-3.5 Turbo (cheap, fast, $0.50/$1.50 per M tokens)
OPENAI_MODEL=gpt-3.5-turbo

# O1 Preview (advanced reasoning, $15/$60 per M tokens)
OPENAI_MODEL=o1-preview

# O1 Mini (fast reasoning, $3/$12 per M tokens)
OPENAI_MODEL=o1-mini
```

**Pricing:** Varies by model (see above)

---

### 3. Ollama (Local Models)

**Best for:** Privacy, free usage, experimentation, offline work

#### Setup

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Or download from https://ollama.com/download
   ```

2. **Pull a model:**
   ```bash
   # Large, powerful (requires ~40GB RAM)
   ollama pull llama3.1:70b

   # Medium (requires ~16GB RAM)
   ollama pull llama3.1:8b

   # Coding-optimized
   ollama pull codellama:13b

   # Fastest
   ollama pull mistral:7b
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   # Runs on http://localhost:11434
   ```

4. **Configure Kosmos `.env`:**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=ollama  # Dummy key for compatibility
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_MODEL=llama3.1:70b
   ```

#### Model Recommendations

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| llama3.1:70b | 40GB | 64GB | Best quality, research tasks |
| llama3.1:8b | 5GB | 8GB | Balanced speed/quality |
| mistral:7b | 4GB | 8GB | Fast, good reasoning |
| codellama:13b | 7GB | 16GB | Code generation |
| mixtral:8x7b | 26GB | 32GB | High quality, mixture of experts |

**Pricing:** Free! Runs locally

---

### 4. OpenRouter (100+ Models)

**Best for:** Access to many models, comparing providers, flexible costs

#### Setup

1. Get API key from [openrouter.ai/keys](https://openrouter.ai/keys)
2. Browse models at [openrouter.ai/docs#models](https://openrouter.ai/docs#models)
3. Configure `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-or-v1-your-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=anthropic/claude-3.5-sonnet
```

#### Popular Models on OpenRouter

```bash
# Claude via OpenRouter
OPENAI_MODEL=anthropic/claude-3.5-sonnet
OPENAI_MODEL=anthropic/claude-3-opus

# GPT models
OPENAI_MODEL=openai/gpt-4-turbo
OPENAI_MODEL=openai/gpt-4

# Open source models
OPENAI_MODEL=meta-llama/llama-3.1-70b-instruct
OPENAI_MODEL=google/gemini-pro-1.5

# Specialized models
OPENAI_MODEL=mistralai/mixtral-8x7b-instruct
OPENAI_MODEL=deepseek/deepseek-coder-33b-instruct
```

**Pricing:** Varies by model, typically cheaper than direct APIs

---

### 5. LM Studio (Local GUI)

**Best for:** Non-technical users, easy local model management, testing

#### Setup

1. **Download LM Studio:** [lmstudio.ai](https://lmstudio.ai/)
2. **Download a model** using LM Studio's GUI (e.g., Llama 3.1)
3. **Start local server:**
   - In LM Studio: Go to "Local Server" tab
   - Click "Start Server"
   - Note the port (usually 1234)

4. **Configure Kosmos `.env`:**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=lm-studio
   OPENAI_BASE_URL=http://localhost:1234/v1
   OPENAI_MODEL=local-model  # Use the name shown in LM Studio
   ```

**Pricing:** Free! Runs locally

---

### 6. Together AI

**Best for:** Open-source models at scale, fast inference

#### Setup

1. Get API key from [api.together.xyz](https://api.together.xyz/)
2. Configure `.env`:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-together-key
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

**Pricing:** $0.88/M tokens (input+output) for Llama 3.1 70B

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `anthropic` | Provider to use: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | If using Anthropic | - | Anthropic API key or `999...` for CLI |
| `CLAUDE_MODEL` | No | `claude-3-5-sonnet-20241022` | Claude model name |
| `CLAUDE_MAX_TOKENS` | No | `4096` | Max tokens per request |
| `CLAUDE_TEMPERATURE` | No | `0.7` | Sampling temperature (0.0-1.0) |
| `CLAUDE_ENABLE_CACHE` | No | `true` | Enable prompt caching |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4-turbo` | Model name |
| `OPENAI_MAX_TOKENS` | No | `4096` | Max tokens per request |
| `OPENAI_TEMPERATURE` | No | `0.7` | Sampling temperature (0.0-2.0) |
| `OPENAI_BASE_URL` | No | - | Custom base URL for compatible APIs |
| `OPENAI_ORGANIZATION` | No | - | OpenAI organization ID |

---

## Switching Providers

### At Runtime (Configuration)

Simply change your `.env` file and restart Kosmos:

```bash
# Switch from Anthropic to OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Or switch to local Ollama
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:70b
```

### In Code (Advanced)

```python
from kosmos.core.providers import get_provider

# Get provider from config
provider = get_provider("openai", {
    'api_key': 'sk-...',
    'model': 'gpt-4-turbo',
    'max_tokens': 4096
})

response = provider.generate("Your research question")
print(response.content)
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Ensure `.env` file exists and contains `ANTHROPIC_API_KEY=...`
- If using OpenAI, set `LLM_PROVIDER=openai`

### "OpenAI provider not available"
- Install OpenAI package: `pip install openai>=1.0.0`
- Check that `openai` is in your environment

### Ollama connection refused
- Ensure Ollama is running: `ollama serve`
- Check the port matches: `http://localhost:11434/v1`
- Pull the model first: `ollama pull llama3.1:70b`

### OpenRouter rate limits
- OpenRouter has per-model rate limits
- Check your dashboard: [openrouter.ai/account](https://openrouter.ai/account)
- Consider upgrading your plan or switching models

### Local models are slow
- Check model size vs. available RAM
- Use quantized models (smaller, faster)
- Try GPU acceleration if available
- Use smaller models for testing (7B/8B parameter models)

### Cost tracking not working for local models
- This is expected - local models don't report usage stats
- Cost will show as `$0.00`
- Token counts are estimated (rough approximation)

---

## Best Practices

### Cost Optimization
1. **Use Anthropic caching** - Save 30%+ with `CLAUDE_ENABLE_CACHE=true`
2. **Mix providers** - Use GPT-3.5 for simple tasks, GPT-4/Claude for complex
3. **Local for development** - Use Ollama for testing, cloud for production
4. **Monitor usage** - Check provider dashboards regularly

### Privacy & Security
1. **Local models for sensitive data** - Use Ollama/LM Studio
2. **Never commit API keys** - Use `.env` (already in `.gitignore`)
3. **Rotate keys regularly** - Especially for production
4. **Use environment variables** - Not hardcoded credentials

### Performance
1. **Choose right model size** - Bigger ≠ always better
2. **Local models need RAM** - Match model size to hardware
3. **Use caching** - Anthropic's cache saves API calls
4. **Batch requests** - More efficient for multiple tasks

### Reliability
1. **Test fallbacks** - Have backup provider configured
2. **Monitor rate limits** - Respect provider quotas
3. **Handle errors gracefully** - Providers can have outages
4. **Keep dependencies updated** - `pip install --upgrade openai anthropic`

---

## Comparison Guide

### When to use Anthropic (Claude)
**Pros:**
- Best structured output quality
- Strong reasoning and analysis
- Good at following complex instructions
- Prompt caching saves costs

**Cons:**
- More expensive than OpenAI for simple tasks

### When to use OpenAI
**Pros:**
- Wide ecosystem and tooling
- O1 models for complex reasoning
- GPT-3.5 very fast and cheap
- Good for code generation

**Cons:**
- No prompt caching (more expensive for repetitive tasks)

### When to use Ollama/Local
**Pros:**
- Completely free
- Full privacy (data never leaves machine)
- Works offline
- Good for experimentation

**Cons:**
- Requires powerful hardware
- Slower than cloud APIs
- Quality lower than top cloud models

### When to use OpenRouter
**Pros:**
- Access to 100+ models
- Compare providers easily
- Often cheaper than direct APIs
- Single API key for everything

**Cons:**
- Additional layer (potential latency)
- Rate limits can be stricter

---

## Next Steps

1. **Choose your provider** based on your needs (cost, privacy, quality)
2. **Configure `.env`** with provider settings
3. **Test the connection** - Run a simple research query
4. **Monitor costs** - Check your provider dashboard
5. **Experiment** - Try different models for different tasks

For migration from Claude-only setup, see [MIGRATION_MULTI_PROVIDER.md](../MIGRATION_MULTI_PROVIDER.md)

---

## Support

- **Documentation:** [Main README](../../README.md)
- **Issues:** [GitHub Issues](https://github.com/jimmc414/Kosmos/issues)
- **Feature Request:** Issue #3 - Multi-Provider Support
- **API Docs:** [LLM Provider API](../api/llm.md)
