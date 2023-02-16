from .aws import *

#
# for production, we log to stdout, and then redirect to syslog
# remove log file to avoid crowding the disk: hx provision does not configure
# rotation nor cleanup for app log files!
#
LOGGING["loggers"]["django"]["handlers"] = ["console"]
LOGGING["loggers"]["django.request"]["handlers"] = ["console"]
LOGGING["loggers"]["django.db.backends"]["handlers"] = ["console"]
LOGGING["loggers"]["hx_lti_initializer"]["handlers"] = ["console"]
LOGGING["loggers"]["hx_lti_assignment"]["handlers"] = ["console"]
LOGGING["loggers"]["target_object_database"]["handlers"] = ["console"]
LOGGING["loggers"]["annostore"]["handlers"] = ["console"]
LOGGING["loggers"]["hxat.middleware"]["handlers"] = ["console"]
