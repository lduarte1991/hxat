from rest_framework import serializers
from target_object_database.models import TargetObject


class TargetObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetObject
        fields = (
            "target_title",
            "target_author",
            "target_content",
            "target_citation",
            "target_type",
        )
