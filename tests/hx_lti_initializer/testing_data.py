
def build_json(id, context_id):
    testing_data_dict = {
        "test_fetch_annotations_by_course_success_new_highlighter": {
                "data": {
                    "id": f"{id}",
                    "body": {
                        "type": "List",
                        "items": [
                            {
                                "type": "TextualBody",
                                "value": "<p>testing text 2</p>",
                                "purpose": "commenting",
                            },
                        ],
                    },
                    "type": "Annotation",
                    "target": {
                        "type": "List",
                        "items": [
                            {
                                "type": "Thumbnail",
                                "format": "image/jpg",
                                "source": "https://damsssl.llgc.org.uk/iiif/2.0/image/4389768/720,601,2382,1123/300,/0/default.jpg"
                            },
                            {
                                "type": "Image",
                                "source": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
                                "selector": {
                                    "type": "Choice",
                                    "items": [
                                        {
                                            "type": "FragmentSelector",
                                            "value": "xywh=720,601,2382,1123"
                                        },
                                        {
                                            "type": "SvgSelector",
                                            "value": "<svg xmlns='http://www.w3.org/2000/svg'><path xmlns=\"http://www.w3.org/2000/svg\" d=\"M720.5,600.96875h1191v0h1191v561.46875v561.46875h-1191h-1191v-561.46875z\" data-paper-data=\"{&quot;strokeWidth&quot;:2.5,&quot;rotation&quot;:0,&quot;deleteIcon&quot;:null,&quot;rotationIcon&quot;:null,&quot;group&quot;:null,&quot;editable&quot;:true,&quot;annotation&quot;:null}\" id=\"rectangle_bc2e4859-17b6-4932-804b-6ab48eab0585\" fill-opacity=\"0\" fill=\"#00bfff\" fill-rule=\"nonzero\" stroke=\"#00bfff\" stroke-width=\"1\" stroke-linecap=\"butt\" stroke-linejoin=\"miter\" stroke-miterlimit=\"10\" stroke-dasharray=\"\" stroke-dashoffset=\"0\" font-family=\"none\" font-weight=\"none\" font-size=\"none\" text-anchor=\"none\" style=\"mix-blend-mode: normal\"/></svg>"
                                        }
                                    ]
                                }
                            }
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
                "expected_response": {
                    "totalCount": 1, 
                    "rows": [
                        {
                            "id": f"{id}", 
                            "created": "2021-10-04T18:37:59+00:00", 
                            "updated": "2021-10-04T18:37:59+00:00", 
                            "text": "<p>testing text 2</p>", 
                            "permissions": {}, 
                            "user": {
                                "id": f"{id}", 
                                "name": "Vesna Tan"
                            }, 
                            "totalComments": "0", 
                            "tags": [], 
                            "parent": "0", 
                            "ranges": [], 
                            "contextId": context_id,
                            "collectionId": "1", 
                            "uri": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json", 
                            "media": "image", 
                            "quote": "",
                            "manifest_url": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
                            "thumb": "https://damsssl.llgc.org.uk/iiif/2.0/image/4389768/720,601,2382,1123/300,/0/default.jpg",
                            "rangePosition": [
                                    { "type": "FragmentSelector", "value": "xywh=720,601,2382,1123" },
                                    {
                                        "type": "SvgSelector",
                                        "value": '<svg xmlns=\'http://www.w3.org/2000/svg\'><path xmlns="http://www.w3.org/2000/svg" d="M720.5,600.96875h1191v0h1191v561.46875v561.46875h-1191h-1191v-561.46875z" data-paper-data="{&quot;strokeWidth&quot;:2.5,&quot;rotation&quot;:0,&quot;deleteIcon&quot;:null,&quot;rotationIcon&quot;:null,&quot;group&quot;:null,&quot;editable&quot;:true,&quot;annotation&quot;:null}" id="rectangle_bc2e4859-17b6-4932-804b-6ab48eab0585" fill-opacity="0" fill="#00bfff" fill-rule="nonzero" stroke="#00bfff" stroke-width="1" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10" stroke-dasharray="" stroke-dashoffset="0" font-family="none" font-weight="none" font-size="none" text-anchor="none" style="mix-blend-mode: normal"/></svg>',
                                    },
                                ],
                            "bounds": {"height": "1123", "width": "2382", "x": "720", "y": "601"},
                        }
                    ]
                }
            },
            "test_fetch_annotations_by_course_success_old_highlighter": {
                "data": {
                    "id": f"{id}",
                    "body": {
                        "type": "List",
                        "items": [
                            {
                                "type": "TextualBody",
                                "value": "<p>testing text 2</p>",
                                "purpose": "commenting",
                            },
                        ],
                    },
                    "type": "Annotation",
                    "target": {
                        "type": "List",
                        "items": [
                            {
                                "type": "Image",
                                "scope": {
                                    "type": "Viewport",
                                    "value": "xywh=1545,1499,1286,799"
                                },
                                "source": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
                                "selector": {
                                    "type": "List",
                                    "items": [
                                        {
                                            "full": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
                                            "@type": "oa:SpecificResource",
                                            "within": {
                                                "@id": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json",
                                                "@type": "sc:Manifest"
                                            },
                                            "selector": {
                                                "item": {
                                                    "@type": "oa:SvgSelector",
                                                    "value": "<svg xmlns='http://www.w3.org/2000/svg'><path xmlns=\"http://www.w3.org/2000/svg\" d=\"M1544.86605,1498.80408h643.15795v0h643.15795v399.3005v399.3005h-643.15795h-643.15795v-399.3005z\" data-paper-data=\"{&quot;strokeWidth&quot;:1,&quot;rotation&quot;:0,&quot;deleteIcon&quot;:null,&quot;rotationIcon&quot;:null,&quot;group&quot;:null,&quot;editable&quot;:true,&quot;annotation&quot;:null}\" id=\"rectangle_002c2296-5e76-42a8-abec-64efd743dce2\" fill-opacity=\"0\" fill=\"#00bfff\" fill-rule=\"nonzero\" stroke=\"#00bfff\" stroke-width=\"1\" stroke-linecap=\"butt\" stroke-linejoin=\"miter\" stroke-miterlimit=\"10\" stroke-dasharray=\"\" stroke-dashoffset=\"0\" font-family=\"none\" font-weight=\"none\" font-size=\"none\" text-anchor=\"none\" style=\"mix-blend-mode: normal\"/></svg>"
                                                },
                                                "@type": "oa:Choice",
                                                "default": {
                                                    "@type": "oa:FragmentSelector",
                                                    "value": "xywh=1545,1499,1286,799"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "type": "Thumbnail",
                                "format": "image/jpg",
                                "source": "https://damsssl.llgc.org.uk/iiif/2.0/image/4389768/1545,1499,1286,799/300,/0/default.jpg"
                            }
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
                "expected_response": {
                    "totalCount": 1, 
                    "rows": [
                        {
                            "id": f"{id}", 
                            "created": "2021-10-04T18:37:59+00:00", 
                            "updated": "2021-10-04T18:37:59+00:00", 
                            "text": "<p>testing text 2</p>", 
                            "permissions": {}, 
                            "user": {
                                "id": f"{id}", 
                                "name": "Vesna Tan"
                            }, 
                            "totalComments": "0", 
                            "tags": [], 
                            "parent": "0", 
                            "ranges": [], 
                            "contextId": context_id,
                            "collectionId": "1", 
                            "uri": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json", 
                            "media": "image", 
                            "quote": "",
                            "manifest_url": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json",
                            "thumb": "https://damsssl.llgc.org.uk/iiif/2.0/image/4389768/1545,1499,1286,799/300,/0/default.jpg",
                            "rangePosition": [
                                    {
                                        "full": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/canvas/4389768.json",
                                        "@type": "oa:SpecificResource",
                                        "within": {
                                            "@id": "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json",
                                            "@type": "sc:Manifest",
                                        },
                                        "selector": {
                                            "item": {
                                                "@type": "oa:SvgSelector",
                                                "value": '<svg xmlns=\'http://www.w3.org/2000/svg\'><path xmlns="http://www.w3.org/2000/svg" d="M1544.86605,1498.80408h643.15795v0h643.15795v399.3005v399.3005h-643.15795h-643.15795v-399.3005z" data-paper-data="{&quot;strokeWidth&quot;:1,&quot;rotation&quot;:0,&quot;deleteIcon&quot;:null,&quot;rotationIcon&quot;:null,&quot;group&quot;:null,&quot;editable&quot;:true,&quot;annotation&quot;:null}" id="rectangle_002c2296-5e76-42a8-abec-64efd743dce2" fill-opacity="0" fill="#00bfff" fill-rule="nonzero" stroke="#00bfff" stroke-width="1" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10" stroke-dasharray="" stroke-dashoffset="0" font-family="none" font-weight="none" font-size="none" text-anchor="none" style="mix-blend-mode: normal"/></svg>',
                                            },
                                            "@type": "oa:Choice",
                                            "default": {
                                                "@type": "oa:FragmentSelector",
                                                "value": "xywh=1545,1499,1286,799",
                                            },
                                        },
                                    },
                                ],
                              "bounds": { "x": "1545", "y": "1499", "width": "1286", "height": "799" },
                        }
                    ]
                }
            },
            "test_fetch_annotations_by_course_failing": {
                "data": {
                    "id": f"{id}",
                    "body": {
                        "type": "List",
                        "items": [
                            {
                                "type": "TextualBody",
                                "value": "<p>testing text 2</p>",
                                "purpose": "commenting",
                            },
                        ],
                    },
                    "type": "Annotation",
                #    missing target field
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
                "expected_response": {"rows": [], "totalCount": 1}
            },
            "test_dashboard_annotations_success": {
                "https://iiif.bodleian.ox.ac.uk/iiif/manifest/60834383-7146-41ab-bfe1-48ee97bc04be.json":
                    {
                    "id": 14,
                    "target_title": "bodleian",
                    "target_content":
                        "https://iiif.bodleian.ox.ac.uk/iiif/manifest/60834383-7146-41ab-bfe1-48ee97bc04be.json",
                    "target_type": "ig",
                    },
                "https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/661":
                    {
                    "id": 15,
                    "target_title": "nubian-message-1992",
                    "target_content":
                        "https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/661",
                    "target_type": "ig",
                    },
                "https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/662":
                    {
                    "id": 16,
                    "target_title": "nubian-message-1992",
                    "target_content":
                        "https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest/662",
                    "target_type": "ig",
                    },
                "https://digital.library.villanova.edu/Item/vudl:92879/Manifest": {
                    "id": 9,
                    "target_title": "test old",
                    "target_content":
                    "https://digital.library.villanova.edu/Item/vudl:92879/Manifest",
                    "target_type": "ig",
                },
                "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json": {
                    "id": 12,
                    "target_title": "test old2",
                    "target_content":
                    "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json",
                    "target_type": "ig",
                }
            }
        }
    return testing_data_dict