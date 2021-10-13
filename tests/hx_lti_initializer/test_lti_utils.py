import pytest
from requests.sessions import session
from hx_lti_initializer.utils import _fetch_annotations_by_course
import requests
import requests_mock
from uuid import uuid4

def test_fetch_annotations_by_course_success():
    context_id = f"{uuid4()}"
    annotator_auth_token = f"{uuid4()}"
    id = f"{uuid4()}"
    data = [
    {
        "id": f"{id}",
        "body": {
            "type": "List",
            "items": [
            {
                "type": "TextualBody",
                "value": "<p>tdsting old image 2</p>",
                "purpose": "commenting",
            },
            ],
        },
        "type": "Annotation",
        "target": {
            "type": "Choice",
            "items": [
            {
                "type": "Thumbnail",
                "format": "image/jpg",
                "source":
                "https://damsssl.llgc.org.uk/iiif/2.0/image/4389768/1474,1980,721,788/300,/0/default.jpg",
            },
            ],
        },
        "creator": {
            "id": f"{id}",
            "name": "Vesna Tan",
        },
        "created": "2021-10-04T18:37:59+00:00",
        "modified": "2021-10-04T18:37:59+00:00",
        "platform": {
            "context_id": f"{context_id}",
            "collection_id": "1",
            "platform_name": "hxat-edx_v1.0",
            "target_source_id":
            "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
        },
        "permissions": {
        },
        "totalReplies": "0"
        },
    ]

    expected_response = {
    "rows": [
        {
        "id": f"{id}",
        "created": "2021-10-04T18:37:59+00:00",
        "updated": "2021-10-04T18:37:59+00:00",
        "text": "<p>tdsting old image 2</p>",
        "permissions": {},
        "user": { "id": f"{id}", "name": "Vesna Tan" },
        "totalComments": "0",
        "tags": [],
        "parent": "0",
        "ranges": [],
        "contextId": f"{context_id}",
        "collectionId": "1",
        "uri": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
        "media": "thumbnail",
        "quote": "",
        },
    ],
    "totalCount": len(data),
    };
    annotation_db_url = "http://test.com"  
    request_url = f"http://test.com/?contextId={context_id}&limit=1000"
    with requests_mock.Mocker() as requests_mocker:
     requests_mocker.get(request_url, json={"rows":data,"total":len(data)})
     r = _fetch_annotations_by_course(context_id, annotation_db_url, annotator_auth_token)
     assert r == expected_response