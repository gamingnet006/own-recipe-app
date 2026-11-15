"""KH: video links (P7.2, D5): sites whose links are never fetched, because Kochheft does not download videos or
collect from social media (RECHT.md point 2). The frontend keeps the same list in
kh/app/composables/use-kh-drafts.ts."""

import re
from urllib.parse import urlparse

VIDEO_HOSTS = ("instagram.com", "tiktok.com", "youtube.com", "youtu.be", "facebook.com", "fb.watch")


def is_video_link(url: str) -> bool:
    """Whether URL points at one of VIDEO_HOSTS or a subdomain of it (www.youtube.com, vm.tiktok.com). A link pasted
    with words around it counts by the link in it; a broken address is no video link."""
    if found := re.search(r"https?://\S+", url):
        url = found.group()
    try:
        host = (urlparse(url if "//" in url else f"//{url}").hostname or "").lower()
    except ValueError:  # e.g. a broken IPv6 address
        return False
    return any(host == video or host.endswith(f".{video}") for video in VIDEO_HOSTS)
