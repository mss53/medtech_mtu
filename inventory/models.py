from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование категории")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Поставщик")
    contact_info = models.TextField(blank=True, verbose_name="Контактная информация")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    name = models.CharField(max_length=255, verbose_name="Склад")
    location = models.TextField(blank=True, verbose_name="Адрес/расположение")

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    unit = models.CharField(max_length=50, verbose_name="Единица измерения")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

class Stock(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Склад")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")

    class Meta:
        verbose_name = "Остаток"
        verbose_name_plural = "Остатки"

class Receipt(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Склад")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Поставщик")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Поступление"
        verbose_name_plural = "Поступления"

class Move(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='move_from', verbose_name="Со склада")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='move_to', verbose_name="На склад")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Перемещение"
        verbose_name_plural = "Перемещения"

class WriteOff(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Склад")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    reason = models.CharField(max_length=255, verbose_name="Причина списания")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Списание"
        verbose_name_plural = "Списания"

