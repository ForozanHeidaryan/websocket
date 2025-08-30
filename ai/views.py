from .models import TurningPrediction
from .serializers import TurningPredictionSerializer
from .service.customers_db import CustomersDBService
from rest_framework.generics import ListAPIView
from .models import Trainingn
from .serializers import TrainingnSerializer
from .service.train import TrainModel
from ai.service.predict import PredictCustomersData  # کلاس آماده‌ی پیش‌بینی
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status



class TurningPredictionListView(ListAPIView):
    serializer_class = TurningPredictionSerializer

    def get_queryset(self):
        return TurningPrediction.objects.filter(customer_id=self.kwargs.get('customer_id'))


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


class TrainingnListView(ListAPIView):
    queryset = Trainingn.objects.all()
    serializer_class = TrainingnSerializer


class TrainAPIView(APIView):
    def post(self, request):
        try:
            trainer = TrainModel()
            trainer.execute()
            return Response({"message": "Model training completed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)















# ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PredictPayloadSerializer
from .service.predict import PredictCustomersData

class PredictAPIView(APIView):
    """
    Endpoint برای پیش‌بینی y1, y2, y3 و محاسبه similarity
    با دریافت داده های ورودی و mapping.
    """

    def post(self, request):
        serializer = PredictPayloadSerializer(data=request.data)
        if serializer.is_valid():
            payload = serializer.validated_data
            try:
                predictor = PredictCustomersData(payload)
                results = predictor.execute()
                return Response({"data": results}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
