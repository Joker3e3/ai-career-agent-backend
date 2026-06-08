from sqlalchemy import text

from database.database import engine

COLUMNS = [
    ("input_tokens", "BIGINT"),
    ("output_tokens", "BIGINT"),
    ("total_tokens", "BIGINT"),
    ("model_name", "VARCHAR(100)"),
    ("provider", "VARCHAR(50)"),
]


def column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = :table_name
          AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar() is not None


def run():
    print("[MIGRATION] running 001_add_agent_step_token_fields")

    table_name = "agent_steps"

    with engine.begin() as conn:
        for column_name, column_type in COLUMNS:
            if column_exists(conn, table_name, column_name):
                print(f"[SKIP] {table_name}.{column_name} already exists")
                continue

            conn.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            )
            print(f"[OK] added {table_name}.{column_name} {column_type}")


if __name__ == "__main__":
    run()
