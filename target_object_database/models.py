from django.db import models
from hx_lti_initializer.models import LTIProfile, LTICourse


class LTI_TodApi(models.Model):
    class Meta:
        app_label = 'Source Text/Image/Video Database'
        abstract = True


class TargetObject(LTI_TodApi):
    """
    This object will contain the items to be annotated by users for reuse.
    """

    target_title = models.CharField(max_length=255)
    target_author = models.CharField(max_length=255)
    target_content = models.TextField()
    target_citation = models.TextField()
    target_created = models.DateTimeField(auto_now_add=True, auto_now=False)
    target_updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    target_creator = models.ForeignKey(LTIProfile, null=True)
    target_courses = models.ManyToManyField(LTICourse)
    ANNOTATION_TYPES = (
        ('tx', 'Text Annotation'),
        ('vd', 'Video Annotation'),
        ('ig', 'Image Annotation'),
    )

    target_type = models.CharField(
        max_length=2,
        choices=ANNOTATION_TYPES,
        default='tx'
    )

    def __str__(self):
        return "\"" + self.target_title + "\" by " + self.target_author

    def __unicode__(self):
        return u"\"%s\" by %s" % (self.target_title, self.target_author)

    class Meta:
        verbose_name = "Source"
        ordering = ['target_title']

    def get_targets_from_creator(user_requesting, user_requested):
        if (user_requesting.user.is_staff is True):
            return TargetObject.objects.filter(target_creator=user_requested)
        return None

    def get_own_targets(user_requesting):
        if (user_requesting.user.is_staff is True):
            return TargetObject.objects.filter(target_creator=user_requesting)
        return None

    def get_all_targets(user_requesting):
        if(user_requesting.user.is_staff is True):
            return TargetObject.objects.all()
        return None

    def get_target_content_by_title(user_requesting, title_given):
        if(user_requesting.user.is_staff is True):
            return TargetObject.objects.filter(
                target_title__icontains=title_given
            )
        return None

    def get_target_content_from_id(id_requested):
        return TargetObject.objects.get(pk=id_requested)

    def get_target_content_as_list(self):
        return self.target_content.split(';')
