from django.db import models


class ShopSet(models.Model):
    """Набор товаров в магазине, который можно купить за определённую цену."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True)
    price = models.PositiveSmallIntegerField(default=0, help_text="Цена набора")

    def __str__(self):
        return self.name
