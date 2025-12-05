from django.db import models


class ShopSetComponent(models.Model):
    """ """

    shop_set = models.ForeignKey('ShopSet', on_delete=models.CASCADE)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('shop_set', 'resource'), name='unique_shop_set_component'),
            models.CheckConstraint(check=models.Q(count__gte=1), name="resource_count_gte_1"),
        )

    def __str__(self):
        return self.resource.__str__()
