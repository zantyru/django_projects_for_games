from django.db import models


class ShopSet(models.Model):
    """ """

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True, default=str)
    price = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name
