# Delivery plan and final scope

Yummy Flow Digital Twin is a new, locally runnable portfolio project inspired by earlier business experience. All examples are synthetic. Product functionality is frozen; remaining work is limited to defects, documentation and presentation.

## Delivered milestones

| Milestone | Final state |
| --- | --- |
| 1 — Domain model | Validated assumptions, capacity-constrained economics, break-even, cash and independent arithmetic tests |
| 2 — API and persistence | FastAPI, versioned scenario snapshots, PostgreSQL, Alembic and restart verification |
| 3 — Decision workspace | Overview, Scenario Lab, Operations, Unit Economics and Methodology; explicit save/load/update/delete and scenario comparison |
| 4 — Risk analysis | Six-variable sensitivity and seeded bounded Monte Carlo, using the existing domain engine |
| Local usability | Windows one-click start/stop; tracked process ownership and preserved database volumes |
| Portfolio presentation | Case-study README, coherent real screenshots, reproducible demo record and final validation review |

## Scope decisions

The final navigation is Overview, Scenario Lab, Operations, Unit Economics, Risk & Simulation and Methodology. Existing assumptions CSV exchange is preserved; no additional import capability is planned.

The original forecasting milestone is out of scope. There is no historical dataset, fitted ML, LLM, dynamic cash-depletion model, authentication, multi-user workspace or external API integration. Conditional simulation frequencies are not predictions. No hosting or public live environment is planned. Automated CI is not configured; validation currently runs locally.

## Maintenance gate

Preserve the architecture and financial calculation boundary. Fix only demonstrated defects; document any changed modelling assumption before changing formulas. Validate relevant arithmetic/API/browser behaviour and both PostgreSQL checks. A passing test count or coverage percentage alone is not proof of economic correctness.

See [final portfolio review](PORTFOLIO_REVIEW.md), [methodology](METHODOLOGY.md), [assumptions](ASSUMPTIONS.md) and the earlier [backend review](REVIEW.md). This folder has its own standalone Git repository. Only project source and intended portfolio artifacts belong in commits; sibling workspaces and ignored local configuration must never be included.
