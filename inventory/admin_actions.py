# inventory/admin_actions.py

import openpyxl
from django.http import HttpResponse
from .models import InventoryRecord
from io import BytesIO


def export_inventory_to_excel(modeladmin, request, queryset):
    if queryset.model.__name__ == "InventorySession":
        records = InventoryRecord.objects.filter(session__in=queryset).select_related(
            "session", "item_card", "location", "item_card__item"
        )
    else:
        records = queryset

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Инвентаризация"

    headers = [
        "Номер инвентаризации",
        "Склад",
        "Ячейка",
        "Наименование",
        "Серийный номер",
        "Партия",
        "Факт. количество",
        "Сист. количество",
        "Отклонение",
        "Комментарий"
    ]
    ws.append(headers)

    for r in records:
        ws.append([
            r.session.number,
            r.session.warehouse.name,
            r.location.code if r.location else "",
            r.item_card.item.name,
            r.item_card.serial_number,
            r.item_card.batch,
            float(r.quantity_fact),
            float(r.quantity_system),
            float(r.difference),
            r.comment
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'
    return response
