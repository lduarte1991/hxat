from abc import *

class TODAPI_LTI:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def get_own_targets_from_course(user_requesting, course_id):
        return None
    
    @abstractmethod
    def get_own_targets_as_user(user_requesting):
        return None
