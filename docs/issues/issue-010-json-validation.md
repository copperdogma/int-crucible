# Issue 010: Missing JSON schema validation for world models and constraints

**Status**: Open
**Priority**: High
**Category**: Data Integrity
**Discovered**: 2025-11-24
**Related Story**: (TBD)

## Description
Critical data structures (ProblemSpec constraints, WorldModel data, ScenarioSuite scenarios, Candidate scores) are stored as unvalidated JSON, allowing invalid data to persist and cause runtime errors during processing.

## Current Behavior
```python
# In db/models.py
class ProblemSpec(Base):
    constraints = Column(JSON, nullable=False, default=list)  # No validation!
    goals = Column(JSON, nullable=False, default=list)        # No validation!

class WorldModel(Base):
    model_data = Column(JSON, nullable=False, default=dict)   # No validation!

# In service layer
def update_problem_spec(session, project_id, constraints, goals, ...):
    # constraints could be anything: [1, 2, 3], "string", {}, malformed objects
    # No validation before persistence!
    spec.constraints = constraints  # ❌ Dangerous!
    session.commit()
```

## Expected Behavior
All JSON fields should have Pydantic schemas that validate:
1. **Structure**: Required fields exist
2. **Types**: Fields have correct types
3. **Constraints**: Values meet domain rules (e.g., weights 0-100)
4. **Completeness**: No missing required data

## Impact on Users

### Data Corruption
```python
# Example bad data that could be persisted
constraints = [
    {"name": "budget"},  # ❌ Missing description, weight
    {"weight": 150},      # ❌ Missing name, invalid weight > 100
    "invalid string",     # ❌ Should be object
]
# This persists successfully, then crashes during evaluation!
```

### Runtime Errors
```python
# Later in ranker_service.py
for constraint in constraints:
    weight = constraint["weight"]  # ❌ KeyError: 'weight'
    # Run crashes mid-execution
```

### Silent Failures
```python
# Invalid world model data
world_model.model_data = {
    "actors": "should be dict but is string"  # ❌ Persists silently
}
# Later causes cryptic errors in designer agent
```

## Investigation Notes

### Affected JSON Fields

| Model | Field | Current Type | Issues |
|-------|-------|--------------|--------|
| `ProblemSpec` | `constraints` | `JSON` (list) | No validation of constraint structure |
| `ProblemSpec` | `goals` | `JSON` (list) | Can be empty, malformed strings |
| `WorldModel` | `model_data` | `JSON` (dict) | No validation of actors, mechanisms, resources |
| `ScenarioSuite` | `scenarios` | `JSON` (list) | No validation of scenario structure |
| `Candidate` | `scores` | `JSON` (dict) | No validation of P, R, I fields |
| `Candidate` | `predicted_effects` | `JSON` | No validation |
| `Evaluation` | `P` | `JSON` | Can be number or structured object |
| `Evaluation` | `R` | `JSON` | Can be number or structured object |
| `Evaluation` | `constraint_satisfaction` | `JSON` | No validation |

### Root Cause
System was built without Pydantic validation for JSON columns. SQLAlchemy accepts any JSON-serializable data, no type checking.

## Proposed Solution

### Step 1: Define Pydantic Schemas

```python
# crucible/models/domain_schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

# ProblemSpec schemas
class Constraint(BaseModel):
    """A single constraint definition."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    weight: int = Field(..., ge=0, le=100, description="Constraint weight 0-100")
    is_hard: bool = Field(default=False, description="Whether constraint is hard (must satisfy)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Budget",
                "description": "Solution must stay under $100k budget",
                "weight": 90,
                "is_hard": True
            }
        }

class ProblemSpecData(BaseModel):
    """Validated ProblemSpec data."""
    constraints: List[Constraint] = Field(..., min_length=1)
    goals: List[str] = Field(..., min_length=1)

    @validator('goals')
    def validate_goals_not_empty(cls, v):
        if not v or all(not g.strip() for g in v):
            raise ValueError("At least one non-empty goal required")
        return [g.strip() for g in v if g.strip()]

# WorldModel schemas
class Actor(BaseModel):
    """An actor in the world model."""
    name: str
    description: str
    capabilities: List[str] = []
    constraints: List[str] = []

class Mechanism(BaseModel):
    """A mechanism in the world model."""
    name: str
    description: str
    inputs: List[str] = []
    outputs: List[str] = []
    actors: List[str] = []

class Resource(BaseModel):
    """A resource in the world model."""
    name: str
    description: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

class WorldModelData(BaseModel):
    """Validated WorldModel data structure."""
    actors: Dict[str, Actor] = Field(default_factory=dict)
    mechanisms: Dict[str, Mechanism] = Field(default_factory=dict)
    resources: Dict[str, Resource] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    simplifications: List[str] = Field(default_factory=list)

    @validator('actors')
    def validate_actors_not_empty(cls, v):
        if not v:
            raise ValueError("At least one actor required in world model")
        return v

    @validator('mechanisms')
    def validate_mechanisms_not_empty(cls, v):
        if not v:
            raise ValueError("At least one mechanism required in world model")
        return v

# Scenario schemas
class Scenario(BaseModel):
    """A single test scenario."""
    id: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = []
    stress_factors: List[str] = []

class ScenarioSuiteData(BaseModel):
    """Validated scenario suite."""
    scenarios: List[Scenario] = Field(..., min_length=1)

    @validator('scenarios')
    def validate_unique_ids(cls, v):
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Scenario IDs must be unique")
        return v

# Candidate scores
class CandidateScores(BaseModel):
    """Validated candidate scores."""
    I: Optional[float] = Field(None, description="Intelligence score (P/R)")
    P: Optional[float] = Field(None, ge=0, le=1, description="Prediction quality 0-1")
    R: Optional[float] = Field(None, ge=0, description="Resource cost")
    constraint_satisfaction: Dict[str, float] = Field(default_factory=dict)

    @validator('I')
    def validate_I_matches_formula(cls, v, values):
        """Ensure I = P / R if both P and R exist."""
        P = values.get('P')
        R = values.get('R')
        if v is not None and P is not None and R is not None and R > 0:
            expected_I = P / R
            if abs(v - expected_I) > 0.001:  # Allow small floating point error
                raise ValueError(f"I score {v} doesn't match P/R formula: {P}/{R} = {expected_I}")
        return v
```

### Step 2: Add Validation to Services

```python
# crucible/services/problemspec_service.py
from crucible.models.domain_schemas import ProblemSpecData, Constraint

class ProblemSpecService:
    def update_problem_spec(
        self,
        project_id: str,
        constraints: List[Dict],
        goals: List[str],
        ...
    ):
        """Update ProblemSpec with validation."""
        # Validate before persisting
        try:
            validated_data = ProblemSpecData(
                constraints=[Constraint(**c) for c in constraints],
                goals=goals
            )
        except ValidationError as e:
            raise ValueError(f"Invalid ProblemSpec data: {e.errors()}")

        # Now safe to persist
        spec = get_problem_spec(self.session, project_id)
        spec.constraints = [c.dict() for c in validated_data.constraints]
        spec.goals = validated_data.goals
        self.session.commit()
```

### Step 3: Add Validation to API Layer

```python
# crucible/api/main.py
from pydantic import BaseModel, ValidationError
from crucible.models.domain_schemas import Constraint

class UpdateProblemSpecRequest(BaseModel):
    """API request to update ProblemSpec."""
    constraints: List[Constraint]  # Validated by Pydantic
    goals: List[str]
    resolution: Optional[str] = None
    mode: Optional[str] = None

@app.put("/projects/{project_id}/problemspec")
async def update_problem_spec(
    project_id: str,
    request: UpdateProblemSpecRequest,  # FastAPI validates automatically
    session: Session = Depends(get_session)
):
    """Update ProblemSpec with validated data."""
    service = ProblemSpecService(session)

    # Data is already validated by FastAPI
    result = service.update_problem_spec(
        project_id=project_id,
        constraints=[c.dict() for c in request.constraints],
        goals=request.goals,
        ...
    )
    return result
```

### Step 4: Add Migration for Existing Data

```python
# alembic/versions/xxx_validate_existing_json.py
"""Validate and clean existing JSON data."""

def upgrade():
    """Validate existing JSON fields, log/fix invalid data."""
    from crucible.models.domain_schemas import ProblemSpecData, WorldModelData

    # Get all ProblemSpecs
    connection = op.get_bind()
    specs = connection.execute("SELECT id, constraints, goals FROM crucible_problem_specs").fetchall()

    for spec in specs:
        try:
            # Attempt validation
            validated = ProblemSpecData(
                constraints=spec.constraints or [],
                goals=spec.goals or []
            )
        except ValidationError as e:
            # Log invalid data
            print(f"WARN: ProblemSpec {spec.id} has invalid data: {e}")
            # Apply fix (e.g., add default values, remove invalid entries)
            # ...
```

## Implementation Plan

### Phase 1: Define Schemas (4 hours)
1. Create `crucible/models/domain_schemas.py`
2. Define Pydantic models for all JSON fields
3. Add comprehensive validators

### Phase 2: Add Service Validation (4 hours)
1. Update all service methods to validate before persistence
2. Add proper error handling for validation failures
3. Update unit tests

### Phase 3: Add API Validation (2 hours)
1. Create Pydantic request models
2. Update API endpoints to use validated models
3. Update API tests

### Phase 4: Migrate Existing Data (2-4 hours)
1. Write migration to validate existing data
2. Fix or flag invalid existing data
3. Test migration on dev database

### Total Effort: 12-14 hours

## Testing Strategy

```python
# tests/unit/models/test_domain_schemas.py
def test_constraint_validation():
    """Test constraint validation."""
    # Valid constraint
    constraint = Constraint(
        name="Budget",
        description="Must be under $100k",
        weight=90,
        is_hard=True
    )
    assert constraint.weight == 90

    # Invalid: weight > 100
    with pytest.raises(ValidationError):
        Constraint(name="X", description="Y", weight=150)

    # Invalid: missing name
    with pytest.raises(ValidationError):
        Constraint(description="Y", weight=50)

def test_world_model_validation():
    """Test world model validation."""
    # Valid
    data = WorldModelData(
        actors={"user": Actor(name="User", description="End user")},
        mechanisms={"auth": Mechanism(name="Auth", description="Authentication")}
    )
    assert len(data.actors) == 1

    # Invalid: no actors
    with pytest.raises(ValidationError):
        WorldModelData(actors={}, mechanisms={"x": ...})
```

## Benefits

1. **Data Integrity**: Catch 90%+ of data errors at write time
2. **Better API Docs**: Pydantic schemas → OpenAPI documentation
3. **Type Safety**: Full typing in Python code
4. **Clearer Errors**: Validation errors show exactly what's wrong
5. **IDE Support**: Autocomplete for nested JSON structures

## Dependencies
- `pydantic>=2.0` (already in project)
- No new dependencies needed

## Risk Assessment
- **Medium risk**: Existing invalid data may fail validation
- **Mitigation**: Migration script to fix/flag invalid data
- **Testing**: Comprehensive unit tests for all schemas

## Related Issues
- Issue 003: May help identify why results don't match goals

## Notes
- This is **#3 priority** for data integrity
- Consider adding validation incrementally (start with ProblemSpec, then WorldModel)
- Validation errors should be user-friendly, not technical stack traces
