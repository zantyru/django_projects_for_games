from django.db import models


class ConfigOfInitialPlayerCostume(models.Model):
    """ """

    costume = models.OneToOneField('Costume', unique=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Initial '{self.costume.__str__()}'"
