from django.test import TestCase

from apps.discussions.models import Comment, CommentVote
from apps.discussions.services import remove_comment_vote, set_comment_vote
from apps.publications.models import Publication
from apps.users.models import User


class CommentVoteServiceTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            nickname="author",
            email="author@example.com",
            password="test-password-123",
            country="RU",
            nationality="RU",
        )
        self.voter = User.objects.create_user(
            nickname="voter",
            email="voter@example.com",
            password="test-password-123",
            country="RU",
            nationality="RU",
        )
        self.publication = Publication.objects.create(
            author=self.author,
            kind=Publication.Type.TOPIC,
            title="Vote test",
            content=[{"type": "paragraph", "text": "Topic"}],
            content_text="Topic",
        )
        self.comment = Comment.objects.create(
            publication=self.publication,
            author=self.author,
            kind=Comment.Kind.ANSWER,
            content=[{"type": "paragraph", "text": "Answer"}],
            content_text="Answer",
            depth=0,
        )

    def test_upvote_switch_and_remove(self):
        comment, my_vote = set_comment_vote(
            comment=self.comment,
            user=self.voter,
            value=1,
        )
        self.assertEqual(comment.score, 1)
        self.assertEqual(my_vote, 1)
        self.assertEqual(CommentVote.objects.count(), 1)

        comment, my_vote = set_comment_vote(
            comment=comment,
            user=self.voter,
            value=-1,
        )
        self.assertEqual(comment.score, -1)
        self.assertEqual(my_vote, -1)
        self.assertEqual(CommentVote.objects.count(), 1)

        comment = remove_comment_vote(
            comment=comment,
            user=self.voter,
        )
        self.assertEqual(comment.score, 0)
        self.assertEqual(CommentVote.objects.count(), 0)

    def test_put_is_idempotent(self):
        comment, _ = set_comment_vote(
            comment=self.comment,
            user=self.voter,
            value=1,
        )
        comment, _ = set_comment_vote(
            comment=comment,
            user=self.voter,
            value=1,
        )
        self.assertEqual(comment.score, 1)
        self.assertEqual(CommentVote.objects.count(), 1)

    def test_self_vote_is_rejected(self):
        with self.assertRaisesMessage(
            ValueError,
            "You cannot vote for your own comment.",
        ):
            set_comment_vote(
                comment=self.comment,
                user=self.author,
                value=1,
            )
