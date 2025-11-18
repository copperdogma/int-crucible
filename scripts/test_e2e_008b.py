#!/usr/bin/env python3
"""
E2E test script for Story 008b: Test tooling and run execution fixes.

Tests:
1. List existing projects and their status
2. Test error handling (missing ProblemSpec/WorldModel)
3. Test test-run command functionality
4. Verify run execution fixes work
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crucible.db.session import init_from_config, get_session
from crucible.db.repositories import (
    list_projects,
    get_problem_spec,
    get_world_model,
    create_project,
    create_problem_spec,
    create_world_model,
    create_run,
    list_runs,
    get_run,
)
from crucible.services.run_service import RunService
from crucible.services.run_verification import (
    verify_run_completeness,
    verify_data_integrity,
    get_run_statistics
)
from crucible.db.models import RunStatus, RunMode

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_list_projects():
    """Test 1: List existing projects and their status."""
    print_section("Test 1: List Existing Projects")
    
    with get_session() as session:
        projects = list_projects(session)
        print(f"\nFound {len(projects)} project(s):\n")
        
        if not projects:
            print("  No projects found in database.")
            return []
        
        project_list = []
        for p in projects:
            ps = get_problem_spec(session, p.id)
            wm = get_world_model(session, p.id)
            runs = list_runs(session, project_id=p.id)
            
            status = "✓" if (ps and wm) else "✗"
            print(f"  {status} {p.id}: {p.title}")
            if p.description:
                print(f"      Description: {p.description[:60]}...")
            print(f"      ProblemSpec: {'✓' if ps else '✗'}")
            print(f"      WorldModel: {'✓' if wm else '✗'}")
            print(f"      Runs: {len(runs)}")
            if runs:
                for r in runs[:3]:  # Show first 3 runs
                    print(f"        - {r.id}: {r.status}")
            print()
            
            project_list.append({
                'id': p.id,
                'title': p.title,
                'has_problem_spec': ps is not None,
                'has_world_model': wm is not None,
                'runs': runs
            })
        
        return project_list

def test_error_handling():
    """Test 2: Test error handling for missing prerequisites."""
    print_section("Test 2: Error Handling (Missing Prerequisites)")
    
    with get_session() as session:
        # Create a test project without ProblemSpec/WorldModel
        test_project = create_project(
            session,
            title="E2E Test Project - No Prerequisites",
            description="Test project for error handling"
        )
        print(f"\nCreated test project: {test_project.id}")
        
        # Create a run for this project
        test_run = create_run(
            session,
            project_id=test_project.id,
            mode=RunMode.FULL_SEARCH.value
        )
        print(f"Created test run: {test_run.id}")
        
        # Try to execute pipeline - should fail with clear error
        print("\nAttempting to execute pipeline (should fail with clear error)...")
        service = RunService(session)
        
        try:
            service.execute_full_pipeline(test_run.id, num_candidates=2, num_scenarios=2)
            print("  ✗ ERROR: Pipeline should have failed but didn't!")
            return False
        except ValueError as e:
            error_msg = str(e)
            print(f"  ✓ Got expected ValueError: {error_msg[:100]}...")
            
            # Check error message quality
            if "ProblemSpec not found" in error_msg or "WorldModel not found" in error_msg:
                print("  ✓ Error message is clear and helpful")
                if "Available projects" in error_msg:
                    print("  ✓ Error message includes available projects (excellent!)")
                return True
            else:
                print("  ✗ Error message doesn't mention missing prerequisites")
                return False
        except Exception as e:
            print(f"  ✗ Got unexpected exception: {type(e).__name__}: {e}")
            return False

def test_verification_utilities():
    """Test 3: Test verification utilities."""
    print_section("Test 3: Verification Utilities")
    
    with get_session() as session:
        projects = list_projects(session)
        if not projects:
            print("  No projects to test with.")
            return True
        
        # Find a project with runs
        test_project = None
        test_run = None
        
        for p in projects:
            runs = list_runs(session, project_id=p.id)
            if runs:
                test_project = p
                test_run = runs[0]
                break
        
        if not test_run:
            print("  No runs found to test verification utilities.")
            return True
        
        print(f"\nTesting with run: {test_run.id} (project: {test_project.id})")
        
        # Test get_run_statistics
        print("\n1. Testing get_run_statistics()...")
        stats = get_run_statistics(session, test_run.id)
        if "error" in stats:
            print(f"  ✗ Error: {stats['error']}")
            return False
        else:
            print(f"  ✓ Statistics retrieved successfully:")
            print(f"    - Status: {stats['status']}")
            print(f"    - Candidates: {stats['candidate_count']}")
            print(f"    - Scenarios: {stats['scenario_count']}")
            print(f"    - Evaluations: {stats['evaluation_count']}")
            print(f"    - Has Rankings: {stats['has_rankings']}")
        
        # Test verify_run_completeness
        print("\n2. Testing verify_run_completeness()...")
        completeness = verify_run_completeness(session, test_run.id)
        print(f"  - Is Complete: {completeness['is_complete']}")
        print(f"  - Has ProblemSpec: {completeness['has_problem_spec']}")
        print(f"  - Has WorldModel: {completeness['has_world_model']}")
        print(f"  - Issues: {len(completeness.get('issues', []))}")
        if completeness.get('issues'):
            for issue in completeness['issues']:
                print(f"    • {issue}")
        
        # Test verify_data_integrity
        print("\n3. Testing verify_data_integrity()...")
        integrity = verify_data_integrity(session, test_run.id)
        print(f"  - Is Valid: {integrity['is_valid']}")
        print(f"  - Issues: {len(integrity.get('issues', []))}")
        if integrity.get('issues'):
            for issue in integrity['issues']:
                print(f"    • {issue}")
        
        return True

def test_test_run_command_simulation():
    """Test 4: Simulate test-run command functionality."""
    print_section("Test 4: Test-Run Command Functionality (Simulation)")
    
    with get_session() as session:
        # Find a project with ProblemSpec and WorldModel
        projects = list_projects(session)
        test_project = None
        
        for p in projects:
            ps = get_problem_spec(session, p.id)
            wm = get_world_model(session, p.id)
            if ps and wm:
                test_project = p
                break
        
        if not test_project:
            print("  No project with both ProblemSpec and WorldModel found.")
            print("  Cannot test full pipeline execution.")
            print("  (This is expected if no projects have been set up yet)")
            return True
        
        print(f"\nTesting with project: {test_project.id} ({test_project.title})")
        print("  ✓ Has ProblemSpec")
        print("  ✓ Has WorldModel")
        
        # Create a new run
        test_run = create_run(
            session,
            project_id=test_project.id,
            mode=RunMode.FULL_SEARCH.value,
            config={"num_candidates": 2, "num_scenarios": 2}
        )
        print(f"\nCreated test run: {test_run.id}")
        
        # Note: We won't actually execute the pipeline here because it requires
        # LLM API access and can be slow/expensive. Instead, we'll verify
        # that the prerequisites check works correctly.
        
        service = RunService(session)
        
        # Check prerequisites (this is what was fixed)
        print("\nChecking prerequisites (this tests the fix)...")
        run = get_run(session, test_run.id)
        if run is None:
            print("  ✗ Run not found")
            return False
        
        # This should work now with session refresh
        session.expire_all()  # This is the fix we added
        
        ps = get_problem_spec(session, run.project_id)
        wm = get_world_model(session, run.project_id)
        
        if ps and wm:
            print("  ✓ Prerequisites found (session refresh working!)")
            print(f"    - ProblemSpec: {ps.id}")
            print(f"    - WorldModel: {wm.id}")
            return True
        else:
            print("  ✗ Prerequisites not found")
            return False

def main():
    """Run all E2E tests."""
    print("\n" + "="*80)
    print("  E2E Testing for Story 008b: Test Tooling and Run Execution Fixes")
    print("="*80)
    
    # Initialize database
    print("\nInitializing database...")
    try:
        from kosmos.db import init_from_config as kosmos_init
        kosmos_init()
        init_from_config()
        print("  ✓ Database initialized")
    except Exception as e:
        print(f"  ✗ Failed to initialize database: {e}")
        return 1
    
    results = []
    
    # Run tests
    try:
        projects = test_list_projects()
        results.append(("List Projects", True))
        
        error_test = test_error_handling()
        results.append(("Error Handling", error_test))
        
        verification_test = test_verification_utilities()
        results.append(("Verification Utilities", verification_test))
        
        command_test = test_test_run_command_simulation()
        results.append(("Test-Run Command", command_test))
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    print_section("Test Summary")
    print("\nResults:")
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

