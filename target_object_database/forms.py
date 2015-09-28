from django import forms
from target_object_database.models import TargetObject


class SourceForm(forms.ModelForm):

    class Meta:
        model = TargetObject
        fields = (
            'target_title',
            'target_author',
            'target_content',
            'target_citation',
            'target_creator',
            'target_courses',
            'target_type'
        )
