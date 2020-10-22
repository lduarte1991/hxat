"""
    This is the file that should change when talking about changing 
    Target Object Databases! Change the Current_Implementation functions to call
    whatever functions you are currently using. This will allow you to keep the 
    API intact as well as automatically run tests. 

"""
from abc import *

from hx_lti_initializer.models import LTICourse, LTIProfile
from target_object_database.models import TargetObject


class TODAPI_LTI(ABC):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_own_targets_from_course(user_requesting, course_id):
        """
        This function should return a list of objects (following the model created in hx_annotations/hx_lti_todapi) from the course given.
        """
        raise NotImplementedError("Should implement get_own_targets_from_course()!")

    @abstractmethod
    def get_own_targets_as_user(user_requesting):
        raise NotImplementedError("Should implement get_own_targets_as_user()!")


class TOD_Implementation(TODAPI_LTI):

    @staticmethod
    def get_own_targets_from_course(course_id):
        """
        This function should return a list of objects with the attributes set up above. 
        """
        course_for_user = LTICourse.get_course_by_id(course_id)
        response = TargetObject.objects.filter(target_courses=course_for_user).order_by('assignmenttargets')
        return response

    @staticmethod
    def get_dict_of_files_from_courses(courses):
        files_in_courses = dict()
        for course_item in courses:
            files_found = TOD_Implementation.get_own_targets_from_course(course_item.course_id)
            files_in_courses[course_item.course_name] = list(files_found)
        return files_in_courses

    @staticmethod
    def get_own_targets_as_user(user_requesting):
        """
        This function should return all the files 
        """
        courses_for_user = LTICourse.objects.filter(course_admins=user_requesting.id)
        files_in_courses = []
        for course_item in courses_for_user:
            files_found = TargetObject.objects.filter(target_courses=course_item)
            files_in_courses += list(files_found)
        return files_in_courses

TODAPI_LTI.register(TOD_Implementation)
