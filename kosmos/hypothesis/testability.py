"""
Testability Analyzer for hypotheses.

Assesses whether and how hypotheses can be tested:
1. Testability assessment (is it testable?)
2. Resource requirement estimation
3. Experiment type suggestion
4. Challenge and limitation identification
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from kosmos.models.hypothesis import Hypothesis, TestabilityReport, ExperimentType
from kosmos.core.llm import get_client

logger = logging.getLogger(__name__)


class TestabilityAnalyzer:
    """
    Analyze testability of hypotheses.

    Determines if a hypothesis can be tested, suggests appropriate
    experiment types, and estimates resource requirements.

    Example:
        ```python
        analyzer = TestabilityAnalyzer()

        report = analyzer.analyze_testability(hypothesis)

        if report.is_testable:
            print(f"Can test using: {report.primary_experiment_type}")
            print(f"Estimated cost: ${report.estimated_cost_usd}")
        else:
            print(f"Not testable: {report.challenges}")
        ```
    """

    def __init__(
        self,
        testability_threshold: float = 0.3,
        use_llm_for_assessment: bool = True
    ):
        """
        Initialize testability analyzer.

        Args:
            testability_threshold: Minimum score to be considered testable (0.0-1.0)
            use_llm_for_assessment: Use LLM for detailed assessment
        """
        self.testability_threshold = testability_threshold
        self.use_llm_for_assessment = use_llm_for_assessment

        self.llm_client = get_client() if use_llm_for_assessment else None

        logger.info(f"Initialized TestabilityAnalyzer with threshold={testability_threshold}")

    def analyze_testability(self, hypothesis: Hypothesis) -> TestabilityReport:
        """
        Analyze testability of a hypothesis.

        Args:
            hypothesis: Hypothesis to analyze

        Returns:
            TestabilityReport: Detailed testability analysis

        Example:
            ```python
            report = analyzer.analyze_testability(hypothesis)
            print(f"Testability: {report.testability_score:.2f}")
            print(f"Suggested experiments: {[e['type'] for e in report.suggested_experiments]}")
            ```
        """
        logger.info(f"Analyzing testability for: {hypothesis.statement[:50]}...")

        # Step 1: Basic testability assessment
        basic_score = self._assess_basic_testability(hypothesis)

        # Step 2: Suggest experiment types
        suggested_experiments = self._suggest_experiment_types(hypothesis)

        # Step 3: Estimate resources
        resource_estimates = self._estimate_resources(hypothesis, suggested_experiments)

        # Step 4: Identify challenges
        challenges = self._identify_challenges(hypothesis)

        # Step 5: Identify limitations
        limitations = self._identify_limitations(hypothesis)

        # Step 6: LLM-based enhancement (if enabled)
        if self.use_llm_for_assessment and self.llm_client:
            llm_assessment = self._llm_testability_assessment(hypothesis)

            # Merge LLM insights
            if llm_assessment:
                # Adjust score based on LLM confidence
                llm_confidence = llm_assessment.get("confidence", 0.5)
                basic_score = (basic_score + llm_confidence) / 2  # Average

                # Add LLM-identified challenges and limitations
                challenges.extend(llm_assessment.get("additional_challenges", []))
                limitations.extend(llm_assessment.get("additional_limitations", []))

        # Final testability score
        testability_score = max(0.0, min(1.0, basic_score))

        # Determine if testable
        is_testable = testability_score >= self.testability_threshold

        # Select primary experiment type
        primary_experiment_type = self._select_primary_experiment(suggested_experiments)

        # Determine recommendation
        recommended = is_testable and testability_score >= 0.5 and len(challenges) <= 5

        # Generate summary
        summary = self._generate_summary(
            testability_score=testability_score,
            is_testable=is_testable,
            primary_experiment_type=primary_experiment_type,
            challenges=challenges,
            estimated_cost=resource_estimates.get("cost_usd")
        )

        # Update hypothesis
        hypothesis.testability_score = testability_score
        hypothesis.suggested_experiment_types = [exp["type"] for exp in suggested_experiments[:2]]
        hypothesis.estimated_resources = resource_estimates

        return TestabilityReport(
            hypothesis_id=hypothesis.id or "unknown",
            testability_score=testability_score,
            is_testable=is_testable,
            testability_threshold_used=self.testability_threshold,
            suggested_experiments=suggested_experiments,
            primary_experiment_type=primary_experiment_type,
            estimated_compute_hours=resource_estimates.get("compute_hours"),
            estimated_cost_usd=resource_estimates.get("cost_usd"),
            estimated_duration_days=resource_estimates.get("duration_days"),
            required_data_sources=resource_estimates.get("data_sources", []),
            challenges=challenges,
            limitations=limitations,
            summary=summary,
            recommended=recommended
        )

    def _assess_basic_testability(self, hypothesis: Hypothesis) -> float:
        """
        Basic rule-based testability assessment.

        Args:
            hypothesis: Hypothesis to assess

        Returns:
            float: Testability score (0.0-1.0)
        """
        score = 0.5  # Start at neutral

        statement = hypothesis.statement.lower()

        # Positive indicators
        positive_indicators = [
            (r'\b(increase|decrease|improve|reduce)\b', 0.15, "Directional prediction"),
            (r'\b(will|should|would)\b', 0.10, "Predictive statement"),
            (r'\b\d+%|\d+\s*(percent|fold)\b', 0.15, "Quantitative prediction"),
            (r'\b(correlat|associat|affect|influence|cause)\b', 0.10, "Causal/correlational claim"),
            (r'\b(compare|contrast|differ|similar)\b', 0.10, "Comparative claim"),
            (r'\b(measure|quantify|assess|evaluate)\b', 0.10, "Measurable outcome"),
        ]

        for pattern, weight, description in positive_indicators:
            if re.search(pattern, statement):
                score += weight
                logger.debug(f"Positive indicator: {description} (+{weight})")

        # Negative indicators
        negative_indicators = [
            (r'\b(may|might|possibly|perhaps|potentially)\b', -0.15, "Vague/uncertain language"),
            (r'\b(always|never|everyone|everything|all)\b', -0.10, "Absolute claim (hard to test)"),
            (r'\b(consciousness|soul|essence|meaning of life)\b', -0.20, "Philosophical/untestable concept"),
            (r'\?$', -0.20, "Question format (not a statement)"),
        ]

        for pattern, weight, description in negative_indicators:
            if re.search(pattern, statement):
                score += weight
                logger.debug(f"Negative indicator: {description} ({weight})")

        # Check for measurable variables
        if any(term in statement for term in ["metric", "score", "rate", "ratio", "percentage", "accuracy"]):
            score += 0.10
            logger.debug("Contains measurable metrics (+0.10)")

        # Check rationale quality
        if len(hypothesis.rationale) > 100:
            score += 0.05  # Detailed rationale suggests well-thought-out testability

        # Domain-specific adjustments
        if hypothesis.domain in ["machine_learning", "data_science", "statistics"]:
            score += 0.10  # Computational domains are generally more testable

        if hypothesis.domain in ["philosophy", "ethics", "metaphysics"]:
            score -= 0.15  # Harder to test empirically

        return max(0.0, min(1.0, score))

    def _suggest_experiment_types(
        self,
        hypothesis: Hypothesis
    ) -> List[Dict[str, Any]]:
        """
        Suggest appropriate experiment types with rankings.

        Args:
            hypothesis: Hypothesis

        Returns:
            List[Dict]: Suggested experiments with scores
        """
        statement = hypothesis.statement.lower()
        domain = hypothesis.domain.lower()

        experiments = []

        # Computational experiment assessment
        comp_score = 0.3  # Base score
        if any(term in statement for term in ["simulate", "model", "algorithm", "computation", "predict"]):
            comp_score += 0.4
        if any(term in domain for term in ["machine_learning", "computer_science", "ai", "physics", "chemistry"]):
            comp_score += 0.2
        if "data" not in statement and "dataset" not in statement:
            comp_score += 0.1  # No existing data needed

        experiments.append({
            "type": ExperimentType.COMPUTATIONAL,
            "score": min(1.0, comp_score),
            "description": "Computational simulation or algorithmic analysis",
            "feasibility": "high" if comp_score > 0.7 else ("medium" if comp_score > 0.4 else "low"),
            "rationale": "Hypothesis can be tested through simulation, modeling, or algorithmic analysis"
        })

        # Data analysis experiment assessment
        data_score = 0.3
        if any(term in statement for term in ["correlat", "associat", "pattern", "trend", "relationship", "data"]):
            data_score += 0.4
        if any(term in statement for term in ["dataset", "existing data", "historical", "observational"]):
            data_score += 0.2
        if any(term in domain for term in ["data_science", "statistics", "epidemiology", "economics"]):
            data_score += 0.1

        experiments.append({
            "type": ExperimentType.DATA_ANALYSIS,
            "score": min(1.0, data_score),
            "description": "Statistical analysis of existing datasets",
            "feasibility": "high" if data_score > 0.7 else ("medium" if data_score > 0.4 else "low"),
            "rationale": "Hypothesis can be tested by analyzing existing datasets or collecting observational data"
        })

        # Literature synthesis assessment
        lit_score = 0.2
        if any(term in statement for term in ["literature", "studies", "research shows", "prior work", "existing"]):
            lit_score += 0.3
        if any(term in statement for term in ["review", "synthesis", "meta-analysis", "survey"]):
            lit_score += 0.3
        if "novel" in hypothesis.rationale.lower() or "gap" in hypothesis.rationale.lower():
            lit_score += 0.1  # Novelty suggests lit review needed

        experiments.append({
            "type": ExperimentType.LITERATURE_SYNTHESIS,
            "score": min(1.0, lit_score),
            "description": "Systematic review or meta-analysis of existing literature",
            "feasibility": "high" if lit_score > 0.6 else ("medium" if lit_score > 0.3 else "low"),
            "rationale": "Hypothesis can be evaluated by synthesizing findings from existing literature"
        })

        # Sort by score (highest first)
        experiments.sort(key=lambda x: x["score"], reverse=True)

        return experiments

    def _estimate_resources(
        self,
        hypothesis: Hypothesis,
        suggested_experiments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Estimate resource requirements.

        Args:
            hypothesis: Hypothesis
            suggested_experiments: Suggested experiment types

        Returns:
            Dict: Resource estimates
        """
        if not suggested_experiments:
            return {
                "compute_hours": None,
                "cost_usd": None,
                "duration_days": None,
                "data_sources": []
            }

        primary_exp = suggested_experiments[0]
        exp_type = primary_exp["type"]

        # Base estimates by experiment type
        if exp_type == ExperimentType.COMPUTATIONAL:
            compute_hours = 10.0  # Base: 10 hours
            if "large" in hypothesis.statement.lower() or "big" in hypothesis.statement.lower():
                compute_hours *= 5

            cost_usd = compute_hours * 0.50  # $0.50/hour compute cost estimate
            duration_days = 3  # Setup + run + analysis
            data_sources = []

        elif exp_type == ExperimentType.DATA_ANALYSIS:
            compute_hours = 2.0  # Mostly analysis, less compute
            cost_usd = 50.0  # May need to purchase datasets
            duration_days = 7  # Data collection/access + analysis
            data_sources = ["publicly_available_datasets", "kaggle", "uci_ml_repository"]

        else:  # LITERATURE_SYNTHESIS
            compute_hours = 0.5  # Minimal compute
            cost_usd = 10.0  # API costs for literature search
            duration_days = 5  # Literature review + synthesis
            data_sources = ["arxiv", "semantic_scholar", "pubmed"]

        # Domain-specific adjustments
        if "biology" in hypothesis.domain.lower() or "medicine" in hypothesis.domain.lower():
            duration_days *= 1.5  # Biological experiments take longer
            cost_usd *= 1.5

        if "machine_learning" in hypothesis.domain.lower():
            compute_hours *= 2  # ML experiments need more compute
            cost_usd += 20.0  # API costs (Claude, embeddings)

        return {
            "compute_hours": round(compute_hours, 1),
            "cost_usd": round(cost_usd, 2),
            "duration_days": round(duration_days),
            "data_sources": data_sources
        }

    def _identify_challenges(self, hypothesis: Hypothesis) -> List[str]:
        """
        Identify challenges in testing the hypothesis.

        Args:
            hypothesis: Hypothesis

        Returns:
            List[str]: Identified challenges
        """
        challenges = []
        statement = hypothesis.statement.lower()

        # Check for vague language
        if any(word in statement for word in ["maybe", "might", "possibly", "perhaps", "potentially"]):
            challenges.append("Hypothesis uses vague language, making it difficult to define success criteria")

        # Check for unmeasurable outcomes
        abstract_terms = ["better", "worse", "good", "bad", "quality", "effectiveness"]
        if any(term in statement for term in abstract_terms) and not any(q in statement for q in ["measure", "metric", "score"]):
            challenges.append("Outcome is abstract without clear measurement criteria")

        # Check for causal claims
        if any(word in statement for word in ["cause", "causes", "caused"]):
            challenges.append("Causal claims require controlled experiments or robust causal inference methods")

        # Check for absolute claims
        if any(word in statement for word in ["always", "never", "all", "none", "every"]):
            challenges.append("Absolute claims are difficult to test exhaustively")

        # Check for multiple variables
        if statement.count(" and ") > 2 or statement.count(",") > 2:
            challenges.append("Hypothesis involves multiple variables, requiring careful experimental design")

        # Domain-specific challenges
        if hypothesis.domain in ["biology", "medicine", "neuroscience"]:
            challenges.append("Biological systems are complex; may require wet-lab experiments beyond computational scope")

        if hypothesis.domain in ["social_science", "psychology", "economics"]:
            challenges.append("Human behavior is complex and context-dependent; may require large sample sizes")

        # Check for data availability
        if "dataset" in statement or "data" in statement:
            if "specific" in statement or "proprietary" in statement:
                challenges.append("May require access to specific or proprietary datasets")

        return challenges

    def _identify_limitations(self, hypothesis: Hypothesis) -> List[str]:
        """
        Identify limitations in testing the hypothesis.

        Args:
            hypothesis: Hypothesis

        Returns:
            List[str]: Identified limitations
        """
        limitations = []

        # Computational testing limitations
        limitations.append("Testing is limited to computational/analytical methods (no physical experiments)")

        # Domain limitations
        if hypothesis.domain in ["physics", "chemistry", "materials_science"]:
            limitations.append("Cannot perform physical experiments; limited to simulation and existing data")

        if hypothesis.domain in ["biology", "medicine"]:
            limitations.append("Cannot perform wet-lab or clinical experiments; relying on computational biology and existing datasets")

        # Statistical limitations
        if "correlation" in hypothesis.statement.lower() or "association" in hypothesis.statement.lower():
            limitations.append("Correlation does not imply causation; causal claims require additional analysis")

        # Generalization limitations
        limitations.append("Results may not generalize beyond the specific datasets or simulations used")

        return limitations

    def _select_primary_experiment(
        self,
        suggested_experiments: List[Dict[str, Any]]
    ) -> ExperimentType:
        """
        Select the primary (most suitable) experiment type.

        Args:
            suggested_experiments: List of suggested experiments with scores

        Returns:
            ExperimentType: Primary experiment type
        """
        if not suggested_experiments:
            return ExperimentType.COMPUTATIONAL  # Default

        return suggested_experiments[0]["type"]

    def _llm_testability_assessment(self, hypothesis: Hypothesis) -> Optional[Dict[str, Any]]:
        """
        Use LLM for detailed testability assessment.

        Args:
            hypothesis: Hypothesis

        Returns:
            Optional[Dict]: LLM assessment results
        """
        try:
            prompt = f"""Assess the testability of this scientific hypothesis:

Hypothesis: "{hypothesis.statement}"

Rationale: {hypothesis.rationale}

Domain: {hypothesis.domain}

Evaluate:
1. How testable is this hypothesis using computational methods? (0.0-1.0)
2. What additional challenges might arise in testing it?
3. What limitations should be considered?

Provide assessment as JSON:
{{
    "confidence": 0.0-1.0,
    "additional_challenges": ["challenge 1", "challenge 2"],
    "additional_limitations": ["limitation 1"]
}}"""

            response = self.llm_client.generate_structured(
                prompt=prompt,
                schema={"confidence": "float", "additional_challenges": ["string"], "additional_limitations": ["string"]},
                max_tokens=500,
                temperature=0.3
            )

            return response

        except Exception as e:
            logger.error(f"Error in LLM testability assessment: {e}")
            return None

    def _generate_summary(
        self,
        testability_score: float,
        is_testable: bool,
        primary_experiment_type: ExperimentType,
        challenges: List[str],
        estimated_cost: Optional[float]
    ) -> str:
        """
        Generate human-readable testability summary.

        Args:
            testability_score: Testability score
            is_testable: Whether hypothesis is testable
            primary_experiment_type: Primary experiment type
            challenges: List of challenges
            estimated_cost: Estimated cost in USD

        Returns:
            str: Summary text
        """
        if not is_testable:
            return (
                f"NOT TESTABLE (score: {testability_score:.2f}). "
                f"This hypothesis falls below the testability threshold. "
                f"Primary challenges: {', '.join(challenges[:2]) if challenges else 'unclear testing criteria'}. "
                f"Consider refining the hypothesis to make it more testable."
            )

        elif testability_score >= 0.8:
            cost_str = f"${estimated_cost:.2f}" if estimated_cost else "unknown"
            return (
                f"HIGHLY TESTABLE (score: {testability_score:.2f}). "
                f"This hypothesis can be readily tested using {primary_experiment_type.value} methods. "
                f"Estimated cost: {cost_str}. "
                f"Recommended for immediate testing."
            )

        elif testability_score >= 0.6:
            return (
                f"TESTABLE (score: {testability_score:.2f}). "
                f"This hypothesis can be tested using {primary_experiment_type.value} methods. "
                f"Some challenges exist: {challenges[0] if challenges else 'none identified'}. "
                f"Recommended with caveats."
            )

        else:
            return (
                f"MARGINALLY TESTABLE (score: {testability_score:.2f}). "
                f"This hypothesis barely meets the testability threshold. "
                f"Primary experiment type: {primary_experiment_type.value}. "
                f"Significant challenges: {', '.join(challenges[:2]) if challenges else 'resource intensive'}. "
                f"Consider if testing resources are available."
            )


def analyze_hypothesis_testability(
    hypothesis: Hypothesis,
    testability_threshold: float = 0.3
) -> TestabilityReport:
    """
    Convenience function to analyze hypothesis testability.

    Args:
        hypothesis: Hypothesis to analyze
        testability_threshold: Minimum testability score (default: 0.3)

    Returns:
        TestabilityReport: Testability analysis

    Example:
        ```python
        report = analyze_hypothesis_testability(my_hypothesis)
        if report.is_testable:
            print(f"Test using: {report.primary_experiment_type}")
        ```
    """
    analyzer = TestabilityAnalyzer(testability_threshold=testability_threshold)
    return analyzer.analyze_testability(hypothesis)
