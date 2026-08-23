# Design QA — Scenario Layout and Bilingual Interface

- Source visual truth: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-9e411963-0010-4d85-8d2a-b6050b11495b.png`
- Live implementation evidence: inspected in the in-app browser at 1600 × 1000 desktop and 390 × 844 mobile.
- States compared: source screenshot, current Chinese interface, current English interface, and mobile English interface.

**Full-view comparison evidence**

- The source leaves the four-card group in a narrow central band and produces materially more unused space on the right side of an ultra-wide screen.
- The implementation centers a 1480px workspace between the persistent sidebar and the right viewport edge. At desktop width the four scenarios remain in one row; cards are narrow and vertically extended rather than widened into a 2 × 2 grid.
- Header, hero, cards and shared-core strip retain the same interaction state and information architecture.

**Focused comparison evidence**

- Typography: existing Source Sans/PingFang fallback stack, restrained 48px desktop title, line height and wrapping retained.
- Spacing/layout: cards are taller and less compressed, internal sections have more breathing room, and the page uses balanced horizontal margins instead of leaving one large empty right region.
- Bilingual behavior: CN/EN control stays at the upper-right, persists across routes, and translates navigation, scenarios, project management, enterprise knowledge, sensing, feedback and research-path UI. User answers, evidence originals and report bodies retain their source language.
- Colors/tokens: existing navy, teal, off-white, border and state palette retained without new decorative treatments.
- Image quality: the screen contains no raster illustration or custom imagery; there are no missing or substituted assets.
- Copy/content: four scene names, descriptions, flow summaries and shared-core explanation remain unchanged.

**Findings**

- No actionable P0/P1/P2 mismatch remains.
- P3: very large monitors retain whitespace below the selector because the page intentionally contains only the four requested scenarios. Filling it with unrelated modules would violate the product structure.

**Comparison history**

1. Earlier finding: content capped at 1280px and 355px-tall cards made the main group feel narrow and left the ultra-wide page visually underused.
2. First fix: introduced shared 1480px/1360px workspace tokens and widened scenario/platform/diagnostic pages.
3. Current fix: increased card height to at least 352px, retained a four-column desktop row, expanded card gaps and padding, added persistent CN/EN interface state and routed scenario projects directly into the selected shared research core.
4. Post-fix evidence: at 1600px the four cards form one 380px-tall row with no overflow; the 390px mobile view remains a single-column stack with a separate navigation trigger and an unobstructed language switcher.

**Implementation Checklist**

- [x] Ultra-wide scenario layout balanced.
- [x] Desktop keeps all four scenario cards in one vertically extended row.
- [x] Mobile remains one column with no horizontal overflow.
- [x] Project, knowledge, sensing, feedback and diagnostic containers aligned.
- [x] Research route width increased for visual consistency.
- [x] Primary navigation and scenario cards remain interactive.
- [x] CN/EN switch persists across routes and restores Chinese correctly.
- [x] English mode contains no untranslated UI strings on the primary platform pages.
- [x] Scenario-to-research handoff respects the route selected after diagnostic interview.
- [x] Scenario projects show confirmed interview profile, recommended route and data boundary when entering the shared research workspace.
- [x] Browser console checked: no errors.

**Follow-up Polish**

- Revisit dense evidence and report tables when the next research-workflow UI phase begins; they require task-specific density rules rather than the landing-page card rhythm.

final result: passed
