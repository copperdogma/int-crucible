Database Modules
================

Database modules provide SQLAlchemy models and operations for persisting research data,
hypotheses, experiments, and results.

Database Models
---------------

SQLAlchemy ORM models for data persistence.

.. automodule:: kosmos.db.models
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Database Operations
-------------------

High-level database operations and queries.

.. automodule:: kosmos.db.operations
   :members:
   :undoc-members:
   :show-inheritance:

Database Session Management
---------------------------

Session creation and context management.

.. automodule:: kosmos.db.session
   :members:
   :undoc-members:
   :show-inheritance:

Database Schema
---------------

The database schema includes the following main tables:

**research_runs**
   - id (primary key)
   - question (research question)
   - domain (scientific domain)
   - state (INITIALIZING, RUNNING, COMPLETED, etc.)
   - current_iteration
   - max_iterations
   - budget_usd
   - created_at, updated_at

**hypotheses**
   - id (primary key)
   - research_run_id (foreign key)
   - claim (hypothesis statement)
   - rationale
   - novelty_score
   - priority_score
   - testability_score
   - status (pending, testing, confirmed, rejected)
   - parent_hypothesis_id (for evolution tracking)
   - created_at, updated_at

**experiments**
   - id (primary key)
   - hypothesis_id (foreign key)
   - experiment_type
   - parameters (JSON)
   - status (pending, running, completed, failed)
   - execution_time_seconds
   - created_at, started_at, completed_at

**experiment_results**
   - id (primary key)
   - experiment_id (foreign key)
   - output (JSON)
   - metrics (JSON)
   - plots (JSON - paths to generated plots)
   - statistical_significance
   - effect_size
   - created_at

**literature_references**
   - id (primary key)
   - pmid or doi
   - title, authors, abstract
   - year, journal
   - relevance_score
   - created_at

**research_run_literature**
   - research_run_id (foreign key)
   - literature_reference_id (foreign key)
   - relevance_context

Usage Examples
--------------

**Creating a research run**::

   from kosmos.db.models import ResearchRun
   from kosmos.db.session import get_session

   with get_session() as session:
       run = ResearchRun(
           question="What causes Alzheimer's disease?",
           domain="neuroscience",
           state="INITIALIZING",
           max_iterations=10,
           budget_usd=50.0
       )
       session.add(run)
       session.commit()
       session.refresh(run)

       print(f"Created run: {run.id}")

**Querying research runs**::

   from kosmos.db.models import ResearchRun
   from kosmos.db.session import get_session
   from sqlalchemy import desc

   with get_session() as session:
       # Get recent runs
       recent_runs = session.query(ResearchRun)\\
           .order_by(desc(ResearchRun.created_at))\\
           .limit(10)\\
           .all()

       for run in recent_runs:
           print(f"{run.id}: {run.question} ({run.state})")

       # Filter by domain
       bio_runs = session.query(ResearchRun)\\
           .filter(ResearchRun.domain == "biology")\\
           .all()

       # Filter by state
       active_runs = session.query(ResearchRun)\\
           .filter(ResearchRun.state == "RUNNING")\\
           .all()

**Creating hypotheses**::

   from kosmos.db.models import Hypothesis
   from kosmos.db.session import get_session

   with get_session() as session:
       hypothesis = Hypothesis(
           research_run_id=run.id,
           claim="Beta-amyloid accumulation causes neuronal death",
           rationale="Studies show correlation between plaques and neurodegeneration",
           novelty_score=0.75,
           priority_score=0.85,
           testability_score=0.90,
           status="pending"
       )
       session.add(hypothesis)
       session.commit()

**Creating experiments**::

   from kosmos.db.models import Experiment
   from kosmos.db.session import get_session
   from datetime import datetime

   with get_session() as session:
       experiment = Experiment(
           hypothesis_id=hypothesis.id,
           experiment_type="data_analysis",
           parameters={
               "data_source": "gene_expression",
               "method": "differential_expression",
               "genes": ["APP", "PSEN1", "PSEN2"]
           },
           status="pending"
       )
       session.add(experiment)
       session.commit()

       # Update status when running
       experiment.status = "running"
       experiment.started_at = datetime.utcnow()
       session.commit()

       # Update when complete
       experiment.status = "completed"
       experiment.completed_at = datetime.utcnow()
       experiment.execution_time_seconds = 123.45
       session.commit()

**Storing experiment results**::

   from kosmos.db.models import ExperimentResult
   from kosmos.db.session import get_session

   with get_session() as session:
       result = ExperimentResult(
           experiment_id=experiment.id,
           output={
               "mean_expression": 2.5,
               "std_dev": 0.3,
               "sample_size": 100
           },
           metrics={
               "r_squared": 0.85,
               "mse": 0.12
           },
           plots={
               "scatter": "/output/scatter.png",
               "histogram": "/output/histogram.png"
           },
           statistical_significance=0.001,
           effect_size=0.75
       )
       session.add(result)
       session.commit()

**Complex queries with relationships**::

   from kosmos.db.models import ResearchRun, Hypothesis, Experiment
   from kosmos.db.session import get_session
   from sqlalchemy.orm import joinedload

   with get_session() as session:
       # Get run with all hypotheses and experiments
       run = session.query(ResearchRun)\\
           .options(
               joinedload(ResearchRun.hypotheses)
               .joinedload(Hypothesis.experiments)
           )\\
           .filter(ResearchRun.id == run_id)\\
           .one()

       print(f"Run: {run.question}")
       print(f"Hypotheses: {len(run.hypotheses)}")

       for hyp in run.hypotheses:
           print(f"  Hypothesis: {hyp.claim}")
           print(f"  Experiments: {len(hyp.experiments)}")

           for exp in hyp.experiments:
               print(f"    Experiment: {exp.experiment_type} ({exp.status})")

**Using database operations helper**::

   from kosmos.db.operations import (
       create_research_run,
       get_research_run,
       update_research_run_state,
       add_hypothesis,
       get_hypotheses_for_run
   )

   # Create run
   run_id = create_research_run(
       question="Research question",
       domain="biology",
       max_iterations=10
   )

   # Get run
   run = get_research_run(run_id)

   # Update state
   update_research_run_state(run_id, "RUNNING")

   # Add hypotheses
   hypothesis_ids = []
   for hypothesis_data in hypotheses:
       hyp_id = add_hypothesis(
           research_run_id=run_id,
           **hypothesis_data
       )
       hypothesis_ids.append(hyp_id)

   # Get all hypotheses for run
   hypotheses = get_hypotheses_for_run(run_id)

Database Migrations
-------------------

Use Alembic for database schema migrations:

.. code-block:: bash

   # Initialize Alembic (first time only)
   alembic init alembic

   # Create a migration
   alembic revision --autogenerate -m "Add new column"

   # Apply migrations
   alembic upgrade head

   # Downgrade
   alembic downgrade -1

Connection Configuration
------------------------

Configure database connection in config file:

.. code-block:: python

   from kosmos.config import get_config

   config = get_config()

   # SQLite (default)
   config.database.url = "sqlite:///kosmos.db"

   # PostgreSQL
   config.database.url = "postgresql://user:password@localhost/kosmos"

   # MySQL
   config.database.url = "mysql+pymysql://user:password@localhost/kosmos"

Connection pooling:

.. code-block:: python

   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   engine = create_engine(
       database_url,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20,
       pool_pre_ping=True
   )

Transaction Management
----------------------

Use context managers for automatic transaction handling:

.. code-block:: python

   from kosmos.db.session import get_session

   # Automatic commit on success, rollback on exception
   with get_session() as session:
       run = ResearchRun(question="...")
       session.add(run)
       # Commits here if no exception

   # Explicit transaction control
   with get_session() as session:
       try:
           run = ResearchRun(question="...")
           session.add(run)
           session.commit()
       except Exception as e:
           session.rollback()
           raise

Bulk Operations
---------------

Efficient bulk insert and update:

.. code-block:: python

   from kosmos.db.session import get_session
   from kosmos.db.models import Hypothesis

   with get_session() as session:
       # Bulk insert
       hypotheses = [
           Hypothesis(research_run_id=run_id, claim=f"Hypothesis {i}")
           for i in range(100)
       ]
       session.bulk_save_objects(hypotheses)
       session.commit()

       # Bulk update
       session.query(Hypothesis)\\
           .filter(Hypothesis.research_run_id == run_id)\\
           .update({"status": "reviewed"})
       session.commit()

Data Export
-----------

Export database data:

.. code-block:: python

   from kosmos.db.operations import export_research_run
   import json

   # Export run to JSON
   data = export_research_run(run_id, include_results=True)

   with open("research_run_export.json", "w") as f:
       json.dump(data, f, indent=2, default=str)

   # Export to DataFrame
   import pandas as pd
   from kosmos.db.session import get_session
   from kosmos.db.models import ResearchRun

   with get_session() as session:
       query = session.query(ResearchRun)
       df = pd.read_sql(query.statement, session.bind)
       df.to_csv("research_runs.csv", index=False)

Database Backup and Restore
----------------------------

Backup and restore database:

.. code-block:: bash

   # SQLite backup
   cp kosmos.db kosmos_backup.db

   # PostgreSQL backup
   pg_dump kosmos > kosmos_backup.sql

   # PostgreSQL restore
   psql kosmos < kosmos_backup.sql

Programmatic backup:

.. code-block:: python

   from kosmos.db.operations import backup_database, restore_database

   # Backup
   backup_database(path="backup.db")

   # Restore
   restore_database(path="backup.db")

Database Indexes
----------------

Important indexes for performance:

.. code-block:: python

   from sqlalchemy import Index

   # In models.py
   Index('idx_research_run_state', ResearchRun.state)
   Index('idx_research_run_created_at', ResearchRun.created_at)
   Index('idx_hypothesis_research_run_id', Hypothesis.research_run_id)
   Index('idx_experiment_hypothesis_id', Experiment.hypothesis_id)

   # Composite indexes
   Index('idx_run_domain_state',
         ResearchRun.domain,
         ResearchRun.state)
