from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database.base import Base

# Importa os models para registrá-los no Base.metadata.
# Novos models deverão ser importados aqui futuramente.
from app.models.property import Property  # noqa: F401
from app.models.property_embedding import PropertyEmbedding  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.appointment import Appointment  # noqa: F401

# Objeto de configuração do Alembic.
config = context.config

# Utiliza a mesma DATABASE_URL configurada pela aplicação.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

# Configura o logging definido no alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata utilizada pelo Alembic para detectar alterações nos models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Executa migrations no modo offline.

    Nesse modo, o Alembic não cria uma conexão direta com o banco.
    Os comandos SQL são gerados utilizando apenas a URL configurada.
    """
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa migrations no modo online.

    Nesse modo, o Alembic cria uma conexão com o banco de dados
    e executa as migrations diretamente.
    """
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
