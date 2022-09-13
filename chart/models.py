from django.db import models

# Create your models here.

class Order(models.Model):
    order_number = models.IntegerField(unique=True, null=False)
    price_dollar = models.IntegerField(null = False)
    price_ruble = models.FloatField(null = False)
    delivery_time = models.CharField(max_length = 11)