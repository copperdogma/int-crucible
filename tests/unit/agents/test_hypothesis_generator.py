"""
Tests for kosmos.agents.hypothesis_generator module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from kosmos.agents.hypothesis_generator import HypothesisGeneratorAgent
from kosmos.models.hypothesis import Hypothesis, HypothesisGenerationResponse, ExperimentType
from kosmos.literature.base_client import PaperMetadata


@pytest.fixture
def hypothesis_agent():
    """Create HypothesisGeneratorAgent for testing."""
    return HypothesisGeneratorAgent(config={
        "num_hypotheses": 3,
        "use_literature_context": False  # Disable for faster tests
    })


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for hypothesis generation."""
    return {
        "hypotheses": [
            {
                "statement": "Increasing attention heads from 8 to 16 improves transformer performance by 15-25%",
                "rationale": "Attention mechanisms allow transformers to capture long-range dependencies. More heads provide richer representations.",
                "confidence_score": 0.75,
                "testability_score": 0.90,
                "suggested_experiment_types": ["computational", "data_analysis"]
            },
            {
                "statement": "Pre-training on domain-specific data reduces fine-tuning time by 40%",
                "rationale": "Domain-specific pre-training provides better initialization, requiring fewer fine-tuning steps.",
                "confidence_score": 0.80,
                "testability_score": 0.85,
                "suggested_experiment_types": ["computational"]
            },
            {
                "statement": "Larger batch sizes lead to faster convergence in distributed training",
                "rationale": "Larger batches provide more stable gradients and better utilize parallel compute resources.",
                "confidence_score": 0.70,
                "testability_score": 0.95,
                "suggested_experiment_types": ["computational"]
            }
        ]
    }


@pytest.mark.unit
class TestHypothesisGeneratorInit:
    """Test HypothesisGeneratorAgent initialization."""

    def test_init_default(self):
        """Test default initialization."""
        agent = HypothesisGeneratorAgent()
        assert agent.agent_type == "HypothesisGeneratorAgent"
        assert agent.num_hypotheses == 3
        assert agent.use_literature_context is True

    def test_init_with_config(self):
        """Test initialization with custom config."""
        agent = HypothesisGeneratorAgent(config={
            "num_hypotheses": 5,
            "use_literature_context": False,
            "min_novelty_score": 0.7
        })
        assert agent.num_hypotheses == 5
        assert agent.use_literature_context is False
        assert agent.min_novelty_score == 0.7


@pytest.mark.unit
class TestHypothesisGeneration:
    """Test hypothesis generation."""

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_generate_hypotheses_success(self, mock_get_client, hypothesis_agent, mock_llm_response):
        """Test successful hypothesis generation."""
        # Mock LLM client
        mock_client = Mock()
        mock_client.generate_structured.return_value = mock_llm_response
        mock_client.generate.return_value = "machine_learning"  # Domain detection
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        # Generate hypotheses
        response = hypothesis_agent.generate_hypotheses(
            research_question="How does attention mechanism affect transformer performance?",
            domain="machine_learning",
            store_in_db=False
        )

        # Assertions
        assert isinstance(response, HypothesisGenerationResponse)
        assert len(response.hypotheses) == 3
        assert response.research_question == "How does attention mechanism affect transformer performance?"
        assert response.domain == "machine_learning"
        assert response.generation_time_seconds > 0

        # Check first hypothesis
        hyp = response.hypotheses[0]
        assert isinstance(hyp, Hypothesis)
        assert "attention" in hyp.statement.lower() or "attention" in hyp.rationale.lower()
        assert hyp.confidence_score == 0.75
        assert hyp.testability_score == 0.90
        assert ExperimentType.COMPUTATIONAL in hyp.suggested_experiment_types

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_generate_with_custom_num_hypotheses(self, mock_get_client, hypothesis_agent, mock_llm_response):
        """Test generating custom number of hypotheses."""
        mock_client = Mock()
        mock_client.generate_structured.return_value = {
            "hypotheses": mock_llm_response["hypotheses"][:2]  # Return only 2
        }
        mock_client.generate.return_value = "biology"
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        response = hypothesis_agent.generate_hypotheses(
            research_question="How does CRISPR affect gene expression?",
            num_hypotheses=2,
            store_in_db=False
        )

        assert len(response.hypotheses) == 2

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_domain_auto_detection(self, mock_get_client, hypothesis_agent):
        """Test automatic domain detection."""
        mock_client = Mock()
        mock_client.generate.return_value = "neuroscience"
        mock_client.generate_structured.return_value = {"hypotheses": []}
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        response = hypothesis_agent.generate_hypotheses(
            research_question="How do neurons communicate?",
            domain=None,  # Auto-detect
            store_in_db=False
        )

        assert response.domain == "neuroscience"
        mock_client.generate.assert_called_once()


@pytest.mark.unit
class TestHypothesisValidation:
    """Test hypothesis validation."""

    def test_validate_valid_hypothesis(self, hypothesis_agent):
        """Test validating a valid hypothesis."""
        hyp = Hypothesis(
            research_question="Test question?",
            statement="Increasing parameter X will improve metric Y by 20%",
            rationale="Prior work shows that parameter X affects Y through mechanism Z. This suggests a 20% improvement.",
            domain="machine_learning"
        )

        assert hypothesis_agent._validate_hypothesis(hyp) is True

    def test_validate_statement_too_short(self, hypothesis_agent):
        """Test rejecting hypothesis with too-short statement."""
        hyp = Hypothesis(
            research_question="Test question?",
            statement="Too short",  # Only 2 words
            rationale="This is a reasonable rationale with sufficient detail to explain the hypothesis.",
            domain="test"
        )

        assert hypothesis_agent._validate_hypothesis(hyp) is False

    def test_validate_rationale_too_short(self, hypothesis_agent):
        """Test rejecting hypothesis with too-short rationale."""
        hyp = Hypothesis(
            research_question="Test question?",
            statement="This is a reasonable hypothesis statement",
            rationale="Too short",  # Only 2 words
            domain="test"
        )

        assert hypothesis_agent._validate_hypothesis(hyp) is False

    def test_validate_vague_language_warning(self, hypothesis_agent, caplog):
        """Test warning for vague language (but doesn't fail)."""
        hyp = Hypothesis(
            research_question="Test question?",
            statement="Maybe increasing X might possibly improve Y",
            rationale="This rationale is long enough to pass the minimum length requirement.",
            domain="test"
        )

        # Should pass but log warning
        result = hypothesis_agent._validate_hypothesis(hyp)
        assert result is True  # Doesn't fail, just warns


@pytest.mark.unit
class TestDatabaseOperations:
    """Test database storage and retrieval."""

    @patch('kosmos.agents.hypothesis_generator.get_session')
    def test_store_hypothesis(self, mock_get_session, hypothesis_agent):
        """Test storing hypothesis in database."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        hyp = Hypothesis(
            id="test-123",
            research_question="Test question?",
            statement="Test hypothesis statement",
            rationale="Test rationale with sufficient length for validation",
            domain="test_domain"
        )

        hyp_id = hypothesis_agent._store_hypothesis(hyp)

        assert hyp_id == "test-123"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('kosmos.agents.hypothesis_generator.get_session')
    def test_get_hypothesis_by_id(self, mock_get_session, hypothesis_agent):
        """Test retrieving hypothesis by ID."""
        mock_session = Mock()
        mock_db_hyp = Mock()
        mock_db_hyp.id = "test-123"
        mock_db_hyp.research_question = "Test question"
        mock_db_hyp.statement = "Test statement"
        mock_db_hyp.rationale = "Test rationale"
        mock_db_hyp.domain = "test_domain"
        mock_db_hyp.status.value = "generated"
        mock_db_hyp.testability_score = 0.8
        mock_db_hyp.novelty_score = 0.7
        mock_db_hyp.confidence_score = 0.75
        mock_db_hyp.related_papers = []
        mock_db_hyp.created_at = datetime.utcnow()
        mock_db_hyp.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_db_hyp
        mock_get_session.return_value = mock_session

        hyp = hypothesis_agent.get_hypothesis_by_id("test-123")

        assert hyp is not None
        assert hyp.id == "test-123"
        assert hyp.statement == "Test statement"


@pytest.mark.unit
class TestLiteratureContext:
    """Test literature context gathering."""

    @patch('kosmos.agents.hypothesis_generator.UnifiedLiteratureSearch')
    def test_gather_literature_context(self, mock_search_class, hypothesis_agent):
        """Test gathering literature for context."""
        # Enable literature context
        hypothesis_agent.use_literature_context = True

        mock_search = Mock()
        mock_papers = [
            PaperMetadata(
                title="Attention Is All You Need",
                authors=["Vaswani"],
                abstract="We propose the Transformer...",
                year=2017,
                source="arxiv"
            ),
            PaperMetadata(
                title="BERT",
                authors=["Devlin"],
                abstract="BERT is a transformer-based model...",
                year=2019,
                source="semantic_scholar"
            )
        ]
        mock_search.search.return_value = mock_papers
        mock_search_class.return_value = mock_search
        hypothesis_agent.literature_search = mock_search

        papers = hypothesis_agent._gather_literature_context(
            research_question="How does attention work?",
            domain="machine_learning"
        )

        assert len(papers) == 2
        assert papers[0].title == "Attention Is All You Need"
        mock_search.search.assert_called_once()


@pytest.mark.unit
class TestAgentExecute:
    """Test agent execute method."""

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_execute_generate_hypotheses_task(self, mock_get_client, hypothesis_agent, mock_llm_response):
        """Test executing hypothesis generation via message."""
        from kosmos.agents.base import AgentMessage, MessageType

        mock_client = Mock()
        mock_client.generate_structured.return_value = mock_llm_response
        mock_client.generate.return_value = "test_domain"
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        message = AgentMessage(
            type=MessageType.REQUEST,
            from_agent="test",
            to_agent=hypothesis_agent.agent_id,
            content={
                "task_type": "generate_hypotheses",
                "research_question": "Test question?",
                "num_hypotheses": 2,
                "domain": "test_domain"
            }
        )

        response = hypothesis_agent.execute(message)

        assert response.type == MessageType.RESPONSE
        assert "response" in response.content
        assert response.correlation_id == message.correlation_id


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_empty_llm_response(self, mock_get_client, hypothesis_agent):
        """Test handling empty LLM response."""
        mock_client = Mock()
        mock_client.generate_structured.return_value = {"hypotheses": []}
        mock_client.generate.return_value = "test"
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        response = hypothesis_agent.generate_hypotheses(
            research_question="Test?",
            store_in_db=False
        )

        assert len(response.hypotheses) == 0

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_malformed_llm_response(self, mock_get_client, hypothesis_agent):
        """Test handling malformed LLM response."""
        mock_client = Mock()
        mock_client.generate_structured.return_value = {
            "hypotheses": [
                {"statement": "Valid statement"},  # Missing required fields
                {"rationale": "Valid rationale"}   # Missing statement
            ]
        }
        mock_client.generate.return_value = "test"
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        response = hypothesis_agent.generate_hypotheses(
            research_question="Test?",
            store_in_db=False
        )

        # Should filter out malformed hypotheses
        assert len(response.hypotheses) == 0

    @patch('kosmos.agents.hypothesis_generator.get_client')
    def test_llm_exception_handling(self, mock_get_client, hypothesis_agent):
        """Test handling LLM exceptions."""
        mock_client = Mock()
        mock_client.generate_structured.side_effect = Exception("LLM Error")
        mock_client.generate.return_value = "test"
        mock_get_client.return_value = mock_client
        hypothesis_agent.llm_client = mock_client

        response = hypothesis_agent.generate_hypotheses(
            research_question="Test?",
            store_in_db=False
        )

        # Should return empty list on error
        assert len(response.hypotheses) == 0


@pytest.mark.unit
class TestHypothesisListing:
    """Test listing hypotheses from database."""

    @patch('kosmos.agents.hypothesis_generator.get_session')
    def test_list_hypotheses_all(self, mock_get_session, hypothesis_agent):
        """Test listing all hypotheses."""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_session.return_value = mock_session

        hypotheses = hypothesis_agent.list_hypotheses(limit=100)

        assert isinstance(hypotheses, list)
        mock_session.query.assert_called_once()

    @patch('kosmos.agents.hypothesis_generator.get_session')
    def test_list_hypotheses_with_filters(self, mock_get_session, hypothesis_agent):
        """Test listing hypotheses with domain filter."""
        from kosmos.models.hypothesis import HypothesisStatus

        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_session.return_value = mock_session

        hypotheses = hypothesis_agent.list_hypotheses(
            domain="machine_learning",
            status=HypothesisStatus.GENERATED,
            limit=50
        )

        assert isinstance(hypotheses, list)
        # Should apply both filters
        assert mock_query.filter.call_count == 2


@pytest.mark.integration
@pytest.mark.slow
class TestHypothesisGeneratorIntegration:
    """Integration tests (require real LLM and DB)."""

    @pytest.mark.requires_claude
    def test_real_hypothesis_generation(self):
        """Test real hypothesis generation with Claude."""
        agent = HypothesisGeneratorAgent(config={
            "num_hypotheses": 2,
            "use_literature_context": False
        })

        response = agent.generate_hypotheses(
            research_question="How does learning rate affect neural network convergence?",
            domain="machine_learning",
            store_in_db=False
        )

        assert len(response.hypotheses) > 0
        assert response.domain == "machine_learning"

        for hyp in response.hypotheses:
            assert len(hyp.statement) > 15
            assert len(hyp.rationale) > 30
            assert hyp.confidence_score is not None
