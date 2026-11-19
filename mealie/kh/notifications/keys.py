"""KH: the server's VAPID key pair for web push (D75). It is made on first use and kept in the data folder
(<data>/kh/vapid.json, readable only by the app), never in the repo or in .env."""

import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid02
from py_vapid.utils import b64urlencode

from mealie.core.config import get_app_dirs


def _key_file():
    return get_app_dirs().DATA_DIR / "kh" / "vapid.json"


def _store_new_key() -> int:
    """Makes a key pair, stores its private number and returns it. The file is created with mode 0600."""
    vapid = Vapid02()
    vapid.generate_keys()
    number = vapid.private_key.private_numbers().private_value  # type: ignore[union-attr]
    path = _key_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump({"private": number}, handle)
    return number


@lru_cache
def get_vapid() -> Vapid02:
    """The key pair, loaded from the data folder or made on first use."""
    try:
        number = int(json.loads(_key_file().read_text())["private"])
    except FileNotFoundError, ValueError, KeyError:
        number = _store_new_key()
    return Vapid02(ec.derive_private_key(number, ec.SECP256R1()))


def public_key() -> str:
    """The public key in the form the browser's pushManager.subscribe wants (URL-safe base64, uncompressed point)."""
    raw = get_vapid().public_key.public_bytes(  # type: ignore[union-attr]
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return b64urlencode(raw)
