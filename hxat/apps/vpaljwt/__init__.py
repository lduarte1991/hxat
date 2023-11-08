"""
vpaljwt is used to do authentication for api calls.

Out-of-band, an issuer and key-pair are exchanged with the api-client.
The key-pair (vpaljwt.model.APIKey) is associated to an issuer or user
(django.contrib.auth.models.User, and issuer == User.username)

The api-client must generate a jwt and add it to the request http header:
    Authorization: bearer <jwt>
And every request must have a new jwt, as this login info is not saved in the
session. Each jwt has ttl of 60sec.

The jwt payload should look like:
    {
        "iss": "api client id",    # username
        "sub": "api key",          # uuid
        "iat": "issuing time",     # timestamp integer!
    }

Example to generate a jwt in python:

    # given issuer = "myusername"
    # key_pair = {
    #    "key": "97A911C6-356C-4134-8278-7DDA27ADB24F",
    #    "shared-secret": "70462E11-3824-4D56-9CFD-96A00F8F5E12",
    # }
    import jwt
    from datetime import datetime, timezone

    myjwt = jwt.encode(
        payload={
            "iss": issuer,
            "sub": key_pair["key"],
            "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        },
        secret=key_pair["shared-secret"],
        algorithm="HS256"
    )
    request.META["HTTP_AUTHORIZATION"] = "bearer " + myjwt

Allowed endpoints depends on each key-pair, to check which endpoints are
allowed, use "/jwt/v1/endpoints/". The response is a json list of url paths.

"""
