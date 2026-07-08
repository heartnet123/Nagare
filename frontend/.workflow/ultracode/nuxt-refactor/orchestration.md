# Orchestration: Nuxt Frontend Refactor

## Parent Critical Path
1. Create plan + get approval (current)
2. **Wave 1**: Packet A (Types + Infra)
3. **Wave 2**: Packet B (Stores)
4. **Wave 3**: Packet C (Composables)
5. **Wave 4**: Packets D+E in parallel (Pages + Components)
6. **Wave 5**: Packet F (Server API proxy) — optional, may skip
7. Integration: verify imports, run build
8. Final report

## Packet List

| Packet | Description | Owner | Type | Depends On |
|--------|-------------|-------|------|------------|
| A | Infrastructure & Types | subagent | write | none |
| B | Pinia Stores | subagent | write | A |
| C | Composables Refactor | subagent | write | A |
| D | Pages Reorganization | subagent | write | A, B, C (import refs) |
| E | Components Reorganization | subagent | write | A (type refs) |
| F | Server API Proxy | subagent | write | A (types) |

## Delegation Plan
- **Agents**: Up to 4 `task()` subagents (category: unspecified-high)
- **Waves**: Sequential (A→B→C) then parallel (D+E), then optional F
- **Max parallel agents**: 2 (D+E)
- **Fallback**: If delegation fails, execute packets in parent session sequentially

## Wait Points
- After Wave 3 (C) → before launching D+E in parallel
- After Wave 4 → integration + build
- After Wave 5 (optional) → final build

## Verification Order
1. `pnpm typecheck` after each wave
2. `pnpm build` after final integration
3. Manual route check for all 14 pages
