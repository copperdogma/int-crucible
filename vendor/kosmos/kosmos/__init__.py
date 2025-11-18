"""
Kosmos AI Scientist - Autonomous scientific research powered by Claude.

A fully autonomous AI scientist system that can:
- Generate and test hypotheses across multiple domains
- Design and execute computational experiments
- Analyze results and synthesize insights
- Learn iteratively from outcomes
- Produce publication-quality research
"""

__version__ = "0.2.0"  # Multi-provider support (Anthropic, OpenAI)
__author__ = "Kosmos Development Team"
__license__ = "MIT"

# Expose key components at package level
from kosmos.config import get_config
from kosmos.agents.research_director import ResearchDirectorAgent

__all__ = [
    "__version__",
    "get_config",
    "ResearchDirectorAgent",
]
