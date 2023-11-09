
from django.http import HttpResponse
import hxat


# version info
def info(request):
    return HttpResponse(
        "{} v{} = {}".format(
            hxat.__name__,
            hxat.__version__,
            hxat.vpal_version_comment,
        )
    )
