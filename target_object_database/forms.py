from django import forms
from target_object_database.models import TargetObject
from hx_lti_initializer.utils import debug_printer


class SourceForm(forms.ModelForm):

    def clean(self):
        super(SourceForm, self).clean()
        data = self.cleaned_data.get('target_content')
        targ_type = self.cleaned_data.get('target_type')

        possible_to = None
        try:
            possible_to = TargetObject.objects.filter(target_content__icontains=data)[0]
        except:
            pass
        if possible_to is not None and possible_to.target_type == "ig":
            msg = "This image manifest already exists and is named %s" % possible_to
            self.add_error('target_content', msg)

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
