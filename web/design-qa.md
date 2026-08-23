# Trident Web design QA

## Reference and implementation

- Desktop reference: `../visuals/role-selection-final.png`
- Desktop implementation capture: `/private/tmp/trident-web-desktop.png`
- Mobile implementation capture: `/private/tmp/trident-web-mobile-final.png`
- Desktop viewport: 1440 × 900
- Mobile viewport: 390 × 844

The reference and desktop implementation were inspected in the same comparison
input. The new screen preserves the existing Trident palette, typography
hierarchy, equal card weight, restrained borders, low shadows, whitespace, and
teal primary actions. Copy and information density changed intentionally to
reflect the new research-path model requested for the enterprise product.

## Responsive checks

- The two equal-weight cards become one column below 760 px.
- Heading sizes, card padding, and explanatory copy reduce on mobile.
- The document width does not overflow the mobile viewport.
- The primary actions remain fully visible and touch-sized.

## Interaction checks

- Both research paths enter the shared project form.
- Switching from build-first to review-first preserves entered form content.
- Build-first project creation persisted through FastAPI and opened the saved
  project route.
- Review-first project creation persisted through FastAPI and opened the saved
  project route.
- Project list loading fails safely when the API is unavailable.

## Runtime checks

- Next.js lint: passed.
- Next.js production build: passed.
- Browser DOM and visible hierarchy: passed.
- No current application errors were observed after reload. The only browser
  messages were development-runtime informational messages.

## Final result

**PASSED** — desktop and mobile layouts match the established Trident design
language, core interactions work, both research paths persist through the API,
and no blocking visual or runtime defect remains in this migrated slice.

## 2026-08-23 scenario decision layer

- The scenario selector remains a single desktop row with four equal-width, vertically extended cards.
- Project management remains a separate route; the browser check confirmed the scenario, project, knowledge, sensing, feedback and operations navigation remains linked.
- Company Scorecard and Action Plan use horizontally scrollable compact review tables instead of large per-item cards.
- The tables preserve readable labels, current/market/target comparisons, KPIs, risks, stop conditions and reviewer notes at desktop width; narrow screens scroll the table without expanding the overall page width.
- Both review surfaces use default-accept / explicit-exclude controls and retain a separate confirmation checkbox for the gate.
- Frontend lint and production build passed; the production route manifest includes both new API proxy routes.
