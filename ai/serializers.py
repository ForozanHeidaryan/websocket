# ai/serializers.py
from rest_framework import serializers
from .models import TurningPrediction, Trainingn

# -------------------------
# Model Serializers
# -------------------------
class TurningPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurningPrediction
        fields = '__all__'

class TrainingnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainingn
        fields = '__all__'

# -------------------------
# Flexible mapping serializer
# -------------------------
class FlexibleIDNameSerializer(serializers.Serializer):
    ID = serializers.IntegerField(required=False, default=0)
    Name = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            # normalize کلیدها
            if 'id' in data:
                data['ID'] = data.pop('id')
            elif 'Id' in data:
                data['ID'] = data.pop('Id')
            if 'name' in data:
                data['Name'] = data.pop('name')

            # نرمالایز رشته Name
            if 'Name' in data and isinstance(data['Name'], str):
                data['Name'] = data['Name'].strip()
        return super().to_internal_value(data)

class CategoryMappingSerializer(FlexibleIDNameSerializer):
    pass

class SarfaslMappingSerializer(FlexibleIDNameSerializer):
    pass

class GrouhMappingSerializer(FlexibleIDNameSerializer):
    pass

class MappingSerializer(serializers.Serializer):
    categories = CategoryMappingSerializer(many=True, required=False, default=[])
    sarfasls = SarfaslMappingSerializer(many=True, required=False, default=[])
    grouhs = GrouhMappingSerializer(many=True, required=False, default=[])

# -------------------------
# Predict Input Serializer
# -------------------------
class PredictPayloadSerializer(serializers.Serializer):
    data = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        allow_empty=False
    )
    mapping = MappingSerializer(required=False, default=MappingSerializer().to_internal_value({}))

    def validate(self, attrs):
        # normalize کلیدهای داده ورودی
        for item in attrs.get('data', []):
            for key in list(item.keys()):
                new_key = key.strip() if isinstance(key, str) else key
                item[new_key] = item.pop(key)
        return attrs
