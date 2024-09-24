from django.db import models

from djutils.models import SearchableModel


class Town(SearchableModel):
    name = models.CharField(max_length=100)
    province = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.province})"

    class Meta(SearchableModel.Meta):
        db_table = "town"
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ["name"]
        unique_together = [["name", "province"]]


class Place(SearchableModel):
    name = models.CharField(max_length=100)
    town = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="places", related_query_name="place")

    def __str__(self):
        return f"{self.name} - {self.town}" if self.name != self.town.name else f"{self.town}"

    class Meta(SearchableModel.Meta):
        db_table = "place"
        verbose_name = "Lugar"
        verbose_name_plural = "Lugares"
        ordering = ["name"]
        unique_together = [["name", "town"]]
