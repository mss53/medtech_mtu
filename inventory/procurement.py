from django.db import models
from django.contrib.auth.models import User

class RequestStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    PENDING = 'pending', 'На согласовании'
    APPROVED = 'approved', 'Согласовано'
    ORDERED = 'ordered', 'Заказано'
    COMPLETED = 'completed', 'Выполнено'
    REJECTED = 'rejected', 'Отклонено'
    DELAYED = 'delayed', 'Задержка'
    ERROR = 'error', 'Несоответствие'

class PurchaseRequest(models.Model):
    department = models.ForeignKey('inventory.Department', on_delete=models.CASCADE, verbose_name="Подразделение")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.DRAFT,
        verbose_name="Статус"
    )
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests', verbose_name="Согласующий")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата согласования")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Заявка на закупку"
        verbose_name_plural = "Заявки на закупку"

    def __str__(self):
        return f"Заявка №{self.id} ({self.department})"

class PurchaseRequestItem(models.Model):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items', verbose_name="Заявка")
    item = models.ForeignKey('inventory.Item', on_delete=models.CASCADE, verbose_name="Материал/оборудование")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Позиция заявки"
        verbose_name_plural = "Позиции заявок"

class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Поставщик")
    contact_info = models.TextField(blank=True, verbose_name="Контактная информация")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="Поставщик")
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, verbose_name="Заявка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Ожидание'), ('sent', 'Отправлен'), ('completed', 'Выполнен'), ('delayed', 'Задержка')],
        default='pending',
        verbose_name="Статус"
    )
    contract_number = models.CharField(max_length=100, blank=True, verbose_name="Номер договора")
    contract_file = models.FileField(upload_to='contracts/', blank=True, null=True, verbose_name="Файл договора")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Заказ поставщику"
        verbose_name_plural = "Заказы поставщикам"

    def __str__(self):
        return f"Заказ {self.id} ({self.supplier})"




