![Build Status](https://travis-ci.org/Harvard-ATG/annotationsx.svg?branch=master)
![Coverage Status](./coverage.svg)

# The HarvardX Annotation Tool (HxAT)

Tool for annotating text, images, and videos. Integrates with LMS platforms such as [edX](https://www.edx.org/) and [Canvas](https://www.instructure.com/canvas/) via [LTI](https://www.imsglobal.org/activity/learning-tools-interoperability).

### Requirements

- **Application:** python3 and [django](https://www.djangoproject.com/)
- **Database:** postgres 
- **Annotation Store:** [catchpy](https://github.com/nmaekawa/catchpy) 

A minimal install requires a postgres database for the application, but it will not be able to persist annotations. To persist annotations, a service such as [catchpy](https://github.com/nmaekawa/catchpy) must be running as well.

### Quickstart

```
$ cp annotationsx/settings/secure.py.example annotationsx/settings/secure.py 
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

Note: that you will need to edit `secure.py` to configure the database and modify other values as appropriate.

## LTI Installation

For **Canvas**:

1. In your Canvas course, click `Settings -> Apps -> View App Configurations -> Add App` and then:
2. Select "By URL" for Configuration Type.
3. Then enter the following:
    - Name: AnnotationsX
    - Consumer Key: annotationsx
    - Shared Secret: secret
    - Config URL: https://localhost:8000/lti/config
4. If the installation worked, the tool should appear in your left navigation.

## LTI Details

### Platform Compatibility

This tool is compatible with [Edx](https://www.edx.org/) and [Canvas](https://www.canvaslms.com/), integrating through the LTI protocol for LMS platforms. The primary difference is that edX displays an annotation author's name using the username, and Canvas uses an author's full name.

### Launch configuration

When the tool launches (i.e. authenticates a user for a particular course context), there are two possible configurations: 

1. **Display a list of annotation assignments (default)**
	- The tool displays all annotation assignments associated with the course context. This is most often used to make all assignments available to students and teaching staff alike in Canvas when it is added to the left-navigation of the course.
2. **Display a specific annotation assignment**
	- The tool is passed custom parameters so it knows exactly which target object and annotation assignment should be rendered immediatley. This is most often used to embed an annotation assignment in edX or in a Canvas module.

### Privacy 

As much as possible, the tool avoids storing student information, and in cases where it must identify students (i.e. annotations), it uses the anonymous `user_id` that is provided by the LTI consumer along with the provided name. Instructor information is, however, stored in the tool database.

## Developer documentation


**To update the coverage badge**

```
$ coverage run --source='.' manage.py test
$ coverage-badge -f -o coverage.svg
```

Then commit and push the changes!

**Uniqueness of user_id in edX compared to Canvas:**

In edX, the opaque `user_id` is  unique within the scope of a course. In Canvas, the opaque `user_id` is unique within the scope of the university-wide hosted instance. 

**The meaning of the ORG variable:**

Older versions of the tool used a global `ORG` variable to encode some differences, but this has been deprecated and should not be used.