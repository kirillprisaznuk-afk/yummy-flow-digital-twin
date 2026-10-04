"""Compose capacity, economics, economic break-even and static cash runway."""

from decimal import Decimal
from fractions import Fraction

from app.domain.assumptions import Assumptions
from app.domain.capacity import calculate_capacity, capacity_state
from app.domain.economics import calculate_economics
from app.domain.precision import as_decimal, calculation
from app.domain.reporting import reporting
from app.domain.results import BreakEvenResult, CashResult, Evaluation


@calculation
def evaluate(a: Assumptions) -> Evaluation:
    a = Assumptions.model_validate(a)
    capacity = calculate_capacity(a)
    economics = calculate_economics(a)
    if economics.fixed_operating_costs == 0:
        # Zero activity already breaks even; this is not evidence of viable growth.
        break_even = BreakEvenResult(
            monthly_fulfilled_orders=Decimal(0),
            fulfilled_orders_per_day=Decimal(0),
            requested_orders_per_day=Decimal(0),
            monthly_revenue=Decimal(0),
            reachable_at_current_capacity=True,
            reason="zero_fixed_costs",
        )
    elif economics.contribution_per_order <= 0:
        break_even = BreakEvenResult(
            monthly_fulfilled_orders=None,
            fulfilled_orders_per_day=None,
            requested_orders_per_day=None,
            monthly_revenue=None,
            reachable_at_current_capacity=False,
            reason="nonpositive_contribution",
        )
    else:
        monthly = Fraction(economics.fixed_operating_costs) / Fraction(
            economics.contribution_per_order
        )
        daily = monthly / a.operating_days_per_month
        requested = daily / (1 - Fraction(a.stockout_rate)) if a.stockout_rate < 1 else None
        reachable = daily <= capacity_state(a).system_capacity and requested is not None
        break_even = BreakEvenResult(
            monthly_fulfilled_orders=as_decimal(monthly),
            fulfilled_orders_per_day=as_decimal(daily),
            requested_orders_per_day=as_decimal(requested) if requested is not None else None,
            monthly_revenue=as_decimal(monthly * Fraction(a.average_order_value + a.delivery_fee)),
            reachable_at_current_capacity=reachable,
            reason="all_demand_stocked_out"
            if requested is None
            else ("reachable" if reachable else "capacity_shortfall"),
        )
    burn = max(Decimal(0), -economics.operating_profit)
    cash = CashResult(
        monthly_operating_burn=burn,
        static_runway_months=a.starting_cash / burn if burn else None,
        runway_status="burning_cash" if burn else "no_operating_burn",
        cash_balance_is_zero=a.starting_cash == 0,
    )
    return Evaluation(
        capacity=capacity,
        economics=economics,
        break_even=break_even,
        cash=cash,
        reporting=reporting(a, capacity, economics),
    )
