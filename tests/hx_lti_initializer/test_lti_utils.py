import pytest
from requests.sessions import session
from hx_lti_initializer.utils import _fetch_annotations_by_course
import requests
import requests_mock
from testing_data import build_json
from uuid import uuid4

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
