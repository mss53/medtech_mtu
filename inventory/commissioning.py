
from django.db import models

class CommissioningAct(models.Model):
    item_card = models.ForeignKey('ItemCard', on_delete=models.CASCADE, verbose_name="Карточка МТС", related_name="commissioning_acts")
    act_number = models.CharField(max_length=100, verbose_name="Номер акта")
    act_file = models.FileField(upload_to='acts/', verbose_name="Скан акта")
    date_commissioned = models.DateField(verbose_name="Дата ввода в эксплуатацию")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Акт ввода в эксплуатацию"
        verbose_name_plural = "Акты ввода в эксплуатацию"

    def __str__(self):
        return f"Акт {self.act_number} — {self.item_card}"

