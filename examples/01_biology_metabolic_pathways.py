"""
Example 1: Biology - Metabolic Pathways Analysis

Description:
    Analyzes metabolic pathways using KEGG database to understand relationships
    between metabolites, enzymes, and pathways. This example demonstrates basic
    Kosmos usage for biology research.

Domain: Biology
Difficulty: Beginner
Duration: ~30 minutes
Cost: ~$5-10 (with caching)

Prerequisites:
- Kosmos installed and configured
- API key configured (Anthropic or Claude Code CLI)
- Internet connection for KEGG API

Learning Objectives:
- Set up a basic research project
- Use domain-specific APIs (KEGG)
- Interpret hypothesis and experiment results
- Export results for further analysis

Research Question:
    "What are the key metabolic pathway differences between glucose and fructose metabolism?"
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kosmos import ResearchDirectorAgent
from kosmos.config import get_config
from kosmos.cli.views.results_viewer import ResultsViewer
from kosmos.cli.utils import console, print_success, print_info, print_error

# ==============================================================================
# Configuration
# ==============================================================================

def setup_configuration() -> Dict[str, Any]:
    """
    Configure research parameters.

    Returns:
        Dictionary with research configuration
    """
    config = {
        "question": "What are the key metabolic pathway differences between glucose and fructose metabolism?",
        "domain": "biology",
        "max_iterations": 5,  # Start with fewer iterations for this example
        "budget_usd": 10.0,   # Set budget limit
        "enable_cache": True,  # Enable caching to reduce costs
        "context": {
            "metabolites": ["glucose", "fructose"],
            "focus": "metabolic pathways",
            "databases": ["KEGG"],
        }
    }
    return config


# ==============================================================================
# Research Execution
# ==============================================================================

def run_research(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the research using Kosmos.

    Args:
        config: Research configuration dictionary

    Returns:
        Research results dictionary
    """
    console.print("\n[h1]🧪 Metabolic Pathways Research[/h1]\n")
    console.print(f"[info]Question:[/info] {config['question']}")
    console.print(f"[info]Domain:[/info] {config['domain']}")
    console.print(f"[info]Max Iterations:[/info] {config['max_iterations']}")
    console.print(f"[info]Budget:[/info] ${config['budget_usd']:.2f}\n")

    # Get Kosmos configuration
    kosmos_config = get_config()
    kosmos_config.research.max_iterations = config["max_iterations"]
    kosmos_config.research.budget_usd = config["budget_usd"]

    # Initialize research director
    print_info("Initializing Research Director...")
    director = ResearchDirectorAgent(config=kosmos_config)

    # Run research
    print_info("Starting research (this may take 20-30 minutes)...")
    print_info("You can monitor progress with: kosmos status <run_id> --watch")

    try:
        results = director.conduct_research(
            question=config["question"],
            domain=config["domain"],
            max_iterations=config["max_iterations"]
        )

        return results

    except KeyboardInterrupt:
        print_error("Research interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Research failed: {e}")
        raise


# ==============================================================================
# Results Analysis
# ==============================================================================

def analyze_results(results: Dict[str, Any]) -> None:
    """
    Analyze and display research results.

    Args:
        results: Research results dictionary
    """
    console.print("\n[h1]📊 Research Results[/h1]\n")

    # Summary statistics
    console.print("[h2]Summary[/h2]")
    console.print(f"Run ID: [bright_blue]{results.get('id', 'N/A')}[/bright_blue]")
    console.print(f"Status: [success]{results.get('state', 'N/A')}[/success]")
    console.print(f"Iterations: {results.get('current_iteration', 0)}/{results.get('max_iterations', 0)}")
    console.print(f"Duration: {results.get('duration_minutes', 0):.1f} minutes")
    console.print(f"Cost: ${results.get('cost_usd', 0):.2f}\n")

    # Hypotheses
    hypotheses = results.get('hypotheses', [])
    if hypotheses:
        console.print(f"[h2]Hypotheses Generated ({len(hypotheses)})[/h2]")
        for i, hyp in enumerate(hypotheses[:5], 1):  # Show top 5
            console.print(f"\n{i}. [bold]{hyp.get('claim', 'N/A')}[/bold]")
            console.print(f"   Novelty: [yellow]{hyp.get('novelty_score', 0):.2f}[/yellow]")
            console.print(f"   Priority: [cyan]{hyp.get('priority_score', 0):.2f}[/cyan]")
            console.print(f"   Status: [{'success' if hyp.get('status') == 'confirmed' else 'warning'}]{hyp.get('status', 'N/A')}[/]")
            console.print(f"   Rationale: {hyp.get('rationale', 'N/A')[:100]}...")

    # Experiments
    experiments = results.get('experiments', [])
    if experiments:
        console.print(f"\n[h2]Experiments Executed ({len(experiments)})[/h2]")
        for i, exp in enumerate(experiments[:5], 1):  # Show top 5
            console.print(f"\n{i}. {exp.get('experiment_type', 'N/A')}")
            console.print(f"   Status: [{'success' if exp.get('status') == 'completed' else 'warning'}]{exp.get('status', 'N/A')}[/]")
            console.print(f"   Duration: {exp.get('execution_time_seconds', 0):.1f}s")
            console.print(f"   Description: {exp.get('description', 'N/A')[:100]}...")

    # Key findings
    findings = results.get('findings', {})
    if findings:
        console.print("\n[h2]Key Findings[/h2]")
        key_insights = findings.get('key_insights', [])
        for i, insight in enumerate(key_insights[:3], 1):
            console.print(f"{i}. {insight}")

        recommendations = findings.get('recommendations', [])
        if recommendations:
            console.print("\n[h2]Recommendations[/h2]")
            for i, rec in enumerate(recommendations[:3], 1):
                console.print(f"{i}. {rec}")


# ==============================================================================
# Results Export
# ==============================================================================

def export_results(results: Dict[str, Any], output_dir: Path) -> None:
    """
    Export results in multiple formats.

    Args:
        results: Research results dictionary
        output_dir: Directory to save results
    """
    output_dir.mkdir(exist_ok=True)

    # Initialize results viewer
    viewer = ResultsViewer()

    # Export to JSON
    json_path = output_dir / "metabolic_pathways_results.json"
    print_info(f"Exporting results to JSON: {json_path}")
    viewer.export_to_json(results, json_path)

    # Export to Markdown
    md_path = output_dir / "metabolic_pathways_results.md"
    print_info(f"Exporting results to Markdown: {md_path}")
    viewer.export_to_markdown(results, md_path)

    print_success(f"Results exported to {output_dir}")


# ==============================================================================
# Additional Analysis Functions
# ==============================================================================

def analyze_pathway_differences(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform additional analysis on pathway differences.

    Args:
        results: Research results dictionary

    Returns:
        Analysis summary dictionary
    """
    analysis = {
        "pathway_comparison": {},
        "enzyme_differences": [],
        "metabolite_interactions": [],
        "regulatory_differences": []
    }

    # Extract pathway information from hypotheses and experiments
    hypotheses = results.get('hypotheses', [])

    for hyp in hypotheses:
        claim = hyp.get('claim', '')

        # Look for pathway-related claims
        if 'pathway' in claim.lower():
            if 'glucose' in claim.lower():
                analysis["pathway_comparison"]["glucose"] = {
                    "claim": claim,
                    "score": hyp.get('priority_score', 0)
                }
            elif 'fructose' in claim.lower():
                analysis["pathway_comparison"]["fructose"] = {
                    "claim": claim,
                    "score": hyp.get('priority_score', 0)
                }

        # Look for enzyme differences
        if 'enzyme' in claim.lower():
            analysis["enzyme_differences"].append({
                "enzyme": extract_enzyme_name(claim),
                "function": claim,
                "confidence": hyp.get('novelty_score', 0)
            })

    return analysis


def extract_enzyme_name(text: str) -> str:
    """
    Extract enzyme name from text (simplified).

    Args:
        text: Text containing enzyme name

    Returns:
        Extracted enzyme name or 'Unknown'
    """
    # This is a simplified version - in practice, use NLP or regex
    keywords = ['kinase', 'synthase', 'dehydrogenase', 'isomerase', 'aldolase']
    for keyword in keywords:
        if keyword in text.lower():
            # Extract surrounding words
            words = text.split()
            for i, word in enumerate(words):
                if keyword in word.lower() and i > 0:
                    return f"{words[i-1]} {word}"
    return "Unknown"


def visualize_pathways(results: Dict[str, Any], output_dir: Path) -> None:
    """
    Create pathway visualizations (placeholder).

    Args:
        results: Research results dictionary
        output_dir: Directory to save visualizations
    """
    # This is a placeholder - in practice, you would:
    # 1. Extract pathway data from KEGG
    # 2. Use NetworkX or similar for graph visualization
    # 3. Generate plots with matplotlib/plotly

    print_info("Pathway visualization would be generated here")
    print_info("Consider using: NetworkX, matplotlib, or specialized tools like Cytoscape")


# ==============================================================================
# Main Execution
# ==============================================================================

def main():
    """Main execution function."""
    console.print("\n[bold bright_blue]=" * 40 + "[/bold bright_blue]")
    console.print("[bold bright_blue]  Kosmos Example: Metabolic Pathways[/bold bright_blue]")
    console.print("[bold bright_blue]=" * 40 + "[/bold bright_blue]\n")

    try:
        # 1. Setup configuration
        console.print("[h2]Step 1: Configuration[/h2]")
        config = setup_configuration()
        print_success("Configuration loaded")

        # 2. Run research
        console.print("\n[h2]Step 2: Execute Research[/h2]")
        results = run_research(config)
        print_success("Research completed successfully")

        # 3. Analyze results
        console.print("\n[h2]Step 3: Analyze Results[/h2]")
        analyze_results(results)

        # 4. Additional analysis
        console.print("\n[h2]Step 4: Pathway Analysis[/h2]")
        pathway_analysis = analyze_pathway_differences(results)
        console.print(f"Found {len(pathway_analysis['enzyme_differences'])} enzyme differences")
        console.print(f"Identified {len(pathway_analysis['pathway_comparison'])} pathway comparisons")

        # 5. Export results
        console.print("\n[h2]Step 5: Export Results[/h2]")
        output_dir = Path("./output/metabolic_pathways")
        export_results(results, output_dir)

        # 6. Summary
        console.print("\n[h1]✅ Example Complete![/h1]\n")
        console.print("[success]Research successfully completed and exported.[/success]")
        console.print(f"\n[info]Results saved to:[/info] {output_dir.absolute()}")
        console.print("\n[h2]Next Steps:[/h2]")
        console.print("1. Review the exported JSON and Markdown files")
        console.print("2. Examine the hypotheses and their novelty scores")
        console.print("3. Check the experiment results and statistical tests")
        console.print("4. Try modifying the research question")
        console.print("5. Experiment with different configuration parameters")
        console.print("\n[h2]Related Examples:[/h2]")
        console.print("- 02_biology_gene_expression.py - Gene expression analysis")
        console.print("- 05_materials_property_prediction.py - Materials science")
        console.print("- 07_multidomain_synthesis.py - Cross-domain research")

    except Exception as e:
        print_error(f"Example failed: {e}")
        console.print("\n[h2]Troubleshooting:[/h2]")
        console.print("1. Check API key configuration: kosmos doctor")
        console.print("2. Verify Kosmos installation: kosmos version")
        console.print("3. Review logs: tail -f ~/.kosmos/logs/kosmos.log")
        console.print("4. See troubleshooting guide: docs/troubleshooting.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
