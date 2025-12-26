import os
from urllib.parse import quote

import pytest

from af.cli import make_local


def test_replace_image_links_downloads_and_rewrites(tmp_path, monkeypatch):
    input_md = tmp_path / "doc.md"
    output_md = tmp_path / "out.md"
    media_dir = tmp_path / "media"

    input_md.write_text(
        "[![preview](https://example.com/pic.jpg)](https://example.com/full)\n"
        "[![preview](https://example.com/pic.webp)](https://example.com/pic.webp)\n"
        "![plain](https://example.com/plain.png)\n",
        encoding="utf-8",
    )

    calls = []

    def fake_download(url, destination):
        calls.append((url, destination))
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as f:
            f.write(b"data")

    monkeypatch.setattr(make_local, "download_image", fake_download)

    make_local.replace_image_links(
        str(input_md), str(output_md), str(media_dir), force=False
    )

    content = output_md.read_text(encoding="utf-8")

    expected_first = f"[![preview]({quote(str(media_dir / 'pic.jpg'))})](https://example.com/full)"
    expected_second = f"![preview]({quote(str(media_dir / 'pic.jpg'))})"
    expected_third = f"![plain]({quote(str(media_dir / 'plain.png'))})"

    assert expected_first in content
    assert expected_second in content
    assert expected_third in content
    assert calls == [
        ("https://example.com/pic.jpg", os.path.join(str(media_dir), "pic.jpg")),
        ("https://example.com/pic.webp", os.path.join(str(media_dir), "pic.webp")),
        ("https://example.com/plain.png", os.path.join(str(media_dir), "plain.png")),
    ]
    assert (media_dir / "pic.jpg").is_file()
    assert (media_dir / "pic.webp").is_file()
    assert (media_dir / "plain.png").is_file()


def test_replace_image_links_skips_local_images(tmp_path, monkeypatch):
    input_md = tmp_path / "doc.md"
    output_md = tmp_path / "out.md"
    media_dir = tmp_path / "media"
    local_image = f"{media_dir}/existing.png"

    input_md.write_text(f"![local]({local_image})", encoding="utf-8")

    download_calls = []
    monkeypatch.setattr(make_local, "download_image", lambda *args, **kwargs: download_calls.append(args))

    make_local.replace_image_links(
        str(input_md), str(output_md), str(media_dir), force=False
    )

    assert output_md.read_text(encoding="utf-8") == f"![local]({local_image})"
    assert download_calls == []


def test_replace_image_links_errors_when_output_exists_without_force(tmp_path):
    input_md = tmp_path / "doc.md"
    output_md = tmp_path / "out.md"
    media_dir = tmp_path / "media"

    input_md.write_text("![alt](https://example.com/image.png)", encoding="utf-8")
    output_md.write_text("existing", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Output file already exists"):
        make_local.replace_image_links(
            str(input_md), str(output_md), str(media_dir), force=False
        )
