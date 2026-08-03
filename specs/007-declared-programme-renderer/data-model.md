# Data Model: Declared Programme Renderer

## Unchanged

- **Published questionnaire**: immutable and versioned; carries the component specification and
  answer schema.
- **Session answer**: validated server-side before direct mapping to the declared target.
- **Result, provenance, health, readiness, and next interaction**: recalculated through the
  existing deterministic session flow after each accepted answer.

## Programme Declaration

Published presentation metadata for the domain-neutral `declared_programme` component.

| Field | Rule |
| --- | --- |
| `groups` | Required non-empty collection of layout groups. Group IDs are non-empty and unique; groups are presentation structure only. |
| `groups[].label` | Required respondent-facing label; never emitted as evidence. |
| `groups[].items` | Required non-empty collection of selectable items. Each item has globally unique non-empty `value` and non-empty `label`. |
| `statuses` | Required non-empty collection of available statuses. Every status has unique non-empty stable `value` and non-empty `label`. |
| `details` | Optional collection of supported item-detail declarations. Keys are non-empty and unique; labels are presentation-only. |
| `details[].component` | Initially `single_select`, `short_text`, `long_text`, `number`, or `boolean`. Select details declare non-empty stable-value options. |

## Programme Answer

One typed object submitted by the renderer and accepted through the normal session answer path.

```json
{
  "selections": [
    {
      "item_id": "front_foyer",
      "status": "required",
      "details": {
        "size": "generous",
        "floor": "main_floor",
        "special_requirements": "Direct covered access from the garage."
      }
    }
  ]
}
```

| Field | Rule |
| --- | --- |
| `selections` | Required array with the declaration's minimum-selection rule; each `item_id` occurs at most once. |
| `selections[].item_id` | Required stable item value from the declaration's flattened groups. |
| `selections[].status` | Required stable status value from the declaration. |
| `selections[].details` | Optional object containing only declared detail keys with values compatible with each declared detail schema. |

## Programme Renderer Props

Client-only derived props: validated groups, statuses, optional detail descriptors, label, current
typed value, and disabled state. The renderer does not receive output targets, questionnaire IDs,
health rules, or custom-home terminology.

## Programme Compatibility Issue

A deterministic draft issue with a stable code, author-facing message, and declaration pointer.
It covers missing/duplicate stable values, missing labels, empty groups/statuses, unsupported or
incomplete details, and answer-schema incompatibility. Issues block publication but never mutate
published versions or active sessions.