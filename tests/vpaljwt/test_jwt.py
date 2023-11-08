# -*- coding: utf-8 -*-

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from hxat.apps.vpaljwt.jwt import Vpaljwt, VpaljwtException, encode_token
from hxat.apps.vpaljwt.middleware import VpaljwtMiddleware


@pytest.mark.django_db
def test_jwt_error_in_constructor(vpaljwt_makejwt):
    username = "krenak"
    expire_in = 300  # good for next 5min
    (user, apikey, jwt) = vpaljwt_makejwt(username=username, expire_in=expire_in)

    jwt_error = encode_token(
        {
            "sub": str(uuid.uuid4()),
            "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        },
        str(apikey.secret),
    )
    with pytest.raises(VpaljwtException) as e:
        _ = Vpaljwt(jwt_error)
    assert 'missing the "iss" claim' in e.__str__()

    jwt_error = encode_token(
        {
            "sub": str(uuid.uuid4()),
            "iat": int(datetime.now(tz=timezone.utc).timestamp()),
            "iss": user.username,
        },
        str(apikey.secret),
    )
    with pytest.raises(VpaljwtException) as e:
        _ = Vpaljwt(jwt_error)
    assert "unknown apikey" in e.__str__()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "username, good_for, replace_claim, secret, error_msg",
    [
        pytest.param("guajajara", -10, {}, "none", "expired"),
        pytest.param("raoni", 10, {"iss": "kayapo"}, "none", "expected user(raoni)"),
        pytest.param("munduruki", 10, {}, str(uuid.uuid4()), "verification failed"),
    ],
)
def test_validate_jwt(
    username, good_for, replace_claim, secret, error_msg, vpaljwt_makejwt
):
    (user, apikey, jwt) = vpaljwt_makejwt(username=username, expire_in=good_for)
    payload = Vpaljwt.decode(jwt)
    # replace claims and reencode payload
    for claim in replace_claim:
        payload[claim] = replace_claim[claim]
    jwt_error = encode_token(
        payload, secret if secret != "none" else str(apikey.secret)
    )

    vpaljwt = Vpaljwt(jwt_error)
    with pytest.raises(VpaljwtException) as e:
        _ = vpaljwt.validate()
    assert error_msg in e.__str__()


@pytest.mark.django_db
def test_validate_jwt_apikey(vpaljwt_makejwt):
    (user, apikey, jwt) = vpaljwt_makejwt(username="katumirim", expire_in=10)
    # set apikey expiration date in the past
    apikey.expire_on = datetime.now(tz=timezone.utc) - timedelta(days=15)
    apikey.save()

    vpaljwt = Vpaljwt(jwt)
    with pytest.raises(VpaljwtException) as e:
        _ = vpaljwt.validate()
    assert "expired" in e.__str__()


"""
@pytest.mark.django_db
def test_middleware_ok(vpaljwt_makejwt):
    def my_getresponse(request):
        return JsonResponse({})

    (user, apikey, jwt) = vpaljwt_makejwt(username="myriankrexu", expire_in=10)
    factory = APIRequestFactory()
    request = factory.get(reverse("kondo:project-report-detail", args=["slate"]))
    request.META[settings.VPALJWT_HTTP_HEADER] = "bearer {}".format(jwt)
    assert request.META.get(settings.VPALJWT_HTTP_HEADER, None) is not None

    mymiddle = VpaljwtMiddleware(my_getresponse)
    _ = mymiddle(request)

    assert getattr(request, "vpaljwt", None) is not None
    assert request.vpaljwt == jwt
"""


@pytest.mark.django_db
def test_allowedendpoints(vpaljwt_makejwt):
    (user, apikey, jwt) = vpaljwt_makejwt(username="wapichana", expire_in=10)
    cli = APIClient()
    cli.credentials(**{settings.VPALJWT_HTTP_HEADER: "bearer {}".format(jwt)})
    response = cli.get("/jwt/v1/endpoints/")
    assert response.status_code == 200

    # sanity check on response
    user_audience = user.apikey.audience.sort()
    resp_json = json.loads(response.content)
    assert resp_json.sort() == user_audience

    # same request without jwt
    other_cli = APIClient()
    response = other_cli.get("/jwt/v1/endpoints/")
    assert response.status_code == 403

