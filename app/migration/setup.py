from sqlalchemy import text

from app.core.database import session_scope


def column_exists(session, table_name, column_name):
    sql = """
          SELECT 1
          FROM information_schema.columns
          WHERE table_name = :table
            AND column_name = :column \
          """
    result = session.execute(
        text(sql),
        {"table": table_name, "column": column_name}
    ).fetchone()
    return result is not None


def upgrade():
    with session_scope() as session:
        if not column_exists(session, "article", "website"):
            alter_sql = """
                        ALTER TABLE article
                            ADD COLUMN website VARCHAR(32) \
                        """
            session.execute(text(alter_sql))
        change_tid_type_sql = """
                              ALTER TABLE article ALTER COLUMN tid TYPE BIGINT; \
                              """
        session.execute(text(change_tid_type_sql))
        update_empty_website_sql = """
                                   update article
                                   set website = 'sehuatang'
                                   where website is null; \
                                   """
        session.execute(text(update_empty_website_sql))