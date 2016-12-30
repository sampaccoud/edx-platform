# -*- coding: utf-8 -*-
"""
Utilities for adaptive learning features.
"""

import hashlib
import json
import logging
import requests

from lazy import lazy

log = logging.getLogger(__name__)


class AdaptiveLearningConfiguration(object):
    """
    Stores configuration that is necessary for interacting with external services
    that provide adaptive learning features.
    """

    def __init__(self, **kwargs):
        """
        Creates an attribute for each key in `kwargs` and sets it to the corresponding value.
        """
        self._configuration = kwargs
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __str__(self):
        """
        Returns string listing all custom attributes set on `self`.
        """
        return str(self._configuration)


class AdaptiveLearningAPIMixin(object):
    """
    Provides methods for interacting with external service that provides adaptive learning features.
    """

    @lazy
    def _adaptive_learning_configuration(self):
        """
        Return configuration for accessing external service that provides adaptive learning features.

        This configuration is a course-wide setting, so in order to access it,
        we need to (lazily) load the parent course from the DB.
        """
        course = self.parent_course
        return AdaptiveLearningConfiguration(
            **course.adaptive_learning_configuration
        )

    @lazy
    def _pending_reviews_url(self):
        """
        Return URL for accessing pending reviews.
        """
        instance_url = self._instance_url(self._adaptive_learning_configuration)
        return '{base_url}/review_utils/fetch_reviews'.format(base_url=instance_url)

    @lazy
    def _request_headers(self):
        """
        Return custom headers for requests to external service that provides adaptive learning features.
        """
        return self.__request_headers(self._adaptive_learning_configuration)

    @classmethod
    def _adaptive_learning_url(cls, adaptive_learning_configuration):
        """
        Return base URL for external service that provides adaptive learning features.

        The base URL is a combination of the URL (url) and API version (api_version)
        specified in the adaptive learning configuration for the parent course.
        """
        url = adaptive_learning_configuration.url
        api_version = adaptive_learning_configuration.api_version
        return '{url}/{api_version}'.format(url=url, api_version=api_version)

    @classmethod
    def _instance_url(cls, adaptive_learning_configuration):
        """
        Return URL for requesting instance-specific data from external service
        that provides adaptive learning features.
        """
        instance_id = adaptive_learning_configuration.instance_id
        adaptive_learning_url = cls._adaptive_learning_url(adaptive_learning_configuration)
        return '{base_url}/instances/{instance_id}'.format(
            base_url=adaptive_learning_url, instance_id=instance_id
        )

    @classmethod
    def _students_url(cls, adaptive_learning_configuration):
        """
        Return URL for requests dealing with students.
        """
        instance_url = cls._instance_url(adaptive_learning_configuration)
        return '{base_url}/students'.format(base_url=instance_url)

    @classmethod
    def _events_url(cls, adaptive_learning_configuration):
        """
        Return URL for requests dealing with events.
        """
        instance_url = cls._instance_url(adaptive_learning_configuration)
        return '{base_url}/events'.format(base_url=instance_url)

    @classmethod
    def _knowledge_node_students_url(cls, adaptive_learning_configuration):
        """
        Return URL for accessing 'knowledge node student' objects.
        """
        instance_url = cls._instance_url(adaptive_learning_configuration)
        return '{base_url}/knowledge_node_students'.format(base_url=instance_url)

    @classmethod
    def __request_headers(cls, adaptive_learning_configuration):
        """
        Return custom headers for requests to external service that provides adaptive learning features.
        """
        access_token = adaptive_learning_configuration.access_token
        return {
            'Authorization': 'Token token={access_token}'.format(access_token=access_token)
        }

    @classmethod
    def _get_knowledge_node_student_id(cls, adaptive_learning_configuration, block_id, user_id):
        """
        Return ID of 'knowledge node student' object linking student identified by `user_id`
        to unit identified by `block_id`.
        """
        knowledge_node_student = cls._get_or_create_knowledge_node_student(
            adaptive_learning_configuration, block_id, user_id
        )
        return knowledge_node_student.get('id')

    @classmethod
    def _get_or_create_knowledge_node_student(cls, adaptive_learning_configuration, block_id, user_id):
        """
        Return 'knowledge node student' object for user identified by `user_id`
        and unit identified by `block_id`.
        """
        # Create student
        cls._get_or_create_student(adaptive_learning_configuration, user_id)
        # Link student to unit
        knowledge_node_student = cls._get_knowledge_node_student(
            adaptive_learning_configuration, block_id, user_id
        )
        if knowledge_node_student is None:
            knowledge_node_student = cls._create_knowledge_node_student(
                adaptive_learning_configuration, block_id, user_id
            )
        return knowledge_node_student

    @classmethod
    def _get_or_create_student(cls, adaptive_learning_configuration, user_id):
        """
        Create a new student on external service if it doesn't exist,
        and return it.
        """
        student = cls._get_student(adaptive_learning_configuration, user_id)
        if student is None:
            student = cls._create_student(adaptive_learning_configuration, user_id)
        return student

    @classmethod
    def _get_student(cls, adaptive_learning_configuration, user_id):
        """
        Return external information about student identified by `user_id`,
        or None if external service does not know about student.
        """
        students = cls._get_students(adaptive_learning_configuration)
        try:
            student = next(s for s in students if s.get('uid') == user_id)
        except StopIteration:
            student = None
        return student

    @classmethod
    def _get_students(cls, adaptive_learning_configuration):
        """
        Return list of all students that external service knows about.
        """
        url = cls._students_url(adaptive_learning_configuration)
        request_headers = cls.__request_headers(adaptive_learning_configuration)
        response = requests.get(url, headers=request_headers)
        students = json.loads(response.content)
        return students

    @classmethod
    def _create_student(cls, adaptive_learning_configuration, user_id):
        """
        Create student identified by `user_id` on external service,
        and return it.
        """
        url = cls._students_url(adaptive_learning_configuration)
        payload = {'uid': user_id}
        request_headers = cls.__request_headers(adaptive_learning_configuration)
        response = requests.post(url, headers=request_headers, data=payload)
        student = json.loads(response.content)
        return student

    @classmethod
    def _get_knowledge_node_student(cls, adaptive_learning_configuration, block_id, user_id):
        """
        Return 'knowledge node student' object for user identified by `user_id`
        and unit identified by `block_id`, or None if it does not exist.
        """
        # Get 'knowledge node student' objects
        links = cls._get_knowledge_node_students(adaptive_learning_configuration)
        # Filter them by `block_id` and `user_id`
        try:
            link = next(
                l for l in links if l.get('knowledge_node_uid') == block_id and l.get('student_uid') == user_id
            )
        except StopIteration:
            link = None
        return link

    @classmethod
    def _get_knowledge_node_students(cls, adaptive_learning_configuration):
        """
        Return list of all 'knowledge node student' objects for this course.
        """
        url = cls._knowledge_node_students_url(adaptive_learning_configuration)
        request_headers = cls.__request_headers(adaptive_learning_configuration)
        response = requests.get(url, headers=request_headers)
        links = json.loads(response.content)
        return links

    @classmethod
    def _create_knowledge_node_student(cls, adaptive_learning_configuration, block_id, user_id):
        """
        Create 'knowledge node student' object that links student identified by `user_id`
        to unit identified by `block_id`, and return it.
        """
        url = cls._knowledge_node_students_url(adaptive_learning_configuration)
        request_headers = cls.__request_headers(adaptive_learning_configuration)
        payload = {'knowledge_node_uid': block_id, 'student_uid': user_id}
        response = requests.post(url, headers=request_headers, data=payload)
        knowledge_node_student = json.loads(response.content)
        return knowledge_node_student

    @classmethod
    def _create_event(cls, adaptive_learning_configuration, block_id, user_id, event_type, **data):
        """
        Create event of type `event_type` for unit identified by `block_id` and student identified by `user_id`,
        sending any kwargs in `data` along with the default payload.
        """
        url = cls._events_url(adaptive_learning_configuration)
        request_headers = cls.__request_headers(adaptive_learning_configuration)
        knowledge_node_student_id = cls._get_knowledge_node_student_id(
            adaptive_learning_configuration, block_id, user_id
        )
        payload = {
            'knowledge_node_student_id': knowledge_node_student_id,
            'event_type': event_type,
        }
        payload.update(data)

        # Send request
        response = requests.post(url, headers=request_headers, data=payload)
        event = json.loads(response.content)
        return event

    @classmethod
    def _make_anonymous_user_id(cls, adaptive_learning_configuration, course_id, user_id):
        """
        Return anonymous ID for user identified by `user_id`.

        Incorporate `course_id` and access token from `adaptive_learning_configuration` into digest.
        """
        # Include the access token for this course as a salt
        hasher = hashlib.md5()
        hasher.update(adaptive_learning_configuration.access_token)
        hasher.update(unicode(user_id))
        hasher.update(course_id.to_deprecated_string().encode('utf-8'))
        anonymous_user_id = hasher.hexdigest()
        return anonymous_user_id

    # Public API

    @classmethod
    def create_result_event(cls, course, block_id, user_id, result):
        """
        Create result event for unit identified by `block_id` and student identified by `user_id`
        using adaptive learning configuration from `course`.
        """
        adaptive_learning_configuration = AdaptiveLearningConfiguration(
            **course.adaptive_learning_configuration
        )
        user_id = cls._make_anonymous_user_id(adaptive_learning_configuration, course.id, user_id)
        if result == 'correct':
            result = '100'
        elif result == 'incorrect':
            result = '0'
        data = {'payload': result}

        return cls._create_event(adaptive_learning_configuration, block_id, user_id, 'EventResult', **data)

    def make_anonymous_user_id(self, user_id):
        """
        Return anonymous ID for user identified by `user_id`.

        Incorporate `course_id` and access token for external service into digest.
        """
        return self._make_anonymous_user_id(self._adaptive_learning_configuration, self.course_id, user_id)

    def create_read_event(self, block_id, user_id):
        """
        Create read event for unit identified by `block_id` and student identified by `user_id`.
        """
        return self._create_event(self._adaptive_learning_configuration, block_id, user_id, 'EventRead')

    def create_knowledge_node_students(self, block_ids, user_id):
        """
        Create 'knowledge node student' objects that link student identified by `user_id`
        to review questions identified by block IDs listed in `block_ids`, and return them.
        """
        knowledge_node_students = []
        for block_id in block_ids:
            knowledge_node_student = self._get_or_create_knowledge_node_student(
                self._adaptive_learning_configuration, block_id, user_id
            )
            knowledge_node_students.append(knowledge_node_student)
        return knowledge_node_students

    def get_pending_reviews(self, user_id):
        """
        Return pending reviews for user identified by `user_id`.
        """
        url = self._pending_reviews_url
        payload = {'student_uid': user_id}
        response = requests.get(url, headers=self._request_headers, data=payload)
        pending_reviews_user = json.loads(response.content)
        return pending_reviews_user
