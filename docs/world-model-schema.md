# WorldModel JSON Schema

This document defines the structure of the WorldModel `model_data` JSON field.

## Structure

```json
{
  "actors": [
    {
      "id": "actor_1",
      "name": "Actor Name",
      "description": "Description of the actor's role and capabilities",
      "type": "person|system|organization|other",
      "capabilities": ["capability1", "capability2"],
      "constraints": ["constraint1", "constraint2"]
    }
  ],
  "mechanisms": [
    {
      "id": "mechanism_1",
      "name": "Mechanism Name",
      "description": "Description of how the mechanism works",
      "type": "process|system|algorithm|other",
      "inputs": ["input1", "input2"],
      "outputs": ["output1", "output2"],
      "actors_involved": ["actor_1"],
      "resources_required": ["resource_1"]
    }
  ],
  "resources": [
    {
      "id": "resource_1",
      "name": "Resource Name",
      "description": "Description of the resource",
      "type": "material|energy|information|time|other",
      "units": "unit_name",
      "availability": "abundant|limited|scarce",
      "constraints": ["constraint1"]
    }
  ],
  "constraints": [
    {
      "id": "constraint_1",
      "name": "Constraint Name",
      "description": "Detailed description of the constraint",
      "type": "hard|soft",
      "weight": 0-100,
      "applies_to": ["actor_1", "mechanism_1"]
    }
  ],
  "assumptions": [
    {
      "id": "assumption_1",
      "description": "Description of the assumption",
      "rationale": "Why this assumption is made",
      "confidence": "high|medium|low",
      "source": "user|agent|inferred"
    }
  ],
  "simplifications": [
    {
      "id": "simplification_1",
      "description": "What is being simplified",
      "rationale": "Why this simplification is acceptable",
      "impact": "Description of what might be lost or approximated"
    }
  ],
  "provenance": [
    {
      "type": "add|update|remove",
      "entity_type": "actor|mechanism|resource|constraint|assumption|simplification",
      "entity_id": "entity_id",
      "timestamp": "ISO8601 timestamp",
      "actor": "user|agent|system",
      "source": "chat_message_id|agent_run_id|manual_edit",
      "description": "What changed and why"
    }
  ]
}
```

## Field Descriptions

### Actors
- **id**: Unique identifier for the actor
- **name**: Human-readable name
- **description**: What the actor does and its role
- **type**: Category of actor
- **capabilities**: What the actor can do
- **constraints**: Constraints that apply to this actor

### Mechanisms
- **id**: Unique identifier for the mechanism
- **name**: Human-readable name
- **description**: How the mechanism works
- **type**: Category of mechanism
- **inputs**: What the mechanism requires
- **outputs**: What the mechanism produces
- **actors_involved**: IDs of actors that participate
- **resources_required**: IDs of resources needed

### Resources
- **id**: Unique identifier for the resource
- **name**: Human-readable name
- **description**: What the resource is
- **type**: Category of resource
- **units**: How the resource is measured
- **availability**: How available the resource is
- **constraints**: Constraints on resource usage

### Constraints
- **id**: Unique identifier for the constraint
- **name**: Human-readable name
- **description**: Detailed constraint description
- **type**: Whether constraint is hard (must satisfy) or soft (preference)
- **weight**: Importance weight (0-100)
- **applies_to**: IDs of entities this constraint applies to

### Assumptions
- **id**: Unique identifier for the assumption
- **description**: What is being assumed
- **rationale**: Why this assumption is reasonable
- **confidence**: How confident we are in this assumption
- **source**: Where the assumption came from

### Simplifications
- **id**: Unique identifier for the simplification
- **description**: What is being simplified
- **rationale**: Why simplification is acceptable
- **impact**: What might be lost or approximated

### Provenance
- **type**: Type of change (add, update, remove)
- **entity_type**: What kind of entity changed
- **entity_id**: ID of the entity that changed
- **timestamp**: When the change occurred
- **actor**: Who/what made the change (user, agent, system)
- **source**: Reference to source of change (message ID, agent run, etc.)
- **description**: Description of what changed and why

## MVP Notes

For the MVP, the WorldModeller should aim for "usable but not exhaustive" models. It's acceptable to:
- Leave less-critical details out
- Use simpler structures where appropriate
- Focus on actors, mechanisms, and constraints that are most relevant to scenario generation and evaluation

The structure should be flexible enough to support future enhancements while being simple enough for the MVP.

