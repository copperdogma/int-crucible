# Changelog

All notable changes to Kosmos AI Scientist will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2025-11-13

### Added - Multi-Provider LLM Support

**Major Feature:** Kosmos now supports multiple LLM providers for maximum flexibility.

#### Supported Providers
- **Anthropic Claude** (default) - API + CLI mode
- **OpenAI** - GPT-4 Turbo, GPT-4, GPT-3.5, O1 models
- **Ollama** - Free local models (Llama, Mistral, etc.)
- **OpenRouter** - Access to 100+ models
- **LM Studio** - Local models with GUI
- **Together AI** - Open-source models at scale

#### Core Implementation
- Provider abstraction layer with unified `LLMProvider` interface ([#3](https://github.com/jimmc414/Kosmos/issues/3))
- Configuration-driven provider switching via `LLM_PROVIDER` environment variable
- `AnthropicProvider` - Refactored from `ClaudeClient` with full backward compatibility
- `OpenAIProvider` - Full OpenAI API + OpenAI-compatible endpoints support
- Provider factory pattern for easy extensibility
- Unified response format (`LLMResponse`, `UsageStats`, `Message`)

#### Configuration
- New `LLM_PROVIDER` environment variable for provider selection
- New `OpenAIConfig` class with full OpenAI configuration
- Support for custom base URLs (enables Ollama, OpenRouter, etc.)
- `.env.example` expanded with comprehensive provider examples

#### Documentation
- `docs/providers/README.md` - Complete setup guide for all 6+ providers
- `docs/MIGRATION_MULTI_PROVIDER.md` - Migration guide (emphasizes zero breaking changes)
- `docs/api/llm.md` - API documentation for provider interface
- `docs/releases/MULTI_PROVIDER_RELEASE.md` - Detailed release notes
- Updated `README.md` with multi-provider comparison table

#### Testing
- Manual test scripts for provider validation:
  - `tests/manual/test_provider_switching.py` - Test switching between providers
  - `tests/manual/test_basic_generation.py` - Test core generation features
  - `tests/manual/test_ollama.py` - Test Ollama local model integration
- Existing test suite validation (15/17 tests pass, 2 pre-existing cache issues)

### Changed
- `get_client()` function now supports provider selection from configuration
- `kosmos/core/llm.py` updated with provider-aware singleton pattern
- Added `get_provider()` function as recommended API for new code
- Updated README tagline to reflect multi-provider support

### Dependencies
- Added `openai>=1.0.0` for OpenAI provider support

### Backward Compatibility
- **100% backward compatible** - No breaking changes
- Existing `ANTHROPIC_API_KEY` and `CLAUDE_*` variables still work
- Default provider remains Anthropic
- `ClaudeClient` class maintained as alias
- All existing code continues to work unchanged

### Added - Persistent Knowledge Graphs

**Major Feature:** Automatic research knowledge graph that persists between sessions.

#### Core Capabilities
- **Automatic Persistence** - All research artifacts automatically saved to Neo4j knowledge graph
- **Entity Types** - ResearchQuestion, Hypothesis, ExperimentProtocol, ExperimentResult
- **Relationship Types** - SPAWNED_BY, TESTS, SUPPORTS, REFUTES, REFINED_FROM, PRODUCED_BY
- **Rich Provenance** - Every entity and relationship includes metadata:
  - Agent that created it (e.g., HypothesisGeneratorAgent, DataAnalystAgent)
  - Timestamp of creation
  - Confidence scores
  - Statistical significance (p-values, effect sizes)
  - Iteration and generation numbers

#### CLI Commands
- `kosmos graph --stats` - View knowledge graph statistics
- `kosmos graph --export FILE` - Export graph to JSON for backup/sharing
- `kosmos graph --import FILE` - Import graph from JSON export
- `kosmos graph --reset` - Clear all graph data (with confirmation)

#### Implementation
- **Dual Persistence Architecture** - Both SQL (SQLAlchemy) and Graph (Neo4j) storage
  - SQL for structured queries and ACID transactions
  - Graph for relationship traversal and provenance
  - Graceful degradation when Neo4j unavailable
- **World Model Abstraction Layer**
  - `WorldModelInterface` - Abstract interface for future storage backends
  - `Neo4jWorldModel` - Production implementation using py2neo
  - Factory pattern with singleton support
  - Helper methods for entity/relationship creation (from_hypothesis, from_protocol, etc.)
- **ResearchDirectorAgent Integration**
  - Automatic persistence in 6 message handlers
  - Research question entity created on initialization
  - Hypothesis entities with SPAWNED_BY relationships
  - Protocol entities with TESTS relationships
  - Result entities with SUPPORTS/REFUTES relationships
  - Refinement tracking via REFINED_FROM relationships
  - Convergence annotations

#### Configuration
- New `WorldModelConfig` class:
  - `WORLD_MODEL_ENABLED` - Enable/disable graph persistence (default: true)
  - `WORLD_MODEL_MODE` - Storage mode: "simple" or "production"
  - `WORLD_MODEL_PROJECT` - Optional project namespace
  - `WORLD_MODEL_AUTO_SAVE_INTERVAL` - Auto-export interval in seconds
- Existing `Neo4jConfig` extended with connection pool settings

#### Documentation
- `docs/user/world_model_guide.md` - Comprehensive 500+ line user guide
  - Quick start and CLI reference
  - Use cases (knowledge accumulation, collaboration, backup)
  - Advanced topics (direct Cypher queries, programmatic access)
  - Troubleshooting and FAQ
  - Best practices for exports and versioning
- `README.md` - New "Persistent Knowledge Graphs" section with examples
- `docs/user/user-guide.md` - Updated Neo4j setup + CLI commands section
- `docs/planning/` - Complete implementation documentation and checkpoints

#### Testing
- **Unit Tests** - 101 tests passing (100% pass rate)
  - `tests/unit/world_model/test_models.py` - Entity/Relationship models (31 tests)
  - `tests/unit/world_model/test_interface.py` - WorldModelInterface (20 tests)
  - `tests/unit/world_model/test_factory.py` - Factory pattern (28 tests)
  - `tests/unit/cli/test_graph_commands.py` - CLI commands (22 tests)
- **Integration Tests** - 7 tests created (require Neo4j)
  - `tests/integration/test_world_model_persistence.py` - Full workflow tests
  - Research question persistence
  - Hypothesis persistence with relationships
  - Refined hypothesis tracking
  - Protocol and result persistence
  - Dual persistence verification

#### Benefits
- **Knowledge Accumulation** - Build expertise over weeks/months
- **Research Provenance** - Full audit trail of research decisions
- **Collaboration** - Export/import enables team sharing
- **Reproducibility** - Complete graph captures research context
- **Version Control** - Export snapshots at milestones

#### Technical Details
- ~2,600 lines of production code
- ~1,300 lines of test code
- Neo4j 5.13+ required (optional - graceful degradation)
- Export format: JSON with full graph structure
- Performance: <100ms per entity/relationship (tested up to 1000+ entities)

### Commits
- `b06749d` - Persistent knowledge graphs implementation (Week 2 Days 1-4)
- `[current]` - Documentation and validation (Week 2 Day 5)
- `35dc159` - Core multi-provider infrastructure (Phases 1-3, 5)
- `[pending]` - Documentation and testing (Phases 7-9)

---

## [0.1.0] - 2025-11-06

### Initial Production Release

#### Major Features
- **Autonomous Research Cycle** - End-to-end scientific workflow automation
- **Multi-Domain Support** - Biology, physics, chemistry, neuroscience, materials science
- **Claude Integration** - Powered by Claude Sonnet 4.5
- **Agent-Based Architecture** - Modular agents for hypothesis, experiment design, analysis
- **Command-line Interface** - Rich terminal interface with 8 commands
- **Safety-First Design** - Sandboxed execution, validation, reproducibility

#### Performance & Optimization (v1.0)
- **20-40× Overall Performance** - Combined optimizations
- **Parallel Execution** - 4-16× faster experiments via ProcessPoolExecutor
- **Concurrent Operations** - 2-4× faster research cycles
- **Smart Caching** - 30%+ API cost reduction
- **Database Optimization** - 10× faster queries with 32 strategic indexes
- **Auto-Scaling** - Kubernetes HorizontalPodAutoscaler support

#### Production Features (v1.0)
- **Health Monitoring** - Prometheus metrics, alerts (email/Slack/PagerDuty)
- **Performance Profiling** - CPU, memory, bottleneck detection
- **Docker Deployment** - Complete docker-compose stack
- **Kubernetes Ready** - 8 manifests for production deployment
- **Cloud Support** - AWS, GCP, Azure deployment guides
- **Comprehensive Testing** - 90%+ test coverage

#### Caching System
- Multi-tier caching (Claude, Experiment, Embedding, General)
- 25-35% cache hit rate for LLM responses
- 40-50% cache hit rate for computational results
- Automatic cache budget alerts
- Cache statistics and monitoring

#### Developer Experience
- **Flexible Integration** - Anthropic API + Claude Code CLI support
- **Rich Documentation** - 10,000+ lines of documentation
- **11 Example Projects** - Across all supported domains
- **CLI Tools** - run, status, history, cache, config, profile commands

#### Literature Integration
- ArXiv, Semantic Scholar, PubMed integration
- Automated paper search and summarization
- Novelty checking for hypotheses
- Knowledge graph construction

#### Core Components
- **Hypothesis Generation** - AI-powered hypothesis generation with literature context
- **Experiment Designer** - Automated experimental protocol design
- **Data Analyst** - Statistical analysis and interpretation
- **Literature Analyzer** - Paper analysis and knowledge extraction
- **Research Director** - Orchestrates full research cycle

#### Database & Storage
- PostgreSQL for relational data
- ChromaDB for vector embeddings
- Neo4j for knowledge graphs
- Redis for caching

#### Safety & Validation
- Code validation and sandboxing
- Reproducibility tracking
- Resource limit enforcement
- Guardrails for experimental safety

### Dependencies
- Python 3.11+
- `anthropic>=0.40.0` - Claude API integration
- `pydantic>=2.0.0` - Configuration validation
- `sqlalchemy>=2.0.0` - Database ORM
- `chromadb>=0.4.0` - Vector database
- Scientific computing: numpy, pandas, scipy, scikit-learn, statsmodels
- Visualization: matplotlib, seaborn, plotly
- CLI: rich, typer, click

### Documentation
- Comprehensive README with quick start
- Architecture documentation (1,680 lines)
- User guide (1,156 lines)
- Developer guide (870 lines)
- Troubleshooting guide (547 lines)
- API documentation (10 .rst files)
- CONTRIBUTING.md (580 lines)

### Known Issues
- Test suite has 2 cache-related test failures (pre-existing, non-blocking)

---

## Release Notes

- **[v0.2.0 Multi-Provider Release](docs/releases/MULTI_PROVIDER_RELEASE.md)**

---

## Links

- **Homepage**: https://github.com/jimmc414/Kosmos
- **Documentation**: docs/
- **Issues**: https://github.com/jimmc414/Kosmos/issues
- **Contributing**: CONTRIBUTING.md
