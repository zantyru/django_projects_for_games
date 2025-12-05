from django.db import models


class ConfigOfInitialPlayerResource(models.Model):
    """ """

    resource = models.OneToOneField('Resource', unique=True, on_delete=models.CASCADE)
    initial_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Initial '{self.resource.__str__()}' x {self.initial_count}"
