#!/usr/bin/env python3
"""
Validation script for Story 017: Candidate ranking explanations.

This script:
1. Creates a test project with ProblemSpec
2. Runs a small pipeline (2-3 candidates, 3-4 scenarios)
3. Verifies that ranking explanations are generated
4. Prints sample explanations for review
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crucible.db.session import init_from_config, get_session
from crucible.db.repositories import (
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    list_candidates,
    get_problem_spec,
)
from crucible.services.run_service import RunService
from crucible.db.models import RunMode, RunStatus

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def main():
    """Run validation test."""
    print_section("Story 017: Ranking Explanations Validation")
    
    # Initialize database
    init_from_config()
    
    with get_session() as session:
        # Create test project
        print("\n[1/5] Creating test project...")
        project = create_project(
            session,
            title="Ranking Explanations Test",
            description="Test project for validating ranking explanation generation"
        )
        print(f"✓ Created project: {project.id}")
        
        # Create ProblemSpec with constraints
        print("\n[2/5] Creating ProblemSpec with constraints...")
        problem_spec = create_problem_spec(
            session,
            project_id=project.id,
            constraints=[
                {"name": "latency", "description": "Response time must be under 100ms", "weight": 100},
                {"name": "scalability", "description": "Must handle 1000+ concurrent users", "weight": 80},
                {"name": "cost", "description": "Implementation cost should be reasonable", "weight": 50}
            ],
            goals=["Build a fast, scalable system"],
            resolution="medium",
            mode="full_search"
        )
        print(f"✓ Created ProblemSpec with {len(problem_spec.constraints)} constraints")
        
        # Create minimal WorldModel
        print("\n[3/5] Creating WorldModel...")
        world_model = create_world_model(
            session,
            project_id=project.id,
            model_data={
                "actors": [{"id": "user", "type": "external"}],
                "mechanisms": [{"id": "api", "type": "service"}],
                "resources": [{"id": "compute", "type": "infrastructure"}]
            }
        )
        print("✓ Created WorldModel")
        
        # Create run
        print("\n[4/5] Creating run...")
        run = create_run(
            session,
            project_id=project.id,
            mode=RunMode.FULL_SEARCH.value,
            config={"num_candidates": 3, "num_scenarios": 4}
        )
        print(f"✓ Created run: {run.id}")
        
        # Execute pipeline
        print("\n[5/5] Executing full pipeline (this may take a moment)...")
        service = RunService(session)
        try:
            result = service.execute_full_pipeline(
                run_id=run.id,
                num_candidates=3,
                num_scenarios=4
            )
            print("✓ Pipeline execution completed")
            print(f"  - Candidates: {result.get('candidates', {}).get('count', 0)}")
            print(f"  - Scenarios: {result.get('scenarios', {}).get('count', 0)}")
            print(f"  - Evaluations: {result.get('evaluations', {}).get('count', 0)}")
            print(f"  - Rankings: {result.get('rankings', {}).get('count', 0)}")
        except Exception as e:
            print(f"✗ Pipeline execution failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Verify explanations
        print_section("Verifying Ranking Explanations")
        candidates = list_candidates(session, run_id=run.id)
        
        if not candidates:
            print("✗ No candidates found!")
            return 1
        
        print(f"\nFound {len(candidates)} candidates. Checking for explanations...\n")
        
        explanations_found = 0
        for idx, candidate in enumerate(candidates, 1):
            scores = candidate.scores or {}
            explanation = scores.get("ranking_explanation")
            factors = scores.get("ranking_factors", {})
            
            print(f"Candidate #{idx} ({candidate.id[:8]}...):")
            print(f"  I score: {scores.get('I', 'N/A')}")
            
            if explanation:
                explanations_found += 1
                print(f"  ✓ Explanation: {explanation}")
                if factors.get("top_positive_factors"):
                    print(f"  ✓ Positive factors: {factors['top_positive_factors']}")
                if factors.get("top_negative_factors"):
                    print(f"  ✓ Negative factors: {factors['top_negative_factors']}")
            else:
                print(f"  ✗ No explanation found")
            print()
        
        # Summary
        print_section("Validation Summary")
        if explanations_found == len(candidates):
            print(f"✓ SUCCESS: All {explanations_found} candidates have ranking explanations!")
            print("\nSample explanations have been printed above for review.")
            return 0
        else:
            print(f"✗ PARTIAL: Only {explanations_found}/{len(candidates)} candidates have explanations")
            return 1

if __name__ == "__main__":
    sys.exit(main())

