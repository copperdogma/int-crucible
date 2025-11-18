Agent Modules
=============

The agent framework provides autonomous AI agents that collaborate to conduct scientific research.
Each agent has a specialized role in the research pipeline.

Agent Base Classes
------------------

Base Agent
^^^^^^^^^^

Abstract base class for all Kosmos agents.

.. automodule:: kosmos.agents.base
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Agent Registry
^^^^^^^^^^^^^^

Registry for managing and discovering available agents.

.. automodule:: kosmos.agents.registry
   :members:
   :undoc-members:
   :show-inheritance:

Research Director
-----------------

The orchestrator agent that coordinates the entire research workflow.

.. automodule:: kosmos.agents.research_director
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Hypothesis Generator
--------------------

Generates scientific hypotheses based on research questions and existing knowledge.

.. automodule:: kosmos.agents.hypothesis_generator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Experiment Designer
-------------------

Designs computational experiments to test hypotheses.

.. automodule:: kosmos.agents.experiment_designer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Data Analyst
------------

Analyzes experimental results and generates insights.

.. automodule:: kosmos.agents.data_analyst
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Literature Analyzer
-------------------

Integrates scientific literature and existing knowledge.

.. automodule:: kosmos.agents.literature_analyzer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Agent Communication
-------------------

Agents communicate through a message-passing system with typed messages:

- **HypothesisMessage**: Hypothesis generation requests/responses
- **ExperimentMessage**: Experiment design and execution
- **AnalysisMessage**: Data analysis results
- **FeedbackMessage**: Iterative refinement signals

Agent Lifecycle
---------------

All agents follow a standard lifecycle:

1. **Initialize**: Load configuration and domain knowledge
2. **Execute**: Process input and generate output
3. **Persist**: Save state and intermediate results
4. **Cleanup**: Release resources

Usage Examples
--------------

**Using the Research Director**::

   from kosmos.agents.research_director import ResearchDirectorAgent
   from kosmos.config import get_config

   # Initialize director with configuration
   config = get_config()
   director = ResearchDirectorAgent(config=config)

   # Conduct research
   results = director.conduct_research(
       question="What causes Alzheimer's disease?",
       domain="neuroscience",
       max_iterations=10
   )

   # Access results
   hypotheses = results.get("hypotheses", [])
   experiments = results.get("experiments", [])
   findings = results.get("findings", "")

**Generating hypotheses directly**::

   from kosmos.agents.hypothesis_generator import HypothesisGeneratorAgent

   generator = HypothesisGeneratorAgent()
   hypotheses = generator.generate_hypotheses(
       question="How do cells regulate metabolism?",
       domain="biology",
       context={"existing_knowledge": "..."}
   )

   for hyp in hypotheses:
       print(f"Hypothesis: {hyp.claim}")
       print(f"Novelty: {hyp.novelty_score:.2f}")
       print(f"Priority: {hyp.priority_score:.2f}")

**Designing experiments**::

   from kosmos.agents.experiment_designer import ExperimentDesignerAgent

   designer = ExperimentDesignerAgent()
   experiments = designer.design_experiments(
       hypothesis="Increased glucose metabolism correlates with tumor growth",
       domain="biology",
       available_tools=["KEGG", "expression_analysis"]
   )

   for exp in experiments:
       print(f"Experiment: {exp.description}")
       print(f"Type: {exp.experiment_type}")
       print(f"Estimated duration: {exp.estimated_duration}")

**Analyzing literature**::

   from kosmos.agents.literature_analyzer import LiteratureAnalyzerAgent

   analyzer = LiteratureAnalyzerAgent()
   analysis = analyzer.analyze_literature(
       query="synaptic plasticity mechanisms",
       domain="neuroscience",
       max_papers=50
   )

   print(f"Found {len(analysis['papers'])} relevant papers")
   print(f"Key themes: {', '.join(analysis['themes'])}")
   print(f"Knowledge gaps: {analysis['gaps']}")

Agent State Management
----------------------

Agents persist their state to enable recovery and iteration:

.. code-block:: python

   # Save agent state
   director.save_state("run_123")

   # Load previous state
   director = ResearchDirectorAgent.load_state("run_123")

   # Continue from checkpoint
   results = director.resume_research()

Creating Custom Agents
-----------------------

To create a custom agent, inherit from `BaseAgent`:

.. code-block:: python

   from kosmos.agents.base import BaseAgent
   from typing import Dict, Any

   class MyCustomAgent(BaseAgent):
       \"\"\"Custom agent for specialized research tasks.\"\"\"

       def __init__(self, config: Optional[Dict] = None):
           super().__init__(config)
           self.name = "MyCustomAgent"

       def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
           \"\"\"Execute the agent's main logic.\"\"\"
           # Your custom logic here
           result = self._process_input(input_data)
           return {"output": result}

       def _process_input(self, data: Dict) -> Any:
           \"\"\"Process input data.\"\"\"
           # Implementation here
           pass

See :doc:`../developer_guide` for more details on extending the agent framework.
