import json
import logging
from collections import OrderedDict

from django.db import IntegrityError
from rest_framework import serializers

from hx_lti_assignment.models import Assignment
from hx_lti_initializer.models import LTICourse, LTIProfile
from target_object_database.models import TargetObject


class LTIProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    anon_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    scope = serializers.CharField(required=False, allow_blank=True, max_length=1024)
    created_at = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)
    updated_at = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)

    class Meta:
        model = LTIProfile
        fields = [
            "id",
            "anon_id",
            "name",
            "scope",
            "created_at",
            "updated_at",
        ]


class TargetObjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    target_title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    target_created = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)
    target_updated = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)
    target_creator = LTIProfileSerializer(required=False)
    target_type = serializers.CharField(max_length=2, default="TX")

    class Meta:
        model = TargetObject
        fields = [
            "id",
            "target_title",
            "target_created",
            "target_updated",
            "target_creator",
            "target_type",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    assignment_id = serializers.CharField(required=True, allow_blank=False, max_length=100)
    assignment_name = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    assignment_objects = TargetObjectSerializer(many=True)
    annotation_database_url = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    annotation_database_apikey = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    annotation_database_secret_token = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    created_at = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)
    updated_at = serializers.DateTimeField(format="iso-8601", required=False, allow_null=True)

    class Meta:
        model = Assignment
        fields = [
            "assignment_id",
            "assignment_name",
            "assignment_objects",
            "annotation_database_url",
            "annotation_database_apikey",
            "annotation_database_secret_token",
            "created_at",
            "updated_at",
        ]


class LTICourseSerializer(serializers.ModelSerializer):
    course_id = serializers.CharField(
        required=True, allow_blank=False, max_length=255
    )
    course_name = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    course_admins = LTIProfileSerializer(many=True)
    assignments = AssignmentSerializer(many=True)

    class Meta:
        model = LTICourse
        fields = [
            "course_id",
            "course_name",
            "course_admins",
            "assignments",
        ]




