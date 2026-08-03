# Declared Programme Component Contract

## Purpose

`declared_programme` is a client-owned, domain-neutral component for a published catalogue of
grouped items. It captures an item's declared status and optional declared details as one typed
object. The grouping and display labels are presentation metadata; they are not output mappings or
stored values.

## Presentation Props

```json
{
  "groups": [
    {
      "id": "entry",
      "label": "Entry and main floor",
      "items": [
        { "value": "front_foyer", "label": "Front foyer" },
        { "value": "mudroom", "label": "Mudroom" }
      ]
    }
  ],
  "statuses": [
    { "value": "required", "label": "Required" },
    { "value": "possible", "label": "Possible" },
    { "value": "not_needed", "label": "Not needed" }
  ],
  "details": [
    {
      "key": "size",
      "label": "Preferred size",
      "component": "single_select",
      "options": [
        { "value": "compact", "label": "Compact" },
        { "value": "generous", "label": "Generous" }
      ]
    },
    {
      "key": "special_requirements",
      "label": "Special requirements",
      "component": "long_text"
    }
  ]
}
```

## Answer Schema Contract

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["selections"],
  "properties": {
    "selections": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["item_id", "status"],
        "properties": {
          "item_id": { "type": "string", "enum": ["front_foyer", "mudroom"] },
          "status": { "type": "string", "enum": ["required", "possible", "not_needed"] },
          "details": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "size": { "type": "string", "enum": ["compact", "generous"] },
              "special_requirements": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

## Renderer Behavior

- The renderer displays declared group and item labels.
- The renderer emits the corresponding item and status `value` fields, never labels or group IDs.
- Details are associated with the selected item's `item_id` and are omitted when empty.
- Each `item_id` can occur no more than once in `selections`.
- Invalid or incompatible published props resolve to the standard unsupported component state.
- This component does not know the questionnaire, output mapping target, domain vocabulary, or
  health policy.

## Publication Validation

Publication must reject a declaration when:

- groups, group IDs, item values, status values, or detail keys are absent, empty, or duplicate;
- display labels are absent or empty;
- a detail component is unsupported, or select details omit options;
- the answer schema does not define the compatible `selections[].item_id`, `status`, and optional
  `details` structure and stable-value enums;
- the answer schema permits a declared detail that does not match its declared control semantics.

## Runtime Boundary

The ordinary `POST /api/v1/sessions/{session_id}/answers` endpoint accepts the typed object using
its existing request shape. The existing direct mapping writes the accepted answer to the declared
target. No component-specific endpoint or API schema is introduced.