from celery import shared_task

from ai.models import Customers
from ai.service.customers_db import CustomersDBService
from ai.service.predict import PredictCustomersData
from ai.service.train import TrainModel


@shared_task
def get_customers_data():
    customers = Customers.objects.all()
    for customer in customers:
        get_customer_data.delay(customer.id)
        get_customer_data(customer.id)

@shared_task
def get_customer_data(customer_id):
    CustomersDBService(customer_id).execute()

@shared_task
def predict_customer_data():
    PredictCustomersData().execute()

@shared_task
def train_model_files():
    TrainModel().execute()
