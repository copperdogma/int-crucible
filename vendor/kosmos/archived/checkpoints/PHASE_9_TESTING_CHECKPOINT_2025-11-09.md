# Phase 9 Testing Checkpoint - November 9, 2025

**Purpose**: Comprehensive checkpoint for completing Phase 9 test implementation after compaction.

**Status**: All test stubs created, ready for implementation.

---

## Current State Summary

### Completed ✅
1. **Domain Router Tests** (`tests/unit/core/test_domain_router.py`)
   - 43 tests across 8 test classes
   - ~600 lines
   - Fixed with `mock_env_vars` fixture

2. **Domain KB Tests** (`tests/unit/knowledge/test_domain_kb.py`)
   - 46 tests across 7 test classes
   - ~520 lines
   - Complete and ready

3. **Test Stubs Created** (12 files)
   - Biology domain (4 files, ~140 test signatures)
   - Neuroscience domain (4 files, ~115 test signatures)
   - Materials domain (3 files, ~95 test signatures)
   - Integration (1 file, ~15 test signatures)
   - **Total**: ~365 test method signatures

### Pending Implementation 🔄
- Implement all test stubs (~5,700 lines of test code)
- Run full test suite
- Verify >80% coverage
- Fix any failures

---

## Test Files Structure

### Core Tests (Complete, needs env fix)
```
tests/unit/core/test_domain_router.py          # 43 tests ✓
tests/unit/knowledge/test_domain_kb.py          # 46 tests ✓
```

### Biology Domain Tests (Stubs)
```
tests/unit/domains/biology/
├── __init__.py
├── test_apis.py           # 50 tests (10 API clients x 5 tests)
├── test_metabolomics.py   # 30 tests (MetabolomicsAnalyzer)
├── test_genomics.py       # 30 tests (GenomicsAnalyzer)
└── test_ontology.py       # 30 tests (BiologyOntology)
```

### Neuroscience Domain Tests (Stubs)
```
tests/unit/domains/neuroscience/
├── __init__.py
├── test_apis.py                # 40 tests (7 API clients)
├── test_connectomics.py        # 25 tests (ConnectomicsAnalyzer)
├── test_neurodegeneration.py   # 30 tests (NeurodegenerationAnalyzer)
└── test_ontology.py            # 20 tests (NeuroscienceOntology)
```

### Materials Domain Tests (Stubs)
```
tests/unit/domains/materials/
├── __init__.py
├── test_apis.py          # 35 tests (5 API clients)
├── test_optimization.py  # 35 tests (MaterialsOptimizer)
└── test_ontology.py      # 25 tests (MaterialsOntology)
```

### Integration Tests (Stub)
```
tests/integration/
└── test_multi_domain.py  # 15 tests (end-to-end workflows)
```

---

## Environment Setup Issue & Solution

### Problem
Tests fail with: `ValidationError: ANTHROPIC_API_KEY Field required`

### Solution
Use the `mock_env_vars` fixture (already defined in `tests/conftest.py`):

```python
@pytest.fixture
def domain_router(mock_llm_client, mock_env_vars):  # ← Add mock_env_vars
    """Create DomainRouter instance with mocked LLM"""
    router = DomainRouter(claude_client=mock_llm_client)
    return router
```

**Pattern**: Any fixture or test that creates components requiring `ClaudeConfig` must include `mock_env_vars` parameter.

---

## Testing Patterns Reference

### Pattern 1: API Client Testing

```python
@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API calls"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "compound_id": "C00385",
        "name": "Xanthine",
        "pathway": "purine_metabolism"
    }
    mock_client.get.return_value = mock_response
    return mock_client

@pytest.mark.unit
class TestKEGGClient:
    def test_get_compound_success(self, mock_httpx_client):
        """Test successful compound retrieval."""
        with patch('httpx.Client', return_value=mock_httpx_client):
            client = KEGGClient()
            compound = client.get_compound("C00385")

            assert compound is not None
            assert compound["name"] == "Xanthine"
            assert compound["pathway"] == "purine_metabolism"
            mock_httpx_client.get.assert_called_once()
```

### Pattern 2: Analyzer Testing

```python
@pytest.fixture
def metabolomics_analyzer():
    """Create MetabolomicsAnalyzer instance"""
    mock_kegg = Mock()
    return MetabolomicsAnalyzer(kegg_client=mock_kegg)

@pytest.fixture
def sample_metabolite_data():
    """Sample metabolite concentration data"""
    return pd.DataFrame({
        'metabolite': ['C00385', 'C00299', 'C00147'],
        'control_mean': [10.5, 15.2, 8.3],
        'treatment_mean': [18.7, 14.8, 12.1],
        'pvalue': [0.001, 0.45, 0.03]
    })

def test_group_comparison(self, metabolomics_analyzer, sample_metabolite_data):
    """Test group comparison analysis."""
    result = metabolomics_analyzer.analyze_group_comparison(
        data=sample_metabolite_data,
        group1='control',
        group2='treatment'
    )

    assert isinstance(result, MetabolomicsResult)
    assert result.significant_metabolites is not None
    assert len(result.significant_metabolites) > 0
    assert result.pvalue < 0.05
```

### Pattern 3: Ontology Testing

```python
@pytest.fixture
def biology_ontology():
    """Create BiologyOntology instance"""
    return BiologyOntology()

def test_purine_metabolism_pathway(self, biology_ontology):
    """Test purine metabolism pathway exists."""
    assert "purine_metabolism" in biology_ontology.concepts

    pathway = biology_ontology.concepts["purine_metabolism"]
    assert pathway.name == "Purine Metabolism"
    assert pathway.type == "pathway"

    # Check relations
    related = biology_ontology.get_related_concepts("purine_metabolism")
    assert len(related) > 0
    assert any(c.concept_id == "purine_salvage" for c in related)
```

### Pattern 4: Parametrized Testing

```python
@pytest.mark.parametrize("compound_id,expected_category,expected_type", [
    ("C00385", "purine", "salvage_precursor"),
    ("C00299", "pyrimidine", "synthesis_product"),
    ("C00147", "purine", "nucleotide"),
])
def test_categorize_known_compounds(self, metabolomics_analyzer,
                                     compound_id, expected_category, expected_type):
    """Test categorization of known compounds."""
    category = metabolomics_analyzer.categorize_metabolite(compound_id)

    assert category.category == expected_category
    assert category.metabolite_type == expected_type
```

### Pattern 5: Integration Testing

```python
@pytest.mark.integration
def test_full_pipeline_question_to_experiment_protocol(
    self, domain_router, domain_kb, template_registry, mock_env_vars
):
    """Test full pipeline from research question to experiment protocol."""

    # Step 1: Classify question
    question = "How do genes regulate metabolic pathways?"
    classification = domain_router.classify_research_question(question)

    assert classification.primary_domain == ScientificDomain.BIOLOGY

    # Step 2: Route to domain
    route = domain_router.route(question, classification)

    assert ScientificDomain.BIOLOGY in route.selected_domains
    assert len(route.required_tools) > 0

    # Step 3: Get templates
    templates = template_registry.get_by_domain(Domain.BIOLOGY)

    assert len(templates) > 0
    assert any(t.metadata.name == "metabolomics_comparison" for t in templates)
```

---

## Implementation Order (Recommended)

### Session 1: Complete Core Tests (30 min)
1. Fix and run domain router tests
2. Fix and run domain KB tests
3. Verify both pass: `pytest tests/unit/core/test_domain_router.py tests/unit/knowledge/test_domain_kb.py -v`

### Session 2: Biology Domain (60 min)
1. Implement `test_apis.py` (50 tests, ~600 lines)
2. Implement `test_metabolomics.py` (30 tests, ~400 lines)
3. Implement `test_genomics.py` (30 tests, ~400 lines)
4. Implement `test_ontology.py` (30 tests, ~400 lines)
5. Run: `pytest tests/unit/domains/biology/ -v`

### Session 3: Neuroscience Domain (60 min)
1. Implement `test_apis.py` (40 tests, ~500 lines)
2. Implement `test_connectomics.py` (25 tests, ~400 lines)
3. Implement `test_neurodegeneration.py` (30 tests, ~400 lines)
4. Implement `test_ontology.py` (20 tests, ~300 lines)
5. Run: `pytest tests/unit/domains/neuroscience/ -v`

### Session 4: Materials Domain (45 min)
1. Implement `test_apis.py` (35 tests, ~400 lines)
2. Implement `test_optimization.py` (35 tests, ~500 lines)
3. Implement `test_ontology.py` (25 tests, ~300 lines)
4. Run: `pytest tests/unit/domains/materials/ -v`

### Session 5: Integration & Coverage (30 min)
1. Implement `test_multi_domain.py` (15 tests, ~400 lines)
2. Run full suite: `pytest tests/unit/domains/ tests/unit/core/test_domain_router.py tests/unit/knowledge/test_domain_kb.py tests/integration/test_multi_domain.py -v`
3. Generate coverage: `pytest --cov=kosmos.domains --cov=kosmos.core.domain_router --cov=kosmos.knowledge.domain_kb --cov-report=html`
4. Fix any failures
5. Verify >80% coverage

---

## Key Testing Commands

### Run Specific Test File
```bash
pytest tests/unit/domains/biology/test_apis.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/domains/biology/test_apis.py::TestKEGGClient -v
```

### Run Specific Test Method
```bash
pytest tests/unit/domains/biology/test_apis.py::TestKEGGClient::test_get_compound_success -v
```

### Run with Coverage
```bash
pytest tests/unit/domains/biology/ --cov=kosmos.domains.biology --cov-report=html
```

### Run All Domain Tests
```bash
pytest tests/unit/domains/ -v
```

### Run Full Phase 9 Test Suite
```bash
pytest \
  tests/unit/core/test_domain_router.py \
  tests/unit/knowledge/test_domain_kb.py \
  tests/unit/domains/ \
  tests/integration/test_multi_domain.py \
  -v --tb=short
```

---

## Common Issues & Solutions

### Issue 1: Import Errors
**Problem**: `ImportError: cannot import name 'ClassName'`

**Solution**: Check actual class names in implementation files. Update imports in test file.

### Issue 2: Mock Not Working
**Problem**: Real API calls being made instead of mocks

**Solution**: Ensure mock is patched at correct location:
```python
# If code does: from kosmos.domains.biology.apis import KEGGClient
# Patch at: 'kosmos.domains.biology.apis.KEGGClient'

with patch('kosmos.domains.biology.apis.KEGGClient') as mock:
    # test code
```

### Issue 3: Fixture Not Found
**Problem**: `fixture 'mock_env_vars' not found`

**Solution**: Ensure `tests/conftest.py` is in path and fixture is defined there. Check fixture scope.

### Issue 4: Assertion Failures
**Problem**: Tests fail with unexpected values

**Solution**:
1. Print actual values: `print(f"Got: {actual}, Expected: {expected}")`
2. Check mock return values match expected structure
3. Verify implementation logic

---

## Coverage Targets

### Minimum Required: >80%

**Expected Coverage by Module**:
- `kosmos/core/domain_router.py`: >85%
- `kosmos/knowledge/domain_kb.py`: >90%
- `kosmos/domains/biology/*.py`: >75%
- `kosmos/domains/neuroscience/*.py`: >75%
- `kosmos/domains/materials/*.py`: >75%

**To Check Coverage**:
```bash
pytest \
  --cov=kosmos.core.domain_router \
  --cov=kosmos.knowledge.domain_kb \
  --cov=kosmos.domains \
  --cov-report=term-missing \
  --cov-report=html
```

Open `htmlcov/index.html` to see detailed coverage report.

---

## Recovery Prompt for Next Session

```
I need to complete Phase 9 testing implementation after compaction.

Recovery Steps:
1. Read @docs/PHASE_9_TESTING_CHECKPOINT_2025-11-09.md for testing plan
2. Review @IMPLEMENTATION_PLAN.md Phase 9 section
3. Check test stub structure in tests/unit/domains/

Current Status:
- Domain router tests: Complete (needs env fix)
- Domain KB tests: Complete
- Test stubs: All created (12 files, ~365 test signatures)
- Pending: Implement all test stubs (~5,700 lines)

Next Steps:
1. Start with Session 1 (Core tests - 30 min)
2. Continue through Sessions 2-5
3. Achieve >80% coverage
4. Move to Phase 9 completion documentation

Please confirm you've recovered context and begin test implementation from Session 1.
```

---

## Test Stub Summary

| Domain | File | Tests | Lines | Status |
|--------|------|-------|-------|--------|
| Core | `test_domain_router.py` | 43 | ~600 | ✓ Complete |
| Core | `test_domain_kb.py` | 46 | ~520 | ✓ Complete |
| Biology | `test_apis.py` | 50 | ~600 | Stub |
| Biology | `test_metabolomics.py` | 30 | ~400 | Stub |
| Biology | `test_genomics.py` | 30 | ~400 | Stub |
| Biology | `test_ontology.py` | 30 | ~400 | Stub |
| Neuroscience | `test_apis.py` | 40 | ~500 | Stub |
| Neuroscience | `test_connectomics.py` | 25 | ~400 | Stub |
| Neuroscience | `test_neurodegeneration.py` | 30 | ~400 | Stub |
| Neuroscience | `test_ontology.py` | 20 | ~300 | Stub |
| Materials | `test_apis.py` | 35 | ~400 | Stub |
| Materials | `test_optimization.py` | 35 | ~500 | Stub |
| Materials | `test_ontology.py` | 25 | ~300 | Stub |
| Integration | `test_multi_domain.py` | 15 | ~400 | Stub |
| **TOTAL** | **14 files** | **454** | **~6,720** | **2 done, 12 stubs** |

---

## Next Milestone

After completing all tests:
1. Run full test suite
2. Verify >80% coverage
3. Create `PHASE_9_COMPLETION.md`
4. Update `IMPLEMENTATION_PLAN.md`
5. Commit all changes
6. Move to Phase 10 (Optimization & Production)

---

**Document Version**: 1.0
**Created**: 2025-11-09
**Purpose**: Enable efficient test implementation after compaction
**Estimated Completion Time**: 3-4 hours across 5 sessions
