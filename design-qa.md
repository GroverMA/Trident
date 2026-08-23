# Design QA — Scenario and Workspace Layout

- Source visual truth: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-9e411963-0010-4d85-8d2a-b6050b11495b.png`
- Implementation screenshot: `/Users/calin/Documents/PhD Application 2/Trident/qa-scenario-layout-after.png`
- Combined comparison: `/Users/calin/Documents/PhD Application 2/Trident/qa-scenario-layout-comparison.png`
- Viewport: 2509 × 1138 CSS pixels, desktop state, density normalized by matching source and implementation pixel dimensions before comparison.
- Additional responsive check: 1440 × 900 desktop and 390 × 844 mobile.

**Full-view comparison evidence**

- The source leaves the four-card group in a narrow central band and produces materially more unused space on the right side of an ultra-wide screen.
- The implementation centers a 1480px workspace between the persistent sidebar and the right viewport edge. The four cards occupy a balanced 1480px row, each 358px wide and 312px tall.
- Header, hero, cards and shared-core strip retain the same interaction state and information architecture.

**Focused comparison evidence**

- Typography: existing Source Sans/PingFang fallback stack, restrained 48px desktop title, line height and wrapping retained.
- Spacing/layout: hero-to-card gap reduced; card height reduced from 355px to 312px; internal gaps tightened; ultra-wide horizontal margins are symmetrical.
- Colors/tokens: existing navy, teal, off-white, border and state palette retained without new decorative treatments.
- Image quality: the screen contains no raster illustration or custom imagery; there are no missing or substituted assets.
- Copy/content: four scene names, descriptions, flow summaries and shared-core explanation remain unchanged.

**Findings**

- No actionable P0/P1/P2 mismatch remains.
- P3: very large monitors retain whitespace below the selector because the page intentionally contains only the four requested scenarios. Filling it with unrelated modules would violate the product structure.

**Comparison history**

1. Earlier finding: content capped at 1280px and 355px-tall cards made the main group feel narrow and left the ultra-wide page visually underused.
2. Fix: introduced shared 1480px/1360px workspace tokens, widened scenario/platform/diagnostic pages, shortened cards, tightened vertical rhythm and widened the research-mode selector.
3. Post-fix evidence: 2509px viewport shows a centered 1480px card row with no overflow; project, knowledge, sensing and feedback pages use the same width. The 390px mobile view remains a single-column stack with a working navigation drawer and no console errors.

**Implementation Checklist**

- [x] Ultra-wide scenario layout balanced.
- [x] Standard desktop uses a comfortable two-column card grid.
- [x] Mobile remains one column with no horizontal overflow.
- [x] Project, knowledge, sensing, feedback and diagnostic containers aligned.
- [x] Research route width increased for visual consistency.
- [x] Primary navigation and scenario cards remain interactive.
- [x] Browser console checked: no errors.

**Follow-up Polish**

- Revisit dense evidence and report tables when the next research-workflow UI phase begins; they require task-specific density rules rather than the landing-page card rhythm.

final result: passed
