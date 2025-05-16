from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TurningPrediction
from .serializers import TurningPredictionSerializer
from .service.customers_db import CustomersDBService
from .service.predict import PredictCustomersData


class TurningPredictionListView(ListAPIView):
    queryset = TurningPrediction.objects.all()
    serializer_class = TurningPredictionSerializer

class ExecuteCustomerDBView(APIView):
    def post(self, request, customer_id):
        try:
            CustomersDBService(customer_id).execute()
            return Response({"message": "Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ExecutePrediction(APIView):
    def post(self, request, *args, **kwargs):
        try:
            PredictCustomersData().execute()
            return Response({"message": "Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

