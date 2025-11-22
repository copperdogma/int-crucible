# Issue 002: Flag Issue dialog needs better Issue Type descriptions

**Status**: Open  
**Priority**: Medium  
**Category**: UX  
**Discovered**: 2025-01-21  
**Related Story**: (if applicable)

## Description

When users click the "Flag Issue" button, they see a dropdown for "Issue Type" with options:
- Model (World Model / Problem Spec)
- Constraint
- Evaluator
- Scenario

These terms may not be clear to users who aren't familiar with the Int Crucible system. Users may not understand what each type means or when to use it.

## Steps to Reproduce

1. Open a project
2. Click "Flag Issue" button (either in Spec Panel or Results View)
3. Observe the Issue Type dropdown
4. Notice there's no explanation of what each type means

## Expected Behavior

When users select an Issue Type, they should see a brief, one-line description explaining:
- What that component is
- What kind of problems relate to it
- When to flag an issue of that type

For example:
- **Constraint**: Rules or limits that must be satisfied (e.g., "must be under budget", "must be completed by deadline")
- **Evaluator**: The scoring system that rates candidates (e.g., "the evaluator is too harsh", "the evaluator ignores important factors")
- **Scenario**: Test cases used to evaluate candidates (e.g., "missing edge cases", "scenarios don't match real-world conditions")

## Actual Behavior

Users see dropdown options without any explanation of what they mean. Users may guess incorrectly which type to select, leading to misclassified issues.

## Environment

- **Component**: `frontend/components/IssueDialog.tsx`
- **Lines**: 67-77 (Issue Type select dropdown)

## Investigation Notes

### Current Implementation

The IssueDialog component has a simple `<select>` dropdown:
```tsx
<select
  value={type}
  onChange={(e) => setType(e.target.value as typeof type)}
  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
  required
>
  <option value="model">Model (World Model / Problem Spec)</option>
  <option value="constraint">Constraint</option>
  <option value="evaluator">Evaluator</option>
  <option value="scenario">Scenario</option>
</select>
```

### UX Options Considered

1. **Tooltip on hover** - Good for quick reference, but not discoverable
2. **Description text below dropdown** - Shows description for selected option
3. **Help text/icon with modal** - More information but requires extra click
4. **Descriptive option text** - Include description in option label itself

### Recommended Approach

Show a description below the dropdown that updates when the selection changes. This is:
- Always visible
- Context-aware (shows description for selected option)
- Doesn't require extra clicks
- Easy to implement

## Proposed Solution

Add a description div below the Issue Type select that displays a helpful one-line description based on the selected type:

```tsx
<div className="mb-4">
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Issue Type *
  </label>
  <select
    value={type}
    onChange={(e) => setType(e.target.value as typeof type)}
    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
    required
  >
    <option value="model">Model (World Model / Problem Spec)</option>
    <option value="constraint">Constraint</option>
    <option value="evaluator">Evaluator</option>
    <option value="scenario">Scenario</option>
  </select>
  <p className="mt-1 text-sm text-gray-500">
    {type === 'model' && 'The problem specification or world model is incorrect or incomplete'}
    {type === 'constraint' && 'A rule or limit that must be satisfied is wrong or missing'}
    {type === 'evaluator' && 'The scoring system that rates candidates has issues'}
    {type === 'scenario' && 'A test case used to evaluate candidates is problematic'}
  </p>
</div>
```

Alternatively, use a more detailed option with an info icon that shows a tooltip or expands on click.

## Resolution

[Pending implementation]

---

**Last Updated**: 2025-01-21  
**Updated By**: AI Agent

