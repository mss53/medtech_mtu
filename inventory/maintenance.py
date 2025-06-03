from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

class MaintenanceSchedule(models.Model):
    item_card = models.ForeignKey('ItemCard', on_delete=models.CASCADE, verbose_name="Оборудование")
    maintenance_type = models.CharField(
        max_length=50, 
        choices=[('ТО', 'ТО'), ('ремонт', 'Ремонт'), ('поверка', 'Поверка')],
        verbose_name="Вид обслуживания"
    )
    interval_days = models.PositiveIntegerField(verbose_name="Интервал (дней)")
    next_due_date = models.DateField(verbose_name="Следующая дата обслуживания")
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ответственный сотрудник")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "График ТО/ремонта"
        verbose_name_plural = "Графики ТО/ремонта"

    def __str__(self):
        return f"{self.item_card} ({self.maintenance_type}) — след. {self.next_due_date}"

class MaintenanceLog(models.Model):
    schedule = models.ForeignKey('MaintenanceSchedule', on_delete=models.CASCADE, verbose_name="График обслуживания")
    date_performed = models.DateField(verbose_name="Дата выполнения")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_maintenance", verbose_name="Исполнитель")
    result = models.CharField(max_length=255, verbose_name="Результат")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Журнал ТО/ремонта"
        verbose_name_plural = "Журнал ТО/ремонта"
        ordering = ['-date_performed']

    def __str__(self):
        return f"{self.schedule.item_card} ({self.schedule.maintenance_type}) — {self.date_performed}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # После сохранения записи о проведении ТО — обновить next_due_date в расписании
        schedule = self.schedule
        from datetime import timedelta
        schedule.next_due_date = self.date_performed + timedelta(days=schedule.interval_days)
        schedule.save(update_fields=['next_due_date'])

