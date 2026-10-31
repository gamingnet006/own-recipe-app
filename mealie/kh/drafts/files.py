"""KH: files of drafts in Mealie's data folder: photos and screenshots are checked, turned upright and
stored smaller, like Mealie's recipe images, as DATA_DIR/kh/drafts/<draft id>/original-<n>.webp."""

import io
import shutil
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from pydantic import UUID4

from mealie.core.config import get_app_dirs

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
