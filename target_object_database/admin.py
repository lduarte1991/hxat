from django.contrib import admin
from models import TargetObject

class TargetObjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'target_type', 'target_title', 'target_author', 'target_creator', 'target_created')
    list_filter = ('target_type','target_created')
    search_fields = ('target_title', 'target_author')

admin.site.register(TargetObject, TargetObjectAdmin)
