"""KH: encodes a multipart/form-data body for POST /api/kh/drafts; the standard library has no encoder."""

from uuid import uuid4


def encode(fields: dict[str, str], images: list[bytes]) -> tuple[bytes, str]:
    """The body for text FIELDS and IMAGES (all sent as the repeated field "images"), and its Content-Type."""
    boundary = uuid4().hex
    body = b""
    for name, value in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += value.encode() + b"\r\n"
    for number, image in enumerate(images, start=1):
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="images"; filename="telegram-{number}.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode()
        body += image + b"\r\n"
    return body + f"--{boundary}--\r\n".encode(), f"multipart/form-data; boundary={boundary}"
