from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from leads_atlas.s3.s3utils import (
    as_patterns,
    ensure_gitignore,
    fetch_or_download,
    format_s3_location,
    head_size_bytes,
    list_s3_objects,
    matches_globs,
    parse_s3_uri,
    s3_prefix_to_local_dir,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_s3_client(objects: list[dict] | None = None) -> MagicMock:
    s3 = MagicMock()

    def _download_file(bucket, key, dst, **kwargs):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).touch()

    s3.download_file.side_effect = _download_file

    page = {"Contents": objects or []}
    paginator = MagicMock()
    paginator.paginate.return_value = [page]
    s3.get_paginator.return_value = paginator

    return s3


# ---------------------------------------------------------------------------
# parse_s3_uri
# ---------------------------------------------------------------------------


def test_parse_s3_uri_basic():
    loc = parse_s3_uri("s3://my-bucket/path/to/key")
    assert loc.bucket == "my-bucket"
    assert loc.key == "path/to/key"


def test_parse_s3_uri_bucket_root():
    loc = parse_s3_uri("s3://my-bucket")
    assert loc.bucket == "my-bucket"
    assert loc.key == ""


def test_parse_s3_uri_strips_leading_slash():
    loc = parse_s3_uri("s3://my-bucket/key")
    assert loc.key == "key"


def test_parse_s3_uri_wrong_scheme():
    with pytest.raises(ValueError, match="Not an s3 uri"):
        parse_s3_uri("https://bucket/key")


def test_parse_s3_uri_missing_bucket():
    with pytest.raises(ValueError, match="Missing bucket"):
        parse_s3_uri("s3:///key")


# ---------------------------------------------------------------------------
# ensure_gitignore
# ---------------------------------------------------------------------------


def test_ensure_gitignore_creates_dir_and_file(tmp_path):
    cache = tmp_path / "cache"
    ensure_gitignore(cache)
    assert cache.is_dir()
    assert (cache / ".gitignore").exists()
    assert "*" in (cache / ".gitignore").read_text()


def test_ensure_gitignore_does_not_overwrite_existing(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / ".gitignore").write_text("custom")
    ensure_gitignore(cache)
    assert (cache / ".gitignore").read_text() == "custom"


def test_ensure_gitignore_idempotent(tmp_path):
    cache = tmp_path / "cache"
    ensure_gitignore(cache)
    ensure_gitignore(cache)
    assert (cache / ".gitignore").exists()


# ---------------------------------------------------------------------------
# format_s3_location
# ---------------------------------------------------------------------------


def test_format_s3_location_nested_key():
    assert format_s3_location("bucket", "a/b/file.txt") == "file.txt (s3://bucket/a/b)"


def test_format_s3_location_top_level_key():
    assert format_s3_location("bucket", "file.txt") == "file.txt (s3://bucket)"


# ---------------------------------------------------------------------------
# head_size_bytes
# ---------------------------------------------------------------------------


def test_head_size_bytes_returns_size():
    s3 = MagicMock()
    s3.head_object.return_value = {"ContentLength": 1234}
    assert head_size_bytes(s3, bucket="b", key="k") == 1234


def test_head_size_bytes_returns_none_if_no_content_length():
    s3 = MagicMock()
    s3.head_object.return_value = {}
    assert head_size_bytes(s3, bucket="b", key="k") is None


def test_head_size_bytes_returns_none_on_client_error():
    s3 = MagicMock()
    s3.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": ""}}, "HeadObject"
    )
    assert head_size_bytes(s3, bucket="b", key="k") is None


# ---------------------------------------------------------------------------
# as_patterns
# ---------------------------------------------------------------------------


def test_as_patterns_none():
    assert as_patterns(None) == []


def test_as_patterns_string():
    assert as_patterns("*.csv") == ["*.csv"]


def test_as_patterns_list():
    assert as_patterns(["*.csv", "*.json"]) == ["*.csv", "*.json"]


# ---------------------------------------------------------------------------
# matches_globs
# ---------------------------------------------------------------------------


def test_matches_globs_no_filters():
    assert matches_globs("a/b.txt", allowlist=[], blocklist=[]) is True


def test_matches_globs_allowlist_match():
    assert matches_globs("a/b.csv", allowlist=["*.csv"], blocklist=[]) is True


def test_matches_globs_allowlist_no_match():
    assert matches_globs("a/b.txt", allowlist=["*.csv"], blocklist=[]) is False


def test_matches_globs_blocklist_match():
    assert matches_globs("a/b.txt", allowlist=[], blocklist=["*.txt"]) is False


def test_matches_globs_blocklist_no_match():
    assert matches_globs("a/b.csv", allowlist=[], blocklist=["*.txt"]) is True


def test_matches_globs_allowlist_and_blocklist_both_match():
    assert matches_globs("a/b.csv", allowlist=["*.csv"], blocklist=["*.csv"]) is False


def test_matches_globs_double_star_wildcard():
    assert (
        matches_globs("deep/nested/file.csv", allowlist=["**/*.csv"], blocklist=[])
        is True
    )


# ---------------------------------------------------------------------------
# list_s3_objects
# ---------------------------------------------------------------------------


def test_list_s3_objects_returns_objects_under_prefix():
    s3 = make_s3_client(
        [{"Key": "data/a.csv", "Size": 10}, {"Key": "data/b.csv", "Size": 10}]
    )
    result = list_s3_objects(s3=s3, bucket="b", prefix="data")
    assert [o["Key"] for o in result] == ["data/a.csv", "data/b.csv"]


def test_list_s3_objects_skips_directory_markers():
    s3 = make_s3_client(
        [{"Key": "data/", "Size": 0}, {"Key": "data/a.csv", "Size": 10}]
    )
    result = list_s3_objects(s3=s3, bucket="b", prefix="data")
    assert all(not o["Key"].endswith("/") for o in result)


def test_list_s3_objects_allowlist_filtering():
    s3 = make_s3_client(
        [{"Key": "data/a.csv", "Size": 10}, {"Key": "data/b.json", "Size": 10}]
    )
    result = list_s3_objects(s3=s3, bucket="b", prefix="data", allowlist=["*.csv"])
    assert len(result) == 1
    assert result[0]["Key"] == "data/a.csv"


def test_list_s3_objects_blocklist_filtering():
    s3 = make_s3_client(
        [{"Key": "data/a.csv", "Size": 10}, {"Key": "data/b.json", "Size": 10}]
    )
    result = list_s3_objects(s3=s3, bucket="b", prefix="data", blocklist=["*.json"])
    assert len(result) == 1
    assert result[0]["Key"] == "data/a.csv"


def test_list_s3_objects_empty_prefix():
    s3 = make_s3_client([{"Key": "a.csv", "Size": 10}])
    result = list_s3_objects(s3=s3, bucket="b", prefix="")
    assert result[0]["Key"] == "a.csv"


# ---------------------------------------------------------------------------
# s3_prefix_to_local_dir
# ---------------------------------------------------------------------------


def test_s3_prefix_to_local_dir_with_prefix(tmp_path):
    result = s3_prefix_to_local_dir(
        cache_dir=tmp_path, bucket="bucket", prefix="data/sub"
    )
    assert result == tmp_path / "bucket" / "data" / "sub"


def test_s3_prefix_to_local_dir_empty_prefix(tmp_path):
    result = s3_prefix_to_local_dir(cache_dir=tmp_path, bucket="bucket", prefix="")
    assert result == tmp_path / "bucket"


def test_s3_prefix_to_local_dir_trailing_slash_stripped(tmp_path):
    result = s3_prefix_to_local_dir(cache_dir=tmp_path, bucket="bucket", prefix="data/")
    assert result == tmp_path / "bucket" / "data"


# ---------------------------------------------------------------------------
# fetch_or_download
# ---------------------------------------------------------------------------


def test_fetch_or_download_downloads_when_file_missing(tmp_path):
    s3 = make_s3_client()
    dst = tmp_path / "bucket" / "key.txt"
    fetch_or_download(
        s3=s3, bucket="bucket", key="key.txt", dst=dst, show_progress=False
    )
    s3.download_file.assert_called_once()
    assert dst.exists()


def test_fetch_or_download_skips_download_on_cache_hit(tmp_path):
    s3 = make_s3_client()
    dst = tmp_path / "key.txt"
    dst.touch()
    fetch_or_download(
        s3=s3,
        bucket="bucket",
        key="key.txt",
        dst=dst,
        use_cache=True,
        show_progress=False,
    )
    s3.download_file.assert_not_called()


def test_fetch_or_download_redownloads_when_use_cache_false(tmp_path):
    s3 = make_s3_client()
    dst = tmp_path / "key.txt"
    dst.touch()
    fetch_or_download(
        s3=s3,
        bucket="bucket",
        key="key.txt",
        dst=dst,
        use_cache=False,
        show_progress=False,
    )
    s3.download_file.assert_called_once()


def test_fetch_or_download_returns_dst_path(tmp_path):
    s3 = make_s3_client()
    dst = tmp_path / "key.txt"
    result = fetch_or_download(
        s3=s3, bucket="bucket", key="key.txt", dst=dst, show_progress=False
    )
    assert result == dst
