"""
Hypothesis Prioritizer.

Ranks hypotheses using multi-criteria scoring:
1. Novelty (from novelty checker)
2. Feasibility (resource estimates)
3. Impact (LLM prediction)
4. Testability (from testability analyzer)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from kosmos.models.hypothesis import Hypothesis, PrioritizedHypothesis
from kosmos.hypothesis.novelty_checker import NoveltyChecker
from kosmos.hypothesis.testability import TestabilityAnalyzer
from kosmos.core.llm import get_client

logger = logging.getLogger(__name__)


class HypothesisPrioritizer:
    """
    Prioritize and rank hypotheses using multi-criteria analysis.

    Combines novelty, feasibility, impact, and testability into a
    single priority score for ranking.

    Example:
        ```python
        prioritizer = HypothesisPrioritizer(weights={
            "novelty": 0.30,
            "feasibility": 0.25,
            "impact": 0.25,
            "testability": 0.20
        })

        ranked = prioritizer.prioritize(hypotheses)

        for hyp in ranked[:3]:  # Top 3
            print(f"{hyp.hypothesis.statement}")
            print(f"Priority: {hyp.priority_score:.2f}")
        ```
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        use_novelty_checker: bool = True,
        use_testability_analyzer: bool = True,
        use_impact_prediction: bool = True
    ):
        """
        Initialize hypothesis prioritizer.

        Args:
            weights: Scoring weights (novelty, feasibility, impact, testability)
            use_novelty_checker: Run novelty checking
            use_testability_analyzer: Run testability analysis
            use_impact_prediction: Use LLM for impact prediction
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            "novelty": 0.30,
            "feasibility": 0.25,
            "impact": 0.25,
            "testability": 0.20
        }

        # Validate weights
        total_weight = sum(self.weights.values())
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.use_novelty_checker = use_novelty_checker
        self.use_testability_analyzer = use_testability_analyzer
        self.use_impact_prediction = use_impact_prediction

        # Components
        self.novelty_checker = NoveltyChecker() if use_novelty_checker else None
        self.testability_analyzer = TestabilityAnalyzer() if use_testability_analyzer else None
        self.llm_client = get_client() if use_impact_prediction else None

        logger.info(f"Initialized HypothesisPrioritizer with weights: {self.weights}")

    def prioritize(
        self,
        hypotheses: List[Hypothesis],
        run_analysis: bool = True
    ) -> List[PrioritizedHypothesis]:
        """
        Prioritize and rank a list of hypotheses.

        Args:
            hypotheses: List of hypotheses to prioritize
            run_analysis: Whether to run novelty/testability analysis (if not already done)

        Returns:
            List[PrioritizedHypothesis]: Ranked hypotheses (highest priority first)

        Example:
            ```python
            ranked = prioritizer.prioritize(hypotheses)
            best = ranked[0]
            print(f"Top hypothesis: {best.hypothesis.statement}")
            print(f"Priority: {best.priority_score:.2f}")
            print(f"  - Novelty: {best.novelty_score:.2f}")
            print(f"  - Impact: {best.impact_score:.2f}")
            ```
        """
        if not hypotheses:
            logger.warning("No hypotheses to prioritize")
            return []

        logger.info(f"Prioritizing {len(hypotheses)} hypotheses")

        prioritized = []

        for hyp in hypotheses:
            try:
                # Run analysis if needed
                if run_analysis:
                    self._run_analysis(hyp)

                # Calculate component scores
                novelty_score = self._get_novelty_score(hyp)
                testability_score = self._get_testability_score(hyp)
                feasibility_score = self._calculate_feasibility_score(hyp)
                impact_score = self._predict_impact_score(hyp)

                # Calculate weighted priority score
                priority_score = (
                    self.weights["novelty"] * novelty_score +
                    self.weights["feasibility"] * feasibility_score +
                    self.weights["impact"] * impact_score +
                    self.weights["testability"] * testability_score
                )

                priority_score = max(0.0, min(1.0, priority_score))

                # Generate rationale
                rationale = self._generate_rationale(
                    novelty_score, feasibility_score, impact_score, testability_score
                )

                # Create prioritized hypothesis
                prioritized_hyp = PrioritizedHypothesis(
                    hypothesis=hyp,
                    priority_score=priority_score,
                    novelty_score=novelty_score,
                    feasibility_score=feasibility_score,
                    impact_score=impact_score,
                    testability_score=testability_score,
                    weights=self.weights.copy(),
                    priority_rationale=rationale
                )

                prioritized.append(prioritized_hyp)

                logger.debug(f"Scored hypothesis: {hyp.statement[:50]}... = {priority_score:.2f}")

            except Exception as e:
                logger.error(f"Error prioritizing hypothesis: {e}", exc_info=True)
                continue

        # Sort by priority (highest first)
        prioritized.sort(key=lambda p: p.priority_score, reverse=True)

        # Assign ranks
        for rank, p in enumerate(prioritized, start=1):
            p.rank = rank
            p.update_hypothesis_priority()

        logger.info(f"Prioritized {len(prioritized)} hypotheses successfully")
        return prioritized

    def _run_analysis(self, hypothesis: Hypothesis) -> None:
        """
        Run novelty and testability analysis if not already done.

        Args:
            hypothesis: Hypothesis to analyze
        """
        # Run novelty check if score missing
        if hypothesis.novelty_score is None and self.novelty_checker:
            try:
                novelty_report = self.novelty_checker.check_novelty(hypothesis)
                hypothesis.novelty_score = novelty_report.novelty_score
                hypothesis.novelty_report = novelty_report.summary
                hypothesis.similar_work = [p["title"] for p in novelty_report.similar_papers[:5]]
            except Exception as e:
                logger.error(f"Error checking novelty: {e}")
                hypothesis.novelty_score = 0.5  # Default neutral score

        # Run testability analysis if score missing
        if hypothesis.testability_score is None and self.testability_analyzer:
            try:
                testability_report = self.testability_analyzer.analyze_testability(hypothesis)
                hypothesis.testability_score = testability_report.testability_score
                hypothesis.suggested_experiment_types = [exp["type"] for exp in testability_report.suggested_experiments[:2]]
                hypothesis.estimated_resources = {
                    "compute_hours": testability_report.estimated_compute_hours,
                    "cost_usd": testability_report.estimated_cost_usd,
                    "duration_days": testability_report.estimated_duration_days
                }
            except Exception as e:
                logger.error(f"Error analyzing testability: {e}")
                hypothesis.testability_score = 0.5  # Default neutral score

    def _get_novelty_score(self, hypothesis: Hypothesis) -> float:
        """
        Get or default the novelty score.

        Args:
            hypothesis: Hypothesis

        Returns:
            float: Novelty score (0.0-1.0)
        """
        if hypothesis.novelty_score is not None:
            return hypothesis.novelty_score

        logger.warning("No novelty score available, using default 0.5")
        return 0.5

    def _get_testability_score(self, hypothesis: Hypothesis) -> float:
        """
        Get or default the testability score.

        Args:
            hypothesis: Hypothesis

        Returns:
            float: Testability score (0.0-1.0)
        """
        if hypothesis.testability_score is not None:
            return hypothesis.testability_score

        logger.warning("No testability score available, using default 0.5")
        return 0.5

    def _calculate_feasibility_score(self, hypothesis: Hypothesis) -> float:
        """
        Calculate feasibility score based on resource estimates.

        Args:
            hypothesis: Hypothesis with resource estimates

        Returns:
            float: Feasibility score (0.0-1.0), higher = more feasible
        """
        if not hypothesis.estimated_resources:
            logger.debug("No resource estimates, using default feasibility 0.6")
            return 0.6

        score = 1.0  # Start optimistic

        # Cost factor (lower cost = higher feasibility)
        cost = hypothesis.estimated_resources.get("cost_usd", 0)
        if cost > 1000:
            score -= 0.4
        elif cost > 500:
            score -= 0.3
        elif cost > 100:
            score -= 0.2
        elif cost > 50:
            score -= 0.1

        # Duration factor (shorter = higher feasibility)
        duration = hypothesis.estimated_resources.get("duration_days", 0)
        if duration > 30:
            score -= 0.3
        elif duration > 14:
            score -= 0.2
        elif duration > 7:
            score -= 0.1

        # Compute hours factor
        compute_hours = hypothesis.estimated_resources.get("compute_hours", 0)
        if compute_hours > 100:
            score -= 0.2
        elif compute_hours > 50:
            score -= 0.1

        # Data availability (having required data sources is good)
        data_sources = hypothesis.estimated_resources.get("data_sources", [])
        if data_sources:
            # Having data sources available increases feasibility
            score += 0.1

        return max(0.0, min(1.0, score))

    def _predict_impact_score(self, hypothesis: Hypothesis) -> float:
        """
        Predict impact score using LLM or heuristics.

        Args:
            hypothesis: Hypothesis

        Returns:
            float: Impact score (0.0-1.0)
        """
        if not self.use_impact_prediction or not self.llm_client:
            # Heuristic fallback
            return self._heuristic_impact_score(hypothesis)

        try:
            prompt = f"""Assess the potential scientific impact of this hypothesis:

Hypothesis: "{hypothesis.statement}"

Rationale: {hypothesis.rationale}

Domain: {hypothesis.domain}

Rate the potential impact on a scale of 0.0 to 1.0, considering:
- Significance to the field
- Potential for advancing knowledge
- Practical applications
- Breadth of implications

Provide a JSON response:
{{
    "impact_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

            response = self.llm_client.generate_structured(
                prompt=prompt,
                schema={"impact_score": "float", "reasoning": "string"},
                max_tokens=300,
                temperature=0.5
            )

            impact_score = response.get("impact_score", 0.5)
            logger.debug(f"LLM impact score: {impact_score:.2f} - {response.get('reasoning', '')[:50]}")

            return max(0.0, min(1.0, impact_score))

        except Exception as e:
            logger.error(f"Error predicting impact with LLM: {e}")
            return self._heuristic_impact_score(hypothesis)

    def _heuristic_impact_score(self, hypothesis: Hypothesis) -> float:
        """
        Heuristic-based impact scoring (fallback).

        Args:
            hypothesis: Hypothesis

        Returns:
            float: Impact score (0.0-1.0)
        """
        score = 0.5  # Start neutral

        statement = hypothesis.statement.lower()
        rationale = hypothesis.rationale.lower()

        # Quantitative predictions suggest higher impact
        if any(term in statement for term in ["increase", "decrease", "improve", "reduce"]) and \
           any(char in statement for char in ["%", "fold", "factor"]):
            score += 0.15

        # Causal claims have higher potential impact
        if any(term in statement for term in ["cause", "lead to", "result in", "affect"]):
            score += 0.10

        # Novel mechanisms/explanations
        if any(term in rationale for term in ["novel", "new", "first", "unexplored"]):
            score += 0.10

        # Practical applications
        if any(term in rationale for term in ["application", "practical", "real-world", "deploy"]):
            score += 0.10

        # Fundamental questions
        if any(term in statement for term in ["fundamental", "core", "key", "crucial", "essential"]):
            score += 0.10

        # Broad implications
        if any(term in rationale for term in ["broader", "wide", "general", "universal"]):
            score += 0.05

        # Confidence score as proxy for impact
        if hypothesis.confidence_score:
            score += (hypothesis.confidence_score - 0.5) * 0.2  # ±0.1 adjustment

        return max(0.0, min(1.0, score))

    def _generate_rationale(
        self,
        novelty_score: float,
        feasibility_score: float,
        impact_score: float,
        testability_score: float
    ) -> str:
        """
        Generate human-readable priority rationale.

        Args:
            novelty_score: Novelty score
            feasibility_score: Feasibility score
            impact_score: Impact score
            testability_score: Testability score

        Returns:
            str: Rationale text
        """
        # Identify strengths and weaknesses
        scores = {
            "novelty": novelty_score,
            "feasibility": feasibility_score,
            "impact": impact_score,
            "testability": testability_score
        }

        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        strengths = [name for name, score in sorted_scores if score >= 0.7]
        weaknesses = [name for name, score in sorted_scores if score < 0.5]

        rationale_parts = []

        # Highlight strengths
        if strengths:
            strengths_str = ", ".join(strengths)
            rationale_parts.append(f"Strong {strengths_str}")

        # Note weaknesses
        if weaknesses:
            weaknesses_str = ", ".join(weaknesses)
            rationale_parts.append(f"Weaker {weaknesses_str}")

        # Overall assessment
        priority_score = (
            self.weights["novelty"] * novelty_score +
            self.weights["feasibility"] * feasibility_score +
            self.weights["impact"] * impact_score +
            self.weights["testability"] * testability_score
        )

        if priority_score >= 0.75:
            rationale_parts.append("Highly recommended for testing")
        elif priority_score >= 0.60:
            rationale_parts.append("Good candidate for testing")
        elif priority_score >= 0.45:
            rationale_parts.append("Moderate priority")
        else:
            rationale_parts.append("Lower priority due to challenges")

        return ". ".join(rationale_parts) + "."


class FeasibilityEstimator:
    """
    Estimate feasibility of testing hypotheses.

    Considers resources, time, data availability, and complexity.
    (This is a utility class used by HypothesisPrioritizer)
    """

    @staticmethod
    def estimate(hypothesis: Hypothesis) -> float:
        """
        Estimate feasibility score.

        Args:
            hypothesis: Hypothesis with resource estimates

        Returns:
            float: Feasibility score (0.0-1.0)
        """
        # Use the prioritizer's calculation
        prioritizer = HypothesisPrioritizer()
        return prioritizer._calculate_feasibility_score(hypothesis)


class ImpactPredictor:
    """
    Predict scientific impact of hypotheses.

    Uses LLM or heuristics to assess potential impact.
    (This is a utility class used by HypothesisPrioritizer)
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize impact predictor.

        Args:
            use_llm: Whether to use LLM for prediction
        """
        self.use_llm = use_llm
        self.llm_client = get_client() if use_llm else None

    def predict(self, hypothesis: Hypothesis) -> float:
        """
        Predict impact score.

        Args:
            hypothesis: Hypothesis

        Returns:
            float: Impact score (0.0-1.0)
        """
        # Use the prioritizer's calculation
        prioritizer = HypothesisPrioritizer(use_impact_prediction=self.use_llm)
        return prioritizer._predict_impact_score(hypothesis)


def prioritize_hypotheses(
    hypotheses: List[Hypothesis],
    weights: Optional[Dict[str, float]] = None
) -> List[PrioritizedHypothesis]:
    """
    Convenience function to prioritize hypotheses.

    Args:
        hypotheses: List of hypotheses to prioritize
        weights: Optional custom weights

    Returns:
        List[PrioritizedHypothesis]: Ranked hypotheses

    Example:
        ```python
        ranked = prioritize_hypotheses(hypotheses)
        for i, hyp in enumerate(ranked[:5], 1):
            print(f"{i}. {hyp.hypothesis.statement}")
            print(f"   Priority: {hyp.priority_score:.2f}")
        ```
    """
    prioritizer = HypothesisPrioritizer(weights=weights)
    return prioritizer.prioritize(hypotheses)
