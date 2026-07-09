"""Сборка данных лида для Bitrix24.

Разделяем два шага:
1. normalize_* — при постановке в очередь (outbox) превращает ORM-модель лида в
   простой dict. Не требует настроек Bitrix, поэтому вызывается прямо в сервисах.
2. build_lead_fields — при отправке воркером собирает из dict поля crm.lead.add,
   используя BitrixSettings (source_id, ответственный, UF-поле).
"""
from typing import Any

from bot.config import BitrixSettings
from bot.core.enums import ServiceIssueType
from bot.db.models.client_request import ClientRequest
from bot.db.models.service_request import ServiceRequest
from bot.db.models.user import User

# Все обращения идут в одну лид-воронку; тип различается этим ярлыком.
LEAD_TYPE_LABELS: dict[str, str] = {
    "request": "Заявка",
    "consultation": "Консультация",
    "callback": "Обратный звонок",
    "service": "Сервис / запчасти",
}

SERVICE_ISSUE_LABELS: dict[str, str] = {
    ServiceIssueType.WARRANTY.value: "Гарантия",
    ServiceIssueType.REPAIR.value: "Ремонт",
    ServiceIssueType.SPARE_PARTS.value: "Запчасти",
    ServiceIssueType.OTHER.value: "Другое",
}


def normalize_client_request(
    req: ClientRequest, user: User | None = None
) -> dict[str, Any]:
    return {
        "lead_type": req.lead_type.value,
        "name": req.contact_name,
        "phone": req.contact_phone,
        "comment": req.comment,
        "request_id": req.id,
        "telegram_id": user.telegram_id if user else None,
    }


def normalize_service_request(
    req: ServiceRequest, user: User | None = None
) -> dict[str, Any]:
    issue_label = SERVICE_ISSUE_LABELS.get(req.issue_type.value, req.issue_type.value)
    comment_parts = [f"Тип обращения: {issue_label}"]
    if req.equipment:
        comment_parts.append(f"Техника: {req.equipment}")
    comment_parts.append(req.description)
    return {
        "lead_type": "service",
        "name": user.full_name if user else "Клиент",
        "phone": req.contact_phone,
        "comment": "\n".join(comment_parts),
        "request_id": req.id,
        "telegram_id": user.telegram_id if user else None,
    }


def build_lead_fields(
    payload: dict[str, Any],
    settings: BitrixSettings,
    assigned_by_id: int | None = None,
) -> dict[str, Any]:
    lead_type = payload.get("lead_type", "request")
    label = LEAD_TYPE_LABELS.get(lead_type, lead_type)
    name = payload.get("name") or "Клиент"

    fields: dict[str, Any] = {
        "TITLE": f"{settings.title_prefix}: {label} — {name}",
        "NAME": name,
        "PHONE": [{"VALUE": payload.get("phone", ""), "VALUE_TYPE": "WORK"}],
        "SOURCE_ID": settings.source_id,
        "SOURCE_DESCRIPTION": label,
        "COMMENTS": payload.get("comment") or "",
    }
    if assigned_by_id is not None:
        fields["ASSIGNED_BY_ID"] = assigned_by_id
    if settings.uf_lead_type_field:
        fields[settings.uf_lead_type_field] = label
    return fields
