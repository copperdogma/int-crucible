Knowledge Modules
=================

The knowledge management system integrates Neo4j graph database and embedding-based
similarity search for literature synthesis and knowledge discovery.

Knowledge Graph
---------------

Neo4j-based knowledge graph for structured knowledge representation.

.. automodule:: kosmos.knowledge.graph
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Embeddings
----------

Vector embeddings for semantic similarity and literature search.

.. automodule:: kosmos.knowledge.embeddings
   :members:
   :undoc-members:
   :show-inheritance:

Domain Knowledge Bases
----------------------

Domain-specific knowledge bases with curated information.

.. automodule:: kosmos.knowledge.domain_kb
   :members:
   :undoc-members:
   :show-inheritance:

Knowledge Graph Structure
--------------------------

The knowledge graph uses Neo4j to represent:

**Entities**
   - Proteins, genes, compounds, diseases, brain regions, materials, etc.

**Relationships**
   - "regulates", "causes", "correlates_with", "inhibits", etc.

**Properties**
   - Entity metadata, confidence scores, evidence sources

**Hypotheses**
   - Links to related entities and evidence

Graph Schema::

   (Entity)-[:RELATIONSHIP {properties}]->(Entity)
   (Hypothesis)-[:TESTS]->(Entity)
   (Hypothesis)-[:SUPPORTED_BY]->(Evidence)
   (Paper)-[:MENTIONS]->(Entity)

Usage Examples
--------------

**Creating and querying the knowledge graph**::

   from kosmos.knowledge.graph import KnowledgeGraph

   # Initialize graph
   kg = KnowledgeGraph(
       uri="bolt://localhost:7687",
       user="neo4j",
       password="password"
   )

   # Add entities
   kg.add_entity(
       entity_type="protein",
       entity_id="TP53",
       properties={
           "name": "Tumor protein p53",
           "gene": "TP53",
           "function": "Tumor suppressor",
           "species": "human"
       }
   )

   kg.add_entity(
       entity_type="disease",
       entity_id="cancer",
       properties={
           "name": "Cancer",
           "category": "neoplasm"
       }
   )

   # Add relationship
   kg.add_relationship(
       source_id="TP53",
       relationship="prevents",
       target_id="cancer",
       properties={
           "confidence": 0.95,
           "evidence": ["PMID:12345678", "PMID:87654321"]
       }
   )

   # Query relationships
   related = kg.get_related_entities(
       entity_id="TP53",
       relationship_type="prevents",
       max_depth=2
   )

   for entity, path in related:
       print(f"Entity: {entity['name']}")
       print(f"Path: {' -> '.join(path)}")

**Using embeddings for similarity search**::

   from kosmos.knowledge.embeddings import EmbeddingEngine

   # Initialize embedding engine
   embedder = EmbeddingEngine(
       model="sentence-transformers/all-mpnet-base-v2"
   )

   # Create embeddings for documents
   documents = [
       "Protein folding is essential for cellular function",
       "Misfolded proteins cause neurodegenerative diseases",
       "Chaperones assist in protein folding"
   ]

   embeddings = embedder.embed_documents(documents)

   # Find similar documents
   query = "What are protein folding mechanisms?"
   query_embedding = embedder.embed_query(query)

   similar = embedder.find_similar(
       query_embedding=query_embedding,
       document_embeddings=embeddings,
       top_k=2
   )

   for doc_idx, similarity in similar:
       print(f"Document: {documents[doc_idx]}")
       print(f"Similarity: {similarity:.3f}")
       print()

**Working with domain knowledge bases**::

   from kosmos.knowledge.domain_kb import DomainKnowledgeBase

   # Load biology knowledge base
   bio_kb = DomainKnowledgeBase(domain="biology")

   # Query pathways
   pathways = bio_kb.get_pathways(
       involving=["glucose", "ATP"],
       pathway_type="metabolic"
   )

   for pathway in pathways:
       print(f"Pathway: {pathway['name']}")
       print(f"Components: {', '.join(pathway['components'])}")
       print(f"Reactions: {len(pathway['reactions'])}")
       print()

   # Get domain ontology
   ontology = bio_kb.get_ontology()
   print(f"Entities: {len(ontology['entities'])}")
   print(f"Relationships: {len(ontology['relationships'])}")

Literature Integration
----------------------

Integrate literature into knowledge graph:

.. code-block:: python

   from kosmos.knowledge.graph import KnowledgeGraph

   kg = KnowledgeGraph()

   # Add paper
   kg.add_paper(
       pmid="12345678",
       title="Mechanisms of neurodegeneration",
       authors=["Smith J", "Doe J"],
       abstract="...",
       year=2023,
       journal="Nature Neuroscience"
   )

   # Link paper to entities
   kg.link_paper_to_entity(
       pmid="12345678",
       entity_id="alzheimers",
       entity_type="disease",
       mention_context="Alzheimer's disease is characterized by..."
   )

   # Query papers mentioning entity
   papers = kg.get_papers_mentioning(
       entity_id="alzheimers",
       limit=10
   )

Knowledge-Enhanced Hypothesis Generation
-----------------------------------------

Use knowledge graph to generate informed hypotheses:

.. code-block:: python

   from kosmos.hypothesis.generator import HypothesisGenerator
   from kosmos.knowledge.graph import KnowledgeGraph

   kg = KnowledgeGraph()
   generator = HypothesisGenerator()

   # Get context from knowledge graph
   context = kg.get_entity_context(
       entity_id="synaptic_plasticity",
       depth=2
   )

   # Generate hypotheses with knowledge
   hypotheses = generator.generate(
       question="How does synaptic plasticity relate to learning?",
       domain="neuroscience",
       knowledge_context=context
   )

   for hyp in hypotheses:
       print(f"Hypothesis: {hyp.claim}")
       print(f"Supporting entities: {hyp.related_entities}")
       print(f"Knowledge gap: {hyp.addresses_gap}")
       print()

Embedding-Based Literature Search
----------------------------------

Search literature using semantic similarity:

.. code-block:: python

   from kosmos.knowledge.embeddings import EmbeddingEngine
   import json

   embedder = EmbeddingEngine()

   # Index literature corpus
   papers = load_papers_from_pubmed("neuroscience", limit=10000)

   paper_embeddings = embedder.embed_documents(
       [f"{p['title']} {p['abstract']}" for p in papers]
   )

   # Search by research question
   query = "What are the molecular mechanisms of synaptic plasticity?"
   query_embedding = embedder.embed_query(query)

   # Find most relevant papers
   similar_papers = embedder.find_similar(
       query_embedding=query_embedding,
       document_embeddings=paper_embeddings,
       top_k=20
   )

   for paper_idx, similarity in similar_papers:
       paper = papers[paper_idx]
       print(f"Paper: {paper['title']}")
       print(f"Similarity: {similarity:.3f}")
       print(f"PMID: {paper['pmid']}")
       print()

Knowledge Graph Visualization
------------------------------

Visualize graph structure and relationships:

.. code-block:: python

   from kosmos.knowledge.graph import KnowledgeGraph
   import networkx as nx
   import matplotlib.pyplot as plt

   kg = KnowledgeGraph()

   # Get subgraph
   subgraph = kg.get_subgraph(
       center_entity="TP53",
       radius=2
   )

   # Convert to NetworkX
   G = nx.Graph()
   for node in subgraph['nodes']:
       G.add_node(node['id'], **node['properties'])
   for edge in subgraph['edges']:
       G.add_edge(edge['source'], edge['target'], **edge['properties'])

   # Visualize
   plt.figure(figsize=(12, 8))
   nx.draw(G, with_labels=True, node_color='lightblue',
           node_size=2000, font_size=10)
   plt.title("Knowledge Graph around TP53")
   plt.savefig("knowledge_graph.png")

Knowledge Base Statistics
--------------------------

Get statistics about the knowledge base:

.. code-block:: python

   from kosmos.knowledge.graph import KnowledgeGraph

   kg = KnowledgeGraph()

   stats = kg.get_statistics()

   print(f"Total entities: {stats['entity_count']}")
   print(f"Total relationships: {stats['relationship_count']}")
   print(f"Total papers: {stats['paper_count']}")
   print(f"Total hypotheses: {stats['hypothesis_count']}")

   print("\\nEntity types:")
   for entity_type, count in stats['entity_types'].items():
       print(f"  {entity_type}: {count}")

   print("\\nRelationship types:")
   for rel_type, count in stats['relationship_types'].items():
       print(f"  {rel_type}: {count}")

Advanced Queries
----------------

Complex graph queries:

.. code-block:: python

   # Find paths between entities
   paths = kg.find_paths(
       source_id="protein_A",
       target_id="disease_X",
       max_length=4,
       relationship_types=["regulates", "causes", "inhibits"]
   )

   for path in paths:
       print(" -> ".join([node['name'] for node in path]))

   # Find entities with specific patterns
   entities = kg.query(
       cypher="""
       MATCH (p:Protein)-[:REGULATES]->(g:Gene)-[:CAUSES]->(d:Disease)
       WHERE d.name CONTAINS 'cancer'
       RETURN p, g, d
       LIMIT 10
       """
   )

   # Community detection
   communities = kg.detect_communities(
       entity_type="protein",
       algorithm="louvain"
   )

   for community_id, members in communities.items():
       print(f"Community {community_id}: {len(members)} proteins")

Knowledge Graph Maintenance
----------------------------

Keep the knowledge graph up to date:

.. code-block:: python

   # Update entity properties
   kg.update_entity(
       entity_id="TP53",
       properties={"last_updated": "2025-01-15"}
   )

   # Merge duplicate entities
   kg.merge_entities(
       entity_ids=["protein_123", "protein_456"],
       primary_id="protein_123"
   )

   # Remove outdated relationships
   kg.remove_relationships(
       relationship_type="hypothesized",
       age_days=365,
       confidence_threshold=0.3
   )

   # Backup and restore
   kg.backup(path="knowledge_graph_backup.json")
   kg.restore(path="knowledge_graph_backup.json")
