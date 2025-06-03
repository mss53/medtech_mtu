from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Movement, ItemCard, PurchaseRequest, PurchaseOrder, Supplier
from .ItemEventLog import ItemEventLog


@receiver(post_save, sender=PurchaseRequest)
def create_purchase_order(sender, instance, created, **kwargs):
    if not created and instance.status == 'approved':
        # Проверь, есть ли уже заказ для этой заявки
        if not PurchaseOrder.objects.filter(request=instance).exists():
            # Для примера берём первого поставщика (или реализуй свою логику выбора)
            supplier = Supplier.objects.first()
            if supplier:
                PurchaseOrder.objects.create(
                    supplier=supplier,
                    request=instance,
                    status='pending'
                )

def recalc_itemcard_quantity(item_card):
    """
    Пересчитывает quantity для данной карточки МТС
    на основании всех движений Movement.
    """
    # Суммируем все поступления (+), списания (-), перемещения (+/- в зависимости от to_warehouse/from_warehouse)
    from django.db.models import Sum

    # Все поступления (+)
    receipt = Movement.objects.filter(item_card=item_card, type='receipt').aggregate(Sum('quantity'))['quantity__sum'] or 0
    # Все списания (-)
    writeoff = Movement.objects.filter(item_card=item_card, type='writeoff').aggregate(Sum('quantity'))['quantity__sum'] or 0

    # При перемещениях:
    # - если этот item_card на from_warehouse — это минус
    # - если на to_warehouse — это плюс
    move_out = Movement.objects.filter(item_card=item_card, type='move', from_warehouse=item_card.warehouse).aggregate(Sum('quantity'))['quantity__sum'] or 0
    move_in = Movement.objects.filter(item_card=item_card, type='move', to_warehouse=item_card.warehouse).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # Итог
    item_card.quantity = receipt + move_in - move_out - writeoff
    item_card.save(update_fields=['quantity'])

@receiver(post_save, sender=Movement)
def update_quantity_on_save(sender, instance, **kwargs):
    recalc_itemcard_quantity(instance.item_card)

@receiver(post_delete, sender=Movement)
def update_quantity_on_delete(sender, instance, **kwargs):
    recalc_itemcard_quantity(instance.item_card)

@receiver(post_save, sender=Movement)
def log_movement_event(sender, instance, created, **kwargs):
    if created:
        ItemEventLog.objects.create(
            item_card=instance.item_card,
            event_type=instance.type,  # 'receipt', 'move', 'writeoff'
            user=instance.user,
            description=(
                f"{instance.get_type_display()}, количество: {instance.quantity}, "
                f"из: {instance.from_warehouse or instance.from_department} "
                f"в: {instance.to_warehouse or instance.to_department}. "
                f"{instance.comment or ''}"
            )
        )
        
from .commissioning import CommissioningAct

@receiver(post_save, sender=CommissioningAct)
def log_commissioning_event(sender, instance, created, **kwargs):
    if created:
        ItemEventLog.objects.create(
            item_card=instance.item_card,
            event_type='commission',
            user=None,  # или укажи ответственного, если есть
            description=f"Акт ввода в эксплуатацию №{instance.act_number} от {instance.date_commissioned:%d.%m.%Y}",
            related_file=instance.act_file
        )

from .maintenance import MaintenanceLog

@receiver(post_save, sender=MaintenanceLog)
def log_maintenance_event(sender, instance, created, **kwargs):
    if created:
        ItemEventLog.objects.create(
            item_card=instance.schedule.item_card,
            event_type='maintenance',
            user=instance.performed_by,
            description=f"ТО/Ремонт: {instance.result}. {instance.comment}"
        )


