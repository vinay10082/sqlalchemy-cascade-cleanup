import argparse
import sys

from sqlalchemy import select

import config
from cleanup_service import CascadeCleanupService
from database import get_session, init_db
from models import Comment, Post, User


def cmd_init_db(_args: argparse.Namespace) -> None:
    init_db()
    print(f"Database initialized at {config.DATABASE_URI}")


def cmd_seed(_args: argparse.Namespace) -> None:
    with get_session() as session:
        user = User(name="Ada Lovelace", email="ada@example.com")
        post = Post(title="Hello, cascades", body="First post body.", author=user)
        Comment(author_name="Grace Hopper", body="Nice post!", post=post)
        Comment(author_name="Alan Turing", body="Agreed.", post=post)
        session.add(user)
        session.flush()
        print(f"Seeded user {user.id} with 1 post and 2 comments.")


def cmd_list(_args: argparse.Namespace) -> None:
    with get_session() as session:
        users = session.scalars(select(User)).all()
        if not users:
            print("No users found.")
            return
        for user in users:
            print(user)
            for post in user.posts:
                print(f"  {post}")
                for comment in post.comments:
                    print(f"    {comment}")


def cmd_delete_user(args: argparse.Namespace) -> None:
    with get_session() as session:
        user = session.get(User, args.id)
        if user is None:
            print(f"No user with id={args.id}", file=sys.stderr)
            sys.exit(1)
        service = CascadeCleanupService(session)
        service.delete_user(user)
        mode = "soft-deleted" if service.soft_delete_enabled else "hard-deleted"
        print(f"User {args.id} {mode} (cascaded to posts/comments).")


def cmd_delete_post(args: argparse.Namespace) -> None:
    with get_session() as session:
        post = session.get(Post, args.id)
        if post is None:
            print(f"No post with id={args.id}", file=sys.stderr)
            sys.exit(1)
        service = CascadeCleanupService(session)
        service.delete_post(post)
        mode = "soft-deleted" if service.soft_delete_enabled else "hard-deleted"
        print(f"Post {args.id} {mode} (cascaded to comments).")


def cmd_restore_user(args: argparse.Namespace) -> None:
    with get_session() as session:
        user = session.get(User, args.id)
        if user is None:
            print(f"No user with id={args.id}", file=sys.stderr)
            sys.exit(1)
        CascadeCleanupService(session).restore_user(user)
        print(f"User {args.id} restored (cascaded to posts/comments).")


def cmd_purge(args: argparse.Namespace) -> None:
    with get_session() as session:
        service = CascadeCleanupService(session)
        removed = service.purge_soft_deleted(retention_days=args.days)
        print(f"Purged soft-deleted records older than {args.days if args.days is not None else config.SOFT_DELETE_RETENTION_DAYS} day(s): {removed}")


def cmd_prune_orphans(_args: argparse.Namespace) -> None:
    with get_session() as session:
        service = CascadeCleanupService(session)
        removed = service.prune_orphans()
        print(f"Pruned orphaned records: {removed}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Cascading Data Cleanup - SQLAlchemy cascade deletes and soft-delete orchestration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create all tables.").set_defaults(func=cmd_init_db)
    subparsers.add_parser("seed", help="Insert sample User/Post/Comment data.").set_defaults(func=cmd_seed)
    subparsers.add_parser("list", help="List all users with their posts and comments.").set_defaults(func=cmd_list)

    p = subparsers.add_parser("delete-user", help="Delete a user (mode set by ENABLE_SOFT_DELETE).")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete_user)

    p = subparsers.add_parser("delete-post", help="Delete a post (mode set by ENABLE_SOFT_DELETE).")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete_post)

    p = subparsers.add_parser("restore-user", help="Undo a soft-deleted user and its descendants.")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_restore_user)

    p = subparsers.add_parser("purge", help="Hard-delete soft-deleted records past the retention window.")
    p.add_argument("--days", type=int, default=None, help="Override SOFT_DELETE_RETENTION_DAYS.")
    p.set_defaults(func=cmd_purge)

    subparsers.add_parser(
        "prune-orphans", help="Remove rows whose parent record no longer exists."
    ).set_defaults(func=cmd_prune_orphans)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
