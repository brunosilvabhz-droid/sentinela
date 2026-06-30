import pandas as pd

import app.db.base  # noqa: F401
from app.models.alert import Alert
from app.models.data_source import DataSource
from app.services.rule_engine import _build_mask
from app.services.notification_service import render_message_template


def test_build_mask_greater_than_numeric_value():
    series = pd.Series([10, 20, 30])
    mask = _build_mask(series, ">", 15.0)
    assert mask.tolist() == [False, True, True]


def test_alert_model_keeps_tenant_id():
    alert = Alert(tenant_id=7, data_source_id=1, name="Teste")
    assert alert.tenant_id == 7


def test_managed_alert_uses_data_source_type():
    source = DataSource(id=1, tenant_id=7, name="Managed", source_type="managed")
    alert = Alert(tenant_id=7, data_source_id=1, name="Teste", data_source=source)
    assert alert.data_source.source_type == "managed"


def test_birthday_today_condition_matches_day_and_month():
    today = pd.Timestamp.today()
    series = pd.Series([
        today.strftime("%d/%m/1990"),
        (today + pd.Timedelta(days=1)).strftime("%d/%m/1990"),
    ])
    mask = _build_mask(series, "birthday_today", None)
    assert mask.tolist() == [True, False]


def test_render_message_template_maps_variables_to_columns():
    rendered = render_message_template(
        "Ola {{nome}}, seu valor e {{valor}}.",
        {"nome": "cliente_nome", "valor": "valor_total"},
        {"cliente_nome": "Bruno", "valor_total": "150,00"},
    )
    assert rendered == "Ola Bruno, seu valor e 150,00."
