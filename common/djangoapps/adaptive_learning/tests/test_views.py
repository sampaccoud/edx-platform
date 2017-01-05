"""
Tests for views of adaptive_learning app.
"""

import calendar
from datetime import datetime
from dateutil import parser
import json
import random

from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import Mock, patch

from student.tests.factories import UserFactory


class AdaptiveLearningViewsTest(TestCase):
    """
    Tests for views of adaptive_learning app.
    """

    def setUp(self):
        super(AdaptiveLearningViewsTest, self).setUp()
        password = 'password'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)

    def _make_revisions(self):
        """
        Generate list of revisions for testing.
        """
        return [
            {
                'url': 'url-{n}'.format(n=n),
                'name': 'name-{n}'.format(n=n),
                'due_date': self._make_timestamp(self._make_due_date()),
            } for n in range(5)
        ]

    def _make_pending_reviews(self):
        """
        Generate list of pending reviews for testing.
        """
        return {
            'review-question-{n}'.format(n=n): self._make_due_date()
            for n in range(5)
        }

    def _make_due_date(self):
        """
        Return string that represents random date between beginning of Unix time and right now.
        """
        today = self._make_timestamp(datetime.today())
        random_timestamp = random.randint(0, today)
        random_date = datetime.utcfromtimestamp(random_timestamp)
        return random_date.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def _make_timestamp(date):
        """
        Turn `date` into a Unix timestamp and return it.
        """
        if isinstance(date, str):
            date = parser.parse(date)
        return calendar.timegm(date.timetuple())

    @staticmethod
    def _make_mock_modulestore(courses):
        """
        Return mock modulestore whose `get_courses` method returns `courses`.
        """
        mock_modulestore = Mock(autospec=True)
        mock_modulestore.get_courses.return_value = courses
        return mock_modulestore

    def _make_mock_courses(self, *meaningfulness):
        """
        Return list of mock courses with adaptive learning configuration that is (not) meaningful.
        """
        courses = []
        for meaningful in meaningfulness:
            course = Mock()
            course.adaptive_learning_configuration = self._make_adaptive_learning_configuration(meaningful)
            courses.append(course)
        return courses

    @staticmethod
    def _make_adaptive_learning_configuration(meaningful):
        """
        Return adaptive learning configuration that is `meaningful`.
        """
        if meaningful:
            return {
                'a': 'meaningful-value',
                'b': 'another-meaningful-value',
                'c': 42
            }
        else:
            return {
                'a': '',
                'b': '',
                'c': -1
            }

    @patch('adaptive_learning.views.get_pending_revisions')
    def test_revisions(self, mock_get_pending_revisions):
        """
        Test 'revisions' view.
        """
        revisions = self._make_revisions()
        mock_get_pending_revisions.return_value = revisions
        response = self.client.get(reverse('revisions'))
        mock_get_pending_revisions.assert_called_once_with(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, json.dumps(revisions))

    @patch('adaptive_learning.views.modulestore')
    def test_revisions_course_configuration(self, mock_modulestore):
        """
        Test that 'revisions' view takes into account adaptive learning configuration of courses.

        When collecting revisions for display, the view should ignore courses
        that are not properly configured for communicating with external adaptive learning service.
        """
        regular_course, adaptive_learning_course = self._make_mock_courses(False, True)
        mock_modulestore.return_value = self._make_mock_modulestore([regular_course, adaptive_learning_course])
        with patch('adaptive_learning.views.get_pending_reviews') as patched_get_pending_reviews, \
                patch('adaptive_learning.views.make_revisions') as patched_make_revisions:
            pending_reviews = self._make_pending_reviews()
            revisions = self._make_revisions()
            patched_get_pending_reviews.return_value = pending_reviews
            patched_make_revisions.return_value = revisions
            response = self.client.get(reverse('revisions'))
            # Modulestore contains two courses, one course with a meaningful configuration,
            # and one course without a meaningful configuration.
            # So:
            # - Function for obtaining list of pending reviews should have been called once,
            #   with course that has meaningful configuration, and appropriate `user_id`.
            patched_get_pending_reviews.assert_called_once_with(adaptive_learning_course, self.user.id)
            # - Functions for turning list of pending reviews into list of revisions to display
            #   should have been called once, with course that has meaningful configuration,
            #   and list of `pending_reviews`.
            patched_make_revisions.assert_called_once_with(adaptive_learning_course, pending_reviews)
            # - Content of response should be equal to return value of patched `make_revisions` function.
            self.assertEqual(response.content, json.dumps(revisions))

    @patch('adaptive_learning.views.modulestore')
    def test_revisions_no_pending_reviews(self, mock_modulestore):
        """
        Test that 'revisions' view behaves correctly when there are no pending reviews for a course.
        """
        courses = self._make_mock_courses(True)
        mock_modulestore.return_value = self._make_mock_modulestore(courses)
        with patch('adaptive_learning.views.get_pending_reviews') as patched_get_pending_reviews, \
                patch('adaptive_learning.views.make_revisions') as patched_make_revisions:
            patched_get_pending_reviews.return_value = {}
            response = self.client.get(reverse('revisions'))
            patched_get_pending_reviews.assert_called_once_with(courses[0], self.user.id)
            patched_make_revisions.assert_not_called()
            self.assertEqual(response.content, json.dumps([]))
