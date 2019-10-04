from django.db import models

class DeletedManager(models.Manager):
    def get_queryset(self):
        return super(DeletedManager, self).get_queryset().filter(is_deleted=False)

class Annotation(models.Model):
    context_id = models.CharField(db_index=True, max_length=1024, blank=False)
    collection_id = models.CharField(max_length=1024, blank=False)
    uri = models.CharField(max_length=2048, blank=False)
    media = models.CharField(max_length=24)
    user_id = models.CharField(max_length=1024)
    user_name = models.CharField(max_length=1024)
    is_private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    text = models.TextField(blank=True, default='')
    quote = models.TextField(blank=True, default='')
    json = models.TextField(blank=True, default='{}')
    tags =  models.ManyToManyField('AnnotationTags', related_name='annotations')
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    total_comments = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DeletedManager()

class AnnotationTags(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name
