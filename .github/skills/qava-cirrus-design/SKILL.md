---
name: qava-cirrus-design
description: "Use when designing or implementing Qava UI, Vue components, interview screens, result previews, dashboards, authoring tools, transitions, CSS tokens, or visual QA. Applies Qava's futuristic-functional adaptation of the Uiverse Cirrus design direction with accessible light surfaces, cloud atmosphere, semantic status colors, and restrained motion."
---

# Qava Cirrus Design

Build Qava as a calm, futuristic instrument: open atmosphere, precise controls, live data, and motion that explains state change.

This skill is inspired by the publicly visible Cirrus concept at https://uiverse.io/design/systems/cirrus. The downloadable Cirrus package is account-gated; do not claim access to or reproduce unavailable proprietary token files, assets, or component source. The values in this skill are an original Qava adaptation of the public concept.

## When to Use

Use this skill for:

- Qava interview, authoring, result, health, and publication screens;
- Vue component styling and semantic component renderers;
- question-to-question transitions and loading states;
- live canonical-result previews and structured-data displays;
- design tokens, responsive layouts, accessibility, and visual QA.

Also load and follow `vue-best-practices` for Vue implementation. Load `vue-router-best-practices` when route behavior changes.

## Experience Principles

1. **Open sky, dense utility**: use a soft cloud-like page atmosphere around compact work surfaces. Do not turn operational content into a marketing hero.
2. **Output always visible**: on desktop, keep the current canonical output and health visible beside the active question. On narrow screens, expose them through persistent tabs or a bottom sheet without losing answer progress.
3. **One active interaction**: give the current question clear focus. Previous and future context stays subordinate.
4. **Motion explains revision**: animate question replacement, result patches, readiness changes, and attention changes. Avoid ambient motion that competes with work.
5. **Typed controls look native to their meaning**: choices, money, dates, collections, and structured inputs retain distinct affordances while sharing tokens.
6. **Futuristic means precise**: use crisp borders, subtle depth, excellent typography, compact status instrumentation, and immediate feedback. Avoid neon cyberpunk, glass everywhere, decorative grids, and gratuitous glow.

## Visual Direction

### Atmosphere

- Base the page on a very pale blue-white field with a subtle cloudy bitmap or layered radial/linear CSS atmosphere.
- Keep clouds low-contrast and non-interactive. They must never reduce text contrast or obscure focus indicators.
- Use white and near-white operational surfaces with hairline cool-gray borders and ultra-soft shadows.
- Do not use floating decorative orbs, bokeh blobs, purple gradients, or dark-mode-first styling.

### Typography

- Use a geometric sans for interface text and data. Preferred open-source choice: `Manrope`.
- Use one italic serif accent sparingly for a short empty-state phrase, section punctuation, or a single authoring prompt. Preferred open-source choice: `Newsreader Italic`.
- Never use the serif for controls, tables, JSON, health metrics, or long body text.
- Use a monospace face such as `IBM Plex Mono` for JSON pointers, stable IDs, revisions, and canonical output.
- Keep letter spacing at `0`. Use weight, size, and color for hierarchy.

### Palette

Define semantic CSS variables; these Qava values are adaptations, not extracted Cirrus tokens:

```css
:root {
  --qava-sky-50: #f5faff;
  --qava-sky-100: #eaf5ff;
  --qava-sky-500: #3998e8;
  --qava-ink: #111317;
  --qava-ink-muted: #5f6875;
  --qava-surface: #ffffff;
  --qava-surface-soft: #f8fafc;
  --qava-line: #dbe3eb;
  --qava-orange: #f29b38;
  --qava-green: #36a269;
  --qava-red: #d94b58;
  --qava-focus: #1677c8;
  --qava-shadow: 0 16px 48px rgb(28 55 82 / 0.10);
}
```

- Obsidian (`--qava-ink`) is the primary command color.
- Sky blue marks selection, information, and active progress.
- Citrus orange marks attention that does not block publication.
- Meadow green marks valid, ready, and successful states.
- Red is reserved for invalid, destructive, or blocking states.
- Never rely on color alone; pair every status with text and an icon.

### Shape and Depth

- Use pill geometry for compact controls, segmented modes, filters, tags, and primary commands.
- Use 8px or smaller radii for data panels, question surfaces, collection editors, and modals. Do not make every panel pill-shaped.
- Use one level of border and shadow per surface. Do not nest decorative cards.
- Prefer full-height split panes and unframed layout regions over dashboards made entirely of cards.

## Qava Application Shell

Desktop layout:

```text
┌──────────────── top status rail ────────────────┐
│ questionnaire · revision · progress · readiness│
├──────────── interview ─────────┬──── result ────┤
│ topic / question context       │ Canonical JSON │
│ active typed control           │ Health + issues │
│ answer actions                 │ Provenance      │
└────────────────────────────────┴────────────────┘
```

- Use a stable two-pane grid with interview content as the primary pane and the complete live output as the secondary pane.
- Make the divider resizable only if the implementation remains accessible and keyboard-operable; otherwise use a fixed responsive ratio.
- Keep publication visually separate from ordinary answer submission. Use an explicit review/publish command and never place it as the default next-question action.
- Show full canonical output, not a truncated decorative sample. Provide tree and raw JSON modes, copy/download actions, pointer highlighting, and revision identity.
- Show health as compact dimensions plus attention items, not a large unexplained gauge.

Mobile layout:

- Use a stable header and segmented `Question | Result | Health` view control.
- Preserve the active answer draft while switching views.
- Keep the primary answer action reachable above the safe area.
- Do not shrink the desktop split pane into unreadable columns.

## Components

- **Question surface**: prompt, concise reason, required/optional state, typed control, validation, and actions. Avoid putting the surface inside another card.
- **Choice controls**: use visible selected states, stable layout, keyboard navigation, and labels that never substitute for stored IDs.
- **Collection editor**: use compact rows with clear add, duplicate, reorder, and delete controls. Confirm destructive removal when an item has mapped output.
- **Result preview**: render the full document with syntax color that meets contrast requirements; highlight changed JSON pointers after each accepted answer.
- **Health panel**: show all five dimensions, readiness, evidence-linked attention, and blocking status. Use restrained bars or dots, never color-only scoring.
- **Progress rail**: show output requirements satisfied, not merely question count.
- **Clarification**: distinguish it from a normal question with a concise reason and evidence reference, not a radically different layout.
- **Publication review**: show exact revision, destination, validation result, idempotency state, and irreversible external-artifact warning.

Use Lucide icons where an icon exists. Icon-only buttons require accessible names and tooltips when meaning is not universally familiar.

## Motion

- Question replacement: Vue `<Transition mode="out-in">`, keyed by interaction ID.
- Forward movement: outgoing content shifts `-12px`; incoming content begins at `12px`. Reverse these directions when navigating backward.
- Duration: 180-240ms for question swaps, 120-180ms for status changes.
- Animate only `transform` and `opacity` for question transitions.
- Result updates: tint changed JSON lines or tree nodes for 650ms with a subtle sky background;
  do not rerun the whole question transition or rely on color without a changed-state label.
- Readiness changes: crossfade the status label and announce the change through an ARIA live region.
- Respect `prefers-reduced-motion: reduce`: remove translation and reduce fades to near-instant state changes.
- Never delay answer acceptance or API completion to finish an animation.

## Vue Implementation Workflow

1. Map component responsibilities before implementation. Keep route views as composition surfaces.
2. Keep authoritative session state in a focused composable or store; derive progress, readiness labels, and preview highlighting with `computed`.
3. Use typed props down and events up. Renderers emit typed answer actions; they do not map output fields or choose the next question.
4. Key the question transition by interaction ID and use `mode="out-in"` to prevent overlap.
5. Keep global tokens, fonts, atmosphere, and resets in a dedicated stylesheet. Keep feature styles scoped to SFCs.
6. Validate every control at keyboard-only, 200% zoom, reduced motion, and mobile/desktop widths.
7. Verify the full result remains inspectable after long strings, deep objects, large collections, errors, and loading states.

## Definition of Done

- The active question and complete result are both reachable without losing state.
- Question transitions communicate direction, do not overlap, and respect reduced motion.
- Every answer component preserves the typed answer contract and stable machine values.
- Readiness, health, errors, and attention states have text and icon cues in addition to color.
- The primary workflow is keyboard-operable with visible focus.
- No text overlaps or overflows at mobile, desktop, 200% zoom, or with long identifiers.
- Publication is explicit and visually distinct from answer submission.
- The UI reads as light, precise, atmospheric, and work-focused rather than decorative or promotional.
