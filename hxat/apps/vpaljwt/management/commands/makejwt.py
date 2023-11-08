from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.urls import reverse

from hxat.apps.vpaljwt.jwt import encode_vpaljwt
from hxat.apps.vpaljwt.models import APIKey


class Command(BaseCommand):
    help = "creates a vpaljwt to include in http request"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="username the jwt is for, user must already exist ",
        )
        parser.add_argument(
            "--createkey",
            action="store_true",
            help="create apikey for user, ignored if user already has apikey",
        )
        parser.add_argument(
            "--ttl",
            type=int,
            default=15,
            help="time-to-live for the jwt, in seconds; default is 15s - only relevant when creating the apikey",
        )

    def handle(self, *args, **kwargs):
        username = kwargs["username"]
        createkey = kwargs["createkey"]
        ttl = kwargs.get("ttl")

        audience = [
            reverse("api:lticourse-list")
        ]

        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            print("username({}) not found".format(username))
            exit()

        if not hasattr(u, "apikey"):
            if createkey:
                key = APIKey(valid_for_secs=ttl, audience=audience, user=u)
                key.save()
            else:
                print("user({}) does not have assigned apikey".format(username))
                exit()

        jwt = encode_vpaljwt(u.apikey)
        print(jwt)
