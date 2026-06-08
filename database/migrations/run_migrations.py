import importlib
import re
from pathlib import Path


MIGRATION_FILE_PATTERN = re.compile(r"^\d+.*\.py$")
EXCLUDED_FILES = {"__init__.py", "run_migrations.py"}


def discover_migration_modules() -> list[str]:
    migrations_dir = Path(__file__).resolve().parent
    package_name = __package__ or "database.migrations"

    migration_files = sorted(
        (
            path
            for path in migrations_dir.iterdir()
            if path.is_file()
            and path.name not in EXCLUDED_FILES
            and MIGRATION_FILE_PATTERN.match(path.name)
        ),
        key=lambda path: path.name,
    )

    return [f"{package_name}.{path.stem}" for path in migration_files]


def run_all_migrations() -> None:
    for module_name in discover_migration_modules():
        migration_module = importlib.import_module(module_name)
        run = getattr(migration_module, "run", None)
        if run is None or not callable(run):
            raise AttributeError(f"Migration {module_name} must expose callable run()")

        run()

    print("[MIGRATION] all migrations completed")


if __name__ == "__main__":
    run_all_migrations()
