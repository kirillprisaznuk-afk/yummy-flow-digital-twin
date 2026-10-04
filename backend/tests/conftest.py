"""Small, hand-auditable fixtures independent of synthetic demo defaults."""

import pytest

from app.database.session import Database
from app.domain.assumptions import Assumptions


@pytest.fixture
def database_url(tmp_path) -> str:
    url = f"sqlite:///{(tmp_path / 'scenarios.db').as_posix()}"
    database = Database(url)
    try:
        database.initialize()
    finally:
        database.close()
    return url


@pytest.fixture
def assumptions() -> Assumptions:
    return Assumptions(
        orders_per_day="100",
        operating_days_per_month=30,
        operating_hours_per_day="10",
        average_order_value="20",
        delivery_fee="2",
        gross_margin="0.30",
        shrinkage_rate="0.01",
        stockout_rate="0",
        variable_fulfilment_cost_per_order="0.50",
        variable_delivery_cost_per_order="1",
        payment_fee_rate="0.02",
        payment_fee_per_order="0.10",
        customer_acquisition_cost="10",
        new_customer_order_share="0.10",
        monthly_rent="1000",
        monthly_utilities="200",
        monthly_software_admin="100",
        fulfilment_workers=2,
        worker_paid_hours_per_month="150",
        worker_hourly_cost="10",
        worker_productive_fraction="1",
        picking_minutes_per_order="2",
        packing_minutes_per_order="1",
        store_orders_per_hour="20",
        riders=10,
        rider_paid_hours_per_month="150",
        rider_hourly_cost="10",
        rider_productive_fraction="1",
        average_delivery_distance_km="1",
        rider_average_speed_kmh="12",
        delivery_handoff_minutes="5",
        starting_cash="10040",
    )
