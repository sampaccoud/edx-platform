""" Event tracker backend that sends relevant data to adaptive learning service. """

from __future__ import absolute_import

import logging

from opaque_keys.edx.keys import CourseKey, UsageKey

from track.backends import BaseBackend
from xmodule.library_content_module import AdaptiveLibraryContentModule
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


def _is_problem_check(event):
    """
    Return True if `event` is of type `problem_check`, else False.
    """
    event_type = event.get('event_type')
    return event_type == 'problem_check'


def _get_course(event):
    """
    Retrieve course corresponding to course ID mentioned in `event` from DB
    and return it.
    """
    context = event.get('context')
    course_id = context.get('course_id')
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key)
    return course


def _get_block_id(event):
    """
    Return ID of block that `event` belongs to.
    """
    context = event.get('context')
    module = context.get('module')
    usage_key_string = module.get('usage_key')
    usage_key = UsageKey.from_string(usage_key_string)
    block_id = usage_key.block_id
    return block_id


def _get_user_id(event):
    """
    Return ID of user that triggered `event`.
    """
    context = event.get('context')
    user_id = context.get('user_id')
    return user_id


def _get_success(event):
    """
    Return success information from `event`.
    """
    event = event.get('event')
    success = event.get('success')
    return success


class AdaptiveLearningBackend(BaseBackend):
    """
    Event tracker backend for notifying external service that provides adaptive learning features
    about relevant events.
    """

    def send(self, event):
        """
        Instruct AdaptiveLibraryContentModule to send result event
        to external service that provides adaptive learning features.
        """
        if _is_problem_check(event):
            course = _get_course(event)
            block_id = _get_block_id(event)
            user_id = _get_user_id(event)
            success = _get_success(event)
            AdaptiveLibraryContentModule.create_result_event(course, block_id, user_id, success)
