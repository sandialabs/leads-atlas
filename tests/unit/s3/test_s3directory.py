from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from leads_atlas.s3.s3directory import (
    S3Directory,
    _destination_for_key,
    _listing_prefix,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_s3_client(keys: list[str] | None = None) -> MagicMock:
    s3 = MagicMock()

    def _download_file(bucket, key, dst, **kwargs):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).touch()

    s3.download_file.side_effect = _download_file

    objects = [{"Key": k, "Size": 10} for k in (keys or [])]
    page = {"Contents": objects}
    paginator = MagicMock()
    paginator.paginate.return_value = [page]
    s3.get_paginator.return_value = paginator

    return s3


def make_dir(
    tmp_path, keys: list[str] | None = None, uri="s3://bucket/data", **kwargs
) -> S3Directory:
    return S3Directory(
        uri,
        cache_dir=tmp_path,
        s3_client=make_s3_client(keys),
        show_progress=False,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# _listing_prefix
# ---------------------------------------------------------------------------


def test_listing_prefix_empty():
    assert _listing_prefix("") == ""


def test_listing_prefix_basic():
    assert _listing_prefix("data") == "data/"


def test_listing_prefix_trailing_slash_normalised():
    assert _listing_prefix("data/") == "data/"


# ---------------------------------------------------------------------------
# _destination_for_key
# ---------------------------------------------------------------------------


def test_destination_for_key_strips_listing_prefix(tmp_path):
    result = _destination_for_key(
        local_dir=tmp_path, key="data/a.csv", listing_prefix="data/"
    )
    assert result == tmp_path / "a.csv"


def test_destination_for_key_empty_listing_prefix(tmp_path):
    result = _destination_for_key(local_dir=tmp_path, key="a.csv", listing_prefix="")
    assert result == tmp_path / "a.csv"


def test_destination_for_key_nested_key(tmp_path):
    result = _destination_for_key(
        local_dir=tmp_path, key="data/sub/a.csv", listing_prefix="data/"
    )
    assert result == tmp_path / "sub" / "a.csv"


# ---------------------------------------------------------------------------
# Construction and URI parsing
# ---------------------------------------------------------------------------


def test_s3directory_parses_bucket_and_prefix(tmp_path):
    d = make_dir(tmp_path)
    assert d.bucket == "bucket"
    assert d.prefix == "data"


def test_s3directory_strips_trailing_slash_from_prefix(tmp_path):
    d = make_dir(tmp_path, uri="s3://bucket/data/")
    assert d.prefix == "data"


def test_s3directory_local_dir_layout(tmp_path):
    d = make_dir(tmp_path)
    assert d.local_dir == tmp_path / "bucket" / "data"


def test_s3directory_default_cache_dir():
    d = S3Directory("s3://bucket/data", s3_client=MagicMock())
    assert d.cache_dir == Path.cwd() / ".s3cache"


def test_s3directory_bucket_root_uri(tmp_path):
    d = make_dir(tmp_path, keys=["a.csv"], uri="s3://bucket")
    assert d.prefix == ""
    d.download()
    assert (d.local_dir / "a.csv").exists()


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


def test_s3directory_download_creates_files(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv", "data/b.csv"])
    d.download()
    assert (d.local_dir / "a.csv").exists()
    assert (d.local_dir / "b.csv").exists()


def test_s3directory_download_returns_local_dir(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    assert d.download() == d.local_dir


def test_s3directory_download_skips_cached_files(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    d.local_dir.mkdir(parents=True)
    (d.local_dir / "a.csv").touch()
    d.download()
    d.s3_client.download_file.assert_not_called()


def test_s3directory_download_ignores_cache_when_disabled(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"], use_cache=False)
    d.local_dir.mkdir(parents=True)
    (d.local_dir / "a.csv").touch()
    d.download()
    d.s3_client.download_file.assert_called_once()


def test_s3directory_download_creates_gitignore(tmp_path):
    d = make_dir(tmp_path, keys=[])
    d.download()
    assert (tmp_path / ".gitignore").exists()


def test_s3directory_download_allowlist(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv", "data/b.json"], allowlist=["*.csv"])
    d.download()
    assert (d.local_dir / "a.csv").exists()
    assert not (d.local_dir / "b.json").exists()


def test_s3directory_download_blocklist(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv", "data/b.json"], blocklist=["*.json"])
    d.download()
    assert (d.local_dir / "a.csv").exists()
    assert not (d.local_dir / "b.json").exists()


# ---------------------------------------------------------------------------
# path property
# ---------------------------------------------------------------------------


def test_s3directory_path_property_triggers_download(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    assert (d.path / "a.csv").exists()


# ---------------------------------------------------------------------------
# iter_objects
# ---------------------------------------------------------------------------


def test_s3directory_iter_objects_returns_all(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv", "data/b.csv"])
    assert len(d.iter_objects()) == 2


# ---------------------------------------------------------------------------
# s3_client lazy init
# ---------------------------------------------------------------------------


def test_s3directory_s3_client_lazy_init(tmp_path):
    d = S3Directory("s3://bucket/data", cache_dir=tmp_path)
    with patch("leads_atlas.s3.s3directory.boto3.client") as mock_client:
        mock_client.return_value = make_s3_client()
        _ = d.s3_client
        _ = d.s3_client
        mock_client.assert_called_once()


def test_s3directory_s3_client_uses_injected_client(tmp_path):
    injected = MagicMock()
    d = S3Directory("s3://bucket/data", cache_dir=tmp_path, s3_client=injected)
    assert d.s3_client is injected


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_s3directory_clear_removes_local_dir(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    d.download()
    d.clear()
    assert not d.local_dir.exists()


def test_s3directory_clear_missing_ok(tmp_path):
    d = make_dir(tmp_path, keys=[])
    d.clear(missing_ok=True)  # should not raise


def test_s3directory_clear_raises_when_missing_not_ok(tmp_path):
    d = make_dir(tmp_path, keys=[])
    with pytest.raises(FileNotFoundError):
        d.clear(missing_ok=False)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_s3directory_context_manager_returns_path(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    with d as p:
        assert (p / "a.csv").exists()


def test_s3directory_context_manager_clears_on_exit(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"], clear_on_exit=True)
    with d:
        pass
    assert not d.local_dir.exists()


def test_s3directory_context_manager_no_clear_by_default(tmp_path):
    d = make_dir(tmp_path, keys=["data/a.csv"])
    with d:
        pass
    assert d.local_dir.exists()


def test_s3directory_context_manager_does_not_suppress_exceptions(tmp_path):
    d = make_dir(tmp_path, keys=[])
    with pytest.raises(RuntimeError):
        with d:
            raise RuntimeError("test error")
