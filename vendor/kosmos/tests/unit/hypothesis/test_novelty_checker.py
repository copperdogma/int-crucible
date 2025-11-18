"""Tests for novelty_checker module."""

import pytest
from unittest.mock import Mock, patch
from kosmos.hypothesis.novelty_checker import NoveltyChecker
from kosmos.models.hypothesis import Hypothesis

@pytest.fixture
def novelty_checker():
    return NoveltyChecker(similarity_threshold=0.75, use_vector_db=False)

@pytest.fixture
def sample_hypothesis():
    return Hypothesis(
        research_question="Test question",
        statement="Attention mechanism improves transformer performance",
        rationale="Prior work shows attention captures dependencies",
        domain="machine_learning"
    )

@pytest.mark.unit
class TestNoveltyChecker:
    def test_init(self, novelty_checker):
        assert novelty_checker.similarity_threshold == 0.75

    @patch('kosmos.hypothesis.novelty_checker.UnifiedLiteratureSearch')
    @patch('kosmos.hypothesis.novelty_checker.get_session')
    def test_check_novelty_high(self, mock_session, mock_search, novelty_checker, sample_hypothesis):
        mock_search_inst = Mock()
        mock_search_inst.search.return_value = []
        mock_search.return_value = mock_search_inst

        mock_sess = Mock()
        mock_sess.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_sess

        report = novelty_checker.check_novelty(sample_hypothesis)

        assert report.novelty_score >= 0.8
        assert report.is_novel is True
        assert len(report.similar_papers) == 0

    def test_keyword_similarity(self, novelty_checker):
        text1 = "attention mechanism transformer neural network"
        text2 = "transformer attention model deep learning"
        similarity = novelty_checker._keyword_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # Some overlap exists
