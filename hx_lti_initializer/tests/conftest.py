
import pytest

from random import randint

from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.utils import create_new_user


@pytest.fixture(scope='function')
def anon_learner():
    user, profile = create_new_user(
            anon_id='anonymous',
            username='anon_learner',
            display_name='anon_learner',
            roles=['Learner'],
            scope='course123',
            )
    return {'user': user, 'profile': profile}


@pytest.fixture(scope='function')
def random_learner():
    random_id = randint(0, 65534)
    random_name = 'user_{}'.format(random_id)
    display_name = 'User {}'.format(random_id)
    user, profile = create_new_user(
            anon_id=random_id,
            username=random_name,
            display_name=display_name,
            roles=['Learner'],
            scope='course123',
            )
    return {'user': user, 'profile': profile}


@pytest.fixture(scope='function')
def random_instructor():
    random_id = randint(0, 65534)
    random_name = 'user_{}'.format(random_id)
    user, profile = create_new_user(
            anon_id=random_id,
            username=random_name,
            display_name=random_name,
            roles=['Instructor'],
            scope='course123',
            )
    return {'user': user, 'profile': profile}


@pytest.fixture(scope='function')
def random_course_instructor():
    random_id = randint(0, 65534)
    random_name = 'user_{}'.format(random_id)
    random_course = 'harvardX+ABC+{}'.format(randint(0, 65534))
    user, profile = create_new_user(
            anon_id=random_id,
            username=random_name,
            display_name=random_name,
            roles=['Instructor'],
            scope='course123',
            )

    course = LTICourse.create_course(random_course, profile)

    return {'user': user, 'profile': profile, 'course': course}

