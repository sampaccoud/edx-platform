# -*- coding: utf-8 -*-
"""
Unit tests for the localization of emails sent by instructor.api methods.
"""

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from courseware.tests.factories import InstructorFactory
from lang_pref import LANGUAGE_KEY
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from openedx.core.djangoapps.user_api.models import UserPreference
from xmodule.modulestore.tests.factories import CourseFactory


class TestInstructorAPIEnrollmentEmailLocalization(TestCase):
    """
    Test whether the enroll, unenroll and beta role emails are sent in the
    proper language, i.e: the student's language.
    """

    def setUp(self):
        # Platform language is English, instructor's language is Chinese,
        # student's language is French, so the emails should all be sent in
        # French.
        self.course = CourseFactory.create()
        self.instructor = InstructorFactory(course_key=self.course.id)
        UserPreference.set_preference(self.instructor, LANGUAGE_KEY, 'zh-cn')
        self.client.login(username=self.instructor.username, password='test')

        self.student = UserFactory.create()
        UserPreference.set_preference(self.student, LANGUAGE_KEY, 'fr')

    def update_enrollement(self, action):
        """
        Update the current student enrollment status.
        """
        url = reverse('students_update_enrollment', kwargs={'course_id': self.course.id.to_deprecated_string()})
        args = {'identifiers': self.student.email, 'email_students': 'true', 'action': action}
        response = self.client.post(url, args)
        return response

    def check_outbox(self):
        """
        Check that the email outbox contains exactly one message for which both
        the message subject and body start with a certain French string.
        """
        self.assertEqual(1, len(mail.outbox))
        you_have_been_in_french = u"Vous avez été"
        self.assertIn(you_have_been_in_french, mail.outbox[0].subject)
        self.assertIn(you_have_been_in_french, mail.outbox[0].body)

    def test_enroll(self):
        self.update_enrollement("enroll")

        self.check_outbox()

    def test_unenroll(self):
        CourseEnrollment.enroll(
            self.student,
            self.course.id
        )
        self.update_enrollement("unenroll")

        self.check_outbox()

    def test_set_beta_role(self):
        url = reverse('bulk_beta_modify_access', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.client.post(url, {'identifiers': self.student.email, 'action': 'add', 'email_students': 'true'})

        self.check_outbox()
