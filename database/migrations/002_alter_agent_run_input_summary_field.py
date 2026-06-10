from sqlalchemy import text

from database.database import engine


def is_text_type(conn) -> bool:
    result = conn.execute(
        text("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'agent_runs'
          AND column_name = 'input_summary'
        """)
    )

    data_type = result.scalar()

    return data_type == "text"


def run():
    print("[MIGRATION] running 002_change_agent_runs_input_summary_to_text")

    with engine.begin() as conn:
        if is_text_type(conn):
            print("[SKIP] agent_runs.input_summary already TEXT")
            return

        conn.execute(
            text("""
            ALTER TABLE agent_runs
            ALTER COLUMN input_summary TYPE TEXT
            """)
        )

        print("[OK] changed agent_runs.input_summary to TEXT")


if __name__ == "__main__":
    run()