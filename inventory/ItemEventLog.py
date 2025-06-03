from django.db import models
from django.contrib.auth.models import User

class ItemEventLog(models.Model):
    EVENT_TYPE_CHOICES = [
        ('commission', 'Ввод в эксплуатацию'),
        ('receipt', 'Поступление'),
        ('move', 'Перемещение'),
        ('writeoff', 'Списание'),
        ('maintenance', 'ТО/Ремонт'),
        # добавь при необходимости
    ]
    item_card = models.ForeignKey('ItemCard', on_delete=models.CASCADE, related_name='event_logs', verbose_name="Карточка МТС")
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, verbose_name="Тип события")
    date = models.DateTimeField(verbose_name="Дата/время", auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ответственный")
    description = models.TextField(blank=True, verbose_name="Описание/детали")
    related_file = models.FileField(upload_to='item_events/', blank=True, null=True, verbose_name="Документ/файл")

    class Meta:
        verbose_name = "Событие по МТС"
        verbose_name_plural = "События по МТС"
        ordering = ['-date']

    def __str__(self):
        return f"{self.item_card} — {self.get_event_type_display()} ({self.date:%d.%m.%Y %H:%M})"

