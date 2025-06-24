from django.utils import timezone
from django.db import models
from cryptography.fernet import Fernet
import base64
from django.conf import settings

SECRET_KEY = settings.SECRET_KEY[:32]  # Use Django's secret key as a base


def get_cipher():
  return Fernet(base64.urlsafe_b64encode(SECRET_KEY.ljust(32)[:32].encode()))


class BaseModel(models.Model):
  created_at = models.DateTimeField(default=timezone.now, editable=False)
  updated_at = models.DateTimeField(default=timezone.now)

  class Meta:
    abstract = True


class Customers(BaseModel):
  name = models.CharField(max_length=100)
  host = models.GenericIPAddressField()
  user = models.CharField(max_length=120)
  password = models.BinaryField()
  database_name = models.CharField(max_length=120)
  level_number = models.IntegerField(null=True)
  project_id = models.IntegerField(null=True)

  def set_password(self, raw_password):
    cipher = get_cipher()
    self.password = cipher.encrypt(raw_password.encode())

  def get_password(self):
    cipher = get_cipher()
    return cipher.decrypt(self.password).decode()

  def save(self, *args, **kwargs):
    if isinstance(self.password, str):  # Encrypt only if not already encrypted
      self.set_password(self.password)
    super().save(*args, **kwargs)

  def __str__(self):
    return self.name


class CustomerData(BaseModel):
  customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
  name = models.CharField(max_length=250)

  def __str__(self):
    return f'{self.customer_id}:{self.name}'


class TurningPrediction(BaseModel):
  customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
  turning = models.IntegerField()
  sarfasl = models.TextField()
  account_group = models.CharField(max_length=150)
  similarity = models.FloatField()
  title = models.TextField()

class Training(BaseModel):
  group = models.CharField(max_length=150)
  category = models.IntegerField()
  sarfasl = models.CharField(max_length=250)
  title = models.CharField(max_length=250)
