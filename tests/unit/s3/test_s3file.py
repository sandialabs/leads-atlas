from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from leads_atlas.s3.s3file import S3File


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_s3_client() -> MagicMock:
    s3 = MagicMock()

    def _download_file(bucket, key, dst, **kwargs):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).touch()

    s3.download_file.side_effect = _download_file
    return s3


def make_file(tmp_path, uri="s3://bucket/path/to/file.txt", **kwargs) -> S3File:
    return S3File(
        uri,
        cache_dir=tmp_path,
        s3_client=make_s3_client(),
        show_progress=False,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Construction and URI parsing
# ---------------------------------------------------------------------------


def test_s3file_parses_bucket_and_key(tmp_path):
    f = make_file(tmp_path)
    assert f.bucket == "bucket"
    assert f.key == "path/to/file.txt"


def test_s3file_rejects_prefix_uri(tmp_path):
    with pytest.raises(ValueError, match="must point to an object"):
        S3File("s3://bucket/path/", cache_dir=tmp_path)


def test_s3file_rejects_bucket_only_uri(tmp_path):
    with pytest.raises(ValueError, match="must point to an object"):
        S3File("s3://bucket", cache_dir=tmp_path)


def test_s3file_local_path_layout(tmp_path):
    f = make_file(tmp_path)
    assert f.local_path == tmp_path / "bucket" / "path" / "to" / "file.txt"


def test_s3file_default_cache_dir():
    f = S3File("s3://bucket/key.txt", s3_client=MagicMock())
    assert f.cache_dir == Path.cwd() / ".s3cache"


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


def test_s3file_exists_false_when_missing(tmp_path):
    f = make_file(tmp_path)
    assert f.exists() is False


def test_s3file_exists_true_when_present(tmp_path):
    f = make_file(tmp_path)
    f.local_path.parent.mkdir(parents=True)
    f.local_path.touch()
    assert f.exists() is True


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


def test_s3file_download_creates_file(tmp_path):
    f = make_file(tmp_path)
    path = f.download()
    assert path.exists()
    assert path == f.local_path


def test_s3file_download_skips_on_cache_hit(tmp_path):
    f = make_file(tmp_path)
    f.local_path.parent.mkdir(parents=True)
    f.local_path.touch()
    f.download()
    f.s3_client.download_file.assert_not_called()


def test_s3file_download_ignores_cache_when_disabled(tmp_path):
    f = make_file(tmp_path, use_cache=False)
    f.local_path.parent.mkdir(parents=True)
    f.local_path.touch()
    f.download()
    f.s3_client.download_file.assert_called_once()


def test_s3file_download_creates_gitignore(tmp_path):
    f = make_file(tmp_path)
    f.download()
    assert (tmp_path / ".gitignore").exists()


# ---------------------------------------------------------------------------
# path property
# ---------------------------------------------------------------------------


def test_s3file_path_property_triggers_download(tmp_path):
    f = make_file(tmp_path)
    assert f.path.exists()


# ---------------------------------------------------------------------------
# s3_client lazy init
# ---------------------------------------------------------------------------


def test_s3file_s3_client_lazy_init(tmp_path):
    f = S3File("s3://bucket/key.txt", cache_dir=tmp_path)
    with patch("leads_atlas.s3.s3file.boto3.client") as mock_client:
        mock_client.return_value = make_s3_client()
        _ = f.s3_client
        _ = f.s3_client
        mock_client.assert_called_once()


def test_s3file_s3_client_uses_injected_client(tmp_path):
    injected = MagicMock()
    f = S3File("s3://bucket/key.txt", cache_dir=tmp_path, s3_client=injected)
    assert f.s3_client is injected


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_s3file_clear_removes_file(tmp_path):
    f = make_file(tmp_path)
    f.download()
    f.clear()
    assert not f.local_path.exists()


def test_s3file_clear_missing_ok(tmp_path):
    f = make_file(tmp_path)
    f.clear(missing_ok=True)  # should not raise


def test_s3file_clear_raises_when_missing_not_ok(tmp_path):
    f = make_file(tmp_path)
    with pytest.raises(FileNotFoundError):
        f.clear(missing_ok=False)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_s3file_context_manager_returns_path(tmp_path):
    f = make_file(tmp_path)
    with f as p:
        assert p.exists()


def test_s3file_context_manager_clears_on_exit(tmp_path):
    f = make_file(tmp_path, clear_on_exit=True)
    with f:
        pass
    assert not f.local_path.exists()


def test_s3file_context_manager_no_clear_by_default(tmp_path):
    f = make_file(tmp_path)
    with f:
        pass
    assert f.local_path.exists()


def test_s3file_context_manager_does_not_suppress_exceptions(tmp_path):
    f = make_file(tmp_path)
    with pytest.raises(RuntimeError):
        with f:
            raise RuntimeError("test error")
