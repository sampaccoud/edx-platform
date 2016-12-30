from __future__ import absolute_import

import ddt
from django.test import TestCase
from mock import Mock, patch

from track.backends.adaptive_learning import (
    _is_problem_check, _get_course, _get_block_id, _get_user_id, _get_success, AdaptiveLearningBackend
)


@ddt.ddt
class TestAdaptiveLearningBackend(TestCase):
    """
    Tests for AdaptiveLearningBackend and helper functions.
    """

    def setUp(self):
        super(TestAdaptiveLearningBackend, self).setUp()
        self.backend = AdaptiveLearningBackend()

    @ddt.data(
        ('problem_check', True),
        ('other', False)
    )
    @ddt.unpack
    def test__is_problem_check(self, event_type, expected_result):
        """
        Test that `_is_problem_check` function returns True if event is of type "problem_check",
        and False otherwise.
        """
        event = {'event_type': event_type}
        result = _is_problem_check(event)
        self.assertEqual(result, expected_result)

    def test__get_course(self):
        """
        Test that `_get_course` function extracts appropriate value from event and returns it.
        """
        course_id = 'block-v1:org+course+run+type@course+block@course'
        event = {
            'context': {
                'course_id': course_id
            }
        }
        with patch('track.backends.adaptive_learning.CourseKey') as patched_class, \
             patch('track.backends.adaptive_learning.modulestore') as patched_modulestore:
            mock_course_key = Mock()
            patched_class.from_string.return_value = mock_course_key
            mock_modulestore = Mock()
            mock_course = Mock()
            mock_modulestore.get_course.return_value = mock_course
            patched_modulestore.return_value = mock_modulestore
            course = _get_course(event)
            self.assertEqual(course, mock_course)
            patched_class.from_string.assert_called_once_with(course_id)
            patched_modulestore.assert_called_once_with()
            mock_modulestore.get_course.assert_called_once_with(mock_course_key)

    def test__get_block_id(self):
        """
        Test that `_get_block_id` function extracts appropriate value from event and returns it.
        """
        usage_key_string = 'block-v1:org+course+run+type@problem+block@8e52e13fc4g696gb8g33'
        event = {
            'context': {
                'module': {
                    'usage_key': usage_key_string
                }
            }
        }
        with patch('track.backends.adaptive_learning.UsageKey') as patched_class:
            expected_block_id = '8e52e13fc4g696gb8g33'
            mock_usage_key = Mock()
            mock_usage_key.block_id = expected_block_id
            patched_class.from_string.return_value = mock_usage_key
            block_id = _get_block_id(event)
            self.assertEqual(block_id, expected_block_id)
            patched_class.from_string.assert_called_once_with(usage_key_string)

    def test__get_user_id(self):
        """
        Test that `_get_user_id` function extracts appropriate value from event and returns it.
        """
        event = {
            'context': {
                'user_id': 23
            }
        }
        user_id = _get_user_id(event)
        self.assertEqual(user_id, 23)

    @ddt.data('correct', 'incorrect')
    def test__get_success(self, expected_success):
        """
        Test that `_get_success` function extracts appropriate value from event and returns it.
        """
        event = {
            'event': {
                'success': expected_success
            }
        }
        success = _get_success(event)
        self.assertEqual(success, expected_success)

    @ddt.data(True, False)
    def test_adaptive_learning_backend(self, is_problem_check):
        """
        Test that `send` method of AdaptiveLearningBackend triggers logic for sending result event
        to external service that provides adaptive learning features, when appropriate.
        """
        block_id = '8e52e13fc4g696gb8g33'
        user_id = 23
        success = 'correct'
        event = {
            'event_type': 'problem_check',
            'context': {
                'course_id': 'block-v1:org+course+run+type@course+block@course',
                'user_id': user_id,
                'module': {
                    'usage_key': 'block-v1:org+course+run+type@problem+block@{block_id}'.format(block_id=block_id)
                },
            },
            'event': {
                'success': success
            }
        }
        with patch('track.backends.adaptive_learning._is_problem_check') as patched__is_problem_check, \
             patch('track.backends.adaptive_learning._get_course') as patched__get_course, \
             patch('track.backends.adaptive_learning._get_block_id') as patched__get_block_id, \
             patch('track.backends.adaptive_learning._get_user_id') as patched__get_user_id, \
             patch('track.backends.adaptive_learning._get_success') as patched__get_success, \
             patch('track.backends.adaptive_learning.AdaptiveLibraryContentModule') as patched_class:
            patched__is_problem_check.return_value = is_problem_check
            course_mock = Mock()
            patched__get_course.return_value = course_mock
            patched__get_block_id.return_value = block_id
            patched__get_user_id.return_value = user_id
            patched__get_success.return_value = success
            mock_create_result_event = Mock()
            patched_class.create_result_event = mock_create_result_event
            self.backend.send(event)
            if is_problem_check:
                patched__get_course.assert_called_once_with(event)
                patched__get_block_id.assert_called_once_with(event)
                patched__get_user_id.assert_called_once_with(event)
                patched__get_success.assert_called_once_with(event)
                mock_create_result_event.assert_called_once_with(course_mock, block_id, user_id, success)
            else:
                patched__get_course.assert_not_called()
                patched__get_block_id.assert_not_called()
                patched__get_user_id.assert_not_called()
                patched__get_success.assert_not_called()
                mock_create_result_event.assert_not_called()
