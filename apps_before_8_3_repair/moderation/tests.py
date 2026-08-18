from django.test import TestCase

from apps.discussions.models import Comment
from apps.discussions.services import accept_answer, create_root_comment
from apps.moderation.models import ModerationAction, Report
from apps.moderation.services import create_report, set_comment_hidden, set_publication_hidden
from apps.publications.models import Publication
from apps.publications.services import create_publication
from apps.users.models import User


class ModerationServiceTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            nickname="author",
            email="author@example.com",
            password="StrongPass-2026!",
            first_name="Author",
            last_name="User",
            country="RU",
            nationality="RU",
        )
        self.reporter = User.objects.create_user(
            nickname="reporter",
            email="reporter@example.com",
            password="StrongPass-2026!",
            first_name="Reporter",
            last_name="User",
            country="RU",
            nationality="RU",
        )
        self.moderator = User.objects.create_superuser(
            nickname="moderator",
            email="moderator@example.com",
            password="StrongPass-2026!",
            first_name="Mod",
            last_name="User",
            country="RU",
            nationality="RU",
        )
        self.publication = create_publication(
            author=self.author,
            kind=Publication.Type.TOPIC,
            title="Topic",
            content=[{"type": "paragraph", "text": "Question"}],
            community=None,
            tag_names=[],
        )

    def test_duplicate_active_report_is_rejected(self):
        create_report(
            reporter=self.reporter,
            target_type=Report.TargetType.PUBLICATION,
            target=self.publication,
            reason=Report.Reason.SPAM,
        )
        with self.assertRaises(ValueError):
            create_report(
                reporter=self.reporter,
                target_type=Report.TargetType.PUBLICATION,
                target=self.publication,
                reason=Report.Reason.OTHER,
            )

    def test_publication_hide_and_unhide_are_audited(self):
        publication, changed = set_publication_hidden(
            publication=self.publication,
            moderator=self.moderator,
            hidden=True,
            reason="Moderation test",
        )
        self.assertTrue(changed)
        self.assertEqual(publication.visibility, Publication.Visibility.HIDDEN)

        publication, changed = set_publication_hidden(
            publication=publication,
            moderator=self.moderator,
            hidden=False,
        )
        self.assertTrue(changed)
        self.assertEqual(publication.visibility, Publication.Visibility.PUBLISHED)
        self.assertEqual(ModerationAction.objects.count(), 2)

    def test_hiding_accepted_answer_clears_accepted_flag(self):
        answer = create_root_comment(
            publication=self.publication,
            author=self.reporter,
            content=[{"type": "paragraph", "text": "Answer"}],
        )
        accept_answer(answer=answer, actor=self.author)
        answer.refresh_from_db()
        self.assertTrue(answer.is_accepted)

        answer, _ = set_comment_hidden(
            comment=answer,
            moderator=self.moderator,
            hidden=True,
        )
        self.assertEqual(answer.visibility, Comment.Visibility.HIDDEN)
        self.assertFalse(answer.is_accepted)
