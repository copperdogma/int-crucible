Domain Modules
==============

Domain modules provide specialized tools, APIs, and knowledge bases for different scientific fields.
Each domain has its own set of external API clients, data analysis tools, and prompt templates.

Domain Structure
----------------

Each domain module typically contains:

- **APIs**: External service clients (KEGG, UniProt, Materials Project, etc.)
- **Tools**: Domain-specific analysis and visualization tools
- **Prompts**: Specialized prompt templates for hypothesis generation
- **Ontologies**: Domain knowledge graphs and taxonomies

Biology Domain
--------------

APIs for biological data and analysis.

Biology APIs
^^^^^^^^^^^^

.. automodule:: kosmos.domains.biology.apis
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Biology Tools
^^^^^^^^^^^^^

.. automodule:: kosmos.domains.biology.tools
   :members:
   :undoc-members:
   :show-inheritance:

Biology Prompts
^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.biology.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Neuroscience Domain
-------------------

Tools for neuroscience research and brain connectivity analysis.

Neuroscience APIs
^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.neuroscience.apis
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Neuroscience Tools
^^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.neuroscience.tools
   :members:
   :undoc-members:
   :show-inheritance:

Neuroscience Prompts
^^^^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.neuroscience.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Materials Science Domain
------------------------

Tools for materials property prediction and optimization.

Materials APIs
^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.materials.apis
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Materials Tools
^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.materials.tools
   :members:
   :undoc-members:
   :show-inheritance:

Materials Ontology
^^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.materials.ontology
   :members:
   :undoc-members:
   :show-inheritance:

Materials Prompts
^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.materials.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Physics Domain
--------------

Physics-specific tools and constants.

Physics Tools
^^^^^^^^^^^^^

.. automodule:: kosmos.domains.physics.tools
   :members:
   :undoc-members:
   :show-inheritance:

Physics Prompts
^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.physics.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Chemistry Domain
----------------

Chemistry analysis and molecular tools.

Chemistry Tools
^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.chemistry.tools
   :members:
   :undoc-members:
   :show-inheritance:

Chemistry Prompts
^^^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.chemistry.prompts
   :members:
   :undoc-members:
   :show-inheritance:

General Domain
--------------

Cross-domain tools and general-purpose utilities.

General Tools
^^^^^^^^^^^^^

.. automodule:: kosmos.domains.general.tools
   :members:
   :undoc-members:
   :show-inheritance:

General Prompts
^^^^^^^^^^^^^^^

.. automodule:: kosmos.domains.general.prompts
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

**Using Biology APIs**::

   from kosmos.domains.biology.apis import KEGGClient, UniProtClient

   # Get compound information from KEGG
   kegg = KEGGClient()
   compound = kegg.get_compound("C00031")  # Glucose
   print(f"Name: {compound['name']}")
   print(f"Formula: {compound['formula']}")

   # Get protein information from UniProt
   uniprot = UniProtClient()
   protein = uniprot.get_protein("P04637")  # TP53 protein
   print(f"Gene: {protein['gene']}")
   print(f"Function: {protein['function']}")

**Using Neuroscience APIs**::

   from kosmos.domains.neuroscience.apis import FlyWireClient

   # Query FlyWire for connectomics data
   flywire = FlyWireClient()
   connections = flywire.get_connections(neuron_id="12345")
   print(f"Found {len(connections)} synaptic connections")

**Using Materials Project API**::

   from kosmos.domains.materials.apis import MaterialsProjectClient

   # Query Materials Project
   mp = MaterialsProjectClient(api_key="your_key_here")
   materials = mp.search_materials(
       formula="Li2O",
       properties=["band_gap", "formation_energy"]
   )

   for mat in materials:
       print(f"Material: {mat['formula']}")
       print(f"Band gap: {mat['band_gap']} eV")

**Using Domain Tools**::

   from kosmos.domains.biology.tools import analyze_expression
   from kosmos.domains.neuroscience.tools import analyze_connectivity

   # Analyze gene expression
   expression_results = analyze_expression(
       data=expression_data,
       conditions=["control", "treatment"]
   )

   # Analyze brain connectivity
   connectivity_results = analyze_connectivity(
       adjacency_matrix=conn_matrix,
       method="graph_metrics"
   )

Adding New Domains
------------------

To add a new domain:

1. Create a new directory under `kosmos/domains/`
2. Implement API clients in `apis.py`
3. Create analysis tools in `tools.py`
4. Define prompt templates in `prompts.py`
5. Add domain-specific tests
6. Update domain router configuration

See :doc:`../developer_guide` for detailed instructions.

Domain-Specific Prompt Templates
---------------------------------

Each domain provides specialized prompt templates for:

- Hypothesis generation
- Experiment design
- Result interpretation
- Literature synthesis

These templates are optimized for domain-specific terminology and research patterns.

API Client Best Practices
--------------------------

When implementing API clients:

1. Use `@retry` decorator for resilience
2. Implement rate limiting
3. Cache responses when appropriate
4. Handle errors gracefully
5. Provide clear error messages
6. Support both synchronous and async operations
7. Include comprehensive docstrings

Example::

   from tenacity import retry, stop_after_attempt, wait_exponential
   import httpx

   class MyAPIClient:
       \"\"\"Client for MyAPI service.\"\"\"

       def __init__(self, api_key: Optional[str] = None):
           self.api_key = api_key
           self.client = httpx.Client(timeout=30.0)
           self.base_url = "https://api.example.com"

       @retry(
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=2, max=10)
       )
       def get_data(self, resource_id: str) -> Dict[str, Any]:
           \"\"\"Get data for a resource.

           Args:
               resource_id: ID of the resource to fetch

           Returns:
               Dictionary containing resource data

           Raises:
               ValueError: If resource_id is invalid
               httpx.HTTPError: If API request fails
           \"\"\"
           url = f"{self.base_url}/resources/{resource_id}"
           response = self.client.get(url)
           response.raise_for_status()
           return response.json()
