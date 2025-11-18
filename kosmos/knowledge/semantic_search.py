"""
High-level semantic search API for scientific literature.

Combines unified literature search with vector database and embeddings
for intelligent paper discovery and recommendation.
"""

from typing import List, Optional, Dict, Any, Tuple
import logging

from kosmos.literature.base_client import PaperMetadata, PaperSource
from kosmos.literature.unified_search import UnifiedLiteratureSearch
from kosmos.knowledge.vector_db import get_vector_db
from kosmos.knowledge.embeddings import get_embedder

logger = logging.getLogger(__name__)


class SemanticLiteratureSearch:
    """
    Semantic search engine for scientific literature.

    Provides intelligent paper search by:
    1. Searching literature APIs (arXiv, Semantic Scholar, PubMed)
    2. Computing embeddings for results
    3. Storing in vector database
    4. Re-ranking by semantic similarity
    """

    def __init__(
        self,
        vector_db_collection: str = "papers",
        use_cache: bool = True,
        semantic_scholar_api_key: Optional[str] = None,
        pubmed_api_key: Optional[str] = None,
        pubmed_email: Optional[str] = None
    ):
        """
        Initialize semantic literature search.

        Args:
            vector_db_collection: Vector database collection name
            use_cache: Whether to use caching for API calls
            semantic_scholar_api_key: Optional Semantic Scholar API key
            pubmed_api_key: Optional PubMed API key
            pubmed_email: Optional email for PubMed
        """
        # Initialize unified search
        self.unified_search = UnifiedLiteratureSearch(
            semantic_scholar_api_key=semantic_scholar_api_key,
            pubmed_api_key=pubmed_api_key,
            pubmed_email=pubmed_email
        )

        # Initialize vector database
        self.vector_db = get_vector_db(collection_name=vector_db_collection)

        # Initialize embedder
        self.embedder = get_embedder()

        logger.info("Initialized semantic literature search")

    def search(
        self,
        query: str,
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        fields: Optional[List[str]] = None,
        sources: Optional[List[PaperSource]] = None,
        use_api_search: bool = True,
        use_vector_search: bool = True,
        rerank_by_semantic: bool = True,
        extract_full_text: bool = False,
        **kwargs
    ) -> List[PaperMetadata]:
        """
        Perform semantic search for papers.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            year_from: Optional start year filter
            year_to: Optional end year filter
            fields: Optional field filters
            sources: Optional source filters (arXiv, Semantic Scholar, PubMed)
            use_api_search: Whether to search literature APIs
            use_vector_search: Whether to search vector database
            rerank_by_semantic: Whether to rerank results by semantic similarity
            extract_full_text: Whether to extract full PDF text
            **kwargs: Additional parameters

        Returns:
            List of PaperMetadata objects, ranked by relevance

        Example:
            ```python
            search = SemanticLiteratureSearch()

            # Simple search
            papers = search.search("machine learning for drug discovery", max_results=10)

            # Advanced search
            papers = search.search(
                "CRISPR gene editing",
                max_results=20,
                year_from=2020,
                sources=[PaperSource.PUBMED, PaperSource.SEMANTIC_SCHOLAR],
                rerank_by_semantic=True,
                extract_full_text=True
            )

            for paper in papers:
                print(f"{paper.title} ({paper.year})")
            ```
        """
        results = []

        # 1. Search literature APIs
        if use_api_search:
            api_results = self.unified_search.search(
                query=query,
                max_results_per_source=max_results // 2 if use_vector_search else max_results,
                year_from=year_from,
                year_to=year_to,
                fields=fields,
                sources=sources,
                deduplicate=True,
                extract_full_text=extract_full_text,
                **kwargs
            )

            logger.info(f"Found {len(api_results)} papers from literature APIs")
            results.extend(api_results)

            # Add to vector database for future searches
            if api_results:
                self._index_papers(api_results)

        # 2. Search vector database
        if use_vector_search:
            vector_results = self._search_vector_db(
                query,
                max_results=max_results,
                year_from=year_from,
                year_to=year_to,
                fields=fields
            )

            logger.info(f"Found {len(vector_results)} papers from vector database")

            # Merge results (deduplicate)
            results = self._merge_results(results, vector_results)

        # 3. Rerank by semantic similarity
        if rerank_by_semantic and results:
            results = self._rerank_by_semantic_similarity(query, results)

        # 4. Limit to max_results
        results = results[:max_results]

        logger.info(f"Returning {len(results)} papers")
        return results

    def find_similar(
        self,
        paper: PaperMetadata,
        max_results: int = 10,
        min_similarity: float = 0.7
    ) -> List[Tuple[PaperMetadata, float]]:
        """
        Find papers similar to a given paper.

        Args:
            paper: Paper to find similar papers for
            max_results: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of (paper, similarity_score) tuples

        Example:
            ```python
            similar_papers = search.find_similar(paper, max_results=5)

            for similar_paper, score in similar_papers:
                print(f"{similar_paper.title}: {score:.3f}")
            ```
        """
        # Search vector database by paper
        results = self.vector_db.search_by_paper(
            paper,
            top_k=max_results
        )

        # Convert to PaperMetadata objects with scores
        similar_papers = []

        for result in results:
            if result["score"] >= min_similarity:
                # Try to reconstruct paper from metadata
                # (In practice, you'd fetch full paper from database or API)
                similar_papers.append((result, result["score"]))

        return similar_papers

    def get_recommendations(
        self,
        based_on_papers: List[PaperMetadata],
        max_results: int = 10,
        diversity_weight: float = 0.3
    ) -> List[PaperMetadata]:
        """
        Get paper recommendations based on a set of papers.

        Uses centroid of paper embeddings for recommendation.

        Args:
            based_on_papers: Papers to base recommendations on
            max_results: Maximum number of recommendations
            diversity_weight: Weight for diversity vs similarity (0-1)

        Returns:
            List of recommended papers

        Example:
            ```python
            # Get recommendations based on user's reading list
            recommendations = search.get_recommendations(
                based_on_papers=reading_list,
                max_results=10
            )
            ```
        """
        if not based_on_papers:
            return []

        # Compute centroid embedding
        embeddings = self.embedder.embed_papers(based_on_papers)
        centroid = embeddings.mean(axis=0)

        # Search by centroid
        # Note: This would require extending vector_db to support direct embedding queries
        # For now, we'll use the first paper as a proxy
        results = self.vector_db.search_by_paper(
            based_on_papers[0],
            top_k=max_results * 2  # Get more for diversity filtering
        )

        # Apply diversity filtering (simplified version)
        recommended = []
        seen_titles = set(p.title.lower() for p in based_on_papers)

        for result in results:
            title = result["metadata"].get("title", "").lower()

            # Skip if too similar to input papers
            if title in seen_titles:
                continue

            recommended.append(result)

            if len(recommended) >= max_results:
                break

        return recommended[:max_results]

    def build_corpus_index(
        self,
        papers: List[PaperMetadata],
        batch_size: int = 100,
        show_progress: bool = True
    ):
        """
        Build vector index from a corpus of papers.

        Args:
            papers: List of papers to index
            batch_size: Batch size for processing
            show_progress: Whether to show progress

        Example:
            ```python
            # Index a large corpus
            search.build_corpus_index(all_papers, batch_size=100)
            ```
        """
        logger.info(f"Building index for {len(papers)} papers")

        # Compute embeddings in batches
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]

            embeddings = self.embedder.embed_papers(
                batch,
                batch_size=batch_size,
                show_progress=show_progress
            )

            self.vector_db.add_papers(batch, embeddings=embeddings)

            logger.info(f"Indexed {min(i + batch_size, len(papers))}/{len(papers)} papers")

        logger.info("Index building complete")

    def get_corpus_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the indexed corpus.

        Returns:
            Dictionary with corpus statistics
        """
        db_stats = self.vector_db.get_stats()

        return {
            **db_stats,
            "sources_enabled": [source.value for source in self.unified_search.clients.keys()]
        }

    def _search_vector_db(
        self,
        query: str,
        max_results: int,
        year_from: Optional[int],
        year_to: Optional[int],
        fields: Optional[List[str]]
    ) -> List[PaperMetadata]:
        """
        Search vector database with filters.

        Args:
            query: Search query
            max_results: Max results
            year_from: Start year
            year_to: End year
            fields: Fields filter

        Returns:
            List of papers from vector database
        """
        # Build filters
        filters = {}

        if year_from:
            filters["year"] = {"$gte": year_from}

        if year_to:
            if "year" in filters:
                filters["year"]["$lte"] = year_to
            else:
                filters["year"] = {"$lte": year_to}

        if fields and len(fields) > 0:
            filters["domain"] = {"$in": [f.lower() for f in fields]}

        # Search
        results = self.vector_db.search(
            query,
            top_k=max_results,
            filters=filters if filters else None
        )

        # Convert to PaperMetadata (simplified - would need full reconstruction)
        # For now, return empty as placeholder
        # In production, you'd store full paper data or fetch from database
        return []

    def _index_papers(self, papers: List[PaperMetadata]):
        """
        Index papers in vector database.

        Args:
            papers: Papers to index
        """
        try:
            # Only index papers not already in database
            new_papers = []

            for paper in papers:
                paper_id = f"{paper.source.value}:{paper.primary_identifier}"
                if not self.vector_db.get_paper(paper_id):
                    new_papers.append(paper)

            if new_papers:
                self.vector_db.add_papers(new_papers)
                logger.info(f"Indexed {len(new_papers)} new papers")

        except Exception as e:
            logger.error(f"Error indexing papers: {e}")

    def _merge_results(
        self,
        results1: List[PaperMetadata],
        results2: List[PaperMetadata]
    ) -> List[PaperMetadata]:
        """
        Merge and deduplicate two result lists.

        Args:
            results1: First result list
            results2: Second result list

        Returns:
            Merged, deduplicated list
        """
        # Use set of identifiers for deduplication
        seen_ids = set()
        merged = []

        for paper in results1 + results2:
            paper_id = paper.primary_identifier

            if paper_id not in seen_ids:
                seen_ids.add(paper_id)
                merged.append(paper)

        return merged

    def _rerank_by_semantic_similarity(
        self,
        query: str,
        papers: List[PaperMetadata]
    ) -> List[PaperMetadata]:
        """
        Rerank papers by semantic similarity to query.

        Args:
            query: Search query
            papers: Papers to rerank

        Returns:
            Reranked papers
        """
        # Compute query embedding
        query_embedding = self.embedder.embed_query(query)

        # Compute paper embeddings
        paper_embeddings = self.embedder.embed_papers(papers, show_progress=False)

        # Compute similarities
        similarities = []
        for i, paper_emb in enumerate(paper_embeddings):
            sim = self.embedder.compute_similarity(query_embedding, paper_emb)
            similarities.append((i, sim, papers[i]))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return reranked papers
        return [paper for _, _, paper in similarities]
