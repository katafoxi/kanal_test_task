from django.db import models


class Contracts(models.Model):
    id = models.IntegerField(primary_key=True)
    contract = models.IntegerField()
    price_usd = models.IntegerField()
    price_rub = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contracts'