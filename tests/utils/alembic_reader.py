import importlib.util
import pathlib
from functools import lru_cache

from alembic.config import Config
from alembic.script import ScriptDirectory

from mealie.db.init_db import ALEMBIC_DIR

ALEMBIC_MIGRATIONS = ALEMBIC_DIR / "versions"


def import_file(module_name: str, file_path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to import {module_name} from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# KH: asks Alembic for the heads instead of taking the newest file in Mealie's versions folder,
# so Küchenhelfer's own migrations (mealie/kh/alembic/versions, on the same chain) count too.
@lru_cache(1)
def alembic_versions():
    script = ScriptDirectory.from_config(Config(str(ALEMBIC_DIR / "alembic.ini")))
    return [{"version_num": head} for head in script.get_heads()]
