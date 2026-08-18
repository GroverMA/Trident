---
name: sizing-industry-markets
description: Estimate historical and forecast market size with explicit scope, equations, source inputs, reconciliation, uncertainty, and reproducible cross-checks.
---

# Market Sizing

Sizing starts only after Gate 0 approves the scope and statistical unit. Never substitute a third-party number for a model without checking its definition.

## Workflow

1. Declare currency, nominal/real basis, geography, period, revenue/shipments/installed-base unit, and value-chain position.
2. Select top-down, bottom-up, demand-side, supply-side, or triangulated models according to available evidence.
3. Show every equation and input with source, year, transformation, and assumption status.
4. Separate historical observations, estimates, forecasts, and analyst scenarios.
5. Reconcile company, segment, region, and total figures; explain residuals and double counting.
6. Cross-check with at least one independent method where feasible.
7. Report low/base/high ranges and sensitivities when key assumptions are uncertain.

## Minimum formulas

- Bottom-up: addressable entities × penetration × annual volume × price.
- Supply-side: sum of in-scope company revenue adjusted for coverage and overlap.
- Growth: CAGR = (ending / beginning)^(1 / years) - 1.
- Forecasts must state drivers and must not imply precision beyond the evidence.

## Hard failures

- Scope or statistical unit differs from Gate 0.
- Arithmetic cannot be reproduced.
- Historical and forecast values are mixed.
- Currency/year conversions or double-count adjustments are hidden.
- A single opaque market-report number is treated as verified truth.

## Output contract

Return model choice, equations, source table, calculations, reconciliation, range, sensitivities, limitations, and evidence IDs.
