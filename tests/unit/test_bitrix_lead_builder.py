from bot.config import BitrixSettings
from bot.services.bitrix_lead_builder import build_lead_fields


def _settings(**overrides) -> BitrixSettings:
    base = {"enabled": True, "source_id": "WEB", "title_prefix": "Бот"}
    base.update(overrides)
    return BitrixSettings(**base)


def test_build_lead_fields_maps_type_label_and_phone():
    fields = build_lead_fields(
        {"lead_type": "callback", "name": "Иван", "phone": "+71234567890", "comment": "перезвоните"},
        _settings(),
    )
    assert fields["SOURCE_DESCRIPTION"] == "Обратный звонок"
    assert "Обратный звонок" in fields["TITLE"]
    assert fields["NAME"] == "Иван"
    assert fields["PHONE"] == [{"VALUE": "+71234567890", "VALUE_TYPE": "WORK"}]
    assert fields["SOURCE_ID"] == "WEB"
    assert fields["COMMENTS"] == "перезвоните"
    # Опциональные поля не добавляются, если не заданы.
    assert "ASSIGNED_BY_ID" not in fields


def test_build_lead_fields_includes_optional_fields_when_set():
    fields = build_lead_fields(
        {"lead_type": "request", "name": "Пётр", "phone": "+700", "comment": None},
        _settings(uf_lead_type_field="UF_CRM_LEAD_TYPE"),
        assigned_by_id=42,
    )
    assert fields["ASSIGNED_BY_ID"] == 42
    assert fields["UF_CRM_LEAD_TYPE"] == "Заявка"
    # comment=None → пустая строка, а не None
    assert fields["COMMENTS"] == ""


def test_build_lead_fields_unknown_type_falls_back_to_raw_value():
    fields = build_lead_fields(
        {"lead_type": "weird", "name": "Аноним", "phone": "+1", "comment": None},
        _settings(),
    )
    assert fields["SOURCE_DESCRIPTION"] == "weird"
