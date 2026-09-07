from sqlalchemy import text

from app.database.session import get_db


def test_get_db_returns_valid_session():
    db_generator = get_db()
    db = next(db_generator)

    try:
        result = db.execute(text("SELECT 1"))

        assert result.scalar() == 1
    finally:
        db_generator.close()