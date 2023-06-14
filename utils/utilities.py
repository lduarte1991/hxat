from datetime import datetime
import json

from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIResourceLinkConfig
from target_object_database.models import TargetObject

import pdb

def report_relationships_for_course(cid):
    try:
        course = LTICourse.objects.get(course_id=cid)
    except LTICourse.DoesNotExist:
        return (None, "course({}) not found".format(cid))

    result = {
        "course_id": cid,
        "id": course.id,
        "assignments": [],
        "target_objects": {},
        "resource_link_ids": [],
        "course_admins": [],
        "course_users": [],
    }
    # all assignments related to this course
    for a in course.assignments.all():
        result["assignments"].append({
            "assignment_id": a.assignment_id,
            "assignment_name": a.assignment_name,
            "use_hxighligter": a.use_hxighlighter,
            "annostore": {
                "url": a.annotation_database_url,
                "key": a.annotation_database_apikey,
                "pwd": a.annotation_database_secret_token,
            },
        })
        # all target objects related to this course
        for t in a.assignment_objects.all():
            result["target_objects"][t.id] = {
                "title": t.target_title,
                "creator_username": t.target_creator.user.username,
                "courses": [x.course_id for x in t.target_courses.all()],
            }

        # all resource_link_ids, via assignment_target, related to this course
        assignment_target_list = AssignmentTargets.objects.filter(assignment=a.id)
        for at in assignment_target_list:
            reslinkcfg_list = LTIResourceLinkConfig.objects.filter(assignment_target=at.id)
            result["resource_link_ids"] = [x.resource_link_id for x in reslinkcfg_list.all()]

    # all course_admins for this course
    for adm in course.course_admins.all():
        result["course_admins"].append({
            "profile_id": adm.id,
            "username": adm.user.username,
            "anon_id": adm.anon_id,
        })
    for usr in course.course_users.all():
        result["course_users"].append({
            "profile_id": usr.id,
            "username": usr.user.username,
            "anon_id": usr.anon_id,
        })
    return (result, "ok")


def no_assign_courses():
    all_courses = LTICourse.objects.all()
    no_assign = []

    for c in all_courses:
        if len(c.assignments.all()) <= 0:
            no_assign.append({
                "course_id": c.course_id,
                "id": c.id,
                "created_at": c.created_at.isoformat(),
            })

    no_assign_sorted = sorted(no_assign, key=lambda item: item["id"])
    return no_assign_sorted

def delete_course(cid):
    try:
        course = LTICourse.objects.get(course_id=cid)
    except LTICourse.DoesNotExist:
        return (False, "course({}) not found".format(cid))

    # delete all assignments first
    for a in course.assignments.all():
        a.delete()

    course.delete()
    return (True, "course({}) DELETED".format(cid))


def courses_with_oldui():
    all_courses = LTICourse.objects.all().order_by("course_id")
    result = {
        "oldui": {"summary": []},
        "ok": {"summary": []},
        "mixed": {"summary": []},
        "none": {"summary": []},
    }

    for c in all_courses:
        c_assigns = {"course_id": c.course_id, "old": [], "new": []}
        for a in c.assignments.all():
            if not a.use_hxighlighter:
                c_assigns["old"].append(a.assignment_id)
            else:
                c_assigns["new"].append(a.assignment_id)
        has_old = len(c_assigns["old"]) > 0
        has_new = len(c_assigns["new"]) > 0
        if has_old:
            if has_new:  # mixed bag
                result["mixed"][c.course_id] = c_assigns
                result["mixed"]["summary"].append(c.course_id)
            else:  # only old
                result["oldui"][c.course_id] = c_assigns
                result["oldui"]["summary"].append(c.course_id)
        elif has_new:  # only new
            result["ok"][c.course_id] = c_assigns
            result["ok"]["summary"].append(c.course_id)
        else:  # no assigns
            result["none"][c.course_id] = c_assigns
            result["none"]["summary"].append(c.course_id)

    return result


def courses_with_annotations(concoll_list):
    concoll = {}
    for (cid, aid) in concoll_list:
        if concoll.get(cid, None) is None:
            concoll[cid] = []
        concoll[cid].append(aid)

    result = {}
    all_courses = LTICourse.objects.all()
    for c in all_courses:
        result[c.course_id] = {}
        if c.course_id in concoll:
            for a in c.assignments.all():
                if a.assignment_id in concoll[c.course_id]:
                    result[c.course_id][a.assignment_id] = "{} - {}".format(
                            "T" if a.use_hxighlighter else "F",
                            a.assignment_name,
                    )

    return result







