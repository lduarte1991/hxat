import json

import pytest
from django import forms
from django.conf import settings
from hx_lti_initializer.forms import EmbedLtiResponseForm, EmbedLtiSelectionForm
from hx_lti_initializer.models import LTICourse
from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint


class LtiContentItemReturnValidator(RequestValidator):
    """
    Used for testing that the response from the tool back to the LMS is valid:

        Tool Provider (HxAT) --(oauth-signed)--> Tool Consumer (Canvas/EdX)

    With the LTI 1.1 Content-Item Process, the tool provider receives a *ContentItemSelectionRequest*
    LTI message, and then needs to send back a *ContentItemSelection* message that includes
    the content-items, which in our case would be a HxAT assignment object to embed in a page.
    That return message must be oauth-signed in order for it to be accepted, so this is used
    to test that oauth-signed request.
    """

    @property
    def enforce_ssl(self):
        return False

    def check_client_key(self, key):
        return len(key) > 0

    def check_nonce(self, nonce):
        return len(nonce) > 0

    def validate_client_key(self, client_key, request):
        return client_key == settings.CONSUMER_KEY

    def validate_timestamp_and_nonce(
        self,
        client_key,
        timestamp,
        nonce,
        request,
        request_token=None,
        access_token=None,
    ):
        return True

    def get_client_secret(self, client_key, request):
        return settings.LTI_SECRET


@pytest.mark.django_db
def test_EmbedLtiSelectionForm_fields(user_profile_factory, assignment_target_factory):
    instructor = user_profile_factory(roles=["Instructor"])
    course_object = LTICourse.create_course("test_course_id", instructor)

    num_assignments = 5
    for i in range(num_assignments):
        assignment_target_factory(course_object)

    content_item_return_url = "https://canvas.test/courses/123456/external_content/success/external_tool_dialog"
    form = EmbedLtiSelectionForm(
        course_instance=course_object,
        content_item_return_url=content_item_return_url,
    )

    assert "content_item_return_url" in form.fields
    assert isinstance(form.fields["content_item_return_url"], forms.CharField)
    assert form.fields["content_item_return_url"].initial == content_item_return_url

    assert "content_item" in form.fields
    assert isinstance(form.fields["content_item"], forms.ChoiceField)
    assert len(form.fields["content_item"].choices) == num_assignments


def test_EmbedLtiResponseForm_set_oauth_signature():
    launch_url = (
        "https://testserver/lti/launch?custom_collection_id=1&custom_object_id=2"
    )
    content_item_return_url = "https://canvas.test/courses/123456/external_content/success/external_tool_dialog"
    content_items = {
        "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
        "@graph": [
            {
                "@type": "LtiLinkItem",
                "@id": launch_url,
                "url": launch_url,
                "title": "HxAT",
                "text": "HxAT",
                "mediaType": "application/vnd.ims.lti.v1.ltilink",
                "placementAdvice": {
                    "presentationDocumentTarget": "iframe",
                    "displayWidth": "100%",
                    "displayHeight": "700",
                },
            }
        ],
    }
    content_items_json = json.dumps(content_items)
    form = EmbedLtiResponseForm({"content_items": content_items_json})
    form.set_oauth_signature(
        url=content_item_return_url,
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
    )

    assert form.data["lti_message_type"] == "ContentItemSelection"
    assert form.data["lti_version"] == "LTI-1p0"
    assert form.data["content_items"] == content_items_json
    assert form.data["oauth_version"] == "1.0"
    assert form.data["oauth_nonce"] != ""
    assert form.data["oauth_timestamp"] != ""
    assert form.data["oauth_consumer_key"] == settings.CONSUMER_KEY
    assert form.data["oauth_callback"] == "about:blank"
    assert form.data["oauth_signature_method"] == "HMAC-SHA1"
    assert form.data["oauth_signature"] != ""


def test_EmbedLtiResponseForm_oauth_request_validates():
    content_item_return_url = "https://canvas.test/courses/123456/external_content/success/external_tool_dialog"
    form = EmbedLtiResponseForm({"content_items": "some_content_items_as_json_here"})
    form.set_oauth_signature(
        url=content_item_return_url,
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
    )

    oauth_validator = LtiContentItemReturnValidator()
    endpoint = SignatureOnlyEndpoint(oauth_validator)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = dict(form.data)
    valid, request = endpoint.validate_request(
        content_item_return_url, "POST", body, headers
    )
    assert valid
