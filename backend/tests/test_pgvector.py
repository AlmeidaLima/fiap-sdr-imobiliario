from sqlalchemy import text

from app.database.session import engine


def test_pgvector_extension_is_enabled():
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT extname
                FROM pg_extension
                WHERE extname = 'vector'
                """
            )
        )

        assert result.scalar() == "vector"