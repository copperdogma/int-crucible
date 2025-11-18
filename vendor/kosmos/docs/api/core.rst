Core Modules
============

The core modules provide the foundational infrastructure for Kosmos, including LLM communication,
configuration management, caching, logging, and metrics tracking.

LLM Client
----------

The LLM client provides a unified interface for communicating with Claude, supporting both
API mode and CLI mode with intelligent caching.

.. automodule:: kosmos.core.llm
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Configuration
-------------

Configuration management using Pydantic for type-safe settings and environment variable loading.

.. automodule:: kosmos.config
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Caching System
--------------

Multi-tier caching system with in-memory, disk, and hybrid caches for reducing API costs.

Base Cache
^^^^^^^^^^

.. automodule:: kosmos.core.cache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Cache Manager
^^^^^^^^^^^^^

.. automodule:: kosmos.core.cache_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Experiment Cache
^^^^^^^^^^^^^^^^

.. automodule:: kosmos.core.experiment_cache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Claude Cache
^^^^^^^^^^^^

.. automodule:: kosmos.core.claude_cache
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Logging
-------

Structured logging with support for multiple output formats and log levels.

.. automodule:: kosmos.core.logging
   :members:
   :undoc-members:
   :show-inheritance:

Metrics Tracking
----------------

API usage metrics, cost tracking, and performance monitoring.

.. automodule:: kosmos.core.metrics
   :members:
   :undoc-members:
   :show-inheritance:

Workflow Management
-------------------

State machine for research workflow orchestration.

.. automodule:: kosmos.core.workflow
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Feedback System
---------------

Feedback loop management for iterative hypothesis refinement.

.. automodule:: kosmos.core.feedback
   :members:
   :undoc-members:
   :show-inheritance:

Memory Management
-----------------

Working memory for agents to maintain context across iterations.

.. automodule:: kosmos.core.memory
   :members:
   :undoc-members:
   :show-inheritance:

Convergence Detection
---------------------

Detecting when research has converged to stable results.

.. automodule:: kosmos.core.convergence
   :members:
   :undoc-members:
   :show-inheritance:

Domain Router
-------------

Intelligent routing of questions to appropriate domain-specific agents.

.. automodule:: kosmos.core.domain_router
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

**Getting a configured LLM client**::

   from kosmos.core.llm import get_claude_client

   # Get client with default configuration
   client = get_claude_client()

   # Generate a response
   response = client.chat(
       "Explain photosynthesis",
       max_tokens=1000,
       enable_cache=True
   )

**Loading configuration**::

   from kosmos.config import get_config

   config = get_config()
   print(f"Model: {config.claude.model}")
   print(f"Max iterations: {config.research.max_iterations}")

**Using the cache manager**::

   from kosmos.core.cache_manager import get_cache_manager

   cache_mgr = get_cache_manager()

   # Get statistics
   stats = cache_mgr.get_stats()
   for cache_type, cache_stats in stats.items():
       print(f"{cache_type}: {cache_stats['hits']} hits, {cache_stats['misses']} misses")

   # Health check
   health = cache_mgr.health_check()

   # Optimize caches
   removed = cache_mgr.cleanup_expired()

**Tracking metrics**::

   from kosmos.core.metrics import MetricsTracker

   tracker = MetricsTracker()
   tracker.record_api_call(
       model="claude-3-5-sonnet-20241022",
       input_tokens=100,
       output_tokens=200,
       cache_hit=True
   )

   summary = tracker.get_summary()
   print(f"Total cost: ${summary['total_cost_usd']:.2f}")
