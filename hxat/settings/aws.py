from .base import *

#STATICFILES_STORAGE = "hxat.staticfiles.MixedManifestStaticFilesStorage"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        #"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        "BACKEND": "hxat.staticfiles.MixedManifestStaticFilesStorage",
    },
}
