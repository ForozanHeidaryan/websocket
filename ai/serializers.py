from abc import ABC

from rest_framework import serializers
from .models import TurningPrediction
from .models import Trainingn


class TurningPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurningPrediction
        fields = '__all__'


class TrainingnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainingn
        fields = '__all__'















from rest_framework import serializers

class CategorySerializer(serializers.Serializer):
    Category_id = serializers.IntegerField()
    Group = serializers.CharField(max_length=100)

class SarfaslSerializer(serializers.Serializer):
    Sarfasl_id = serializers.IntegerField()
    Sarfasl = serializers.CharField(max_length=100)

class GrouhSerializer(serializers.Serializer):
    Grouh_id = serializers.IntegerField()
    Group = serializers.CharField(max_length=100)

class MappingSerializer(serializers.Serializer):
    categories = CategorySerializer(many=True, required=False)
    sarfasls = SarfaslSerializer(many=True, required=False)
    grouhs = GrouhSerializer(many=True, required=False)






# ai/serializers.py
from rest_framework import serializers

# ---------- Mapping serializers ----------
class CategoryMappingSerializer(serializers.Serializer):
    Category_id = serializers.IntegerField()
    Category = serializers.CharField()

class SarfaslMappingSerializer(serializers.Serializer):
    Sarfasl_id = serializers.IntegerField()
    Sarfasl = serializers.CharField()

class GrouhMappingSerializer(serializers.Serializer):
    Grouh_id = serializers.IntegerField()
    Grouh = serializers.CharField()

class MappingSerializer(serializers.Serializer):
    categories = CategoryMappingSerializer(many=True, required=False)
    sarfasls = SarfaslMappingSerializer(many=True, required=False)
    grouhs = GrouhMappingSerializer(many=True, required=False)

# ---------- Main input serializer ----------
class PredictPayloadSerializer(serializers.Serializer):
    data = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        allow_empty=False
    )
    mapping = MappingSerializer(required=False)

