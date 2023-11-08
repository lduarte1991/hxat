from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "given user, prints associated key from apikey"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="username of user to check apikey",
        )

    def handle(self, *args, **kwargs):
        username = kwargs["username"]

        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            print("username({}) not found".format(username))
            exit()

        if hasattr(u, "apikey"):
            print(
                "username({}), key({}), audience({})".format(
                    username,
                    str(u.apikey.key),
                    u.apikey.audience,
                )
            )
        else:
            print("user({}) does not have assigned apikey".format(username))
