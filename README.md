| [lduarte1991](https://github.com/lduarte1991/hxat) | ![Open PRs](https://img.shields.io/github/issues-pr/lduarte1991/hxat.svg) [![Build Status](https://travis-ci.org/lduarte1991/hxat.svg?branch=master)](https://travis-ci.org/Harvard-ATG/annotationsx) | [harvard-atg](https://github.com/Harvard-ATG/annotationsx) | ![Open PRs](https://img.shields.io/github/issues-pr/harvard-atg/annotationsx.svg) [![Build Status](https://travis-ci.org/Harvard-ATG/annotationsx.svg?branch=master)](https://travis-ci.org/Harvard-ATG/annotationsx) |
|----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
# The HarvardX Annotation Tool (The HxAT)

LTI tool developed by HarvardX in collaboration with HUIT Academic Technology to provide annotations to Text, Images, and Videos on the edX and Canvas platforms.

## Quickstart

Download and install [virtualbox](https://www.virtualbox.org/) and [vagrant](https://www.vagrantup.com/). Run the following commands to provision your virtual box:

```
$ vagrant up                          # start and provision virtual box (see Vagrantfile)
$ vagrant ssh                         # ssh into virtual box
$ cd /vagrant                         # change to shared directory with code
$ ./manage.py migrate                 # initialize database by running django migrations
$ ./manage.py createsuperuser         # (Optional) so you can login to the admin interface
$ ./manage.py runserver 0.0.0.0:8000  # run server on port 8000 (forwarded by virtual box)
```

Note: see `vagrant/provision.sh` script for details on provisioning the server.

## LTI Installation

### Canvas

1. Go to [lti/config](http://localhost:8000/lti/config) and copy the XML output.
2. In your Canvas course, click `Settings -> Apps -> View App Configurations -> Add App` and then:
	* Select 'Paste XML'
	* Paste XML
	* Name your App
	* Enter your key and secret
	* Save
3. If the installation worked, the tool should appear in your left navigation.

### EdX

TODO

## LTI Compatibility

This tool is LTI-compatible with [Edx](https://www.edx.org/) and [Canvas](https://www.canvaslms.com/).

There are some differences in how the tool is used on these platforms. The tool may be configured for each platform as needed in `annotationsx/settings/aws.py`.

Note that older versions of the tool used a global `ORG` variable to encode these differences, but this has been deprecated in favor of more fine-grained settings. Some vestiges of the `ORG` variable are still around.

### Authentication

As much as possible, the tool tries to avoid storing student information, and in cases where it must identify students (i.e. annotations), it uses the anonymous `user_id` that is provided by the LTI consumer. Instructor information is, however, stored in the tool database.

Although the `user_id` uniquely identifies students, it should be noted that the scope of uniqueness differs between edX and Canvas:

- In edX, the opaque `user_id` is only unique within the scope of a course. For example, given an email registered with edX that uniquely and globally identifies a user on the edX platform, a different user ID is passed to each course. 
- In Canvas, the opaque `user_id` is unique within the scope of the university-wide hosted instance. For example, given an SIS ID for a student, the same opaque user ID will be transmitted to the tool for each course on the hosted instance. 

### Launching the tool 

When the tool launches, there are two possible ways to launch:

1. Launch to a TARGET annotation assignment. This is exactly what it sounds like: the tool is passed parameters so it knows exactly which target object and annotation assignment should be rendered. This is most often used to embed an annotation assignment in edX or in a Canvas module.
2. Launch to an INDEX or HUB that lists all the annotation assignments in the course. This is most often used to make all assignments available to students and teaching staff alike in Canvas when it is added to the left-navigation of the course.

### Instructor Dashboard

The instructor dashboard is a tool designed specifically for Canvas instructors to get a listing of all student annotations. Due to issues with scaling/load, it is not currently used for edX courses.

## Technical Information

This section may include technical notes.

### Project Structure

TODO

### Secure Settings

All secure settings and configuration options are stored in `annotations/settings/secure.py`. This file is not included in source control since it will likely contain sensitive/secure values.

See the example to get started: `annotationsx/settings/secure.py.example`.

### Sessions: Cookieless Sessions and Multiple Sessions

TODO

