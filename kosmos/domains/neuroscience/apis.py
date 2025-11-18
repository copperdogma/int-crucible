"""
Neuroscience Domain API Clients

Provides access to neuroscience databases and tools:
- FlyWire: Drosophila whole-brain connectome
- AllenBrain: Gene expression and connectivity atlas
- MICrONS: Mouse cortex connectome
- GEO: Gene Expression Omnibus
- AMPAD: Alzheimer's Disease data portal
- OpenConnectome: Connectome data repository
- WormBase: C. elegans genome and connectome

Example usage:
    # FlyWire connectome
    flywire = FlyWireClient()
    neuron_data = flywire.get_neuron(neuron_id='720575940612453042')

    # Allen Brain Atlas
    allen = AllenBrainClient()
    expression_data = allen.get_gene_expression(gene='SOD2')

    # GEO datasets
    geo = GEOClient()
    dataset = geo.get_dataset(geo_id='GSE153873')
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


# Data models for API responses

@dataclass
class NeuronData:
    """Neuron information from connectome"""
    neuron_id: str
    cell_type: Optional[str] = None
    n_synapses: Optional[int] = None
    degree: Optional[int] = None  # Number of connections
    length_um: Optional[float] = None  # Total length in micrometers
    position: Optional[Dict[str, float]] = None  # x, y, z coordinates
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GeneExpressionData:
    """Gene expression data"""
    gene_symbol: str
    gene_id: Optional[str] = None
    expression_level: Optional[float] = None
    brain_region: Optional[str] = None
    tissue: Optional[str] = None
    experiment_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConnectomeDataset:
    """Connectome dataset information"""
    dataset_id: str
    species: str
    n_neurons: int
    n_synapses: Optional[int] = None
    data_type: str = "connectome"
    resolution_nm: Optional[float] = None
    brain_region: Optional[str] = None
    url: Optional[str] = None


@dataclass
class DifferentialExpressionResult:
    """Differential expression analysis result"""
    gene: str
    log2_fold_change: float
    p_value: float
    adjusted_p_value: float
    base_mean: Optional[float] = None
    significant: bool = False


# API Clients

class FlyWireClient:
    """
    Client for FlyWire Drosophila whole-brain connectome.

    FlyWire provides the largest complete brain connectome dataset:
    - 129,000 neurons
    - 50 million synapses
    - Whole adult fly brain
    """

    BASE_URL = "https://global.daf-apis.com/nglstate/api/v1"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize FlyWire client.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_neuron(self, neuron_id: str) -> Optional[NeuronData]:
        """
        Get neuron information from FlyWire.

        Args:
            neuron_id: FlyWire neuron segment ID

        Returns:
            NeuronData object or None if not found
        """
        # Note: FlyWire API is complex and requires authentication
        # This is a simplified placeholder implementation
        # Real implementation would use FlyWire's CAVE API

        return NeuronData(
            neuron_id=neuron_id,
            cell_type="placeholder",
            metadata={"source": "flywire", "note": "API implementation placeholder"}
        )

    def get_connectivity(
        self,
        neuron_id: str,
        direction: str = "both"
    ) -> Dict[str, List[str]]:
        """
        Get synaptic partners of a neuron.

        Args:
            neuron_id: Neuron segment ID
            direction: "presynaptic", "postsynaptic", or "both"

        Returns:
            Dictionary with lists of connected neuron IDs
        """
        # Placeholder implementation
        return {
            "presynaptic": [],
            "postsynaptic": [],
        }

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class AllenBrainClient:
    """
    Client for Allen Brain Atlas API.

    Provides access to:
    - Gene expression data across brain regions
    - Connectivity maps
    - Cell type transcriptomics
    """

    BASE_URL = "https://api.brain-map.org/api/v2"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize Allen Brain Atlas client.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_gene_expression(
        self,
        gene: str,
        structure: Optional[str] = None
    ) -> Optional[GeneExpressionData]:
        """
        Get gene expression data from Allen Brain Atlas.

        Args:
            gene: Gene symbol (e.g., 'SOD2')
            structure: Brain structure filter (e.g., 'hippocampus')

        Returns:
            GeneExpressionData object or None
        """
        try:
            # Query gene information
            url = f"{self.BASE_URL}/data/query.json"
            params = {
                "criteria": f"model::Gene,rma::criteria,[acronym$eq'{gene}']",
                "include": "probes,gene_aliases",
                "num_rows": "1"
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get('success') or not data.get('msg'):
                return None

            gene_info = data['msg'][0]

            return GeneExpressionData(
                gene_symbol=gene,
                gene_id=str(gene_info.get('id')),
                metadata=gene_info
            )

        except Exception as e:
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def search_experiments(
        self,
        product_id: int = 1,  # 1 = Mouse Brain Atlas
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for experiments in Allen Brain Atlas.

        Args:
            product_id: Product ID (1=Mouse Brain, 2=Human Brain, etc.)
            limit: Maximum number of results

        Returns:
            List of experiment dictionaries
        """
        try:
            url = f"{self.BASE_URL}/data/SectionDataSet/query.json"
            params = {
                "criteria": f"products[id$eq{product_id}]",
                "num_rows": limit
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('msg', [])

        except Exception:
            return []

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class MICrONSClient:
    """
    Client for MICrONS Mouse Cortex Connectome.

    MICrONS provides:
    - Cubic millimeter of mouse visual cortex
    - ~75,000 neurons
    - Functional and structural data
    """

    BASE_URL = "https://microns-explorer.org/api"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize MICrONS client.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    def get_dataset_info(self) -> ConnectomeDataset:
        """
        Get MICrONS dataset metadata.

        Returns:
            ConnectomeDataset information
        """
        return ConnectomeDataset(
            dataset_id="microns_v1",
            species="Mus musculus",
            n_neurons=75000,
            n_synapses=500_000_000,  # Approximate
            brain_region="Visual cortex (V1)",
            resolution_nm=4.0,
            url="https://www.microns-explorer.org/"
        )

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class GEOClient:
    """
    Client for NCBI Gene Expression Omnibus (GEO).

    Provides access to:
    - Gene expression datasets
    - Microarray and RNA-seq data
    - Sample annotations
    """

    BASE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize GEO client.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_dataset(
        self,
        geo_id: str,
        format: str = "text"
    ) -> Optional[Dict[str, Any]]:
        """
        Get GEO dataset information.

        Args:
            geo_id: GEO accession (e.g., 'GSE153873')
            format: Return format ('text', 'xml', 'json')

        Returns:
            Dataset information dictionary or None
        """
        try:
            params = {
                "acc": geo_id,
                "targ": "self",
                "view": "quick",
                "form": format
            }

            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            # Parse response (simplified - real implementation would parse SOFT format)
            return {
                "geo_id": geo_id,
                "title": f"Dataset {geo_id}",
                "raw_data": response.text
            }

        except Exception:
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def search_datasets(
        self,
        query: str,
        organism: str = "Homo sapiens",
        limit: int = 10
    ) -> List[str]:
        """
        Search for GEO datasets.

        Args:
            query: Search query
            organism: Organism filter
            limit: Maximum results

        Returns:
            List of GEO accession IDs
        """
        # Placeholder - real implementation would use NCBI E-utilities
        return []

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class AMPADClient:
    """
    Client for Accelerating Medicines Partnership - Alzheimer's Disease (AMP-AD).

    Provides access to:
    - Alzheimer's disease omics data
    - Longitudinal cognitive data
    - Multi-modal datasets
    """

    BASE_URL = "https://adknowledgeportal.synapse.org"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize AMP-AD client.

        Note: Real access requires Synapse account and authentication

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    def get_study_info(self, study_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an AMP-AD study.

        Args:
            study_id: Study identifier

        Returns:
            Study information dictionary or None
        """
        # Placeholder - real implementation requires Synapse Python client
        return {
            "study_id": study_id,
            "title": f"AMP-AD Study {study_id}",
            "note": "Requires Synapse authentication for real data access"
        }

    def list_datasets(
        self,
        data_type: str = "transcriptomics"
    ) -> List[Dict[str, Any]]:
        """
        List available datasets.

        Args:
            data_type: Type of data ('transcriptomics', 'proteomics', 'metabolomics', etc.)

        Returns:
            List of dataset dictionaries
        """
        # Placeholder
        return []

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class OpenConnectomeClient:
    """
    Client for OpenConnectome Project.

    Provides access to:
    - Multi-species connectome data
    - EM image volumes
    - Reconstruction data
    """

    BASE_URL = "https://openconnecto.me/ocp/ca"

    def __init__(self, timeout: float = 60.0):
        """
        Initialize OpenConnectome client.

        Args:
            timeout: Request timeout in seconds (longer for large data)
        """
        self.client = httpx.Client(timeout=timeout)

    def list_projects(self) -> List[str]:
        """
        List available connectome projects.

        Returns:
            List of project names
        """
        # Known OpenConnectome projects
        return [
            "kasthuri11",  # Mouse cortex
            "bock11",  # Drosophila
            "takemura13",  # Drosophila medulla
        ]

    def get_project_info(self, project_name: str) -> Optional[ConnectomeDataset]:
        """
        Get information about a connectome project.

        Args:
            project_name: Project identifier

        Returns:
            ConnectomeDataset information or None
        """
        # Simplified metadata for known projects
        projects = {
            "kasthuri11": ConnectomeDataset(
                dataset_id="kasthuri11",
                species="Mus musculus",
                n_neurons=1700,
                brain_region="Cortex",
                resolution_nm=3.0,
                url=f"{self.BASE_URL}/kasthuri11"
            ),
            "bock11": ConnectomeDataset(
                dataset_id="bock11",
                species="Drosophila melanogaster",
                n_neurons=379,
                brain_region="Larval CNS",
                resolution_nm=4.0,
                url=f"{self.BASE_URL}/bock11"
            ),
        }

        return projects.get(project_name)

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()


class WormBaseClient:
    """
    Client for WormBase C. elegans database.

    Provides access to:
    - C. elegans connectome
    - Gene information
    - Neuron cell types
    - Synaptic connectivity
    """

    BASE_URL = "https://wormbase.org/rest"

    def __init__(self, timeout: float = 30.0):
        """
        Initialize WormBase client.

        Args:
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_neuron(self, neuron_name: str) -> Optional[NeuronData]:
        """
        Get C. elegans neuron information.

        Args:
            neuron_name: Neuron name (e.g., 'AVAL', 'AVAR')

        Returns:
            NeuronData object or None
        """
        try:
            url = f"{self.BASE_URL}/field/cell/{neuron_name}/connectome"

            response = self.client.get(url)
            response.raise_for_status()

            data = response.json()

            return NeuronData(
                neuron_id=neuron_name,
                cell_type=neuron_name,
                metadata=data
            )

        except Exception:
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_gene(self, gene_name: str) -> Optional[Dict[str, Any]]:
        """
        Get C. elegans gene information.

        Args:
            gene_name: Gene name (e.g., 'sod-2')

        Returns:
            Gene information dictionary or None
        """
        try:
            url = f"{self.BASE_URL}/field/gene/{gene_name}/overview"

            response = self.client.get(url)
            response.raise_for_status()

            return response.json()

        except Exception:
            return None

    def get_connectome_stats(self) -> ConnectomeDataset:
        """
        Get C. elegans connectome statistics.

        Returns:
            ConnectomeDataset information
        """
        return ConnectomeDataset(
            dataset_id="celegans_full",
            species="Caenorhabditis elegans",
            n_neurons=302,
            n_synapses=7000,
            brain_region="Full nervous system",
            url="https://wormbase.org/"
        )

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()
