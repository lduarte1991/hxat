import pytest
from requests.sessions import session
from hx_lti_initializer.utils import _fetch_annotations_by_course, DashboardAnnotations
import requests
import requests_mock
from testing_data import build_json
from uuid import uuid4
from unittest.mock import patch

context_id = f"{uuid4()}"
annotator_auth_token = f"{uuid4()}"
id = f"{uuid4()}"
built_json = build_json(id, context_id)

def test_fetch_annotations_by_course_success_new_highlighter():
    d = built_json["test_fetch_annotations_by_course_success_new_highlighter"]
    data = [d["data"]]
    expected_response = d["expected_response"]
    annotation_db_url = "http://test.com"  
    request_url = f"http://test.com/?context_id={context_id}&limit=1000"
    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.get(request_url, json={"rows":data,"total":len(data)})
        r = _fetch_annotations_by_course(context_id, annotation_db_url, annotator_auth_token)
        assert r == expected_response

def test_fetch_annotations_by_course_success_old_highlighter():
    d = built_json["test_fetch_annotations_by_course_success_old_highlighter"]
    data = [d["data"]]
    expected_response = d["expected_response"]
    annotation_db_url = "http://test.com"  
    request_url = f"http://test.com/?context_id={context_id}&limit=1000"
    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.get(request_url, json={"rows":data,"total":len(data)})
        r = _fetch_annotations_by_course(context_id, annotation_db_url, annotator_auth_token)
        assert r == expected_response

def test_fetch_annotations_by_course_failing():
    d = built_json["test_fetch_annotations_by_course_failing"]
    data = [d["data"]]
    expected_response = d["expected_response"]
    annotation_db_url = "http://test.com"  
    request_url = f"http://test.com/?context_id={context_id}&limit=1000"
    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.get(request_url, json={"rows":data,"total":len(data)})
        r = _fetch_annotations_by_course(context_id, annotation_db_url, annotator_auth_token)
        assert r == expected_response

def test_dashboard_annotations_success_image_uri():
    target_objects_by_content = built_json["test_dashboard_annotations_success"]
    # override DashboardAnnotations __init__
    def __init__(self, request, annotations):
        self.target_objects_by_content = target_objects_by_content

    with patch.object(DashboardAnnotations, '__init__', __init__):
        da = DashboardAnnotations("", {})
        assert da.get_target_id('image', 'https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/661') == 15

def test_dashboard_annotations_success_image_similar_uri():
    target_objects_by_content = built_json["test_dashboard_annotations_success"]
    def __init__(self, request, annotations):
        self.target_objects_by_content = target_objects_by_content

    with patch.object(DashboardAnnotations, '__init__', __init__):
        da = DashboardAnnotations("", {})
        assert da.get_target_id('image', 'https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/662') == 16

def test_dashboard_annotations_success_image_capital_letter_uri():
    target_objects_by_content = built_json["test_dashboard_annotations_success"]
    def __init__(self, request, annotations):
        self.target_objects_by_content = target_objects_by_content

    with patch.object(DashboardAnnotations, '__init__', __init__):
        da = DashboardAnnotations("", {})
        assert da.get_target_id('image', 'https://digital.library.villanova.edu/Item/vudl:92879/Manifest') == 9

# TODO: Fix how we store and match up canvas URI with manifest URI
# Note: test fails because we cant match any of the keys in the target_objects_by_content
# even if the root URI is similar to a matching manifest
def test_dashboard_annotations_failing_image_canvas_uri():
    target_objects_by_content = built_json["test_dashboard_annotations_success"]
    def __init__(self, request, annotations):
        self.target_objects_by_content = target_objects_by_content
    with patch.object(DashboardAnnotations, '__init__', __init__):
        da = DashboardAnnotations("", {})
        assert da.get_target_id('image', 'https://digital.library.villanova.edu/Item/vudl:92879/Canvas/p0') == ""