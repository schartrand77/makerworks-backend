import asyncio
import os

import click

from alembic import command
from alembic.config import Config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALEMBIC_INI = os.path.join(PROJECT_ROOT, "alembic.ini")


@click.group()
def cli() -> None:
    """MakerWorks command line interface."""
    pass


@cli.group()
def update() -> None:
    """Update various system components."""
    pass


@update.command()
@click.argument("revision", default="head")
def alembic(revision: str) -> None:
    """Run Alembic migrations up to REVISION."""
    cfg = Config(ALEMBIC_INI)
    command.upgrade(cfg, revision)
    click.echo(f"✅ Alembic upgraded to {revision}.")


@cli.group()
def db() -> None:
    """Database utilities."""
    pass


@db.command()
def init() -> None:
    """Create all database tables."""
    from app.init_db import init_models

    asyncio.run(init_models())
    click.echo("✅ Database tables created.")


@db.command()
def drop() -> None:
    """Drop all database tables."""
    from app.drop_db import drop_all

    asyncio.run(drop_all())
    click.echo("✅ Database tables dropped.")


@db.command()
def subset() -> None:
    """Create subset of tables (User, Filament)."""
    from app.init_subset import create_subset

    asyncio.run(create_subset())
    click.echo("✅ Subset tables created.")


@cli.group()
def users() -> None:
    """Manage users."""
    pass


@users.command("list")
def list_users_cmd() -> None:
    """List all users."""
    from app.scripts.user_role import list_users

    asyncio.run(list_users())


@users.command("change-role")
@click.option("--email", required=True, help="User email")
@click.option(
    "--role",
    type=click.Choice(["admin", "user"], case_sensitive=False),
    required=True,
    help="New role",
)
def change_role(email: str, role: str) -> None:
    """Change a user's role."""
    from app.scripts.user_role import change_user_role

    asyncio.run(change_user_role(email, role))


@cli.group()
def seed() -> None:
    """Seed initial data."""
    pass


@seed.command("filaments")
def seed_filaments_cmd() -> None:
    """Seed sample filaments."""
    from scripts.seed_filaments import seed_filaments

    asyncio.run(seed_filaments())
    click.echo("✅ Filaments seeded.")


if __name__ == "__main__":
    cli()
