# Kosmos AI Scientist Architecture

**Version:** 0.10.0
**Last Updated:** 2025-01-15

## Table of Contents

1. [Overview](#overview)
2. [System Design Principles](#system-design-principles)
3. [Core Infrastructure](#core-infrastructure)
4. [Caching System](#caching-system)
5. [Agent Framework](#agent-framework)
6. [Research Workflow](#research-workflow)
7. [Execution Engine](#execution-engine)
8. [CLI Layer](#cli-layer)
9. [Domain System](#domain-system)
10. [Knowledge Integration](#knowledge-integration)
11. [Data Flow](#data-flow)
12. [Deployment Architecture](#deployment-architecture)

---

## Overview

Kosmos is a fully autonomous AI scientist powered by Claude that can generate hypotheses, design experiments, execute computational analysis, and iteratively refine understanding across multiple scientific domains.

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                          CLI Layer                             │
│  (Typer + Rich: Interactive UI, Commands, Progress)            │
└─────────────────────┬──────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────┐
│                    Research Director                           │
│  (Orchestrates workflow, manages state, coordinates agents)    │
└───┬───────────┬───────────┬──────────────┬───────────┬─────────┘
    │           │           │              │           │
    ▼           ▼           ▼              ▼           ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌───────────────┐
│Hypoth  │ │Experi  │ │   Data   │ │Litera   │ │  Other        │
│esis    │ │ment    │ │ Analyst  │ │ture     │ │  Specialized  │
│Generat │ │Designer│ │          │ │Analyzer │ │  Agents       │
└────┬───┘ └────┬───┘ └────┬─────┘ └────┬────┘ └───────┬───────┘
     │          │          │             │             │
     └──────────┴──────────┴─────────────┴─────────────┘
                           │
          ┌────────────────┴────────────────────┐
          │                                     │
      ┌───▼───────┐                    ┌────────▼──────┐
      │ LLM Client│                    │   Execution   │
      │  (Claude) │                    │    Engine     │
      └───┬───────┘                    └────────┬──────┘
          │                                     │
      ┌───▼──────────────┐              ┌──────▼────────┐
      │  Cache Manager   │              │Docker Sandbox │
      │ (30%+ savings)   │              │ (Code Safety) │
      └──────────────────┘              └───────────────┘
                           │
          ┌────────────────┴──────────────────┐
          │                                   │
      ┌───▼──────┐                    ┌───────▼───────┐
      │Neo4j KB  │                    │SQLite/Postgres│
      │  Graph   │                    │   Database    │
      └──────────┘                    └───────────────┘
```

### Key Components

- **CLI Layer**: Beautiful terminal interface using Typer and Rich
- **Research Director**: Orchestrates the autonomous research workflow
- **Agent Framework**: Specialized agents for different research tasks
- **LLM Client**: Claude interface with intelligent caching
- **Execution Engine**: Safe, sandboxed code execution
- **Domain System**: Domain-specific tools and knowledge bases
- **Knowledge Graph**: Neo4j for structured knowledge representation
- **Database**: SQLAlchemy for research data persistence

---

## System Design Principles

### 1. Autonomy

Kosmos operates autonomously with minimal human intervention:

- Self-directed hypothesis generation
- Automatic experiment design
- Iterative refinement based on results
- Convergence detection

### 2. Safety

Multiple layers ensure safe code execution:

- AST-based code validation
- Docker containerization
- Resource limits (CPU, memory, time)
- Network isolation

### 3. Efficiency

Optimized for cost and performance:

- Multi-tier caching (30%+ API cost reduction)
- Intelligent model selection (Haiku vs Sonnet)
- Parallel experiment execution
- Request batching

### 4. Extensibility

Designed for easy extension:

- Plugin-based domain system
- Abstract agent base class
- Configurable experiment templates
- Custom tool integration

### 5. Observability

Comprehensive monitoring and logging:

- Structured logging with context
- API usage metrics
- Cost tracking with budget alerts
- Progress visualization

---

## Core Infrastructure

### LLM Client

**Location**: `kosmos/core/llm.py`

The LLM client provides a unified interface to Claude with two operating modes:

#### API Mode

Direct API calls to Anthropic's Claude API:

```python
from kosmos.core.llm import get_claude_client

client = get_claude_client()
response = client.chat(
    message="What are protein folding mechanisms?",
    max_tokens=4096,
    temperature=1.0,
    enable_cache=True  # Use caching system
)
```

**Features**:
- Automatic retry with exponential backoff
- Rate limiting
- Token counting
- Cache integration
- Streaming support

#### CLI Mode

Uses Claude Code (CLI) for local development:

```python
# Configured via environment variable
CLAUDE_MODE=cli

# Client automatically detects and uses CLI
response = client.chat(message)
```

**Benefits**:
- No API key required during development
- Faster iteration
- Local prompt testing

### Configuration System

**Location**: `kosmos/config.py`

Type-safe configuration using Pydantic:

```python
from pydantic import BaseSettings, Field

class ClaudeConfig(BaseSettings):
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 1.0
    enable_cache: bool = True
    is_cli_mode: bool = False

class ResearchConfig(BaseSettings):
    max_iterations: int = 10
    enabled_domains: List[str] = []
    budget_usd: Optional[float] = None
    auto_model_selection: bool = True
```

**Configuration Sources** (in priority order):
1. Environment variables
2. `.env` file
3. Configuration file (`~/.kosmos/config.yml`)
4. Default values

### Logging System

**Location**: `kosmos/core/logging.py`

Structured logging with context:

```python
import logging
from kosmos.core.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Hypothesis generated",
    extra={
        "research_run_id": "run_123",
        "hypothesis_id": "hyp_456",
        "novelty_score": 0.85
    }
)
```

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General information about system operation
- WARNING: Warning messages for recoverable issues
- ERROR: Error messages for failures
- CRITICAL: Critical failures requiring immediate attention

**Log Destinations**:
- Console (with Rich formatting in CLI)
- File (`~/.kosmos/logs/kosmos.log`)
- External logging service (configurable)

### Metrics Tracking

**Location**: `kosmos/core/metrics.py`

Comprehensive API and research metrics:

```python
from kosmos.core.metrics import MetricsTracker

tracker = MetricsTracker()

# Record API call
tracker.record_api_call(
    model="claude-3-5-sonnet-20241022",
    input_tokens=100,
    output_tokens=200,
    cache_hit=True,
    latency_ms=1500
)

# Get summary
summary = tracker.get_summary()
# {
#   "total_calls": 150,
#   "total_input_tokens": 50000,
#   "total_output_tokens": 75000,
#   "cache_hits": 45,
#   "cache_hit_rate": 0.30,
#   "total_cost_usd": 15.50,
#   "cost_saved_usd": 4.65
# }
```

**Tracked Metrics**:
- API calls (count, tokens, cost)
- Cache performance (hits, misses, savings)
- Research iterations
- Experiment success/failure rates
- Execution times
- Resource usage

---

## Caching System

**Locations**: `kosmos/core/cache.py`, `kosmos/core/cache_manager.py`, `kosmos/core/claude_cache.py`, `kosmos/core/experiment_cache.py`

Multi-tier caching system reducing API costs by 30%+.

### Architecture

```
┌────────────────────────────────────────────┐
│          Cache Manager                      │
│  (Orchestrates all cache types)            │
└────┬───────────┬───────────┬──────────┬────┘
     │           │           │          │
     ▼           ▼           ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│ Claude  │ │Experim  │ │Embedding│ │ General  │
│ Cache   │ │  ent    │ │ Cache   │ │  Cache   │
│         │ │ Cache   │ │         │ │          │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘
     │           │           │          │
     └───────────┴───────────┴──────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼─────┐          ┌──────▼────┐
    │In-Memory│          │   Disk    │
    │  Cache  │          │   Cache   │
    └─────────┘          └───────────┘
```

### Cache Types

#### 1. Claude Cache

**Purpose**: Cache LLM responses

**Strategy**:
- Key: Hash of (prompt + model + parameters)
- TTL: 7 days
- Storage: Hybrid (memory + disk)

```python
from kosmos.core.claude_cache import get_claude_cache

cache = get_claude_cache()

# Cache stores response
response = client.chat(message, enable_cache=True)

# Subsequent identical request hits cache
response2 = client.chat(message, enable_cache=True)  # Cache hit!
```

#### 2. Experiment Cache

**Purpose**: Cache experiment results

**Strategy**:
- Key: Hash of (experiment_type + parameters + data_hash)
- TTL: 30 days
- Storage: Disk (results can be large)

```python
from kosmos.core.experiment_cache import get_experiment_cache

cache = get_experiment_cache()

# Check cache before running experiment
cache_key = cache.generate_key(experiment)
result = cache.get(cache_key)

if result is None:
    # Run experiment
    result = executor.execute(experiment)
    # Cache result
    cache.set(cache_key, result, ttl_days=30)
```

#### 3. Embedding Cache

**Purpose**: Cache vector embeddings

**Strategy**:
- Key: Hash of text
- TTL: 90 days
- Storage: Memory (fast lookups)

#### 4. General Cache

**Purpose**: Cache miscellaneous data (API responses, literature searches, etc.)

**Strategy**:
- Key: Custom per use case
- TTL: Configurable
- Storage: Hybrid

### Cache Manager

Orchestrates all caches:

```python
from kosmos.core.cache_manager import get_cache_manager

manager = get_cache_manager()

# Get statistics for all caches
stats = manager.get_stats()
for cache_type, cache_stats in stats.items():
    print(f"{cache_type}:")
    print(f"  Hits: {cache_stats['hits']}")
    print(f"  Misses: {cache_stats['misses']}")
    print(f"  Hit rate: {cache_stats['hit_rate']:.2%}")

# Health check
health = manager.health_check()
for cache_type, status in health.items():
    if not status['healthy']:
        print(f"Cache {cache_type} unhealthy: {status['details']}")

# Cleanup expired entries
removed = manager.cleanup_expired()
print(f"Removed {sum(removed.values())} expired entries")

# Clear specific cache
manager.clear_cache('claude')

# Clear all caches
manager.clear_all()
```

### Cache Statistics

Real-time cache performance tracking:

- **Hit Rate**: Percentage of requests served from cache
- **Miss Rate**: Percentage requiring fresh computation
- **Storage Size**: Disk space used by cache
- **Entry Count**: Number of cached items
- **Cost Savings**: Estimated savings from cache hits

**Typical Performance**:
- Claude Cache: 25-35% hit rate
- Experiment Cache: 40-50% hit rate
- Overall API cost reduction: 30%+

### Cache Eviction

Caches use LRU (Least Recently Used) eviction with TTL:

```python
# Configure cache size and TTL
cache = HybridCache(
    max_memory_mb=512,      # 512 MB in-memory
    max_disk_mb=5120,       # 5 GB on disk
    default_ttl_days=7      # Expire after 7 days
)
```

When limits are reached:
1. Check TTL - remove expired entries first
2. If still over limit, evict LRU entries
3. Disk cache evicted before memory cache

---

## Agent Framework

**Locations**: `kosmos/agents/base.py`, `kosmos/agents/registry.py`, `kosmos/agents/*`

### Agent Architecture

All agents inherit from `BaseAgent`:

```python
from kosmos.agents.base import BaseAgent
from typing import Dict, Any, Optional

class BaseAgent:
    """Abstract base class for all agents."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.llm_client = get_claude_client()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main logic."""
        raise NotImplementedError

    def save_state(self, run_id: str) -> None:
        """Save agent state for resumption."""
        pass

    @classmethod
    def load_state(cls, run_id: str) -> 'BaseAgent':
        """Load agent from saved state."""
        pass
```

### Specialized Agents

#### Research Director Agent

**Location**: `kosmos/agents/research_director.py`

Orchestrates the entire research workflow:

```python
class ResearchDirectorAgent(BaseAgent):
    """Orchestrates autonomous research."""

    def conduct_research(
        self,
        question: str,
        domain: str,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Main research loop."""

        # Initialize state
        self.state = ResearchState.INITIALIZING
        run_id = self.create_research_run(question, domain)

        for iteration in range(max_iterations):
            self.state = ResearchState.RUNNING

            # Generate hypotheses
            hypotheses = self.hypothesis_generator.generate(
                question=question,
                domain=domain,
                context=self.get_context()
            )

            # Design experiments
            experiments = self.experiment_designer.design(
                hypotheses=hypotheses,
                domain=domain
            )

            # Execute experiments
            results = self.execute_experiments(experiments)

            # Analyze results
            analysis = self.data_analyst.analyze(results)

            # Update knowledge and refine hypotheses
            self.update_knowledge(analysis)
            refined_hypotheses = self.refine_hypotheses(hypotheses, analysis)

            # Check convergence
            if self.convergence_detector.has_converged(
                iteration=iteration,
                hypotheses=refined_hypotheses,
                results=results
            ):
                break

        self.state = ResearchState.COMPLETED
        return self.compile_results(run_id)
```

**Responsibilities**:
- Workflow orchestration
- State management
- Agent coordination
- Result compilation

#### Hypothesis Generator Agent

**Location**: `kosmos/agents/hypothesis_generator.py`

Generates scientifically plausible hypotheses:

```python
class HypothesisGeneratorAgent(BaseAgent):
    """Generates hypotheses from research questions."""

    def generate(
        self,
        question: str,
        domain: str,
        context: Dict[str, Any],
        num_hypotheses: int = 5
    ) -> List[Hypothesis]:
        """Generate hypotheses."""

        # Get domain-specific prompt template
        prompt_template = self.get_prompt_template(domain)

        # Incorporate existing knowledge
        knowledge_context = self.knowledge_graph.get_context(question, domain)

        # Generate with Claude
        prompt = prompt_template.format(
            question=question,
            context=context,
            knowledge=knowledge_context,
            num_hypotheses=num_hypotheses
        )

        response = self.llm_client.chat(
            message=prompt,
            max_tokens=4096,
            temperature=1.0
        )

        # Parse hypotheses from response
        hypotheses = self.parse_hypotheses(response)

        # Evaluate novelty and testability
        for hyp in hypotheses:
            hyp.novelty_score = self.novelty_checker.check(hyp, domain)
            hyp.testability_score = self.testability_evaluator.evaluate(hyp)

        # Prioritize
        prioritized = self.prioritizer.prioritize(hypotheses)

        return prioritized
```

**Responsibilities**:
- Hypothesis generation
- Novelty assessment
- Testability evaluation
- Prioritization

#### Experiment Designer Agent

**Location**: `kosmos/agents/experiment_designer.py`

Designs computational experiments:

```python
class ExperimentDesignerAgent(BaseAgent):
    """Designs experiments to test hypotheses."""

    def design(
        self,
        hypotheses: List[Hypothesis],
        domain: str
    ) -> List[Experiment]:
        """Design experiments."""

        experiments = []

        for hypothesis in hypotheses:
            # Get domain tools
            tools = self.get_domain_tools(domain)

            # Design experiment with Claude
            prompt = self.create_design_prompt(
                hypothesis=hypothesis,
                available_tools=tools,
                domain=domain
            )

            response = self.llm_client.chat(message=prompt)

            # Parse experiment design
            experiment = self.parse_experiment(response)
            experiment.hypothesis_id = hypothesis.id

            # Validate design
            if self.validate_experiment(experiment):
                experiments.append(experiment)

        return experiments
```

**Responsibilities**:
- Experiment design
- Tool selection
- Parameter configuration
- Design validation

#### Data Analyst Agent

**Location**: `kosmos/agents/data_analyst.py`

Analyzes experimental results:

```python
class DataAnalystAgent(BaseAgent):
    """Analyzes experiment results."""

    def analyze(
        self,
        results: List[ExperimentResult]
    ) -> Dict[str, Any]:
        """Analyze results."""

        analyses = []

        for result in results:
            # Statistical analysis
            stats = self.compute_statistics(result)

            # Interpret with Claude
            interpretation = self.interpret_results(result, stats)

            # Extract insights
            insights = self.extract_insights(interpretation)

            analyses.append({
                "result_id": result.id,
                "statistics": stats,
                "interpretation": interpretation,
                "insights": insights
            })

        # Synthesize across all results
        synthesis = self.synthesize_results(analyses)

        return {
            "individual_analyses": analyses,
            "synthesis": synthesis
        }
```

**Responsibilities**:
- Statistical analysis
- Result interpretation
- Insight extraction
- Cross-result synthesis

#### Literature Analyzer Agent

**Location**: `kosmos/agents/literature_analyzer.py`

Integrates scientific literature:

```python
class LiteratureAnalyzerAgent(BaseAgent):
    """Analyzes scientific literature."""

    def analyze(
        self,
        query: str,
        domain: str,
        max_papers: int = 50
    ) -> Dict[str, Any]:
        """Analyze literature."""

        # Search literature
        papers = self.search_literature(query, domain, max_papers)

        # Extract key information
        key_info = self.extract_information(papers)

        # Identify themes
        themes = self.identify_themes(key_info)

        # Find knowledge gaps
        gaps = self.find_gaps(themes, query)

        # Update knowledge graph
        self.update_knowledge_graph(papers, themes)

        return {
            "papers": papers,
            "themes": themes,
            "gaps": gaps,
            "key_findings": key_info
        }
```

**Responsibilities**:
- Literature search
- Information extraction
- Theme identification
- Gap analysis
- Knowledge graph updates

### Agent Communication

Agents communicate through typed messages:

```python
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AgentMessage:
    """Base message type."""
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]

@dataclass
class HypothesisMessage(AgentMessage):
    """Hypothesis generation message."""
    hypotheses: List[Hypothesis]
    confidence: float

@dataclass
class ExperimentMessage(AgentMessage):
    """Experiment design message."""
    experiments: List[Experiment]
    estimated_cost: float
```

### Agent Registry

**Location**: `kosmos/agents/registry.py`

Manages agent discovery and lifecycle:

```python
from kosmos.agents.registry import AgentRegistry

registry = AgentRegistry()

# Register agent
registry.register("hypothesis_generator", HypothesisGeneratorAgent)

# Get agent instance
agent = registry.get("hypothesis_generator", config=config)

# List available agents
agents = registry.list_agents()
```

---

## Research Workflow

### Workflow States

```python
from enum import Enum

class ResearchState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    ANALYZING = "analyzing"
    REFINING = "refining"
    CONVERGED = "converged"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
```

### Workflow State Machine

**Location**: `kosmos/core/workflow.py`

```
┌─────────────┐
│ INITIALIZING│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   RUNNING   │◄────┐
└──────┬──────┘     │
       │            │
       ▼            │
┌─────────────┐     │
│  ANALYZING  │     │
└──────┬──────┘     │
       │            │
       ▼            │
┌─────────────┐     │
│  REFINING   │─────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  CONVERGED  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  COMPLETED  │
└─────────────┘
```

### Research Loop

```python
def research_loop(self, question: str, domain: str, max_iterations: int):
    """Main research loop."""

    iteration = 0
    converged = False

    while iteration < max_iterations and not converged:
        # State: RUNNING
        self.state = ResearchState.RUNNING

        # 1. Generate/refine hypotheses
        if iteration == 0:
            hypotheses = self.generate_initial_hypotheses(question, domain)
        else:
            hypotheses = self.refine_hypotheses(previous_hypotheses, previous_results)

        # 2. Design experiments
        experiments = self.design_experiments(hypotheses, domain)

        # 3. Execute experiments
        results = []
        for experiment in experiments:
            result = self.execute_experiment(experiment)
            results.append(result)

        # State: ANALYZING
        self.state = ResearchState.ANALYZING

        # 4. Analyze results
        analysis = self.analyze_results(results)

        # State: REFINING
        self.state = ResearchState.REFINING

        # 5. Update knowledge
        self.update_knowledge_graph(hypotheses, results, analysis)

        # 6. Check convergence
        converged = self.check_convergence(
            iteration=iteration,
            hypotheses=hypotheses,
            results=results,
            history=self.get_history()
        )

        iteration += 1

    # State: CONVERGED or COMPLETED
    if converged:
        self.state = ResearchState.CONVERGED
    else:
        self.state = ResearchState.COMPLETED

    return self.compile_final_report()
```

### Convergence Detection

**Location**: `kosmos/core/convergence.py`

Determines when research has reached stable conclusions:

```python
class ConvergenceDetector:
    """Detects research convergence."""

    def has_converged(
        self,
        iteration: int,
        hypotheses: List[Hypothesis],
        results: List[ExperimentResult],
        history: List[Dict]
    ) -> bool:
        """Check if research has converged."""

        # Multiple convergence criteria
        criteria_met = 0

        # 1. Hypothesis stability
        if self.hypotheses_stable(hypotheses, history):
            criteria_met += 1

        # 2. Result consistency
        if self.results_consistent(results, history):
            criteria_met += 1

        # 3. Diminishing returns
        if self.diminishing_returns(results, history):
            criteria_met += 1

        # 4. High confidence
        if self.high_confidence(hypotheses):
            criteria_met += 1

        # Converged if 3 out of 4 criteria met
        return criteria_met >= 3
```

---

## Execution Engine

**Locations**: `kosmos/execution/code_generator.py`, `kosmos/execution/executor.py`, `kosmos/execution/analyzer.py`

### Execution Pipeline

```
Experiment Design
       │
       ▼
Code Generation ──► Validation ──► Docker Build
                       │               │
                       │               ▼
                       └─────► Execution in Sandbox
                                       │
                                       ▼
                              Resource Monitoring
                                       │
                                       ▼
                               Result Collection
                                       │
                                       ▼
                               Result Analysis
```

### Code Generation

**Location**: `kosmos/execution/code_generator.py`

Generates executable Python code from experiment designs:

```python
class CodeGenerator:
    """Generates executable code from experiments."""

    def generate(
        self,
        experiment_type: str,
        parameters: Dict[str, Any],
        domain: str
    ) -> str:
        """Generate code."""

        # Get template for experiment type
        template = self.get_template(experiment_type, domain)

        # Fill in parameters
        code = template.format(**parameters)

        # Add imports
        code = self.add_imports(code, domain)

        # Add error handling
        code = self.add_error_handling(code)

        # Validate syntax
        if not self.validate_syntax(code):
            raise CodeGenerationError("Invalid syntax")

        return code
```

### Code Execution

**Location**: `kosmos/execution/executor.py`

Safely executes code in Docker containers:

```python
class Executor:
    """Executes code in sandboxed containers."""

    def __init__(
        self,
        docker_image: str = "kosmos-sandbox",
        resource_limits: ResourceLimits = None
    ):
        self.docker_image = docker_image
        self.resource_limits = resource_limits or ResourceLimits()
        self.docker_client = docker.from_env()

    def execute(
        self,
        code: str,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute code."""

        # Validate code first
        validator = CodeValidator()
        if not validator.validate(code).is_safe:
            raise SecurityError("Code failed safety validation")

        # Create temporary directory for I/O
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input"
            output_path = Path(tmpdir) / "output"
            input_path.mkdir()
            output_path.mkdir()

            # Write input data
            with open(input_path / "data.json", "w") as f:
                json.dump(input_data, f)

            # Write code
            code_path = input_path / "script.py"
            code_path.write_text(code)

            # Run container
            container = self.docker_client.containers.run(
                image=self.docker_image,
                command=f"python /input/script.py",
                volumes={
                    str(input_path): {"bind": "/input", "mode": "ro"},
                    str(output_path): {"bind": "/output", "mode": "rw"}
                },
                mem_limit=f"{self.resource_limits.max_memory_mb}m",
                cpu_count=self.resource_limits.max_cpu_time_seconds,
                network_disabled=not self.resource_limits.network_access,
                detach=True
            )

            # Wait for completion with timeout
            try:
                exit_code = container.wait(
                    timeout=self.resource_limits.max_cpu_time_seconds
                )

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode()
                stderr = container.logs(stdout=False, stderr=True).decode()

                # Read output
                output_file = output_path / "result.json"
                if output_file.exists():
                    output = json.loads(output_file.read_text())
                else:
                    output = {"stdout": stdout, "stderr": stderr}

                return ExecutionResult(
                    success=(exit_code == 0),
                    output=output,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code
                )

            except docker.errors.Timeout:
                container.kill()
                return ExecutionResult(
                    success=False,
                    error="Execution timed out"
                )
            finally:
                container.remove()
```

### Resource Limits

**Location**: `kosmos/safety/limits.py`

```python
@dataclass
class ResourceLimits:
    """Resource limits for execution."""
    max_cpu_time_seconds: int = 300     # 5 minutes
    max_memory_mb: int = 4096           # 4 GB
    max_disk_mb: int = 1024             # 1 GB
    max_processes: int = 10             # Max processes
    network_access: bool = False        # No network by default
    allow_gpu: bool = False             # No GPU by default
```

---

## CLI Layer

**Locations**: `kosmos/cli/main.py`, `kosmos/cli/interactive.py`, `kosmos/cli/commands/*`

### CLI Architecture

```
kosmos (Typer App)
  │
  ├─ version          (Show version info)
  ├─ info             (System information)
  ├─ doctor           (Diagnostic checks)
  │
  ├─ run              (Execute research)
  │   ├─ --interactive
  │   ├─ --domain
  │   ├─ --max-iterations
  │   ├─ --budget
  │   └─ --output
  │
  ├─ status           (Show research status)
  │   ├─ --watch
  │   └─ --details
  │
  ├─ history          (Browse past runs)
  │   ├─ --limit
  │   ├─ --domain
  │   ├─ --status
  │   └─ --days
  │
  ├─ cache            (Manage caching)
  │   ├─ --stats
  │   ├─ --health
  │   ├─ --optimize
  │   └─ --clear
  │
  └─ config           (View/validate config)
      ├─ --show
      ├─ --validate
      └─ --path
```

### Theme System

**Location**: `kosmos/cli/themes.py`

```python
from rich.theme import Theme

KOSMOS_THEME = Theme({
    # Status colors
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold cyan",

    # Domain colors
    "domain.biology": "green",
    "domain.neuroscience": "magenta",
    "domain.materials": "cyan",
    "domain.physics": "blue",
    "domain.chemistry": "yellow",
    "domain.general": "white",

    # UI elements
    "h1": "bold bright_blue underline",
    "h2": "bold bright_blue",
    "muted": "dim",
    "highlight": "bold bright_yellow",
})

ICONS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "rocket": "🚀",
    "flask": "🧪",
    "brain": "🧠",
    "dna": "🧬",
    "atom": "⚛",
    "microscope": "🔬",
}
```

### Interactive Mode

**Location**: `kosmos/cli/interactive.py`

Guided research configuration:

```python
def run_interactive_mode() -> Optional[Dict]:
    """Interactive research setup."""

    # Show welcome
    show_welcome()

    # Select domain
    domain = select_domain()  # Rich table with 6 domains

    # Show example questions
    show_examples(domain)

    # Get research question
    question = get_research_question(domain)

    # Configure parameters
    params = configure_research_parameters()
    # - Max iterations (IntPrompt)
    # - Budget (optional, float)
    # - Cache enabled (Confirm)
    # - Auto model selection (Confirm)
    # - Parallel execution (Confirm)

    # Show configuration summary
    show_configuration_summary(domain, question, params)

    # Final confirmation
    if not confirm_and_start():
        return None

    return {
        "domain": domain,
        "question": question,
        **params
    }
```

### Progress Visualization

**Location**: `kosmos/cli/commands/run.py`

```python
from rich.progress import Progress, SpinnerColumn, BarColumn

def run_with_progress(director, question, max_iterations):
    """Run research with live progress."""

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )

    # Create progress bars
    hypothesis_task = progress.add_task(
        "[cyan]Generating hypotheses...",
        total=100
    )
    experiment_task = progress.add_task(
        "[yellow]Designing experiments...",
        total=100
    )
    execution_task = progress.add_task(
        "[green]Executing experiments...",
        total=100
    )
    iteration_task = progress.add_task(
        "[bright_blue]Research progress...",
        total=max_iterations
    )

    with Live(progress, console=console, refresh_per_second=4):
        results = director.conduct_research(
            question=question,
            max_iterations=max_iterations,
            progress_callback=lambda phase, pct: progress.update(
                task_map[phase], completed=pct
            )
        )

    return results
```

---

## Domain System

**Locations**: `kosmos/domains/*/`

### Domain Structure

Each domain module contains:

```
kosmos/domains/<domain>/
  ├─ __init__.py           # Domain exports
  ├─ apis.py               # External API clients
  ├─ tools.py              # Domain-specific tools
  ├─ prompts.py            # Prompt templates
  └─ ontology.py           # Knowledge structures (optional)
```

### Supported Domains

1. **Biology** (`kosmos/domains/biology/`)
   - KEGG, UniProt, GWAS Catalog, GTEx, ENCODE, dbSNP, Ensembl, HMDB, MetaboLights, PDB
   - Gene expression analysis, pathway analysis, genomics tools

2. **Neuroscience** (`kosmos/domains/neuroscience/`)
   - FlyWire, Allen Brain Atlas, NeuroMorpho
   - Connectivity analysis, neuroanatomy tools

3. **Materials Science** (`kosmos/domains/materials/`)
   - Materials Project API
   - Property prediction, optimization, ontology

4. **Physics** (`kosmos/domains/physics/`)
   - Physical constants, unit conversions
   - Simulation tools

5. **Chemistry** (`kosmos/domains/chemistry/`)
   - Molecular tools, RDKit integration
   - Reaction analysis

6. **General** (`kosmos/domains/general/`)
   - Cross-domain tools
   - Statistical analysis, plotting

### Domain Router

**Location**: `kosmos/core/domain_router.py`

Routes questions to appropriate domains:

```python
class DomainRouter:
    """Routes questions to domains."""

    def route(self, question: str) -> str:
        """Determine domain from question."""

        # Use Claude to classify
        prompt = f"""
        Classify this research question into one domain:

        Question: {question}

        Domains:
        - biology: genetics, proteins, cells, diseases
        - neuroscience: brain, neurons, cognition
        - materials: materials science, chemistry
        - physics: physical systems, mechanics
        - chemistry: molecules, reactions
        - general: other or multi-domain

        Return only the domain name.
        """

        response = self.llm_client.chat(prompt)
        domain = response.strip().lower()

        if domain not in SUPPORTED_DOMAINS:
            domain = "general"

        return domain
```

---

## Knowledge Integration

### Knowledge Graph

**Location**: `kosmos/knowledge/graph.py`

Neo4j-based knowledge graph:

```python
from kosmos.knowledge.graph import KnowledgeGraph

kg = KnowledgeGraph()

# Add entity
kg.add_entity(
    entity_type="protein",
    entity_id="TP53",
    properties={"name": "p53", "function": "tumor suppressor"}
)

# Add relationship
kg.add_relationship(
    source_id="TP53",
    relationship="prevents",
    target_id="cancer",
    properties={"confidence": 0.95}
)

# Query
related = kg.get_related_entities("TP53", max_depth=2)
```

### Embeddings

**Location**: `kosmos/knowledge/embeddings.py`

Vector embeddings for semantic search:

```python
from kosmos.knowledge.embeddings import EmbeddingEngine

embedder = EmbeddingEngine()

# Embed documents
embeddings = embedder.embed_documents(documents)

# Search
query_embedding = embedder.embed_query("protein folding")
similar = embedder.find_similar(query_embedding, embeddings, top_k=10)
```

---

## Data Flow

### Research Data Flow

```
User Question
     │
     ▼
Domain Router ──► Select Domain
     │
     ▼
Hypothesis Generator
     │
     ├──► Knowledge Graph (context)
     ├──► Literature (context)
     └──► Claude (generation)
     │
     ▼
Hypotheses [novelty, priority]
     │
     ▼
Experiment Designer
     │
     ├──► Domain Tools
     └──► Claude (design)
     │
     ▼
Experiments [type, parameters]
     │
     ▼
Code Generator ──► Code
     │
     ▼
Executor (Docker Sandbox)
     │
     ▼
Results
     │
     ▼
Data Analyst
     │
     ├──► Statistics
     ├──► Visualization
     └──► Claude (interpretation)
     │
     ▼
Analysis & Insights
     │
     ├──► Update Knowledge Graph
     ├──► Refine Hypotheses
     └──► Check Convergence
     │
     ▼
[Iterate or Complete]
```

### Cache Interaction Points

1. **LLM Calls**: All Claude API calls check cache first
2. **Experiment Execution**: Check if identical experiment was run
3. **Literature Search**: Cache search results
4. **Embeddings**: Cache vector embeddings
5. **Knowledge Graph Queries**: Cache common queries

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────┐
│   Developer Machine                 │
│                                     │
│  ┌────────────────┐                │
│  │ Kosmos CLI     │                │
│  └───────┬────────┘                │
│          │                          │
│  ┌───────▼────────┐                │
│  │ SQLite DB      │                │
│  └────────────────┘                │
│                                     │
│  ┌────────────────┐                │
│  │ Docker Sandbox │                │
│  └────────────────┘                │
│                                     │
│  External APIs:                     │
│  - Claude API                       │
│  - Domain APIs (KEGG, etc.)        │
└─────────────────────────────────────┘
```

### Production Deployment

```
┌────────────────────────────────────────────┐
│   Load Balancer                             │
└──────────┬─────────────────────────────────┘
           │
      ┌────┴────┐
      │         │
┌─────▼───┐ ┌──▼──────┐
│ Web UI  │ │ API     │
│ (Future)│ │ Server  │
└─────┬───┘ └──┬──────┘
      │        │
      └────┬───┘
           │
┌──────────▼─────────────────────────────────┐
│   Application Tier                          │
│  ┌──────────────────────────────────────┐  │
│  │ Kosmos Core (Python)                 │  │
│  │  - Research Director                 │  │
│  │  - Agents                            │  │
│  │  - LLM Client                        │  │
│  └──────────────────────────────────────┘  │
└──────────┬─────────────────────────────────┘
           │
      ┌────┴────┐
      │         │
┌─────▼───┐ ┌──▼─────────┐
│PostgreSQL│ │Neo4j       │
│Database │ │Knowledge   │
│         │ │Graph       │
└─────────┘ └────────────┘

┌──────────────────────────┐
│ Docker Execution Cluster │
│  - Sandboxed execution   │
│  - Auto-scaling          │
│  - Resource isolation    │
└──────────────────────────┘

External Services:
- Claude API (Anthropic)
- Domain APIs (KEGG, UniProt, etc.)
- Object Storage (results, plots)
```

### Scaling Considerations

1. **Stateless Application Tier**: Multiple instances behind load balancer
2. **Database**: PostgreSQL with replication
3. **Knowledge Graph**: Neo4j cluster
4. **Execution**: Kubernetes for Docker sandbox orchestration
5. **Caching**: Redis for distributed caching
6. **Object Storage**: S3/MinIO for results and artifacts

---

## Performance Characteristics

### Typical Research Run

- **Duration**: 30 minutes to 2 hours
- **Iterations**: 5-15
- **Hypotheses per iteration**: 3-5
- **Experiments per hypothesis**: 2-4
- **API calls**: 50-200
- **Cost**: $5-$50 (with caching)

### Cache Performance

- **Hit Rate**: 25-35%
- **Cost Savings**: 30-40%
- **Latency Reduction**: 90%+ on cache hits

### Resource Usage

- **CPU**: 2-4 cores typical, 8+ for parallel execution
- **Memory**: 2-8 GB typical
- **Disk**: 1-5 GB for cache and results
- **Network**: 10-100 MB per run

---

## Security

### Threat Model

1. **Malicious Code Generation**: Claude generates harmful code
2. **Resource Exhaustion**: Code consumes excessive resources
3. **Data Exfiltration**: Code attempts to steal data
4. **Privilege Escalation**: Code escapes sandbox

### Mitigations

1. **Code Validation**: AST analysis before execution
2. **Sandboxing**: Docker containers with resource limits
3. **Network Isolation**: No external network access
4. **Read-only Filesystem**: Most directories read-only
5. **Process Monitoring**: Kill processes exceeding limits
6. **Input Sanitization**: Validate all user inputs

---

## Future Architecture

### Planned Enhancements

1. **Distributed Execution**: Kubernetes-based execution cluster
2. **Multi-Agent Collaboration**: Agents working in parallel
3. **Real-time Streaming**: Live result streaming
4. **Web UI**: Browser-based interface
5. **Collaborative Features**: Multi-user research projects
6. **Enhanced Knowledge Graph**: Automated literature ingestion
7. **Model Fine-tuning**: Domain-specific fine-tuned models

---

## References

- [Claude API Documentation](https://docs.anthropic.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Neo4j Graph Database](https://neo4j.com/docs/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

---

*Last Updated: January 15, 2025*
*Version: 0.10.0*
