from django.db import models
from django.contrib.auth.models import User
from .maintenance import *
from .procurement import *
from .commissioning import CommissioningAct
from .ItemEventLog import ItemEventLog


class Location(models.Model):
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE, verbose_name="Склад")
    code = models.CharField(max_length=50, verbose_name="Код ячейки (адрес)")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Адрес хранения"
        verbose_name_plural = "Адреса хранения"
        unique_together = ('warehouse', 'code')

    def __str__(self):
        return f"{self.warehouse.name} — {self.code}"

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категория")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="Подразделение")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
    def __str__(self):
        return self.name

class Warehouse(models.Model):
    name = models.CharField(max_length=100, verbose_name="Склад")
    address = models.TextField(blank=True, verbose_name="Местоположение")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Подразделение")

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Категория")
    unit = models.CharField(max_length=50, verbose_name="Единица измерения")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Вид МТС"
        verbose_name_plural = "Виды МТС"
    def __str__(self):
        return self.name

class ItemCard(models.Model):
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Адрес хранения")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Вид МТС")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Серийный номер")
    batch = models.CharField(max_length=100, blank=True, verbose_name="Партия")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Срок годности")
    storage_conditions = models.CharField(max_length=255, blank=True, verbose_name="Условия хранения")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, verbose_name="Склад")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Подразделение")
    date_received = models.DateField(null=True, blank=True, verbose_name="Дата поступления")
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Заказ поставщику"
    )

    class Meta:
        verbose_name = "Карточка МТС"
        verbose_name_plural = "Карточки МТС"

    def __str__(self):
        return f"{self.item.name} (серия: {self.batch}, SN: {self.serial_number})"

class Movement(models.Model):
    item_card = models.ForeignKey(ItemCard, on_delete=models.CASCADE, verbose_name="Карточка МТС")
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='move_from', verbose_name="Откуда (склад)")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='move_to', verbose_name="Куда (склад)")
    from_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='move_from_dep', verbose_name="Откуда (подразделение)")
    to_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='move_to_dep', verbose_name="Куда (подразделение)")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата перемещения")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ответственный")
    type = models.CharField(
        max_length=20,
        choices=[('receipt', 'Поступление'), ('move', 'Перемещение'), ('writeoff', 'Списание')],
        verbose_name="Тип операции"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Движение МТС"
        verbose_name_plural = "Движения МТС"

    def __str__(self):
        return f"{self.get_type_display()} - {self.item_card} ({self.quantity})"

from django.utils import timezone

class InventorySession(models.Model):
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE, verbose_name="Склад")
    number = models.CharField(max_length=20, unique=True, verbose_name="Номер инвентаризации", blank=True)
    date_started = models.DateTimeField(auto_now_add=True, verbose_name="Дата начала")
    date_finished = models.DateTimeField(null=True, blank=True, verbose_name="Дата окончания")
    status = models.CharField(
        max_length=20,
        choices=[('open', 'Открыта'), ('closed', 'Закрыта')],
        default='open',
        verbose_name="Статус"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Инвентаризация"
        verbose_name_plural = "Инвентаризации"

    def save(self, *args, **kwargs):
        if not self.number:
            # Формируем номер: ИНВ-год-четырёхзначный ID (например, ИНВ-2024-0005)
            last = InventorySession.objects.filter(
                date_started__year=timezone.now().year
            ).count() + 1
            self.number = f"ИНВ-{timezone.now().year}-{last:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} ({self.warehouse.name})"

class InventoryRecord(models.Model):
    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, verbose_name="Инвентаризация")
    item_card = models.ForeignKey('ItemCard', on_delete=models.CASCADE, verbose_name="Карточка МТС")
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Адрес хранения")
    quantity_fact = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Факт. количество")
    quantity_system = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сист. количество")
    difference = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Отклонение", default=0)
    comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Результат инвентаризации"
        verbose_name_plural = "Результаты инвентаризаций"

    def save(self, *args, **kwargs):
        # Автоматический пересчёт разницы при каждом сохранении записи
        self.difference = self.quantity_fact - self.quantity_system
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.session.number}: {self.item_card.item.name} "
            f"(факт: {self.quantity_fact}, откл.: {self.difference})"
        )
        




