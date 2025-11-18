# Candidate and Scenario Suite JSON Schemas

This document defines the structure of Candidate and ScenarioSuite JSON fields.

## Candidate Structure

Candidates are stored in the `crucible_candidates` table with the following structure:

### Database Fields
- `id`: String (primary key)
- `run_id`: String (foreign key to Run)
- `project_id`: String (foreign key to Project)
- `origin`: Enum (user/system)
- `mechanism_description`: Text (required)
- `predicted_effects`: JSON (optional)
- `scores`: JSON (optional, contains P, R, I, constraint_satisfaction)
- `provenance_log`: JSON array (required, default empty)
- `parent_ids`: JSON array (required, default empty)
- `status`: Enum (new/under_test/promising/weak/rejected)

### JSON Field Structures

#### `predicted_effects` (JSON)
```json
{
  "actors_affected": [
    {
      "actor_id": "actor_1",
      "impact": "positive|negative|neutral|mixed",
      "description": "How this actor is affected"
    }
  ],
  "resources_impacted": [
    {
      "resource_id": "resource_1",
      "change": "increase|decrease|no_change",
      "magnitude": "small|medium|large",
      "description": "How resource availability changes"
    }
  ],
  "mechanisms_modified": [
    {
      "mechanism_id": "mechanism_1",
      "change_type": "enhanced|replaced|removed|new",
      "description": "How the mechanism is modified"
    }
  ]
}
```

#### `scores` (JSON)
```json
{
  "P": {
    "overall": 0.0-1.0,
    "components": {
      "prediction_accuracy": 0.0-1.0,
      "scenario_coverage": 0.0-1.0
    }
  },
  "R": {
    "overall": 0.0-1.0,
    "components": {
      "cost": 0.0-1.0,
      "complexity": 0.0-1.0,
      "resource_usage": 0.0-1.0
    }
  },
  "I": 0.0-1.0,
  "constraint_satisfaction": {
    "constraint_1": {
      "satisfied": true|false,
      "score": 0.0-1.0,
      "explanation": "Why this constraint is satisfied or not"
    }
  }
}
```

#### `provenance_log` (JSON array)
```json
[
  {
    "type": "design|refine|eval_result|feedback",
    "timestamp": "ISO8601 timestamp",
    "actor": "user|system|agent",
    "source": "agent_run_id|chat_session_id|manual_edit",
    "description": "What changed and why",
    "reference_ids": ["candidate_id", "run_id"]
  }
]
```

#### `parent_ids` (JSON array)
Array of candidate IDs that this candidate was derived from or inspired by.

## Scenario Suite Structure

Scenario suites are stored in the `crucible_scenario_suites` table with the following structure:

### Database Fields
- `id`: String (primary key)
- `run_id`: String (foreign key to Run, unique)
- `scenarios`: JSON array (required, default empty)

### `scenarios` (JSON array)
```json
[
  {
    "id": "scenario_1",
    "name": "Scenario Name",
    "description": "Detailed description of the scenario",
    "type": "stress_test|edge_case|normal_operation|failure_mode",
    "focus": {
      "constraints": ["constraint_1", "constraint_2"],
      "assumptions": ["assumption_1"],
      "actors": ["actor_1"],
      "resources": ["resource_1"]
    },
    "initial_state": {
      "actors": {
        "actor_1": {
          "state": "description of initial actor state"
        }
      },
      "resources": {
        "resource_1": {
          "quantity": 100,
          "units": "units"
        }
      },
      "mechanisms": {
        "mechanism_1": {
          "state": "description of initial mechanism state"
        }
      }
    },
    "events": [
      {
        "step": 1,
        "description": "What happens in this step",
        "actor": "actor_1",
        "action": "action description"
      }
    ],
    "expected_outcomes": {
      "success_criteria": [
        "Criterion 1",
        "Criterion 2"
      ],
      "failure_modes": [
        "What could go wrong"
      ]
    },
    "weight": 0.0-1.0
  }
]
```

## MVP Notes

For the MVP:
- Candidates should focus on mechanism descriptions and basic predicted effects
- Rough constraint compliance estimates can be simple boolean or 0-1 scores
- Scenarios should stress high-weight constraints and fragile assumptions
- Scenario structure should be minimal but sufficient for evaluators to consume
- Diversity of candidates is more important than completeness

