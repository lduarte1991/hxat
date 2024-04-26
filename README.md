![Coverage Status](./coverage.svg)

# hxat - HarvardX Annotation Tool

An [LTI](https://www.imsglobal.org/activity/learning-tools-interoperability) 1.2 tool for annotating text, images, and videos.

[LTI](https://www.imsglobal.org/activity/learning-tools-interoperability) integration has been tested with [edX](https://www.edx.org/) and [Canvas](https://www.instructure.com/canvas/).

For annotation storage, see [catchpy](https://github.com/nmaekawa/catchpy).

## requirements
- Python 3.10+
- Postgresql 12+

## using docker

Make sure you have [docker](https://www.docker.com) installed.

```
# clone hxat and catchpy
$> git clone https://github.com/lduarte1991/hxat.git
$> git clone https://github.com/nmaekawa/catchpy.git
$> cd hxat

# start docker services
$> docker compose build
$> docker compose up
```

Since an LTI 1.2 (see [LTI Adoption Roadmap](https://www.imsglobal.org/lti-adoption-roadmap)) tool, to add text, image, or video to annotate, you need an LTI platform.  For demo purposes, we suggest using [local-lti-consumer](https://github.com/wachjose88/local-lti-consumer.git)

```
# clone local-lti-consumer
$> git clone https://github.com/wachjose88/local-lti-consumer.git

# use a virtual environment
$> virtualenv -p python3 venv
$> source venv/bin/activate
(venv) $>  # now using venv

# run lti-consumer on port 8088; docker-compose uses 8000, 8001, 8002, 9000.
(venv) $> cd local-lti-consumer
(venv) $> pip install -r requirements.txt
(venv) $> cd lti-consumer
(venv) $> python manage.py migrate
(venv) $> python manage.py runserver 8088
(venv) $> open http://localhost:8088
```

See below how to config the local-lti-consumer to talk to hxat.
You can also use the docker-compose-hxat-only.yml --- you'll need a compatible annotation storage server. If an annotation storage server is not available to hxat, you still can add text/image/video and annotate them. The annotations won't be saved, but you have the option to export them and save locally.
On both composes, you can reach hxat django admin via http://localhost:8000/admin using user:password as user and password

### local-lti-consumer config

Testcase config
- Launch URL: http://localhost:8000/lti_init/launch_lti/
- Consumer key: sample-consumer
- Consumer secret: sample-secret

Launch Parameters:
- lti_message_type: basic-lti-launch-request
- lti_version: LTI-1p0
- resource_link_id: some-string
- context_id: mycourse
- user_id: some-id
- roles: Instructor
- lis_person_sourcedid

Possible values for "roles" here are "Instructor" or "Learner"; "user_id" is an identifier for the user in the platform, and "lis_person_sourcedid" is the display name for the user.

Once the testcase is created and configured, click "Run" button to launch hxat in a new window. Keep in mind that local-lti-tool testcase page might need to be reloaded if it sits too long because there is a jwt with a short ttl when the page is served and after jwt expires, the lti lanch will return 403.


## LMS Integration

### Platform Compatibility

In theory, hxat is LTI 1.2 compatible, but LMS have their own implementation of LTI. That said, hxat is tested with [Edx](https://www.edx.org/) and [Canvas](https://www.canvaslms.com/). The primary difference is that edX displays an annotation author's name using the username, and Canvas uses an author's full name.

### Installing in Canvas

1. In your Canvas course, click `Settings -> Apps -> View App Configurations -> Add App` and then:
2. Select "By URL" for Configuration Type.
3. Then enter the following:
    - Name: hxat
    - Consumer Key: hxat
    - Shared Secret: secret
    - Config URL: https://localhost:8000/lti/config
4. If the installation worked, the tool should appear in your left navigation.

### Installing in edX

Refer to [10.21.4. Adding an LTI Component to a Course Unit](https://edx.readthedocs.io/projects/open-edx-building-and-running-a-course/en/latest/exercises_tools/lti_component.html#adding-an-lti-component-to-a-course-unit).

### Launch configuration

When the tool launches (i.e. authenticates a user for a particular course context), there are two possible configurations:

1. **Display a list of annotation assignments (default)**
    - The tool displays all annotation assignments associated with the course context. This is most often used to make all assignments available to students and teaching staff alike in Canvas when it is added to the left-navigation of the course.
2. **Display a specific annotation assignment**
    - The tool is passed custom parameters so it knows exactly which target object and annotation assignment should be rendered immediatley. This is most often used to embed an annotation assignment in edX or in a Canvas module.


## unit tests

```
$ pytest tests/
```

## A note about storing user information

As much as possible, the policy of the tool is to avoid storing user information. User information may be stored with annotations in an external store such as catchpy. If user information does need to be stored, only the anonymous `user_id` should be used. Instructor information including the `name` may be stored, however, for administrative purposes.


## A note about the user_id in edX compared to Canvas

In edX, the opaque `user_id` is unique within the scope of a course. In Canvas, the opaque `user_id` is unique within the scope of the platform. In other words, you can't assume that the same user will have the same `user_id` in two different courses when the tool is being used in edX.

