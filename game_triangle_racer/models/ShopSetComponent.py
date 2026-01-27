from django.db import models


class ShopSetComponent(models.Model):
    """Компонент набора магазина - ресурс и его количество в наборе."""

    shop_set = models.ForeignKey('ShopSet', on_delete=models.CASCADE, related_name='shopsetcomponent_set')
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(default=1, help_text="Количество ресурса в наборе")

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('shop_set', 'resource'), name='unique_shop_set_component'),
            models.CheckConstraint(check=models.Q(count__gte=1), name="resource_count_gte_1"),
        )

    def __str__(self):
        return f"{self.shop_set.name} - {self.resource.name} x {self.count}"
