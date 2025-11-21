#!/usr/bin/env python3
"""
Test script for Story 018: Snapshot functionality.

Tests snapshot creation, retrieval, and basic operations.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crucible.db.session import get_session
from crucible.db.repositories import (
    list_projects,
    list_runs,
    get_snapshot,
    list_snapshots,
    create_snapshot,
    get_project,
)
from crucible.services.snapshot_service import SnapshotService

# Initialize database
def init_db():
    """Initialize the database."""
    try:
        from kosmos.db import init_from_config
        init_from_config()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Database initialization warning: {e}")

def test_snapshot_creation():
    """Test creating a snapshot from an existing project."""
    print("=" * 60)
    print("Test 1: Snapshot Creation")
    print("=" * 60)
    
    with get_session() as session:
        # Try to find a project with both ProblemSpec and WorldModel
        projects = list_projects(session)
        project = None
        
        from sqlalchemy import text
        for p in projects:
            # Check if project has both ProblemSpec and WorldModel
            spec_result = session.execute(
                text("SELECT COUNT(*) FROM crucible_problem_specs WHERE project_id = :project_id"),
                {"project_id": p.id}
            ).scalar()
            model_result = session.execute(
                text("SELECT COUNT(*) FROM crucible_world_models WHERE project_id = :project_id"),
                {"project_id": p.id}
            ).scalar()
            
            if spec_result > 0 and model_result > 0:
                project = p
                break
        
        if not project:
            print("⚠ No project found with both ProblemSpec and WorldModel.")
            print("  Creating a minimal test project...")
            import uuid
            from crucible.db.repositories import create_project, create_problem_spec, create_world_model
            from crucible.db.models import ResolutionLevel, RunMode
            
            project_id = str(uuid.uuid4())
            project = create_project(
                session,
                title="Test Project for Snapshot",
                description="Temporary project for snapshot testing",
                project_id=project_id
            )
            
            # Create minimal ProblemSpec
            create_problem_spec(
                session,
                project_id=project_id,
                constraints=[{"name": "test_constraint", "description": "Test", "weight": 50}],
                goals=["Test goal"],
                resolution=ResolutionLevel.MEDIUM.value,
                mode=RunMode.FULL_SEARCH.value
            )
            
            # Create minimal WorldModel
            create_world_model(
                session,
                project_id=project_id,
                model_data={"actors": [], "mechanisms": []}
            )
            
            print(f"✓ Created test project: {project.id}")
        else:
            print(f"✓ Using existing project: {project.id} - {project.title}")
        
        # Check if project has ProblemSpec and WorldModel using raw SQL
        from sqlalchemy import text
        
        spec_result = session.execute(
            text("SELECT COUNT(*) FROM crucible_problem_specs WHERE project_id = :project_id"),
            {"project_id": project.id}
        ).scalar()
        
        model_result = session.execute(
            text("SELECT COUNT(*) FROM crucible_world_models WHERE project_id = :project_id"),
            {"project_id": project.id}
        ).scalar()
        
        if spec_result == 0:
            print("❌ Project has no ProblemSpec. Cannot create snapshot.")
            return False
        
        if model_result == 0:
            print("❌ Project has no WorldModel. Cannot create snapshot.")
            return False
        
        print(f"✓ Project has ProblemSpec and WorldModel")
        
        # Get first run if available (using raw SQL to avoid schema issues)
        run_result = session.execute(
            text("SELECT id FROM crucible_runs WHERE project_id = :project_id ORDER BY created_at DESC LIMIT 1"),
            {"project_id": project.id}
        ).fetchone()
        run_id = run_result[0] if run_result else None
        
        if run_id:
            print(f"✓ Found run: {run_id}")
        else:
            print("⚠ No runs found, creating snapshot without run reference")
        
        # Create snapshot
        service = SnapshotService(session)
        
        try:
            print("  Capturing snapshot data...")
            snapshot_data = service.capture_snapshot_data(
                project_id=project.id,
                run_id=run_id,
                include_chat_context=False,  # Skip chat for now
                max_chat_messages=0
            )
            print(f"✓ Captured snapshot data (version: {snapshot_data.get('version')})")
            
            reference_metrics = None
            if run_id:
                reference_metrics = service.capture_reference_metrics(run_id)
                print(f"✓ Captured reference metrics")
            
            # Create snapshot record (with unique name)
            import time
            unique_name = f"Test Snapshot {project.title[:20]} {int(time.time())}"
            snapshot = create_snapshot(
                session=session,
                project_id=project.id,
                run_id=run_id,
                name=unique_name,
                description=f"Test snapshot for project {project.title}",
                tags=["test", "automated"],
                invariants=[
                    {
                        "type": "min_candidates",
                        "value": 3,
                        "description": "At least 3 candidates must be generated"
                    },
                    {
                        "type": "run_status",
                        "value": "COMPLETED",
                        "description": "Run must complete successfully"
                    }
                ],
                snapshot_data=snapshot_data,
                reference_metrics=reference_metrics
            )
            
            print(f"✓ Created snapshot: {snapshot.id}")
            print(f"  Name: {snapshot.name}")
            print(f"  Version: {snapshot.version}")
            print(f"  Tags: {snapshot.tags}")
            print(f"  Invariants: {len(snapshot.invariants or [])}")
            
            return snapshot.id
            
        except Exception as e:
            print(f"❌ Error creating snapshot: {e}")
            import traceback
            traceback.print_exc()
            return None


def test_snapshot_retrieval(snapshot_id: str):
    """Test retrieving a snapshot."""
    print("\n" + "=" * 60)
    print("Test 2: Snapshot Retrieval")
    print("=" * 60)
    
    with get_session() as session:
        snapshot = get_snapshot(session, snapshot_id)
        if not snapshot:
            print(f"❌ Snapshot not found: {snapshot_id}")
            return False
        
        print(f"✓ Retrieved snapshot: {snapshot.name}")
        print(f"  Project ID: {snapshot.project_id}")
        print(f"  Run ID: {snapshot.run_id or 'None'}")
        print(f"  Snapshot data keys: {list(snapshot.snapshot_data.keys())}")
        print(f"  Reference metrics: {'Yes' if snapshot.reference_metrics else 'No'}")
        
        # Check snapshot data structure
        snapshot_data = snapshot.get_snapshot_data()
        if "problem_spec" in snapshot_data:
            print(f"  ✓ ProblemSpec present")
        if "world_model" in snapshot_data:
            print(f"  ✓ WorldModel present")
        if "run_config" in snapshot_data:
            print(f"  ✓ Run config present")
        
        return True


def test_snapshot_listing():
    """Test listing snapshots."""
    print("\n" + "=" * 60)
    print("Test 3: Snapshot Listing")
    print("=" * 60)
    
    with get_session() as session:
        snapshots = list_snapshots(session)
        print(f"✓ Found {len(snapshots)} snapshot(s)")
        
        if snapshots:
            print("\nSnapshots:")
            for s in snapshots:
                print(f"  - {s.name} (id: {s.id[:8]}...)")
                print(f"    Project: {s.project_id[:8]}...")
                print(f"    Tags: {s.tags}")
                print(f"    Created: {s.created_at}")
        
        return True


def test_snapshot_restore(snapshot_id: str):
    """Test restoring snapshot data (without executing pipeline)."""
    print("\n" + "=" * 60)
    print("Test 4: Snapshot Data Restore")
    print("=" * 60)
    
    with get_session() as session:
        snapshot = get_snapshot(session, snapshot_id)
        if not snapshot:
            print(f"❌ Snapshot not found: {snapshot_id}")
            return False
        
        service = SnapshotService(session)
        snapshot_data = snapshot.get_snapshot_data()
        
        # Create a temporary project for restore test
        import uuid
        from crucible.db.repositories import create_project, get_problem_spec, get_world_model
        
        temp_project_id = str(uuid.uuid4())
        temp_project = create_project(
            session,
            title="Temp Project for Restore Test",
            description="Temporary project for testing snapshot restore",
            project_id=temp_project_id
        )
        print(f"✓ Created temp project: {temp_project_id}")
        
        try:
            # Restore snapshot data
            service.restore_snapshot_data(temp_project_id, snapshot_data)
            print("✓ Restored snapshot data")
            
            # Verify restore using raw SQL
            from sqlalchemy import text
            import json
            
            spec_result = session.execute(
                text("SELECT constraints FROM crucible_problem_specs WHERE project_id = :project_id"),
                {"project_id": temp_project_id}
            ).fetchone()
            
            model_result = session.execute(
                text("SELECT model_data FROM crucible_world_models WHERE project_id = :project_id"),
                {"project_id": temp_project_id}
            ).fetchone()
            
            if spec_result:
                constraints = json.loads(spec_result[0]) if isinstance(spec_result[0], str) else spec_result[0]
                print(f"  ✓ ProblemSpec restored ({len(constraints or [])} constraints)")
            else:
                print("  ❌ ProblemSpec not restored")
                return False
            
            if model_result:
                print(f"  ✓ WorldModel restored")
            else:
                print("  ❌ WorldModel not restored")
                return False
            
            # Clean up temp project using raw SQL to avoid relationship loading issues
            from sqlalchemy import text
            session.execute(text("DELETE FROM crucible_problem_specs WHERE project_id = :project_id"), {"project_id": temp_project_id})
            session.execute(text("DELETE FROM crucible_world_models WHERE project_id = :project_id"), {"project_id": temp_project_id})
            session.execute(text("DELETE FROM crucible_projects WHERE id = :project_id"), {"project_id": temp_project_id})
            session.commit()
            print("✓ Cleaned up temp project")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring snapshot: {e}")
            import traceback
            traceback.print_exc()
            # Clean up on error
            try:
                session.delete(temp_project)
                session.commit()
            except:
                pass
            return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Story 018: Snapshot Functionality Tests")
    print("=" * 60)
    print()
    
    # Initialize database
    init_db()
    print()
    
    # Test 1: Create snapshot
    snapshot_id = test_snapshot_creation()
    if not snapshot_id:
        print("\n❌ Snapshot creation failed. Cannot continue tests.")
        return 1
    
    # Test 2: Retrieve snapshot
    if not test_snapshot_retrieval(snapshot_id):
        print("\n❌ Snapshot retrieval failed.")
        return 1
    
    # Test 3: List snapshots
    if not test_snapshot_listing():
        print("\n❌ Snapshot listing failed.")
        return 1
    
    # Test 4: Restore snapshot data
    if not test_snapshot_restore(snapshot_id):
        print("\n❌ Snapshot restore failed.")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

