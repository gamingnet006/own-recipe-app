"""KH: files of drafts in Mealie's data folder: photos and screenshots are checked, turned upright and
stored smaller, like Mealie's recipe images, as DATA_DIR/kh/drafts/<draft id>/original-<n>.webp."""

import io
import shutil
from pathlib import Path

import sqlalchemy as sa
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from pydantic import UUID4

from mealie.core.config import get_app_dirs
from mealie.db.db_setup import session_context
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.kh.drafts.models import KhDraft
from mealie.kh.drafts.schemas import DraftStatus
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.recipe.recipe import Recipe

register_heif_opener()  # iPhone photos arrive as HEIC

MAX_SIDE = 2048  # longest side of a stored original, as Mealie stores recipe images (pkgs/img/minify.py)
WEBP_QUALITY = 80  # Mealie's quality for recipe images


def drafts_root() -> Path:
    """Folder of all draft files inside Mealie's data folder, so every backup carries them."""
    return get_app_dirs().DATA_DIR / "kh" / "drafts"


def draft_dir(draft_id: UUID4 | str) -> Path:
    """Folder of one draft's originals."""
    return drafts_root() / str(draft_id)


def original_path(draft_id: UUID4 | str, name: str) -> Path:
    """One stored original; the name comes from the draft row, never from the sender."""
    return draft_dir(draft_id) / name


def prepare_original(data: bytes, max_mb: int) -> Image.Image:
    """Checks that DATA is an image of at most MAX_MB and returns it upright and at most MAX_SIDE pixels.
    Raises ValueError("too_large") or ValueError("not_an_image"); only the content counts, not the name."""
    if len(data) > max_mb * 1024 * 1024:
        raise ValueError("too_large")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            upright = ImageOps.exif_transpose(image)  # phone photos store "rotated" only as EXIF
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("not_an_image") from error
    upright.thumbnail((MAX_SIDE, MAX_SIDE))
    return upright if upright.mode in ("RGB", "RGBA") else upright.convert("RGB")


def store_original(draft_id: UUID4 | str, n: int, image: Image.Image) -> str:
    """Saves a prepared image as original-<n>.webp in the draft's folder and returns the file name."""
    folder = draft_dir(draft_id)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"original-{n}.webp"
    image.save(folder / name, format="WEBP", quality=WEBP_QUALITY)
    return name


def remove_draft_dir(draft_id: UUID4 | str) -> None:
    """Deletes a draft's originals, e.g. when the draft is discarded or its creation failed."""
    shutil.rmtree(draft_dir(draft_id), ignore_errors=True)


def remove_recognition_dir(recipe_id: UUID4 | str | None, repos: AllRepositories) -> None:
    """Deletes the folder Mealie created for the recognized recipe's image (DATA_DIR/recipes/<id>), but only
    while no recipe with this ID exists; REPOS must see every group, so no other household's recipe counts
    as missing."""
    if recipe_id is None or repos.recipes.get_one(recipe_id, "id") is not None:
        return
    shutil.rmtree(Recipe.directory_from_id(recipe_id), ignore_errors=True)


def sweep_orphans() -> None:
    """Daily cleanup: origins whose recipe is gone (SQLite does not enforce ON DELETE CASCADE, Postgres does)
    and draft folders without a draft. Mealie's own recipe folders stay untouched."""
    with session_context() as session:
        recipe_exists = sa.exists().where(RecipeModel.id == KhDraft.recipe_id)
        session.execute(
            sa.delete(KhDraft).where(
                KhDraft.status == DraftStatus.approved, KhDraft.recipe_id.is_not(None), ~recipe_exists
            )
        )
        session.commit()
        known = {str(draft_id) for draft_id in session.execute(sa.select(KhDraft.id)).scalars()}
    root = drafts_root()
    if not root.is_dir():
        return
    for folder in root.iterdir():
        if folder.is_dir() and folder.name not in known:
            shutil.rmtree(folder, ignore_errors=True)
