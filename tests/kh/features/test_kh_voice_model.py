"""KH: the voice model (P7.5) is served as it is: the gzip middleware would recompress the 45 MB archive and drop its
Content-Length, so the app's progress bar could not move."""

from pathlib import Path

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Mount

from mealie.routes.spa import SPAStaticFiles


def test_the_voice_model_keeps_its_length_and_is_not_gzipped(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html></html>")
    (tmp_path / "kh-models").mkdir()
    archive = b"\0" * 50_000  # compresses well, so the middleware would gzip it
    (tmp_path / "kh-models" / "model.tar.gz").write_bytes(archive)
    app = Starlette(routes=[Mount("/", SPAStaticFiles(directory=tmp_path, html=True))])
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    with TestClient(app) as client:
        response = client.get("/kh-models/model.tar.gz", headers={"Accept-Encoding": "gzip"})
    assert response.headers["content-length"] == str(len(archive))
    assert response.headers.get("content-encoding") != "gzip"
