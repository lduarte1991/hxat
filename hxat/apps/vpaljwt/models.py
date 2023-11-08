# -*- coding: utf-8 -*-
import datetime
import logging  # noqa
import uuid

from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    DateTimeField,
    JSONField,
    Model,
    OneToOneField,
    PositiveSmallIntegerField,
    TextField,
    UUIDField,
)


def expire_in_weeks(ttl=52):  # default is to expire the key/secret in 1 year
    return datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        weeks=ttl
    )


def expire_in_secs(ttl=15):  # default is to expire jwt in 15sec from iat
    return ttl


def empty_list():
    return []


class APIKey(Model):
    """api key and shared secret tied to a django User."""

    created = DateTimeField(auto_now_add=True, null=True)
    modified = DateTimeField(auto_now=True, null=True)

    key = UUIDField(primary_key=True, default=uuid.uuid4)
    secret = UUIDField(default=uuid.uuid4, null=False, blank=False)
    # date when the key/secret expires
    expire_on = DateTimeField(default=expire_in_weeks, null=False, blank=False)
    # delta in secs the jwt is valid since iat
    valid_for_secs = PositiveSmallIntegerField(
        default=expire_in_secs, null=False, blank=False
    )
    # list of str(endpoints) that this key/secret applies to
    audience = JSONField(default=empty_list, null=False, blank=False)
    # to keep notes
    notes = TextField(null=True, blank=True)
    # django user
    user = OneToOneField(User, on_delete=CASCADE, null=False)

    def has_expired(self, now=None):
        if now is None:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
        return self.expire_on < now

    def __repr__(self):
        return "{}:{}".format(self.user.username, str(self.key))

    def __str__(self):
        return self.__repr__()
