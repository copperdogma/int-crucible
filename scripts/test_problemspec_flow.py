#!/usr/bin/env python3
"""
Test script demonstrating end-to-end ProblemSpec construction.

This script:
1. Creates a project and chat session
2. Adds sample chat messages
3. Calls the ProblemSpec agent to refine the spec
4. Shows the resulting ProblemSpec and follow-up questions
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crucible.db.session import get_session, init_from_config
from crucible.db.repositories import (
    create_project,
    create_chat_session,
    create_message,
    get_problem_spec
)
from crucible.services.problemspec_service import ProblemSpecService
from crucible.config import get_config

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the test flow."""
    # Initialize database
    logger.info("Initializing database...")
    config = get_config()
    init_from_config()

    # Create test project
    logger.info("Creating test project...")
    with get_session() as session:
        project = create_project(
            session,
            title="Test Problem: Improve API Response Time",
            description="We need to improve the response time of our REST API endpoints. Currently, some endpoints take 2-3 seconds to respond, and we'd like to get them under 500ms."
        )
        logger.info(f"Created project: {project.id} - {project.title}")

        # Create chat session
        logger.info("Creating chat session...")
        chat_session = create_chat_session(
            session,
            project_id=project.id,
            title="Initial Problem Discussion",
            mode="setup"
        )
        logger.info(f"Created chat session: {chat_session.id}")

        # Add sample chat messages
        logger.info("Adding sample chat messages...")
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="user",
            content="I need help improving the response time of our REST API. Some endpoints are too slow."
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="agent",
            content="I can help you structure this problem. What specific endpoints are slow?"
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="user",
            content="The user profile endpoint and the search endpoint are the worst offenders. They take 2-3 seconds on average."
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="agent",
            content="Got it. What's your target response time?"
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="user",
            content="We want to get all endpoints under 500ms, ideally under 200ms for the most common ones."
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="agent",
            content="Are there any constraints we should consider? Budget, technical debt, deployment windows?"
        )
        
        create_message(
            session,
            chat_session_id=chat_session.id,
            role="user",
            content="We can't change the database schema without a migration window, which happens monthly. We have a reasonable budget but want to avoid major infrastructure changes if possible."
        )
        
        logger.info("Added sample chat messages")

        # Refine ProblemSpec
        logger.info("Refining ProblemSpec using agent...")
        service = ProblemSpecService(session)
        result = service.refine_problem_spec(
            project_id=project.id,
            chat_session_id=chat_session.id,
            message_limit=20
        )

        logger.info("\n" + "="*80)
        logger.info("PROBLEMSPEC REFINEMENT RESULT")
        logger.info("="*80)
        
        logger.info("\nUpdated Spec:")
        import json
        logger.info(json.dumps(result["updated_spec"], indent=2))
        
        logger.info("\nFollow-up Questions:")
        for i, question in enumerate(result["follow_up_questions"], 1):
            logger.info(f"  {i}. {question}")
        
        logger.info(f"\nReasoning: {result['reasoning']}")
        logger.info(f"\nReady to run: {result['ready_to_run']}")
        logger.info(f"Applied to database: {result['applied']}")

        # Get the ProblemSpec from database
        logger.info("\n" + "="*80)
        logger.info("PROBLEMSPEC FROM DATABASE")
        logger.info("="*80)
        spec = get_problem_spec(session, project.id)
        if spec:
            logger.info(f"\nSpec ID: {spec.id}")
            logger.info(f"Constraints: {len(spec.constraints or [])}")
            for i, constraint in enumerate(spec.constraints or [], 1):
                logger.info(f"  {i}. {constraint.get('name', 'Unknown')} (weight: {constraint.get('weight', 0)})")
            logger.info(f"\nGoals: {len(spec.goals or [])}")
            for i, goal in enumerate(spec.goals or [], 1):
                logger.info(f"  {i}. {goal}")
            logger.info(f"\nResolution: {spec.resolution}")
            logger.info(f"Mode: {spec.mode}")
        else:
            logger.info("No ProblemSpec found in database")

        logger.info("\n" + "="*80)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

