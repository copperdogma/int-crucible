# Kosmos Examples

This directory contains example research projects demonstrating how to use Kosmos across different scientific domains.

## Quick Start

Each example is self-contained and can be run independently:

```bash
# Run an example
python examples/01_biology_metabolic_pathways.py

# Or use the CLI
kosmos run --interactive  # Follow prompts based on example
```

## Examples Overview

### Biology

1. **[Metabolic Pathways](01_biology_metabolic_pathways.py)** (~400 lines)
   - KEGG pathway analysis
   - Metabolite interactions
   - Enzyme activity correlations
   - **Difficulty**: Beginner
   - **Duration**: ~30 minutes
   - **Cost**: ~$5-10

2. **[Gene Expression Analysis](02_biology_gene_expression.py)** (~400 lines)
   - RNA-seq data analysis
   - Differential expression
   - Statistical testing
   - **Difficulty**: Intermediate
   - **Duration**: ~45 minutes
   - **Cost**: ~$10-15

### Neuroscience

3. **[Connectomics Analysis](03_neuroscience_connectomics.py)** (~450 lines)
   - Brain connectivity networks
   - FlyWire integration
   - Network metrics
   - **Difficulty**: Advanced
   - **Duration**: ~1 hour
   - **Cost**: ~$15-20

4. **[Neurodegeneration Research](04_neuroscience_neurodegeneration.py)** (~450 lines)
   - Disease mechanism analysis
   - Multi-modal data integration
   - Literature synthesis
   - **Difficulty**: Advanced
   - **Duration**: ~1.5 hours
   - **Cost**: ~$20-30

### Materials Science

5. **[Property Prediction](05_materials_property_prediction.py)** (~400 lines)
   - Materials Project integration
   - Property optimization
   - ML model training
   - **Difficulty**: Intermediate
   - **Duration**: ~45 minutes
   - **Cost**: ~$10-15

6. **[Parameter Optimization](06_materials_parameter_optimization.py)** (~400 lines)
   - Hyperparameter tuning
   - SHAP analysis
   - Multi-objective optimization
   - **Difficulty**: Advanced
   - **Duration**: ~1 hour
   - **Cost**: ~$15-20

### Cross-Domain

7. **[Multi-Domain Synthesis](07_multidomain_synthesis.py)** (~500 lines)
   - Combining biology and materials
   - Knowledge graph integration
   - Cross-domain insights
   - **Difficulty**: Advanced
   - **Duration**: ~2 hours
   - **Cost**: ~$25-35

### CLI Workflows

8. **[Interactive Workflow](08_cli_interactive_workflow.sh)** (~300 lines)
   - Complete CLI walkthrough
   - Monitoring and management
   - Result export
   - **Difficulty**: Beginner
   - **Duration**: ~20 minutes
   - **Cost**: Variable

9. **[Batch Research](09_cli_batch_research.sh)** (~300 lines)
   - Multiple research projects
   - Automation and scripting
   - Result aggregation
   - **Difficulty**: Intermediate
   - **Duration**: ~1 hour
   - **Cost**: Variable

### Advanced

10. **[Custom Domain Integration](10_advanced_custom_domain.py)** (~400 lines)
    - Creating custom domains
    - API integration
    - Template development
    - **Difficulty**: Expert
    - **Duration**: ~2 hours
    - **Cost**: Varies

## Prerequisites

### Required

- Kosmos installed and configured
- Python 3.9+ with virtual environment
- API key (Anthropic or Claude Code CLI)

### Optional

Some examples require additional setup:

- **KEGG examples**: No additional setup (free API)
- **UniProt examples**: No additional setup (free API)
- **Materials Project**: API key from [materialsproject.org](https://materialsproject.org/)
- **FlyWire**: Account at [flywire.ai](https://flywire.ai/)
- **Neo4j**: Local installation for knowledge graph examples

## Running Examples

### Option 1: Direct Execution

```bash
# Navigate to examples directory
cd examples/

# Run example
python 01_biology_metabolic_pathways.py
```

### Option 2: Interactive Mode

```bash
# Start Kosmos in interactive mode
kosmos run --interactive

# Select domain and provide question from example
# Follow the prompts
```

### Option 3: Copy and Modify

```bash
# Copy example to your project
cp examples/01_biology_metabolic_pathways.py my_research.py

# Edit with your specific question and parameters
nano my_research.py

# Run
python my_research.py
```

## Example Structure

Each example follows this structure:

```python
"""
Example: [Name]

Description: [What this example demonstrates]

Domain: [Scientific domain]
Difficulty: [Beginner/Intermediate/Advanced/Expert]
Duration: [Estimated runtime]
Cost: [Estimated API cost]

Prerequisites:
- [List of requirements]

Learning Objectives:
- [What you'll learn]
"""

# 1. Setup and imports
from kosmos import ResearchDirectorAgent
from kosmos.config import get_config

# 2. Configuration
config = get_config()
director = ResearchDirectorAgent(config=config)

# 3. Research question
question = "Your specific research question"

# 4. Run research
results = director.conduct_research(
    question=question,
    domain="domain_name",
    max_iterations=10
)

# 5. Analyze results
print_results(results)

# 6. Export (optional)
export_results(results, "output.json")
```

## Difficulty Levels

### Beginner
- Basic Kosmos usage
- Simple configurations
- Single-domain questions
- Standard experiment types

### Intermediate
- Multiple experiment types
- Custom configurations
- Multi-iteration research
- Result analysis

### Advanced
- Cross-domain research
- Knowledge graph integration
- Custom experiment templates
- Complex analyses

### Expert
- Custom domain creation
- API integration
- Advanced agent customization
- Production deployment

## Learning Path

**New to Kosmos? Follow this path:**

1. Start with `08_cli_interactive_workflow.sh` - Learn the CLI
2. Try `01_biology_metabolic_pathways.py` - Simple Python example
3. Progress to `02_biology_gene_expression.py` - More complex analysis
4. Explore domain-specific examples based on your field
5. Try `07_multidomain_synthesis.py` - Cross-domain research
6. Customize `10_advanced_custom_domain.py` - Create your own domain

## Common Patterns

### Pattern 1: Basic Research

```python
from kosmos import ResearchDirectorAgent

director = ResearchDirectorAgent()
results = director.conduct_research(
    question="Your question",
    domain="domain",
    max_iterations=5
)
```

### Pattern 2: With Configuration

```python
from kosmos import ResearchDirectorAgent
from kosmos.config import get_config

config = get_config()
config.research.max_iterations = 10
config.research.budget_usd = 25.0

director = ResearchDirectorAgent(config=config)
results = director.conduct_research(question="Your question")
```

### Pattern 3: With Monitoring

```python
from kosmos import ResearchDirectorAgent
from kosmos.cli.utils import print_progress

def progress_callback(phase, progress):
    print_progress(phase, progress)

director = ResearchDirectorAgent()
results = director.conduct_research(
    question="Your question",
    progress_callback=progress_callback
)
```

### Pattern 4: With Export

```python
from kosmos import ResearchDirectorAgent
from kosmos.cli.views.results_viewer import ResultsViewer

director = ResearchDirectorAgent()
results = director.conduct_research(question="Your question")

# Export results
viewer = ResultsViewer()
viewer.export_to_json(results, Path("results.json"))
viewer.export_to_markdown(results, Path("results.md"))
```

## Tips for Success

1. **Start Simple**: Begin with beginner examples and progress gradually
2. **Read Comments**: Each example has detailed inline comments explaining the code
3. **Modify Parameters**: Experiment with different configurations
4. **Monitor Costs**: Use `--budget` flag to limit spending
5. **Cache Enabled**: Keep caching enabled to reduce costs
6. **Check Results**: Always review results before drawing conclusions
7. **Iterate**: Research often requires multiple iterations to refine hypotheses

## Troubleshooting

### Example Won't Run

```bash
# Check Python environment
which python
# Should be in venv

# Reinstall Kosmos
pip install -e .

# Run diagnostics
kosmos doctor
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -e ".[dev]"

# For specific examples
pip install materialsproject  # For materials examples
pip install rdkit  # For chemistry examples
```

### API Errors

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Verify configuration
kosmos config --validate

# Test with simple CLI command
kosmos run "test question" --max-iterations 1
```

### Timeout Errors

```python
# Increase timeout in config
config.safety.max_execution_time = 600  # 10 minutes

# Or in .env
MAX_EXPERIMENT_EXECUTION_TIME=600
```

## Contributing Examples

Have a great example? Contribute it!

1. Follow the example structure above
2. Include detailed comments
3. Test thoroughly
4. Document prerequisites
5. Add to this README
6. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Example Output

Example results structure:

```json
{
  "run_id": "run_xyz789",
  "question": "What causes X?",
  "domain": "biology",
  "hypotheses": [
    {
      "claim": "Hypothesis statement",
      "novelty_score": 0.85,
      "status": "confirmed"
    }
  ],
  "experiments": [...],
  "findings": {
    "key_insights": [...],
    "recommendations": [...]
  },
  "metrics": {
    "cost_usd": 12.50,
    "duration_minutes": 45,
    "api_calls": 125
  }
}
```

## Additional Resources

- [User Guide](../docs/user_guide.md) - Complete usage documentation
- [API Reference](../docs/api/) - Detailed API documentation
- [Architecture](../docs/architecture.md) - System design
- [Developer Guide](../docs/developer_guide.md) - Extending Kosmos

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/kosmos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/kosmos/discussions)
- **Discord**: [Community Server](https://github.com/jimmc414/Kosmos/discussions)

---

For questions or support, see the troubleshooting guide or open an issue on GitHub.
