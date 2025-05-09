from rest_framework import serializers
from .models import TurningPrediction

class TurningPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurningPrediction
        fields = '__all__'