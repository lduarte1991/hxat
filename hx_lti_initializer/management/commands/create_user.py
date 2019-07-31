import os
from django.core.management import BaseCommand

from django.contrib.auth.models import User



class Command(BaseCommand):
    help = 'create an staff user for django admin ui'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', dest='username', required=True,
            help='user to be created',
        )
        parser.add_argument(
            '--password', dest='password', required=True,
            help='password for user to be created',
        )
        parser.add_argument(
            '--is_admin', dest='is_admin', action='store_true',
            help='user allowed to admin database',
        )
        parser.add_argument(
            '--not-admin', dest='is_admin', action='store_false',
            help='user NOT allowed to admin database (DEFAULT)',
        )
        parser.add_argument(
            '--force-update', dest='force_update',
            action='store_true',
            help='force password update if username already exists',
        )
        parser.add_argument(
            '--no-update', dest='force_update',
            action='store_false',
            help='if username already exists, do not update password (DEFAULT)',
        )
        parser.set_defaults(
            is_admin=False,
            force_update=False,
        )


    def handle(self, *args, **kwargs):
        # only creates user if it does not exists
        username = kwargs['username']
        password = kwargs['password']

        try:
            user = User._default_manager.get(username=username)
        except User.DoesNotExist:
            # user need to be created
            u = User(username=username)
            u.set_password(password)
            u.is_staff = True
            u.is_superuser = True if kwargs['is_admin'] else False
            u.save()
        else:
            if kwargs['force_update']:
                user.password = password
                user.is_superuser = True if kwargs['is_admin'] else False
                user.save()
            else:
                return 'user already exists'

