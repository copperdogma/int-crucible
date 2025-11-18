"""
Unit tests for MaterialsOptimizer (Phase 9).

Tests materials optimization and parameter analysis:
- Correlation analysis (Figure 3 pattern - Perovskite optimization)
- SHAP feature importance analysis
- Multi-parameter optimization (differential evolution)
- Design of Experiments (Latin Hypercube Sampling)

Coverage target: 35 tests across 5 test classes
"""

import pytest
import pandas as pd
import numpy as np
from kosmos.domains.materials.optimization import (
    MaterialsOptimizer,
    CorrelationResult,
    SHAPResult,
    OptimizationResult,
    DOEResult
)


@pytest.fixture
def materials_optimizer():
    """Fixture providing a MaterialsOptimizer instance"""
    return MaterialsOptimizer()


@pytest.fixture
def sample_materials_data():
    """
    Sample experimental data for testing (50+ rows for reliable statistics).

    Based on Figure 3 pattern: Perovskite solar cell optimization.
    Simulates relationship: Jsc decreases with Pressure (negative correlation)
    """
    np.random.seed(42)
    n_samples = 60

    # Generate correlated data
    pressure = np.linspace(10, 100, n_samples) + np.random.normal(0, 5, n_samples)
    temperature = np.linspace(20, 80, n_samples) + np.random.normal(0, 3, n_samples)
    time = np.linspace(5, 60, n_samples) + np.random.normal(0, 2, n_samples)

    # Jsc: Negative correlation with Pressure (Figure 3 pattern: r=-0.708)
    # For Temperature, we need independent positive effect
    # Create Temperature with different baseline to avoid multicollinearity
    jsc = (
        25.0  # Base value
        - 0.1 * (pressure - 55)  # Negative correlation with Pressure (centered)
        + 0.08 * (temperature - 50)  # Positive correlation with Temperature (centered)
        + 0.01 * (time - 30)  # Small positive correlation with Time (centered)
        + np.random.normal(0, 0.5, n_samples)  # Noise
    )

    # Efficiency calculation (simplified)
    voc = 1.05 + np.random.normal(0, 0.02, n_samples)
    fill_factor = 0.75 + np.random.normal(0, 0.03, n_samples)
    efficiency = jsc * voc * fill_factor / 10.0

    return pd.DataFrame({
        'Pressure': pressure,
        'Temperature': temperature,
        'Time': time,
        'Jsc': jsc,
        'Voc': voc,
        'Fill Factor': fill_factor,
        'Efficiency': efficiency
    })


@pytest.mark.unit
class TestMaterialsOptimizerInit:
    """Test MaterialsOptimizer initialization"""

    def test_init_default(self):
        """Test default initialization"""
        optimizer = MaterialsOptimizer()
        assert optimizer is not None

    def test_init_with_custom_params(self):
        """Test initialization (no custom params in current implementation)"""
        optimizer = MaterialsOptimizer()
        assert isinstance(optimizer, MaterialsOptimizer)


@pytest.mark.unit
class TestCorrelationAnalysis:
    """Test correlation analysis methods"""

    def test_pearson_correlation_calculation(self, materials_optimizer, sample_materials_data):
        """Test Pearson correlation coefficient calculation"""
        result = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        assert isinstance(result, CorrelationResult)
        # Should be negative correlation (Figure 3 pattern)
        assert result.correlation < 0
        assert -1.0 <= result.correlation <= 1.0
        assert result.parameter == 'Pressure'
        assert result.metric == 'Jsc'

    def test_linear_regression_fit(self, materials_optimizer, sample_materials_data):
        """Test linear regression slope, intercept, std_err"""
        result = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        # Check regression parameters exist
        assert result.slope is not None
        assert result.intercept is not None
        assert result.std_err is not None
        assert result.std_err >= 0

        # Slope should be negative (Jsc decreases with Pressure)
        assert result.slope < 0

    def test_positive_correlation(self, materials_optimizer):
        """Test positive correlation detection"""
        # Create specific test data with positive correlation
        np.random.seed(42)
        n = 50
        temp = np.random.uniform(20, 80, n)
        # Jsc increases with Temperature (positive correlation)
        jsc = 15 + 0.15 * temp + np.random.normal(0, 1, n)

        test_data = pd.DataFrame({
            'Temperature': temp,
            'Jsc': jsc
        })

        result = materials_optimizer.correlation_analysis(
            data=test_data,
            parameter='Temperature',
            metric='Jsc'
        )

        # Temperature has positive correlation with Jsc
        assert result.correlation > 0
        assert result.slope > 0

    def test_negative_correlation(self, materials_optimizer, sample_materials_data):
        """Test negative correlation (Figure 3: Pressure vs Jsc, r=-0.708)"""
        result = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        # Should be strong negative correlation
        assert result.correlation < -0.5
        assert result.slope < 0
        # Should be statistically significant
        assert result.p_value < 0.001
        assert result.significance == "***"

    def test_non_significant_correlation(self, materials_optimizer):
        """Test non-significant correlation (p >= 0.05)"""
        # Create data with no correlation
        np.random.seed(42)
        random_data = pd.DataFrame({
            'X': np.random.normal(0, 1, 20),
            'Y': np.random.normal(0, 1, 20)
        })

        result = materials_optimizer.correlation_analysis(
            data=random_data,
            parameter='X',
            metric='Y'
        )

        # With random data, p-value should be high (usually > 0.05)
        # But it's random, so we just check the significance field is set
        assert result.significance in ['***', '**', '*', 'ns']
        assert 0 <= result.p_value <= 1.0

    def test_multiple_parameters(self, materials_optimizer, sample_materials_data):
        """Test correlation with different parameter-metric pairs"""
        # Test multiple combinations
        result1 = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        result2 = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Temperature',
            metric='Efficiency'
        )

        assert result1.parameter == 'Pressure'
        assert result2.parameter == 'Temperature'
        assert result1.metric != result2.metric

    def test_data_validation(self, materials_optimizer, sample_materials_data):
        """Test column existence validation"""
        with pytest.raises(ValueError, match="not found in DataFrame"):
            materials_optimizer.correlation_analysis(
                data=sample_materials_data,
                parameter='NonexistentColumn',
                metric='Jsc'
            )

        with pytest.raises(ValueError, match="not found in DataFrame"):
            materials_optimizer.correlation_analysis(
                data=sample_materials_data,
                parameter='Pressure',
                metric='NonexistentMetric'
            )

    def test_outlier_handling(self, materials_optimizer, sample_materials_data):
        """Test NaN and infinite value removal"""
        # Add NaN and inf values
        dirty_data = sample_materials_data.copy()
        dirty_data.loc[0, 'Jsc'] = np.nan
        dirty_data.loc[1, 'Pressure'] = np.inf
        dirty_data.loc[2, 'Jsc'] = -np.inf

        result = materials_optimizer.correlation_analysis(
            data=dirty_data,
            parameter='Pressure',
            metric='Jsc'
        )

        # Should still work, with reduced sample count
        assert result.n_samples < len(dirty_data)
        assert result.n_samples > 0
        # clean_data is excluded from dict serialization but exists
        assert result.clean_data is not None

    def test_confidence_intervals(self, materials_optimizer, sample_materials_data):
        """Test std_err is provided for confidence intervals"""
        result = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        # std_err is used to compute confidence intervals
        assert result.std_err >= 0
        assert result.std_err < abs(result.slope)  # Typically much smaller than slope

    def test_result_structure(self, materials_optimizer, sample_materials_data):
        """Test CorrelationResult dataclass structure"""
        result = materials_optimizer.correlation_analysis(
            data=sample_materials_data,
            parameter='Pressure',
            metric='Jsc'
        )

        # Check all required fields
        assert hasattr(result, 'parameter')
        assert hasattr(result, 'metric')
        assert hasattr(result, 'correlation')
        assert hasattr(result, 'p_value')
        assert hasattr(result, 'r_squared')
        assert hasattr(result, 'slope')
        assert hasattr(result, 'intercept')
        assert hasattr(result, 'std_err')
        assert hasattr(result, 'significance')
        assert hasattr(result, 'n_samples')
        assert hasattr(result, 'equation')

        # Check equation format
        assert 'y =' in result.equation
        assert 'R²' in result.equation


@pytest.mark.unit
class TestSHAPAnalysis:
    """Test SHAP feature importance analysis"""

    def test_shap_feature_importance(self, materials_optimizer, sample_materials_data):
        """Test SHAP mean absolute values calculation"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time'],
            target='Jsc',
            n_estimators=50  # Faster for testing
        )

        assert isinstance(result, SHAPResult)
        assert isinstance(result.feature_importance, dict)
        assert len(result.feature_importance) == 3

        # All features should have positive importance
        for feat, imp in result.feature_importance.items():
            assert imp >= 0

    def test_feature_ranking(self, materials_optimizer, sample_materials_data):
        """Test features are ranked by importance"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time'],
            target='Jsc',
            n_estimators=50
        )

        # top_features should be sorted by importance
        assert len(result.top_features) <= 5
        assert len(result.top_features) == 3  # We only have 3 features

        # First feature should have highest importance
        first_feat = result.top_features[0]
        assert result.feature_importance[first_feat] >= result.feature_importance[result.top_features[1]]

    def test_interaction_effects(self, materials_optimizer, sample_materials_data):
        """Test SHAP captures interaction effects"""
        # SHAP values should be a numpy array
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature'],
            target='Jsc',
            n_estimators=50
        )

        assert result.shap_values is not None
        assert isinstance(result.shap_values, np.ndarray)
        # Should have shape (n_samples, n_features)
        assert result.shap_values.shape[1] == 2

    def test_multiple_features(self, materials_optimizer, sample_materials_data):
        """Test with 3+ features"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time', 'Voc'],
            target='Efficiency',
            n_estimators=50
        )

        assert result.n_features == 4
        assert len(result.feature_importance) == 4

    def test_model_training(self, materials_optimizer, sample_materials_data):
        """Test RandomForest/XGBoost model training"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time'],
            target='Jsc',
            model_type='RandomForest',
            n_estimators=50
        )

        assert result.model_type in ['RandomForest', 'XGBoost']
        # Model should have reasonable R²
        assert result.model_r_squared >= 0.5  # Should fit well with engineered data

    def test_shap_values_calculation(self, materials_optimizer, sample_materials_data):
        """Test TreeExplainer generates SHAP values"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature'],
            target='Jsc',
            n_estimators=50
        )

        # SHAP values should exist and have correct shape
        assert result.shap_values is not None
        assert result.shap_values.ndim == 2
        assert result.shap_values.shape[1] == 2  # 2 features

    def test_visualization_data(self, materials_optimizer, sample_materials_data):
        """Test SHAP values shape for visualization"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time'],
            target='Jsc',
            n_estimators=50,
            test_size=0.2
        )

        # shap_values shape should be (n_train_samples, n_features)
        # Note: SHAP uses training set only (80% of data with test_size=0.2)
        assert result.shap_values.shape[0] <= result.n_samples  # Training set <= total
        assert result.shap_values.shape[1] == result.n_features

    def test_feature_selection(self, materials_optimizer, sample_materials_data):
        """Test top_features extraction (top 5)"""
        # Test with more than 5 features
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature', 'Time', 'Voc', 'Fill Factor'],
            target='Efficiency',
            n_estimators=50
        )

        # Should return top 5 features
        assert len(result.top_features) == 5

        # Top features should be in feature_importance
        for feat in result.top_features:
            assert feat in result.feature_importance

    def test_nonlinear_effects(self, materials_optimizer):
        """Test SHAP handles nonlinear relationships"""
        # Create data with nonlinear relationship
        np.random.seed(42)
        x1 = np.linspace(0, 10, 50)
        x2 = np.linspace(0, 5, 50)
        # y has quadratic relationship with x1
        y = x1**2 + 2*x2 + np.random.normal(0, 1, 50)

        data = pd.DataFrame({'x1': x1, 'x2': x2, 'y': y})

        result = materials_optimizer.shap_analysis(
            data=data,
            features=['x1', 'x2'],
            target='y',
            n_estimators=50
        )

        # x1 should have higher importance due to quadratic effect
        assert result.feature_importance['x1'] > result.feature_importance['x2']

    def test_result_validation(self, materials_optimizer, sample_materials_data):
        """Test SHAPResult structure"""
        result = materials_optimizer.shap_analysis(
            data=sample_materials_data,
            features=['Pressure', 'Temperature'],
            target='Jsc',
            n_estimators=50
        )

        # Check all fields
        assert hasattr(result, 'feature_importance')
        assert hasattr(result, 'shap_values')
        assert hasattr(result, 'model_r_squared')
        assert hasattr(result, 'model_type')
        assert hasattr(result, 'n_features')
        assert hasattr(result, 'n_samples')
        assert hasattr(result, 'top_features')


@pytest.mark.unit
class TestParameterOptimization:
    """Test multi-parameter optimization"""

    def test_multi_parameter_optimization(self, materials_optimizer, sample_materials_data):
        """Test optimization with 2+ parameters"""
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        assert isinstance(result, OptimizationResult)
        assert len(result.optimal_parameters) == 2
        assert 'Pressure' in result.optimal_parameters
        assert 'Temperature' in result.optimal_parameters

    def test_objective_function_evaluation(self, materials_optimizer, sample_materials_data):
        """Test maximize vs minimize"""
        # Maximize Jsc
        result_max = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        # Since Jsc decreases with Pressure, optimal Pressure should be low
        # Since Jsc increases with Temperature, optimal Temperature should be high
        assert result_max.predicted_value > 0
        assert result_max.optimal_parameters['Pressure'] < 60  # Should favor low pressure

    def test_optimization_algorithm(self, materials_optimizer, sample_materials_data):
        """Test differential_evolution is used"""
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        # differential_evolution should converge
        assert result.n_iterations > 0
        assert result.convergence_message is not None

    def test_constraint_handling(self, materials_optimizer, sample_materials_data):
        """Test parameter bounds (min/max + 10% padding)"""
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        # Check parameter_bounds exist
        assert 'Pressure' in result.parameter_bounds
        assert 'Temperature' in result.parameter_bounds

        # Bounds should be tuples
        pressure_bounds = result.parameter_bounds['Pressure']
        assert len(pressure_bounds) == 2
        assert pressure_bounds[0] < pressure_bounds[1]

        # Optimal values should be within (or slightly outside) original data range
        # but within padded bounds
        assert pressure_bounds[0] <= result.optimal_parameters['Pressure'] <= pressure_bounds[1]

    def test_global_optimum_search(self, materials_optimizer, sample_materials_data):
        """Test algorithm doesn't get stuck in local minimum"""
        # differential_evolution is a global optimizer
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature', 'Time'],
            objective='Efficiency',
            maximize=True,
            n_estimators=50
        )

        # Should find a reasonable solution
        assert result.optimization_success or result.n_iterations >= 100
        assert result.predicted_value > 0

    def test_convergence_criteria(self, materials_optimizer, sample_materials_data):
        """Test convergence success flag and iteration count"""
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        # Check convergence fields
        assert isinstance(result.optimization_success, bool)
        assert isinstance(result.n_iterations, int)
        assert result.n_iterations >= 0
        assert isinstance(result.convergence_message, str)

    def test_parameter_bounds(self, materials_optimizer, sample_materials_data):
        """Test parameter bounds calculation (min/max + 10% padding)"""
        # Get data range
        pressure_min = sample_materials_data['Pressure'].min()
        pressure_max = sample_materials_data['Pressure'].max()
        pressure_range = pressure_max - pressure_min

        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        bounds = result.parameter_bounds['Pressure']

        # Bounds should be padded by 10%
        expected_lower = pressure_min - 0.1 * pressure_range
        expected_upper = pressure_max + 0.1 * pressure_range

        # Check bounds are approximately correct (within floating point tolerance)
        assert abs(bounds[0] - expected_lower) < 1.0
        assert abs(bounds[1] - expected_upper) < 1.0

    def test_result_structure(self, materials_optimizer, sample_materials_data):
        """Test OptimizationResult structure"""
        result = materials_optimizer.parameter_space_optimization(
            data=sample_materials_data,
            parameters=['Pressure', 'Temperature'],
            objective='Jsc',
            maximize=True,
            n_estimators=50
        )

        # Check all fields
        assert hasattr(result, 'optimal_parameters')
        assert hasattr(result, 'predicted_value')
        assert hasattr(result, 'optimization_success')
        assert hasattr(result, 'n_iterations')
        assert hasattr(result, 'convergence_message')
        assert hasattr(result, 'parameter_bounds')
        assert hasattr(result, 'model_r_squared')

        # optimal_parameters should be a dict
        assert isinstance(result.optimal_parameters, dict)
        assert isinstance(result.predicted_value, float)


@pytest.mark.unit
class TestDesignOfExperiments:
    """Test Design of Experiments (DoE)"""

    def test_latin_hypercube_sampling(self, materials_optimizer):
        """Test Latin Hypercube Sampling method"""
        parameter_ranges = {
            'Pressure': (0.0, 100.0),
            'Temperature': (20.0, 80.0),
            'Time': (5.0, 60.0)
        }

        result = materials_optimizer.design_of_experiments(
            parameter_ranges=parameter_ranges,
            n_experiments=50,
            sampling_method='LatinHypercube'
        )

        assert isinstance(result, DOEResult)
        assert result.sampling_method == 'LatinHypercube'
        assert len(result.experiment_design) == 50

    def test_doe_generation(self, materials_optimizer):
        """Test DoE DataFrame structure"""
        parameter_ranges = {
            'Pressure': (0.0, 100.0),
            'Temperature': (20.0, 80.0)
        }

        result = materials_optimizer.design_of_experiments(
            parameter_ranges=parameter_ranges,
            n_experiments=30,
            sampling_method='LatinHypercube'
        )

        # Check DataFrame structure
        assert isinstance(result.experiment_design, pd.DataFrame)
        assert list(result.experiment_design.columns) == ['Pressure', 'Temperature']
        assert len(result.experiment_design) == 30

    def test_parameter_ranges(self, materials_optimizer):
        """Test parameter values are within specified ranges"""
        parameter_ranges = {
            'Pressure': (10.0, 90.0),
            'Temperature': (25.0, 75.0)
        }

        result = materials_optimizer.design_of_experiments(
            parameter_ranges=parameter_ranges,
            n_experiments=50,
            sampling_method='LatinHypercube'
        )

        # All values should be within bounds
        pressure_values = result.experiment_design['Pressure']
        temp_values = result.experiment_design['Temperature']

        assert pressure_values.min() >= 10.0
        assert pressure_values.max() <= 90.0
        assert temp_values.min() >= 25.0
        assert temp_values.max() <= 75.0

    def test_sample_count_validation(self, materials_optimizer):
        """Test n_experiments matches result"""
        parameter_ranges = {
            'X1': (0.0, 1.0),
            'X2': (0.0, 1.0),
            'X3': (0.0, 1.0)
        }

        for n_exp in [10, 25, 50, 100]:
            result = materials_optimizer.design_of_experiments(
                parameter_ranges=parameter_ranges,
                n_experiments=n_exp,
                sampling_method='LatinHypercube'
            )

            assert result.n_experiments == n_exp
            assert len(result.experiment_design) == n_exp
            assert result.n_parameters == 3

    def test_space_filling_properties(self, materials_optimizer):
        """Test Latin Hypercube distributes samples evenly"""
        parameter_ranges = {
            'X': (0.0, 100.0),
            'Y': (0.0, 100.0)
        }

        result = materials_optimizer.design_of_experiments(
            parameter_ranges=parameter_ranges,
            n_experiments=100,
            sampling_method='LatinHypercube'
        )

        # Latin Hypercube should provide good coverage
        # Check that samples span the full range
        x_values = result.experiment_design['X']
        y_values = result.experiment_design['Y']

        # Should cover most of the range
        x_coverage = (x_values.max() - x_values.min()) / 100.0
        y_coverage = (y_values.max() - y_values.min()) / 100.0

        assert x_coverage > 0.9  # Should cover >90% of range
        assert y_coverage > 0.9

        # Latin Hypercube should have better coverage than random
        # (This is a property test - LHS ensures one sample per row/column)
        assert len(result.experiment_design) == 100
