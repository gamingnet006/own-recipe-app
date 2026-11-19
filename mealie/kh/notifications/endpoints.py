"""KH: which push-service addresses a device may register (D75). The server POSTs to a stored endpoint, so only the
known push services are accepted; anything else would let a signed-in person make the server call any address."""

from urllib.parse import urlsplit

PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com")
PUSH_SUFFIXES = (".push.apple.com", ".notify.windows.com")


def is_push_endpoint(url: str) -> bool:
    """True for an https address on a push service's host: no user info, no explicit port, no odd characters."""
    if not url.isprintable() or " " in url:
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username is not None or parts.password is not None or port is not None:
        return False
    return host in PUSH_HOSTS or host.endswith(PUSH_SUFFIXES)
