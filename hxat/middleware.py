"""
middleware.py
by Arthur Barrett, ATG

For usage of the LTI tool within an iFrame. It checks to make sure that the
iframe is being loaded from one of the sites listed in the
X_FRAME_ALLOWED_SITES set in the settings for the instance of the project.

It then either Denies access to the site or sets an ALLOW-FROM attribute for
that particular URL.

Note: Chrome, Safari, and IE ignore Allow-From, though they should still
load the iframe.
"""
import collections
import importlib
import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from hx_lti_initializer.views import PlatformError
from lti.contrib.django import DjangoToolProvider

from .lti_validators import LTIRequestValidator

logger = logging.getLogger(__name__)

# borrowed deliberately from: https://github.com/arteria/django-ar-organizations/commit/e890d9ab02053a626519ad151a2bb485fb0d9d8c
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:

    class MiddlewareMixin(object):
        pass


def ip_address(request):
    """Returns the real IP address from a request, or if that fails, returns 1.2.3.4."""
    meta = request.META
    # Not using HTTP_X_FORWARDED_FOR because it returns a list: client, proxy1, proxy2, ...
    # which is more prone to varying between requests from the same client
    return meta.get(
        "HTTP_X_REAL_IP", meta.get("HTTP_CLIENT_IP", meta.get("REMOTE_ADDR", "1.2.3.4"))
    )


class LTILaunchError(Exception):
    pass


class LTILaunchSession(object):
    """
    Dict-like object that provides access to the session dict containing for the LTI Launch,
    which is keyed by the resource_link_id.

    The main reason this object exists is to provide better error handling when accessing a
    key that does not exist, usually because the resource_link_id wasn't provided in the
    request. Otherwise, you would just get a generic KeyError from the session dict object.

    Note that we don't validate when the object is created, because it is added as an attribute
    to the request object for all types of requests, some of which don't have an LTI launch
    session associated with them. The Django Admin interface is an example of that. Ideally,
    we would only set the attribute on views where it is applicable.
    """

    def __init__(self, session, resource_link_id=None):
        self.session = session
        self.resource_link_id = resource_link_id

    def valid(self):
        """Returns true if the launch session dict is populated and can be keyed by the resource_link_id, otherwise False."""
        return (
            self.resource_link_id is not None
            and bool(self.session.get("LTI_LAUNCH", {}).get(self.resource_link_id))
            is True
        )

    def assert_valid(self):
        """Raises an exception if a valid launch session is not present, usually because the resource_link_id is not provided."""

        # 03feb20 naomi: these exceptions are raised in the view, when
        # manipulating the session in request.LTI; so it will be handled by the
        # process_exception()
        if not self.resource_link_id:
            raise LTILaunchError("Invalid LTI session: resource_link_id is not present")
        elif "LTI_LAUNCH" not in self.session:
            raise LTILaunchError("Invalid LTI session: missing LTI_LAUNCH dict")
        elif self.resource_link_id not in self.session.get("LTI_LAUNCH", {}):
            raise LTILaunchError(
                "Invalid LTI session: resource_link_id %s not in LTI_LAUNCH dict"
                % self.resource_link_id
            )

    def get(self, key, default_value=None):
        self.assert_valid()
        return self.session["LTI_LAUNCH"][self.resource_link_id].get(key, default_value)

    def __getitem__(self, key):
        self.assert_valid()
        return self.session["LTI_LAUNCH"][self.resource_link_id][key]

    def __setitem__(self, key, value):
        self.assert_valid()
        self.session["LTI_LAUNCH"][self.resource_link_id][key] = value
        self.session.modified = True

    def __delitem__(self, key):
        self.assert_valid()
        try:
            del self.session["LTI_LAUNCH"][self.resource_link_id][key]
            self.session.modified = True
        except KeyError:
            pass

    def __len__(self):
        self.assert_valid()
        return len(self.session["LTI_LAUNCH"][self.resource_link_id])

    def __iter__(self):
        self.assert_valid()
        return self.session["LTI_LAUNCH"][self.resource_link_id].iterkeys()

    def __contains__(self, item):
        self.assert_valid()
        return item in self.session["LTI_LAUNCH"][self.resource_link_id]

    def __repr__(self):
        self.assert_valid()
        return repr(self.session["LTI_LAUNCH"][self.resource_link_id])


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Sets the Content-Security-Policy header to restrict webpages from being
    embedded on other domains. This is better supported and more flexible than X-Frame-Options.

    Expects the CONTENT_SECURITY_POLICY_DOMAIN to be set in the django.settings object.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def process_response(self, request, response):
        if "content-type" in response and response["content-type"].startswith(
            "text/html"
        ):
            self.logger.info(
                "Inside %s process_response: %s"
                % (self.__class__.__name__, request.path)
            )
            domain = getattr(settings, "CONTENT_SECURITY_POLICY_DOMAIN", None)
            if domain:
                policy = "frame-ancestors 'self' {domain}".format(domain=domain)
                response["Content-Security-Policy"] = policy
                self.logger.info("Content-Security-Policy header set to: %s" % policy)
            else:
                self.logger.warning("Content-Security-Policy header not set")
        return response


class CookielessSessionMiddleware(MiddlewareMixin):
    """
    This middleware implements cookieless sessions by retrieving the session identifier
    from  cookies (preferred, if available) or the request URL.

    This must be added to INSTALLED_APPS prior to other middleware that uses the session.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Starting session engine %s" % settings.SESSION_ENGINE)
        engine = importlib.import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def process_request(self, request):
        self.logger.info(
            "Inside %s process_request: %s" % (self.__class__.__name__, request.path)
        )

        check_ip = False

        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        if session_key is not None:
            self.logger.info(
                "Session cookie '%s' returned key: %s"
                % (settings.SESSION_COOKIE_NAME, session_key)
            )
        else:
            self.logger.info(
                "Session cookie '%s' not found!" % settings.SESSION_COOKIE_NAME
            )
            session_key = request.GET.get("utm_source", None)
            self.logger.info("Session get param returned key: %s" % session_key)
            check_ip = True

        request.session = self.SessionStore(session_key)
        if request.session.exists(session_key):
            self.logger.info("Session exists")
            self.logger.debug("Session data: %s" % dict(request.session.items()))
        else:
            self.logger.info("Session does not exist. Creating new session.")
            request.session.create()
            self.logger.info("Created new session: %s" % request.session.session_key)

        logged_ip = request.session.get("LOGGED_IP", None)
        if check_ip and logged_ip is not None:
            self.logger.info("Checking IP address against session")
            request_ip = ip_address(request)
            if request_ip != logged_ip:
                self.logger.warning(
                    "IP address does not match IP logged in session: %s != %s. "
                    % (request_ip, logged_ip)
                )
                # NOTE: commenting these next few lines out because of confirmed reports from students
                #       that their session was being invalidated, which was traced back to this. -abarrett 3/9/18
                # request.session.flush()
                # self.logger.info("Flushed session")


class MultiLTILaunchMiddleware(MiddlewareMixin):
    """
    This middleware detects an LTI launch request, validates it, and stores multiple LTI launches
    in a single session.

    The current LTI launch may be accessed via the request.LTI attribute, which maps to an entry
    in the request.session['LTI_LAUNCH'] dict keyed by the resource_link_id.

    Note: this middleware is derived from django_auth_lti.middleware_patched with some changes for
    this application.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def process_exception(self, request, exception):
        if isinstance(exception, LTILaunchError):
            metadata = {
                k: request.META.get(k, "")
                for k in ("HTTP_REFERER", "HTTP_USER_AGENT", "REQUEST_METHOD")
            }
            self.logger.error(metadata)
            self.logger.error(exception)
            return HttpResponse("LTI launch error. Please try re-launching the tool.")
        elif isinstance(exception, PlatformError):
            self.logger.error("Platform Error - %s" % exception)
            return render(
                request,
                "main/platform_error.html",
                context={"error_message": exception},
                status=424,
            )
        elif isinstance(exception, PermissionDenied):
            return render(
                request,
                "main/permission_error.html",
                context={"error_message": exception},
                status=403,
            )
        self.logger.error(exception)
        return None
        # when moving to django2 and replacing MIDDLEWARE_CLASSES to MIDDLEWARE in
        # settings, the behavior of exceptions in middleware changed:
        # https://docs.djangoproject.com/en/2.2/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
        # "Under MIDDLEWARE_CLASSES, process_exception is applied to exceptions raised from a middleware
        # process_request method. Under MIDDLEWARE, process_exception applies only
        # to exceptions raised from the view."
        #
        # so, middleware classes cannot rely on exceptions to short-circuit the
        # request life-cycle in django anymore! 'unknown exceptions' return 500:
        # - https://docs.djangoproject.com/en/2.2/topics/http/middleware/#exception-handling
        # - https://code.djangoproject.com/ticket/12250#comment:18

    def process_request(self, request):
        self.logger.info(
            "Inside %s process_request: %s" % (self.__class__.__name__, request.path)
        )
        is_basic_lti_launch = (
            request.method == "POST"
            and request.POST.get("lti_message_type") == "basic-lti-launch-request"
        )
        is_lti_content_item_message = (
            request.method == "POST"
            and request.POST.get("lti_message_type") == "ContentItemSelectionRequest"
        )
        if is_basic_lti_launch:
            self.logger.info("handling lti_message_type=basic-lti-launch-request")
            try:
                self._validate_request(request)
                self._update_session(request)
                self._log_ip_address(request)
                self._set_current_session(
                    request, resource_link_id=request.POST.get("resource_link_id")
                )
            except LTILaunchError as e:
                self.logger.debug("LTILaunchError: {}".format(e))
                for k, v in vars(request.session).items():
                    self.logger.debug("*-*-*-*- SESSION[{}]: {}".format(k, v))
                return HttpResponseBadRequest()
            except PlatformError as e:
                self.logger.error("Platform Error - %s" % e)
                return render(
                    request,
                    "main/platform_error.html",
                    context={"error_message": e},
                    status=424,
                )
            except PermissionDenied as e:
                return render(
                    request,
                    "main/permission_error.html",
                    context={"error_message": e},
                    status=403,
                )
            except Exception as e:
                self.logger.debug("Exception: {}".format(e))
                # this potentially returns a 500:
                raise
        elif is_lti_content_item_message:
            self.logger.info("handling lti_message_type=ContentItemSelectionRequest")
            self._validate_request(request)
            self._log_ip_address(request)
        else:
            self._set_current_session(
                request, resource_link_id=request.GET.get("resource_link_id")
            )

        return self.get_response(request)

    def _validate_request(self, request):
        """
        Validates an LTI launch request.
        """
        validator = LTIRequestValidator()
        tool_provider = DjangoToolProvider.from_django_request(request=request)

        postparams = request.POST.dict()
        self.logger.debug("request is secure: %s" % request.is_secure())
        for key in postparams:
            self.logger.debug("POST %s: %s" % (key, postparams.get(key)))
        self.logger.debug("request abs url is %s" % request.build_absolute_uri())
        for key in request.META:
            self.logger.debug("META %s: %s" % (key, request.META.get(key)))

        self.logger.debug("about to check the signature")
        # NOTE: before validating the request, temporarily remove the
        # QUERY_STRING to work around an issue with how Canvas signs requests
        # that contain GET parameters. Before Canvas launches the tool, it duplicates the GET
        # parameters as POST parameters, and signs the POST parameters (*not* the GET parameters).
        # However, the oauth2 library that validates the request generates
        # the oauth signature based on the combination of POST+GET parameters together,
        # resulting in a signature mismatch. By removing the QUERY_STRING before
        # validating the request, the library will generate the signature based only on
        # the POST parameters like Canvas.
        #
        # 03feb20 naomi: TODO check if removing query string still needed,
        # since change to pylti/lti which uses oauthlib. It looks like oauthlib
        # correctly disregards query string in
        # oauthlib/oauth1/rfc5849/signature:base_string_uri()
        # -- could not force a query string in unit tests using django.test.Client
        qs = request.META.pop("QUERY_STRING", "")
        self.logger.debug("removed query string temporarily: %s" % qs)
        request_is_valid = tool_provider.is_valid_request(validator)
        request.META["QUERY_STRING"] = qs  # restore the query string
        self.logger.debug("restored query string: %s" % request.META["QUERY_STRING"])

        if not request_is_valid:
            self.logger.error("signature check failed")
            raise PermissionDenied("LTI Key and Secret are incorrect.")

        self.logger.info("signature verified")

        if (
            "lis_person_sourcedid" not in request.POST
            and "lis_person_name_full" not in request.POST
            and request.POST["user_id"] != "student"
        ):
            self.logger.error(
                "person identifier (i.e. username) or full name was not present in request"
            )
            raise PlatformError(
                "Platform did not send username. Check LTI settings in platform to ensure username is getting sent"
            )

    def _update_session(self, request):
        """
        Updates the session with the current LTI launch request. There may be multiple LTI launches associated with a
        single session. Each LTI launch is mapped to its POST parameters using the resource_link_id as the key.

        Example:

            session = {
                "LTI_LAUNCH": {
                    "5c5d07410": {},
                    "31b533624": {},
                    "023c227e2": {},
                }
            }

        The current LTI launch request may be accessed via the request.LTI attribute, which is automatically set
        to the correct entry in the LTI_LAUNCH mapping.
        """
        resource_link_id = request.POST.get("resource_link_id", None)
        postparams = request.POST.dict()
        lti_params = dict(postparams)
        lti_params.update(
            {
                "roles": [
                    role
                    for role in postparams.get("roles", "").split(",")
                    if role != ""
                ]
            }
        )

        lti_launches = request.session.get("LTI_LAUNCH", None)
        if lti_launches is None:
            lti_launches = collections.OrderedDict()
            request.session["LTI_LAUNCH"] = lti_launches

        max_launches = getattr(settings, "LTI_MAX_LAUNCHES", 10)
        self.logger.info(
            "LTI launch sessions: %s [max=%s]" % (lti_launches.keys(), max_launches)
        )
        if len(lti_launches.keys()) >= max_launches:
            self.logger.info("Invalidating oldest LTI launch (FIFO)")
            invalidated_launch = lti_launches.popitem(last=False)
            self.logger.info(
                "LTI launch invalidated: %s", json.dumps(invalidated_launch, indent=4)
            )

        lti_launches[resource_link_id] = {
            "launch_params": lti_params,
            "resource_link_id": resource_link_id,
        }
        request.session.modified = True
        user_id = lti_params.get("user_id", None)
        self.logger.info(
            "LTI launch session saved: resource_link_id={resource_link_id} user_id={user_id}".format(
                user_id=user_id, resource_link_id=resource_link_id
            )
        )

    def _log_ip_address(self, request):
        """
        Logs the IP address in the session.
        """
        logged_ip = ip_address(request)
        request.session["LOGGED_IP"] = logged_ip
        self.logger.info("LTI launch IP address logged: %s" % logged_ip)

    def _set_current_session(self, request, resource_link_id=None):
        """
        Sets the current session on the request object based on the given resource_link_id.
        The current session is available via the 'LTI' attribute on the request (e.g. request.LTI).
        """

        setattr(request, "LTI", LTILaunchSession(request.session, resource_link_id))
        # setattr(request, 'LTI', request.session.get('LTI_LAUNCH', {}).get(resource_link_id))


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        logging.exception(
            "Exception logged for request: %s message: %s"
            % (request.path, str(exception))
        )
