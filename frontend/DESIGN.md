# Nagare Design System

## 1. Atmosphere & Identity

Nagare is a quiet operations workspace: direct, compact, and evidence-led. Its signature is a warm stone surface system with one emerald action color, letting technical content and current state carry the hierarchy.

## 2. Color

| Role | Token | Light | Dark | Usage |
| --- | --- | --- | --- | --- |
| Surface/primary | `--ui-bg` | stone-50 | stone-950 | Page background |
| Surface/secondary | `--ui-bg-muted` | stone-100 | stone-900 | Toolbars, selected rows |
| Surface/elevated | `--ui-bg-elevated` | white | stone-900 | Panels, overlays |
| Text/primary | `--ui-text` | stone-900 | stone-50 | Body, headings |
| Text/secondary | `--ui-text-muted` | stone-500 | stone-400 | Metadata, helper text |
| Border/default | `--ui-border` | stone-200 | stone-700 | Dividers, controls |
| Accent/primary | `primary` | green-600 | green-400 | Actions, focus, active state |
| Status/success | `success` | green-600 | green-400 | Completed operations |
| Status/warning | `warning` | amber-600 | amber-400 | Recoverable caution |
| Status/error | `error` | red-600 | red-400 | Failures, deletion |

Rules: use Nuxt UI semantic colors before raw palette values. Accent marks actions and focus, never decoration. Blue gradients found on older pages are existing inconsistency, not a pattern for new work.

## 3. Typography

Primary font is Public Sans. Monospace is the platform monospace stack and is reserved for IDs, counts, and code-like metadata.

| Level | Size | Weight | Line height | Usage |
| --- | --- | --- | --- | --- |
| H1 | 30px | 600 | 1.25 | Page title |
| H2 | 20px | 600 | 1.35 | Major section |
| H3 | 16px | 600 | 1.4 | Panel heading |
| Body | 16px | 400 | 1.6 | Main copy |
| Body/sm | 14px | 400 | 1.5 | Controls and rows |
| Caption | 12px | 500 | 1.4 | Metadata |

Letter spacing stays `0`; existing `tracking-tight` page headings are accepted legacy usage.

## 4. Spacing & Layout

Base unit is 4px. Use Tailwind spacing tokens only. Page content caps at `max-w-6xl`, uses 24px horizontal padding, and collapses multi-column tools below 1024px. Standard breakpoints remain `sm`, `md`, `lg`, `xl`, `2xl`.

## 5. Components

### Dashboard Page
- Structure: `DashboardPageScroll`, `DashboardPageHeader`, full-width sections.
- States: loading and page-level error appear in content, not detached toasts.
- Accessibility: one H1, logical heading order, no keyboard traps.

### Upload Drop Area
- Structure: native file input, visible browse action, drag target, helper text.
- States: default, drag-active, focus, disabled/uploading, success, error.
- Accessibility: labeled input, keyboard browse path, status announced with `aria-live`.

### Document Inventory
- Structure: responsive table, metadata columns, icon actions with tooltips.
- States: loading skeleton, empty guidance, row hover, delete-in-progress.
- Accessibility: column headers, action names include document title, 40px minimum action targets.

### Chunk Preview
- Structure: responsive slideover, document metadata, ordered chunk list, pagination footer.
- States: loading skeleton, empty, error, paged content.
- Accessibility: overlay focus management from Nuxt UI, stable chunk numbering, explicit close action.

## 6. Motion & Interaction

Motion intensity is low. Use Nuxt UI overlay transitions and 150ms color/opacity feedback only. No perpetual or decorative motion. Respect `prefers-reduced-motion`; no workflow depends on animation.

## 7. Depth & Surface

Strategy is borders plus small tonal shifts. Dashboard sections remain unframed; repeated records and overlays may use one border. Shadows are limited to Nuxt UI overlay defaults.

## 8. Accessibility Constraints & Accepted Debt

Target WCAG 2.2 AA: 4.5:1 body contrast, visible focus, keyboard reachability, named icon actions, useful error recovery, and no color-only state.

| Item | Location | Why accepted | Owner / Exit |
| --- | --- | --- | --- |
| Older pages mix blue and emerald accents | Existing dashboard routes | Outside this feature scope | Consolidate during dashboard-wide design pass |
| No frontend automated test runner | `frontend/` | Existing project constraint | Add when interaction test infrastructure is adopted |
