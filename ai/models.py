from django.utils import timezone
from django.db import models
from cryptography.fernet import Fernet
import base64
from django.conf import settings

SECRET_KEY = settings.SECRET_KEY[:32]


def get_cipher():
    return Fernet(base64.urlsafe_b64encode(SECRET_KEY.ljust(32)[:32].encode()))


# ---------------------- BaseModel ----------------------

class BaseModel(models.Model):

    class Meta:
        abstract = True


# ---------------------- Organizational ----------------------

class Organizational(BaseModel):
    id = models.AutoField(primary_key=True)
    Grouh = models.CharField(max_length=550)
    Category = models.CharField(max_length=250)
    Sarfasl = models.CharField(max_length=250)
    contorol = models.CharField(max_length=250)
    Title = models.CharField(max_length=250)

    class Meta:
        db_table = 't1'
        managed = False

    def __str__(self):
        return f"[ORG] {self.Title}"


# ---------------------- Indexing ----------------------

"""class Indexing(BaseModel):
    id = models.AutoField(primary_key=True)
    Grouh = models.CharField(max_length=150)
    Category = models.CharField(max_length=250)
    Sarfasl = models.CharField(max_length=250)
    contorol = models.CharField(max_length=250)
    Title = models.CharField(max_length=250)

    class Meta:
        db_table = 'ind1'
        managed = False

    def __str__(self):
        return f"[BEN] {self.Title}"""



