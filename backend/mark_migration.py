#!/usr/bin/env python3
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE tablename = 'alembic_version'"
    ))
    if result.fetchone():
        print('alembic_version table exists')
    else:
        print('Creating alembic_version table...')
        conn.execute(text('''
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        '''))
        conn.commit()
        print('Created alembic_version table')

    try:
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001_initial')"))
        conn.commit()
        print('Inserted 001_initial')
    except Exception as e:
        print(f'Insert result: {e}')
print('Done')
