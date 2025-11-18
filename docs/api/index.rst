API Reference
=============

This section provides detailed API documentation for all Kosmos modules, generated automatically from docstrings.

Architecture Overview
---------------------

Kosmos is organized into several major subsystems:

**Core Infrastructure**
   Foundation modules for LLM client, configuration, caching, logging, and metrics

**Agent Framework**
   Base classes and specialized agents for autonomous research

**Domain System**
   Domain-specific tools, APIs, and knowledge bases for different scientific fields

**Execution Engine**
   Code generation, sandboxed execution, and result analysis

**Hypothesis Management**
   Hypothesis generation, novelty checking, prioritization, and testability evaluation

**Knowledge Integration**
   Neo4j graph database and embedding-based literature synthesis

**Safety & Validation**
   Code validation, resource limits, and safety checks

**CLI Interface**
   Beautiful command-line interface powered by Typer and Rich

Module Reference
----------------

.. toctree::
   :maxdepth: 2

   core
   agents
   domains
   execution
   hypothesis
   knowledge
   safety
   cli
   db

Quick Navigation
----------------

**Core Modules**
   :doc:`core` - LLM client, configuration, caching, metrics

**Agent Modules**
   :doc:`agents` - Research director, hypothesis generator, experiment designer

**Domain Modules**
   :doc:`domains` - Biology, neuroscience, materials science tools

**Execution Modules**
   :doc:`execution` - Code generation and sandboxed execution

**Hypothesis Modules**
   :doc:`hypothesis` - Hypothesis generation and evaluation

**Knowledge Modules**
   :doc:`knowledge` - Knowledge graph and embeddings

**Safety Modules**
   :doc:`safety` - Code validation and safety checks

**CLI Modules**
   :doc:`cli` - Command-line interface

**Database Modules**
   :doc:`db` - SQLAlchemy models and database operations

Common Patterns
---------------

**Using the LLM Client**::

   from kosmos.core.llm import get_claude_client

   client = get_claude_client()
   response = client.chat("What are protein folding mechanisms?")

**Creating a Research Run**::

   from kosmos.agents.research_director import ResearchDirectorAgent

   director = ResearchDirectorAgent()
   results = director.conduct_research("Your research question here")

**Accessing Domain Tools**::

   from kosmos.domains.biology.apis import KEGGClient

   kegg = KEGGClient()
   compound_data = kegg.get_compound("C00031")  # Glucose

**Using the Cache Manager**::

   from kosmos.core.cache_manager import get_cache_manager

   cache_mgr = get_cache_manager()
   stats = cache_mgr.get_stats()

Type Hints and Annotations
---------------------------

All public APIs use Python type hints for better IDE support and documentation.
Many functions also include detailed docstrings following Google/NumPy style.

Contributing
------------

When adding new modules:

1. Add comprehensive docstrings with parameter descriptions
2. Include type hints for all function signatures
3. Add usage examples in docstrings when helpful
4. Update this API reference with a new .rst file

See :doc:`../contributing` for full guidelines.
