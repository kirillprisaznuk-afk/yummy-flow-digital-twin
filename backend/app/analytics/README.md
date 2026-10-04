# Analytics boundary

`contracts.py` defines bounded settings and response contracts. `sensitivity.py` changes one input at a time. `simulation.py` samples independent triangular inputs and calls the existing `domain.evaluation.evaluate` for every draw. No financial or capacity formula is copied here.

Analytics version 1.0 is separate from economic model 1.1. Assumptions and results remain stateless; no schema migration or saved-scenario mutation is required. Standard-library sampling and Decimal/rational aggregation avoid an unnecessary numerical dependency for this bounded workload. Forecasting is outside the final scope.

See [Methodology](../../../docs/METHODOLOGY.md) for formulas, precision, reproducibility and limitations. The API caps runs at 10,000 and permits one simulation at a time per process.
