"""Monthly unit economics. All labour is fixed within each evaluated scenario."""

from decimal import Decimal
from fractions import Fraction

from app.domain.assumptions import Assumptions
from app.domain.capacity import capacity_state
from app.domain.precision import as_decimal, calculation
from app.domain.results import EconomicsResult


@calculation
def calculate_economics(a: Assumptions) -> EconomicsResult:
    a = Assumptions.model_validate(a)
    volume = capacity_state(a).fulfilled * a.operating_days_per_month

    def amount(unit_cost: Decimal) -> Decimal:
        # Do not multiply by an already-rounded daily capacity (e.g. 300 / 7).
        return as_decimal(volume * Fraction(unit_cost))

    revenue_per_order = a.average_order_value + a.delivery_fee
    basket_revenue = amount(a.average_order_value)
    delivery_revenue = amount(a.delivery_fee)
    revenue = amount(revenue_per_order)
    cogs_per_order = a.average_order_value * (1 - a.gross_margin)
    cogs = amount(cogs_per_order)
    shrinkage_per_order = a.average_order_value * a.shrinkage_rate
    payment_per_order = (
        a.average_order_value + a.delivery_fee
    ) * a.payment_fee_rate + a.payment_fee_per_order
    acquisition_per_order = a.customer_acquisition_cost * a.new_customer_order_share
    contribution_per_order = (
        a.average_order_value * a.gross_margin
        + a.delivery_fee
        - shrinkage_per_order
        - a.variable_fulfilment_cost_per_order
        - a.variable_delivery_cost_per_order
        - payment_per_order
        - acquisition_per_order
    )
    contribution = amount(contribution_per_order)
    fulfilment_payroll = a.fulfilment_workers * a.worker_paid_hours_per_month * a.worker_hourly_cost
    rider_payroll = a.riders * a.rider_paid_hours_per_month * a.rider_hourly_cost
    fixed = (
        fulfilment_payroll
        + rider_payroll
        + a.monthly_rent
        + a.monthly_utilities
        + a.monthly_software_admin
    )
    exact_profit = volume * Fraction(contribution_per_order) - Fraction(fixed)
    operating_profit = as_decimal(exact_profit)
    variable_cost_per_order = (
        cogs_per_order
        + shrinkage_per_order
        + a.variable_fulfilment_cost_per_order
        + a.variable_delivery_cost_per_order
        + payment_per_order
        + acquisition_per_order
    )
    exact_costs = volume * Fraction(variable_cost_per_order) + Fraction(fixed)
    total_costs = as_decimal(exact_costs)
    return EconomicsResult(
        monthly_fulfilled_orders=as_decimal(volume),
        product_revenue=basket_revenue,
        delivery_revenue=delivery_revenue,
        total_revenue=revenue,
        product_cogs=cogs,
        product_gross_profit=amount(a.average_order_value * a.gross_margin),
        product_gross_margin=a.gross_margin if basket_revenue else None,
        shrinkage_cost=amount(shrinkage_per_order),
        variable_fulfilment_cost=amount(a.variable_fulfilment_cost_per_order),
        variable_delivery_cost=amount(a.variable_delivery_cost_per_order),
        payment_cost=amount(payment_per_order),
        acquisition_cost=amount(acquisition_per_order),
        contribution=contribution,
        contribution_per_order=contribution_per_order,
        contribution_margin=contribution_per_order / revenue_per_order if revenue else None,
        fulfilment_payroll=fulfilment_payroll,
        rider_payroll=rider_payroll,
        total_delivery_cost=as_decimal(
            Fraction(rider_payroll) + volume * Fraction(a.variable_delivery_cost_per_order)
        ),
        fixed_operating_costs=fixed,
        total_operating_costs=total_costs,
        cost_per_order=as_decimal(exact_costs / volume) if volume else None,
        operating_profit=operating_profit,
        operating_margin=as_decimal(exact_profit / (volume * Fraction(revenue_per_order)))
        if revenue
        else None,
        is_at_or_above_break_even=exact_profit >= 0,
    )
