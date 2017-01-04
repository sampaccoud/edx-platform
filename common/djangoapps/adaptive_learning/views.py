"""
Adaptive Learning
"""
import calendar
from dateutil import parser
import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location, navigation_index
from xmodule.library_content_module import AdaptiveLibraryContentModule
from xmodule.util.adaptive_learning import AdaptiveLearningConfiguration


@login_required
@ensure_csrf_cookie
def revisions(request):
    """
    Return a JSON list of all revisions for a user. Each revision includes a name, due date, and URL.
    """
    user = request.user

    revisions = _get_pending_revisions(user)
    json_revisions = json.dumps(revisions)

    return HttpResponse(json_revisions)


def _get_pending_revisions(user):
    """
    Returns information about each problem that needs revision for a given user,
    including a display name, the due date of the revision, and a courseware URL.
    """
    # Get all courses:
    courses = modulestore().get_courses()

    # For each course, check if it has meaningful configuration for adaptive learning service:
    pending_reviews = []
    for course in courses:
        if AdaptiveLearningConfiguration.is_meaningful(course.adaptive_learning_configuration):

            # If it does:
            # Obtain list of pending reviews for current `user`:
            pending_reviews_course = AdaptiveLibraryContentModule.fetch_pending_reviews(course, user.id)
            if pending_reviews_course:

                pending_reviews_course = {
                    pending_review['review_question_uid'] or 'dd8da3981378e70aced4': pending_review['next_review_at']
                    for pending_review in pending_reviews_course
                }

                # For each pending review, get corresponding block from modulestore:
                # - Get all Adaptive Content Blocks belonging to course,
                #   then filter children of each block by `block_id`
                #   (`block_id` of child must correspond to "review_question_uid" of a pending review).
                course_key = course.location.course_key
                adaptive_content_blocks = modulestore().get_items(
                    course_key, qualifiers={'category': 'adaptive_library_content'}
                )
                for adaptive_content_block in adaptive_content_blocks:
                    for child in adaptive_content_block.children:
                        block_id = child.block_id
                        if block_id in pending_reviews_course:
                            child_block = adaptive_content_block.get_child(child)
                            # For each corresponding block, get
                            # - url (as shown below),
                            # - name (block.display_name),
                            # - due_date (from pending review)
                            (
                                course_key, chapter, section, vertical_unused,
                                position, final_target_id_unused
                            ) = path_to_location(modulestore(), child)
                            url = reverse(
                                'courseware_position',
                                args=(unicode(course_key), chapter, section, navigation_index(position))
                            )
                            name = child_block.display_name
                            due_date = pending_reviews_course[block_id]
                            pending_reviews.append({
                                'url': url,
                                'name': name,
                                'due_date': calendar.timegm(parser.parse(due_date).timetuple())
                            })

    return pending_reviews
