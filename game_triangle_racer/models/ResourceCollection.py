from django.db import models


class ResourceCollection(models.Model):
    """Некоторое количество ресурса. Кучка-коллекция."""

    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1, help_text="Количество ресурса (кучка-коллекция)")

    class Meta:
        constraints = (
            models.CheckConstraint(check=models.Q(count__gte=1), name="resource_collection_count_gte_1"),
        )

    def __str__(self):
        return f"{self.resource.name}: {self.count}"
