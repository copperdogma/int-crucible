"""Materials science experiment templates"""

from kosmos.experiments.templates.materials.parameter_correlation import ParameterCorrelationTemplate
from kosmos.experiments.templates.materials.optimization import MultiParameterOptimizationTemplate
from kosmos.experiments.templates.materials.shap_analysis import SHAPAnalysisTemplate

__all__ = [
    'ParameterCorrelationTemplate',
    'MultiParameterOptimizationTemplate',
    'SHAPAnalysisTemplate',
]
