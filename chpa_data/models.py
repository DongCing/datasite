from django.db import models


class Data(models.Model):
    I = models.CharField(max_length=232)
    II = models.CharField(max_length=232)
    III = models.CharField(max_length=232)
    IV = models.CharField(max_length=232)
    MOLECULE = models.CharField(max_length=232)
    PRODUCT = models.CharField(max_length=232)
    PACKAGE = models.CharField(max_length=232)
    CORPORATION = models.CharField(max_length=232)
    MANUF_TYPE = models.CharField(max_length=232)
    FORMULATION = models.CharField(max_length=232)
    STRENGTH = models.CharField(max_length=232)
    AMOUNT = models.IntegerField()
    UNIT = models.CharField(max_length=232)
    PERIOD = models.CharField(max_length=232)
    DATE = models.DateField()

