![Coverage Status](./coverage.svg)

# The HarvardX Annotation Tool (HxAT)

A tool for annotating text, images, and videos.

Integrates with LMS platforms such as [edX](https://www.edx.org/) and [Canvas](https://www.instructure.com/canvas/) via [LTI](https://www.imsglobal.org/activity/learning-tools-interoperability).

Depends on [CatchPy](https://github.com/nmaekawa/catchpy), a REST API for annotation storage.

## Getting Started
Requirements:

- Python 3.6+ 
- Postgresql 9.6+
- [ASGI](https://asgi.readthedocs.io/en/latest/) application server such as [Daphne](http://github.com/django/daphne).

### Quickstart

```
$ pip install -r requirements.txt
$ cp annotationsx/settings/secure.py.example annotationsx/settings/secure.py 
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

Notes:
- You will need to create a postgres database first (e.g. `createdb hxat`).
- You will need to edit `secure.py` to configure the database connection details.
- The `runserver` command will automatically start daphne (ASGI server), which will handle HTTP and websocket requests. 

### Running Django with SSL

Generate a certificate for local development using a tool such as [mkcert](https://github.com/FiloSottile/mkcert) and then start the server:

```
$ daphne -e ssl:8000:privateKey=key.pem:certKey=cert.pem annotationsx.asgi:application
```

Note: The reason we need to run daphne directly is that at the time of writing, the django `runserver` command doesn't support SSL and `runsslserver` (via [django-sslserver](https://github.com/teddziuba/django-sslserver)) doesn't support ASGI/Daphne. 

## LMS Integration

### Platform Compatibility

This tool is compatible with [Edx](https://www.edx.org/) and [Canvas](https://www.canvaslms.com/), integrating through the LTI protocol for LMS platforms. The primary difference is that edX displays an annotation author's name using the username, and Canvas uses an author's full name.

### Installing in Canvas

1. In your Canvas course, click `Settings -> Apps -> View App Configurations -> Add App` and then:
2. Select "By URL" for Configuration Type.
3. Then enter the following:
    - Name: AnnotationsX
    - Consumer Key: annotationsx
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

## Development

**To run tests:**

```
$ pytest tests/
```

**To update the test coverage badge:**

```
$ coverage run -m pytest
$ coverage-badge -f -o coverage.svg
```

Be sure to commit and push the changes!

**A note about storing user information:**

As much as possible, the policy of the tool is to avoid storing user information. User information may be stored with annotations in an external store such as CatchPy. If user information does need to be stored, only the anonymous `user_id` should be used. Instructor information including the `name` may be stored, however, for administrative purposes.


**A note about the user_id in edX compared to Canvas:**

In edX, the opaque `user_id` is unique within the scope of a course. In Canvas, the opaque `user_id` is unique within the scope of the platform. In other words, you can't assume that the same user will have the same `user_id` in two different courses when the tool is being used in edX.

**The meaning of the ORG variable:**

Older versions of the tool used a global `ORG` variable to encode some differences, but this has been deprecated and should not be used.
