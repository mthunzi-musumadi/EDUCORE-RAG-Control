"""
Migrate Open WebUI SQLite (webui.db) to PostgreSQL
"""
import json
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch

SQLITE_PATH = r"c:\Projects\EDUCORE-RAG-Control\.openwebui_env\Lib\site-packages\open_webui\data\webui.db"
POSTGRES_URL = "postgresql://neondb_owner:npg_WiYfyRLU6dl9@ep-nameless-lab-b4kzjv3t-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Tables ordered by foreign key dependency (parent tables first)
TABLES = [
    "user",
    "auth",
    "group",
    "group_member",
    "folder",
    "file",
    "document",
    "knowledge",
    "knowledge_file",
    "knowledge_directory",
    "model",
    "prompt",
    "prompt_history",
    "tool",
    "function",
    "memory",
    "tag",
    "chat",
    "chat_message",
    "chat_file",
    "shared_chat",
    "access_grant",
    "feedback",
    "config",
]

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(POSTGRES_URL)
pg_cursor = pg_conn.cursor()

for table in TABLES:
    try:
        sqlite_cursor.execute(f'SELECT * FROM "{table}"')
        rows = sqlite_cursor.fetchall()
        if not rows:
            print(f"Skipping empty table: {table}")
            continue

        columns = rows[0].keys()
        col_names = ", ".join([f'"{col}"' for col in columns])
        placeholders = ", ".join(["%s"] * len(columns))

        insert_sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'

        # Get PostgreSQL column data types for boolean mapping
        pg_cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """)
        pg_col_types = {row[0]: row[1] for row in pg_cursor.fetchall()}

        # Convert SQLite types to Python types matching PostgreSQL schema
        data = []
        for row in rows:
            converted_row = []
            for col in columns:
                val = row[col]
                col_type = pg_col_types.get(col, "")
                if col_type == "boolean" and val is not None:
                    val = bool(val)
                elif col_type in ("json", "jsonb") and val is not None:
                    if isinstance(val, (int, float, bool, dict, list)):
                        val = json.dumps(val)
                    elif isinstance(val, str):
                        try:
                            json.loads(val)
                        except Exception:
                            val = json.dumps(val)
                converted_row.append(val)
            data.append(tuple(converted_row))

        execute_batch(pg_cursor, insert_sql, data)
        pg_conn.commit()
        print(f"Successfully migrated {len(data)} rows into {table}")
    except Exception as e:
        pg_conn.rollback()
        print(f"Notice for table {table}: {e}")

sqlite_conn.close()
pg_conn.close()
print("Migration completed successfully!")