from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from lexicon.config import get_settings
from lexicon.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Migrations always run as the admin/owner role, never the ADR-0002-
# restricted application role — that role is granted only INSERT/SELECT on
# the audit tables and could not run these migrations even if pointed at
# them. Falls back to database_url only as a local single-role dev
# convenience (docker-compose's default POSTGRES_USER is already a
# superuser); production deployments should set DATABASE_ADMIN_URL
# explicitly. See ADR-0002 and migrations/0002_adr0002_app_role.py.
settings = get_settings()
admin_url = settings.database_admin_url or settings.database_url
config.set_main_option("sqlalchemy.url", admin_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
