# Plan: Nuxt Frontend Refactor

## Goal
Restructure the Nagare frontend from a flat, ad-hoc layout into a Nuxt 4 best-practice structure with domain-organized pages, typed stores, clean component hierarchy, and proper separation of concerns — mirroring the modular clarity of odysseus.

## Success Criteria
- [ ] Pages grouped by feature domain in subdirectories
- [ ] Components organized by feature + role (no flat mix)
- [ ] Shared state extracted into typed stores (Pinia)
- [ ] API layer separated into focused composables
- [ ] TypeScript types extracted into `types/` directory
- [ ] Route middleware infrastructure present
- [ ] Nuxt server API proxy layer for backend calls
- [ ] `pnpm build` and `pnpm typecheck` pass
- [ ] All existing page functionality preserved identically

## Current Context
- Nuxt 4 + Nuxt UI 4 + Tailwind CSS 4
- 14 flat pages in `app/pages/`
- Components in `dashboard/`, `agent/`, `chat/`, `home/`, `mcp/` + root
- Single composable `useApi.ts` (104 lines) handles ALL API calls
- State via scattered `useState()` calls (no Pinia stores)
- No TypeScript types directory
- No middleware
- No server/ API proxy

## Constraints
- Must NOT change runtime behavior
- Must NOT delete or rewrite working components — only reorganize/rename imports
- Must keep Nuxt UI integration intact
- Each packet must have non-overlapping file ownership

## Risk Level
**High** — repo-wide frontend restructure touching every page and component. Requires careful import path updates.

## Approval Gates
- **Gate 1**: Plan approval before execution
- **Gate 2**: Verify build passes after each packet wave

## Mode
**Delegated** — using `task()` subagents for independent packets

## Work Packets

### Packet A: Infrastructure & Types (write)
- Create `app/types/` with interfaces for Session, Agent, Dataset, NavItem, etc.
- Create `app/types/api.ts` for API response types
- Create `app/plugins/nuxt-ui.ts` (Nuxt UI plugin config)
- Create `app/middleware/` directory with example guard

### Packet B: Stores (write)
- Create `app/stores/` with Pinia stores:
  - `session.ts` — active sessions + chat drawer state
  - `app.ts` — sidebar, theme, UI state
  - `agent.ts` — agent list + skills

### Packet C: Composables Refactor (write)
- Split `useApi.ts` into domain composables:
  - `composables/useApi/evaluations.ts`
  - `composables/useApi/agents.ts`
  - `composables/useApi/datasets.ts`
  - `composables/useApi/sessions.ts`
  - `composables/useApi/mcp.ts`
  - `composables/useApi/logs.ts`
  - `composables/useApi/monitoring.ts`
  - `composables/useApi/index.ts` (barrel export)
- Create `composables/useFormatTime.ts` for time formatting

### Packet D: Pages Reorganization (write)
- Group pages by domain:
  ```
  pages/
    index.vue
    chat.vue
    evaluations/index.vue (from evaluations.vue)
    datasets.vue
    benchmark.vue
    logs.vue
    pipeline.vue
    agents.vue
    monitoring.vue
    analytics.vue
    models.vue
    knowledge.vue
    mcp.vue
    settings.vue
    agents/
      config.vue (extract config panel from agents.vue)
  ```

### Packet E: Components Reorganization (write)
- Create consistent hierarchy:
  ```
  components/
    ui/              # Generic reusable (AppLogo, Badge, StatCard)
    dashboard/       # Dashboard layout pieces (Sidebar, PageHeader, PageScroll)
    chat/            # Chat components (ChatView)
    agent/           # Agent components (AgentConfigPanel)
    home/            # Home page components (Composer)
    mcp/             # MCP components (McpManager)
  ```
- Rename `DashboardXxx` → remove prefix when inside `dashboard/` dir (e.g., `DashboardPageScroll` → `dashboard/PageScroll.vue`)
- Move `AppLogo.vue` and `TemplateMenu.vue` into `ui/`
- Ensure all import paths updated

### Packet F: Server API Proxy (write)
- Create `app/server/api/` proxy routes for backend
- Each route proxies to FastAPI backend

## Eval Contract (inline)
- Outcome: Nuxt best-practice structure with zero behavioral change
- Shared surfaces: `nuxt.config.ts`, `app/app.vue`, import paths across ALL files
- Required checks: `pnpm build`, `pnpm typecheck`
- Blocking conditions: Any type error or import resolution failure
- Handoff evidence: Changed file list per packet

## Integration Policy
- Parent session owns: import path verification across all files, build validation
- Packets D and E must be coordinated to avoid import conflicts
- Run Packet A → B → C sequentially (dependencies), then D+E in parallel (independent file sets)

## Verification Plan
1. `pnpm typecheck` — must pass with zero errors
2. `pnpm build` — must succeed
3. Manual inspection of import paths across changed files
4. Check that all page routes resolve correctly

## Completion Criteria
- All success criteria met
- All verification checks pass
- Final report written to `final-report.md`
