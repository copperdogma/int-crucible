Kosmos AI Scientist Documentation
===================================

**Kosmos** is a fully autonomous AI scientist powered by Claude that can generate hypotheses, design experiments, analyze results, and produce publication-quality research across multiple scientific domains.

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code Style

Features
--------

🧪 **Autonomous Research**
   Generate and test hypotheses across multiple domains

🔬 **Multi-Domain Support**
   Biology, neuroscience, materials science, physics, chemistry, and more

🤖 **Intelligent Agents**
   Specialized agents for hypothesis generation, experiment design, and analysis

📊 **Advanced Analytics**
   Statistical analysis, visualization, and result interpretation

💾 **Smart Caching**
   Reduce API costs by 30%+ with intelligent caching

🎨 **Beautiful CLI**
   Rich terminal interface for interactive research

🔄 **Iterative Learning**
   Refine hypotheses based on experimental outcomes

📚 **Knowledge Integration**
   Neo4j knowledge graph and embeddings for literature synthesis

Quick Start
-----------

Installation::

   git clone https://github.com/yourusername/kosmos.git
   cd kosmos
   pip install -e .

Set up your API key::

   echo "ANTHROPIC_API_KEY=your_key_here" > .env

Run your first research::

   kosmos run --interactive

Or provide a question directly::

   kosmos run "What are the metabolic differences between cancer and normal cells?"

Monitor progress::

   kosmos status <run_id> --watch

Documentation Structure
-----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide
   cli_reference
   examples

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture
   domains
   agents
   caching

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/core
   api/agents
   api/domains
   api/execution
   api/hypothesis
   api/knowledge
   api/safety
   api/cli

.. toctree::
   :maxdepth: 2
   :caption: Development

   developer_guide
   contributing
   troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   license
   faq

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
