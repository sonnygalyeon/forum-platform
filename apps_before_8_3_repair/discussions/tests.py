from django.test import TestCase

from apps.discussions.models import Comment, CommentVote
from apps.discussions.services import (
    accept_answer,
    create_root_comment,
    remove_comment_vote,
    set_comment_vote,
    unaccept_answer,
)
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

class AcceptedAnswerServiceTests(TestCase):
    def setUp(self):
        self.topic_author = User.objects.create_user(
            nickname="topic_author",
            email="topic-author@example.com",
            password="test-password-123",
            country="RU",
            nationality="RU",
        )
        self.first_author = User.objects.create_user(
            nickname="first_answer",
            email="first-answer@example.com",
            password="test-password-123",
            country="RU",
            nationality="RU",
        )
        self.second_author = User.objects.create_user(
            nickname="second_answer",
            email="second-answer@example.com",
            password="test-password-123",
            country="RU",
            nationality="RU",
        )
        self.topic = Publication.objects.create(
            author=self.topic_author,
            kind=Publication.Type.TOPIC,
            title="Accepted answer test",
            content=[{"type": "paragraph", "text": "Question"}],
            content_text="Question",
        )
        self.first = Comment.objects.create(
            publication=self.topic,
            author=self.first_author,
            kind=Comment.Kind.ANSWER,
            content=[{"type": "paragraph", "text": "First"}],
            content_text="First",
            depth=0,
        )
        self.second = Comment.objects.create(
            publication=self.topic,
            author=self.second_author,
            kind=Comment.Kind.ANSWER,
            content=[{"type": "paragraph", "text": "Second"}],
            content_text="Second",
            depth=0,
        )

    def test_topic_author_can_accept_and_switch_answer(self):
        answer = accept_answer(
            answer=self.first,
            actor=self.topic_author,
        )
        self.assertTrue(answer.is_accepted)

        answer = accept_answer(
            answer=self.second,
            actor=self.topic_author,
        )
        self.assertTrue(answer.is_accepted)

        self.first.refresh_from_db()
        self.assertFalse(self.first.is_accepted)
        self.assertEqual(
            Comment.objects.filter(
                publication=self.topic,
                is_accepted=True,
            ).count(),
            1,
        )

    def test_unaccept_is_idempotent(self):
        answer = accept_answer(
            answer=self.first,
            actor=self.topic_author,
        )
        answer = unaccept_answer(
            answer=answer,
            actor=self.topic_author,
        )
        self.assertFalse(answer.is_accepted)

        answer = unaccept_answer(
            answer=answer,
            actor=self.topic_author,
        )
        self.assertFalse(answer.is_accepted)

    def test_non_topic_author_cannot_accept(self):
        with self.assertRaisesMessage(
            PermissionError,
            "Only the topic author can accept an answer.",
        ):
            accept_answer(
                answer=self.first,
                actor=self.second_author,
            )

    def test_reply_cannot_be_accepted(self):
        reply = Comment.objects.create(
            publication=self.topic,
            author=self.second_author,
            parent=self.first,
            kind=Comment.Kind.REPLY,
            content=[{"type": "paragraph", "text": "Reply"}],
            content_text="Reply",
            depth=1,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Only a root topic answer can be accepted.",
        ):
            accept_answer(
                answer=reply,
                actor=self.topic_author,
            )



class BlockedDiscussionInteractionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            nickname="BlockOwner",
            email="block-owner@example.com",
            password="test-pass-12345",
            first_name="Owner",
            last_name="Example",
            country="DE",
            nationality="DE",
        )
        self.actor = User.objects.create_user(
            nickname="BlockActor",
            email="block-actor@example.com",
            password="test-pass-12345",
            first_name="Actor",
            last_name="Example",
            country="DE",
            nationality="DE",
        )
        self.publication = Publication.objects.create(
            author=self.owner,
            kind=Publication.Type.TOPIC,
            title="Blocking test",
            content=[{"type": "paragraph", "text": "Question"}],
            content_text="Question",
        )

    def test_block_prevents_new_root_answer(self):
        from apps.social.services import block_user

        block_user(blocker=self.owner, blocked=self.actor)

        with self.assertRaises(ValueError):
            create_root_comment(
                publication=self.publication,
                author=self.actor,
                content=[{"type": "paragraph", "text": "Answer"}],
            )

    def test_block_prevents_vote_after_comment_exists(self):
        from apps.social.services import block_user

        comment = create_root_comment(
            publication=self.publication,
            author=self.actor,
            content=[{"type": "paragraph", "text": "Answer"}],
        )
        block_user(blocker=self.owner, blocked=self.actor)

        with self.assertRaises(ValueError):
            set_comment_vote(
                comment=comment,
                user=self.owner,
                value=1,
            )
