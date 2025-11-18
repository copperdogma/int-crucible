# Persistent Knowledge Graphs - User Guide

> Build cumulative scientific knowledge that survives between research sessions

## Overview

Kosmos maintains a **persistent knowledge graph** that automatically captures your research journey. Every hypothesis, experiment, and finding is stored in a connected graph that you can explore, export, and build upon over time.

### What Gets Captured

When you run research queries, Kosmos automatically persists:

- **Research Questions** - Your initial scientific inquiries
- **Hypotheses** - Generated hypotheses and their evolution
- **Experiment Protocols** - Designed experiments and methodologies
- **Experimental Results** - Findings and measurements
- **Relationships** - How everything connects (SPAWNED_BY, TESTS, SUPPORTS, REFUTES, REFINED_FROM)
- **Provenance** - Who, when, why for every entity and relationship

### Key Benefits

**Knowledge Accumulation**
Build expertise over weeks and months instead of starting fresh each session.

**Research Provenance**
Track how hypotheses evolved, which experiments tested them, and what the results showed.

**Collaboration**
Export your knowledge graph and share it with colleagues.

**Version Control**
Export graphs at milestones to track your research evolution.

**Data Safety**
Regular exports protect against data loss.

---

## Quick Start

### Viewing Your Knowledge Graph

Check your accumulated knowledge at any time:

```bash
# View statistics
kosmos graph --stats

# Example output:
# 📊 Knowledge Graph Statistics
#
# Entities:        127
# Relationships:   243
#
# Entity Types:
#   Hypothesis: 45
#   ExperimentProtocol: 28
#   ExperimentResult: 23
#   ResearchQuestion: 5
```

### Exporting Your Graph

Save your knowledge graph to a file:

```bash
# Export to JSON
kosmos graph --export my_research.json

# Export is human-readable JSON
cat my_research.json
```

**Export format:**
```json
{
  "version": "1.0",
  "exported_at": "2025-11-15T10:30:00",
  "source": "kosmos",
  "statistics": {
    "entity_count": 127,
    "relationship_count": 243
  },
  "entities": [
    {
      "id": "hyp_001",
      "type": "Hypothesis",
      "properties": {
        "statement": "Neural networks learn...",
        "domain": "machine_learning",
        "confidence_score": 0.85
      }
    }
  ],
  "relationships": [
    {
      "source_id": "hyp_001",
      "target_id": "question_001",
      "type": "SPAWNED_BY",
      "properties": {
        "agent": "HypothesisGeneratorAgent",
        "generation": 1,
        "iteration": 1
      }
    }
  ]
}
```

### Importing a Graph

Restore a previously exported graph:

```bash
# Import (merges with existing data)
kosmos graph --import my_research.json

# Clear and replace
kosmos graph --import my_research.json --clear
```

### Resetting the Graph

**⚠️ DANGEROUS** - Deletes all graph data:

```bash
# Will prompt for confirmation
kosmos graph --reset
```

---

## How It Works

### Automatic Persistence

No manual action needed! When you run research:

```bash
kosmos research "How do transformers learn long-range dependencies?"
```

Kosmos **automatically**:

1. Creates a **ResearchQuestion** entity
2. Generates hypotheses → Creates **Hypothesis** entities + **SPAWNED_BY** relationships
3. Designs experiments → Creates **ExperimentProtocol** entities + **TESTS** relationships
4. Runs experiments → Creates **ExperimentResult** entities + **PRODUCED_BY** relationships
5. Analyzes results → Creates **SUPPORTS/REFUTES** relationships with p-values, effect sizes
6. Refines hypotheses → Creates new **Hypothesis** entities + **REFINED_FROM** relationships

### Knowledge Graph Structure

```
ResearchQuestion
    ↑
    │ SPAWNED_BY
    │ - agent: HypothesisGeneratorAgent
    │ - generation: 1
    │
Hypothesis
    ↓
    │ TESTS
    │ - agent: ExperimentDesignerAgent
    │
ExperimentProtocol
    ↓
    │ PRODUCED_BY
    │ - agent: Executor
    │
ExperimentResult
    ↓
    │ SUPPORTS/REFUTES
    │ - agent: DataAnalystAgent
    │ - confidence: 0.95
    │ - p_value: 0.001
    │ - effect_size: 0.78
    │
Hypothesis (validates or refutes original)
```

### Dual Persistence

Kosmos uses **both** SQL and graph storage:

- **SQL Database** - Structured queries, ACID transactions, existing tools
- **Graph Database** - Relationship traversal, provenance, visualization

This means:
- ✅ Your existing workflows continue to work
- ✅ You get graph capabilities on top
- ✅ System works even if Neo4j is unavailable (graceful degradation)

---

## CLI Commands Reference

### `kosmos graph --stats`

Display knowledge graph statistics.

**Example:**
```bash
kosmos graph --stats

# Output:
# 📊 Knowledge Graph Statistics
#
# Entities:        127
# Relationships:   243
#
# Entity Types:
#   Hypothesis: 45
#   ExperimentProtocol: 28
#   ExperimentResult: 23
#   ResearchQuestion: 5
#
# Relationship Types:
#   SPAWNED_BY: 45
#   TESTS: 28
#   SUPPORTS: 15
#   REFUTES: 8
#   REFINED_FROM: 12
```

### `kosmos graph --export FILE`

Export knowledge graph to JSON file.

**Arguments:**
- `FILE` - Path to export file (e.g., `backup.json`)

**Example:**
```bash
# Export to current directory
kosmos graph --export research_nov15.json

# Export to specific path
kosmos graph --export /backups/research/graph_$(date +%Y%m%d).json
```

**Output:**
```
✅ Exported 127 entities and 243 relationships
   File: research_nov15.json
   Size: 2.3 MB
```

### `kosmos graph --import FILE [--clear]`

Import knowledge graph from JSON file.

**Arguments:**
- `FILE` - Path to import file
- `--clear` - (Optional) Clear existing graph before importing

**Example:**
```bash
# Merge with existing graph
kosmos graph --import colleague_research.json

# Replace entire graph
kosmos graph --import baseline_research.json --clear
```

**Output:**
```
✅ Import complete
   Entities: 127
   Relationships: 243
```

### `kosmos graph --reset`

Clear all knowledge graph data (requires confirmation).

**⚠️ WARNING:** This permanently deletes all graph data!

**Example:**
```bash
kosmos graph --reset

# Prompt:
# ⚠️  Delete all graph data? [y/N]: y
# ✅ Deleted 127 entities
```

---

## Setup and Configuration

### Installing Neo4j

#### Docker (Recommended)

```bash
# Using docker-compose (included in Kosmos)
docker-compose up -d neo4j

# Verify Neo4j is running
docker-compose ps
```

#### Manual Installation

**Ubuntu/Debian:**
```bash
sudo apt install neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

**macOS:**
```bash
brew install neo4j
neo4j start
```

**Windows:**
Download from [neo4j.com/download](https://neo4j.com/download)

### Configuration

Configure Neo4j connection in `.env`:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=kosmos-password
NEO4J_DATABASE=neo4j

# World Model Configuration
WORLD_MODEL_ENABLED=true
WORLD_MODEL_MODE=simple
```

### Verifying Setup

```bash
# Check Neo4j is accessible
neo4j status

# Or via browser
# Open: http://localhost:7474
# Login with credentials from .env

# Run a test query in Neo4j browser:
MATCH (n) RETURN count(n)
```

---

## Use Cases

### 1. Long-Term Knowledge Building

Build expertise over time instead of starting fresh:

```bash
# Week 1: Initial exploration
kosmos research "Neural network optimization techniques"
kosmos graph --export week1_baseline.json

# Week 2: Deep dive into specific area
kosmos research "Adam optimizer convergence properties"
kosmos graph --export week2_progress.json

# Week 3: Compare approaches
kosmos research "SGD vs Adam for transformer training"

# View accumulated knowledge
kosmos graph --stats
# Shows: 300+ entities spanning 3 weeks of research
```

### 2. Collaboration

Share research with colleagues:

```bash
# Export your findings
kosmos graph --export transformer_research.json

# Colleague imports and builds on it
kosmos graph --import transformer_research.json
kosmos research "Extending this work to vision transformers"
```

### 3. Research Checkpoints

Save snapshots at major milestones:

```bash
# After initial hypothesis generation
kosmos graph --export checkpoint_hypotheses.json

# After first round of experiments
kosmos graph --export checkpoint_experiments.json

# After convergence
kosmos graph --export checkpoint_final.json

# Track evolution
ls -lh checkpoint_*.json
# checkpoint_hypotheses.json   - 500 KB
# checkpoint_experiments.json  - 1.2 MB
# checkpoint_final.json        - 2.8 MB
```

### 4. Reproducibility

Reproduce a research session exactly:

```bash
# Save session state
kosmos graph --export session_20251115.json

# Later, restore and continue
kosmos graph --import session_20251115.json --clear
kosmos research "Continue from where we left off"
```

### 5. Backup and Recovery

Protect against data loss:

```bash
# Automated backup (add to cron)
#!/bin/bash
DATE=$(date +%Y%m%d)
kosmos graph --export /backups/kosmos_$DATE.json

# Keep last 30 days
find /backups -name "kosmos_*.json" -mtime +30 -delete

# Recovery
kosmos graph --import /backups/kosmos_20251115.json --clear
```

---

## Advanced Topics

### Querying the Graph Directly

For advanced users, query Neo4j directly via Cypher:

```bash
# Open Neo4j browser
open http://localhost:7474

# Find all supported hypotheses
MATCH (r:ExperimentResult)-[rel:SUPPORTS]->(h:Hypothesis)
WHERE rel.confidence > 0.9
RETURN h.statement, rel.confidence, rel.p_value

# Trace hypothesis evolution
MATCH path = (h:Hypothesis)-[:REFINED_FROM*]->(original:Hypothesis)
WHERE original.generation = 1
RETURN path

# Find most tested hypotheses
MATCH (h:Hypothesis)<-[:TESTS]-(p:ExperimentProtocol)
RETURN h.statement, count(p) as num_experiments
ORDER BY num_experiments DESC
LIMIT 10
```

### Programmatic Access

Access the world model in Python:

```python
from kosmos.world_model import get_world_model

# Get world model instance
wm = get_world_model()

# Query entities
hypotheses = wm.query_entities(
    entity_type="Hypothesis",
    filters={"properties.status": "supported"}
)

# Query relationships
support_rels = wm.query_relationships(
    relationship_type="SUPPORTS",
    filters={"confidence": {"$gte": 0.9}}
)

# Get statistics
stats = wm.get_statistics()
print(f"Total entities: {stats['entity_count']}")
print(f"Total relationships: {stats['relationship_count']}")
```

### Export Formats

Current export format is JSON. Future versions may support:

- GraphML (for visualization tools like Gephi)
- Neo4j Dump (for database migration)
- RDF/Turtle (for semantic web applications)
- CSV (for spreadsheet analysis)

---

## Troubleshooting

### "Failed to connect to Neo4j"

**Symptom:** Warning messages about Neo4j connection failures

**Solution:**

1. Check if Neo4j is running:
   ```bash
   docker-compose ps
   # or
   neo4j status
   ```

2. Verify connection settings in `.env`:
   ```bash
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=kosmos-password
   ```

3. **Graceful degradation:** Kosmos will continue working without Neo4j (just no graph persistence)

### Large Export Files

**Symptom:** Export files are very large (>100 MB)

**Solution:**

1. Export specific subgraphs (future feature)
2. Reset graph periodically:
   ```bash
   kosmos graph --reset
   ```
3. Use Neo4j's built-in dump/restore for very large graphs

### Import Errors

**Symptom:** "Failed to import" or duplicate entity errors

**Solution:**

1. Use `--clear` flag to start fresh:
   ```bash
   kosmos graph --import backup.json --clear
   ```

2. Check export file is valid JSON:
   ```bash
   python -m json.tool backup.json > /dev/null
   ```

### Neo4j Not Available

**Symptom:** Neo4j not installed or accessible

**Solution:**

✅ **Kosmos works without Neo4j!**

- SQL database handles all core functionality
- Graph features are optional enhancements
- Set `WORLD_MODEL_ENABLED=false` in `.env` to disable gracefully

---

## FAQ

### Do I need Neo4j to use Kosmos?

**No!** Neo4j enables persistent knowledge graphs, but Kosmos works perfectly without it. The graph features are optional enhancements.

### What happens if Neo4j goes down?

Kosmos continues working normally. Graph persistence is disabled, but all research functionality remains intact.

### Can I use multiple graphs for different projects?

Currently, all research shares one graph. Multi-project support is planned for future releases. Workaround: Export/import between projects.

### How much disk space do graphs use?

Rough estimates:
- Small research session (10 hypotheses, 5 experiments): ~500 KB
- Medium project (100 hypotheses, 50 experiments): ~5 MB
- Large corpus (1000 hypotheses, 500 experiments): ~50 MB

### Can I visualize the graph?

**Neo4j Browser:** Built-in visualization at http://localhost:7474

**Future:** Dedicated visualization tools and graph analytics

### Is the graph data secure?

- Neo4j runs locally by default (not exposed to internet)
- Export files are plain JSON (encrypt if needed)
- Connection uses bolt:// protocol with authentication
- For production: Use Neo4j Enterprise with encryption

---

## Best Practices

### Regular Exports

```bash
# Daily automated backup
0 0 * * * /path/to/kosmos graph --export /backups/daily_$(date +%Y%m%d).json

# Keep last 7 days
find /backups -name "daily_*.json" -mtime +7 -delete
```

### Meaningful Naming

```bash
# Good export names
kosmos graph --export transformers_nov2025.json
kosmos graph --export hypothesis_generation_baseline.json
kosmos graph --export experiment_round_3.json

# Poor export names
kosmos graph --export export.json
kosmos graph --export backup.json
```

### Periodic Cleanup

```bash
# After major milestones, archive and reset
kosmos graph --export milestone_phase1_complete.json
kosmos graph --reset

# Start fresh for next phase
kosmos research "Phase 2: New research direction"
```

### Version Control Integration

```bash
# Add exports to git (if not too large)
git add research/graph_exports/*.json
git commit -m "Knowledge graph checkpoint: hypothesis validation complete"

# For large graphs, use git-lfs
git lfs track "research/graph_exports/*.json"
```

---

## Roadmap

Future enhancements planned:

- **Multi-Project Support** - Separate graphs per research project
- **Semantic Search** - Find similar hypotheses and related research
- **Graph Analytics** - Identify research patterns and opportunities
- **Visualization Tools** - Interactive graph exploration
- **Collaborative Features** - Merge graphs from multiple researchers
- **Export Formats** - GraphML, RDF, CSV support

---

## Getting Help

### Documentation

- [Main User Guide](user-guide.md)
- [Developer Guide](../developer/developer-guide.md)
- [Troubleshooting](troubleshooting.md)

### Community

- [GitHub Discussions](https://github.com/jimmc414/Kosmos/discussions) - Ask questions
- [GitHub Issues](https://github.com/jimmc414/Kosmos/issues) - Report bugs
- [GitHub Repo](https://github.com/jimmc414/Kosmos) - Source code

### Support

For issues with:
- **Kosmos features** - Open GitHub issue
- **Neo4j installation** - See [Neo4j docs](https://neo4j.com/docs/)
- **Graph queries** - See [Cypher documentation](https://neo4j.com/docs/cypher-manual/)

---

**Last Updated:** November 2025
**Version:** 0.2.0
