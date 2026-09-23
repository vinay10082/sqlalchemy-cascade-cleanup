from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from models import Comment, Post, User


class CascadeCleanupService:
    """Orchestrates referential-integrity-safe deletion of Users -> Posts -> Comments.

    Hard deletes rely on the ORM's ``cascade="all, delete-orphan"`` relationships
    (and DB-level ``ON DELETE CASCADE``) to remove dependents automatically.
    Soft deletes have no such DB support, so this service walks the tree itself.
    """

    def __init__(self, session: Session, enable_soft_delete: bool | None = None):
        self.session = session
        self.soft_delete_enabled = (
            config.ENABLE_SOFT_DELETE if enable_soft_delete is None else enable_soft_delete
        )

    # -- deletion -----------------------------------------------------

    def delete_user(self, user: User) -> None:
        """Delete a user, honoring the ENABLE_SOFT_DELETE setting."""
        if self.soft_delete_enabled:
            self._soft_delete_user_cascade(user)
        else:
            self.session.delete(user)

    def delete_post(self, post: Post) -> None:
        if self.soft_delete_enabled:
            self._soft_delete_post_cascade(post)
        else:
            self.session.delete(post)

    def delete_comment(self, comment: Comment) -> None:
        if self.soft_delete_enabled:
            comment.soft_delete()
        else:
            self.session.delete(comment)

    def _soft_delete_user_cascade(self, user: User) -> None:
        user.soft_delete()
        for post in user.posts:
            self._soft_delete_post_cascade(post)

    def _soft_delete_post_cascade(self, post: Post) -> None:
        post.soft_delete()
        for comment in post.comments:
            comment.soft_delete()

    # -- restoration ----------------------------------------------------

    def restore_user(self, user: User) -> None:
        user.restore()
        for post in user.posts:
            post.restore()
            for comment in post.comments:
                comment.restore()

    # -- pruning ----------------------------------------------------------

    def purge_soft_deleted(self, retention_days: int | None = None) -> dict[str, int]:
        """Hard-delete records that were soft-deleted longer ago than the retention
        window. Deleting a soft-deleted user cascades (via the ORM relationship) to
        its posts and comments, even if those were never individually soft-deleted.
        """
        days = config.SOFT_DELETE_RETENTION_DAYS if retention_days is None else retention_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed = {"users": 0, "posts": 0, "comments": 0}

        stale_users = self.session.scalars(
            select(User).where(User.deleted_at.is_not(None), User.deleted_at <= cutoff)
        ).all()
        for user in stale_users:
            removed["posts"] += len(user.posts)
            removed["comments"] += sum(len(post.comments) for post in user.posts)
            self.session.delete(user)
        removed["users"] = len(stale_users)

        # Posts whose parent user is still alive but the post itself is stale.
        stale_posts = self.session.scalars(
            select(Post).where(
                Post.deleted_at.is_not(None),
                Post.deleted_at <= cutoff,
                ~Post.user_id.in_(select(User.id).where(User.deleted_at.is_not(None))),
            )
        ).all()
        for post in stale_posts:
            removed["comments"] += len(post.comments)
            self.session.delete(post)
        removed["posts"] += len(stale_posts)

        return removed

    def prune_orphans(self) -> dict[str, int]:
        """Remove rows whose parent no longer exists (data-integrity cleanup, useful
        when rows were inserted outside the ORM/without FK enforcement)."""
        removed = {"posts": 0, "comments": 0}

        orphan_posts = self.session.scalars(
            select(Post).where(~Post.user_id.in_(select(User.id)))
        ).all()
        for post in orphan_posts:
            removed["comments"] += len(post.comments)
            self.session.delete(post)
        removed["posts"] = len(orphan_posts)

        orphan_comments = self.session.scalars(
            select(Comment).where(~Comment.post_id.in_(select(Post.id)))
        ).all()
        for comment in orphan_comments:
            self.session.delete(comment)
        removed["comments"] += len(orphan_comments)

        return removed
