from django.urls import path
from .views import TurningPredictionListView, ExecuteCustomerDBView,\
    ExecutePrediction ,  TrainingnListView ,TrainAPIView ,PredictAPIView

urlpatterns = [
    path('turning-predictions/<int:customer_id>/', TurningPredictionListView.as_view(), name='turning-predictions'),
    path('execute-db/<int:customer_id>/', ExecuteCustomerDBView.as_view(), name='execute-customer-db'),
    path('execute-prediction/', ExecutePrediction.as_view(), name='execute-customer-db'),
    path("trainingn/", TrainingnListView.as_view(), name="trainingn-list"),
    path('train/', TrainAPIView.as_view(), name='train-api'),
    path('predict/', PredictAPIView.as_view(), name='predict'),


]





