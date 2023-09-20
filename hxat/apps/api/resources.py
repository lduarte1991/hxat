


class ContextResource(object):
    def __init__(self):
        pass





"""

select
rl.resource_link_id,
target_title,
target_type
from hx_lti_initializer_ltiresourcelinkconfig rl
join target_object_database_targetobject tg
on rl.assignment_target_id = tg.id

select rl.resource_link_id, target_title, target_type from hx_lti_initializer_ltiresourcelinkconfig rl join target_object_database_targetobject tg on rl.assignment_target_id = tg.id


select
a.id,
c.course_id,
t.target_title,
t.target_type
from hx_lti_assignment_assignment a
join hx_lti_initializer_lticourse c
on a.course_id = c.id
join hx_lti_assignment_assignmenttargets at
on at.assignment_id = a.id
join target_object_database_targetobject t
on t.id = at.target_object_id

select a.id, c.course_id from hx_lti_assignment_assignment a join hx_lti_initializer_lticourse c on a.course_id = c.id


select a.id, c.course_id, t.target_title, t.target_type from hx_lti_assignment_assignment a join hx_lti_initializer_lticourse c on a.course_id = c.id join hx_lti_assignment_assignmenttargets on t.assignment_id = a.id


select a.id, c.course_id, t.target_title, t.target_type from hx_lti_assignment_assignment a join hx_lti_initializer_lticourse c on a.course_id = c.id join hx_lti_assignment_assignmenttargets at on at.assignment_id = a.id join target_object_database_targetobject t on t.id = at.target_object_id



COURSE ASSIGNMENTS
select
a.assignment_id, a.assignment_name,
a.annotation_database_url,
a.annotation_database_apikey,
a.annotation_database_secret_token
c.course_id, c.course_name
from hx_lti_assignment_assignment a
join hx_lti_initializer_lticourse c
on a.course_id = c.id

select a.assignment_id, a.assignment_name, a.annotation_database_url, a.annotation_database_apikey, a.annotation_database_secret_token, c.course_id, c.course_name from hx_lti_assignment_assignment a join hx_lti_initializer_lticourse c on a.course_id = c.id order by c.course_id



"""
