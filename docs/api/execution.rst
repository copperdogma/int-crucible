Execution Modules
=================

The execution engine handles code generation, sandboxed execution, and result analysis
for computational experiments.

Code Generation
---------------

Generates executable Python code from experiment designs.

.. automodule:: kosmos.execution.code_generator
   :members:
   :undoc-members:
   :show-inheritance:

Code Execution
--------------

Safely executes generated code in sandboxed Docker containers.

.. automodule:: kosmos.execution.executor
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Result Analysis
---------------

Analyzes execution results and extracts insights.

.. automodule:: kosmos.execution.analyzer
   :members:
   :undoc-members:
   :show-inheritance:

Statistical Analysis
--------------------

Statistical analysis tools for experiment results.

.. automodule:: kosmos.execution.statistics
   :members:
   :undoc-members:
   :show-inheritance:

Execution Pipeline
------------------

The execution pipeline follows these steps:

1. **Code Generation**: Transform experiment design into executable code
2. **Validation**: Check code safety and resource requirements
3. **Execution**: Run code in sandboxed Docker container
4. **Monitoring**: Track resource usage and execution progress
5. **Analysis**: Extract results and compute statistics
6. **Reporting**: Format results for review

Usage Examples
--------------

**Generating code from experiment**::

   from kosmos.execution.code_generator import CodeGenerator

   generator = CodeGenerator()
   code = generator.generate(
       experiment_type="data_analysis",
       parameters={
           "data_source": "kegg_pathway",
           "analysis_method": "differential_expression",
           "variables": ["gene_a", "gene_b"]
       },
       domain="biology"
   )

   print(code)

**Executing code safely**::

   from kosmos.execution.executor import Executor

   executor = Executor(
       docker_image="kosmos-sandbox",
       resource_limits={
           "cpu_count": 2,
           "memory_mb": 4096,
           "timeout_seconds": 300
       }
   )

   result = executor.execute(
       code=generated_code,
       input_data={"dataset": data}
   )

   if result.success:
       print(f"Output: {result.output}")
       print(f"Execution time: {result.execution_time:.2f}s")
   else:
       print(f"Error: {result.error}")

**Analyzing results**::

   from kosmos.execution.analyzer import ResultAnalyzer

   analyzer = ResultAnalyzer()
   analysis = analyzer.analyze(
       results=execution_results,
       experiment_type="correlation_analysis"
   )

   print(f"Significance: {analysis['significance']}")
   print(f"Effect size: {analysis['effect_size']}")
   print(f"Interpretation: {analysis['interpretation']}")

**Statistical analysis**::

   from kosmos.execution.statistics import (
       compute_correlation,
       compute_ttest,
       compute_anova
   )

   # Compute correlation
   corr_result = compute_correlation(
       x=variable_x,
       y=variable_y,
       method="pearson"
   )
   print(f"Correlation: r={corr_result.correlation:.3f}, p={corr_result.p_value:.4f}")

   # T-test for group differences
   ttest_result = compute_ttest(
       group1=control_data,
       group2=treatment_data
   )
   print(f"t-test: t={ttest_result.statistic:.3f}, p={ttest_result.p_value:.4f}")

   # ANOVA for multiple groups
   anova_result = compute_anova(
       groups=[group1, group2, group3]
   )
   print(f"ANOVA: F={anova_result.f_statistic:.3f}, p={anova_result.p_value:.4f}")

Safety and Sandboxing
---------------------

All code execution happens in isolated Docker containers with:

- **Resource Limits**: CPU, memory, and time constraints
- **Network Isolation**: No external network access by default
- **Filesystem Isolation**: Read-only access to most directories
- **Process Monitoring**: Real-time tracking of resource usage

Security Features::

   executor = Executor(
       resource_limits={
           "cpu_count": 2,
           "memory_mb": 4096,
           "timeout_seconds": 300,
           "max_file_size_mb": 100,
           "network_access": False
       }
   )

Code Generation Templates
--------------------------

The code generator uses templates for different experiment types:

- **data_analysis**: Load data, perform analysis, generate plots
- **simulation**: Run computational simulations with parameters
- **optimization**: Parameter optimization with objective functions
- **ml_training**: Train machine learning models
- **statistical_test**: Statistical hypothesis testing

Custom templates can be added for specialized experiment types.

Error Handling
--------------

The execution engine provides detailed error information:

- **Syntax errors**: Code generation or validation failures
- **Runtime errors**: Execution failures with stack traces
- **Resource errors**: Out of memory, timeout, or CPU limit exceeded
- **Data errors**: Invalid input data or missing dependencies

Example error handling::

   try:
       result = executor.execute(code, input_data)
       if not result.success:
           if "timeout" in result.error.lower():
               print("Execution timed out - increase timeout limit")
           elif "memory" in result.error.lower():
               print("Out of memory - reduce data size or increase limit")
           else:
               print(f"Execution failed: {result.error}")
   except Exception as e:
       print(f"Unexpected error: {e}")

Performance Monitoring
----------------------

Monitor execution performance with detailed metrics:

.. code-block:: python

   result = executor.execute(code, input_data)

   print(f"Execution time: {result.execution_time:.2f}s")
   print(f"Peak memory: {result.peak_memory_mb:.1f} MB")
   print(f"CPU usage: {result.cpu_usage:.1f}%")
   print(f"Output size: {result.output_size_bytes} bytes")

Integration with Experiments
-----------------------------

The execution engine integrates with the experiment designer:

.. code-block:: python

   from kosmos.agents.experiment_designer import ExperimentDesignerAgent
   from kosmos.execution.executor import Executor

   # Design experiment
   designer = ExperimentDesignerAgent()
   experiment = designer.design_experiments(hypothesis, domain)[0]

   # Generate code
   code = generator.generate(
       experiment_type=experiment.experiment_type,
       parameters=experiment.parameters,
       domain=domain
   )

   # Execute
   result = executor.execute(code, experiment.input_data)

   # Analyze
   analysis = analyzer.analyze(result, experiment.experiment_type)
