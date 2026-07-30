from __future__ import annotations

import os
import shutil
from pathlib import Path

import boto3
from tqdm.auto import tqdm

from leads_atlas.s3.s3utils import (
    as_patterns,
    ensure_gitignore,
    fetch_or_download,
    list_s3_objects,
    parse_s3_uri,
    s3_prefix_to_local_dir,
)


def _listing_prefix(prefix: str) -> str:
    """Return '' or '<prefix>/' for list_objects_v2 and relative-key slicing."""
    prefix = prefix.rstrip("/")
    return "" if prefix == "" else f"{prefix}/"


def _destination_for_key(*, local_dir: Path, key: str, listing_prefix: str) -> Path:
    """Map an S3 key to a local destination path under local_dir."""
    rel = key[len(listing_prefix) :] if listing_prefix else key
    return local_dir / rel


def _files_progress_bar(*, enabled: bool, bucket: str, prefix: str, total: int):
    """Create outer tqdm bar (or None)."""
    if not enabled:
        return None
    location = f"s3://{bucket}/{prefix}".rstrip("/")
    return tqdm(total=total, desc=f"Downloading {location}", unit="file")


class S3Directory:
    """Materializes an S3 prefix (s3://bucket/prefix/) to a local cached directory.

    Args:
        uri: S3 URI of the form ``"s3://<bucket>/<prefix>"``. The prefix may or may
            not end with ``/``. Use ``s3://bucket`` for bucket root.
        cache_dir: Local directory used to store cached copies. Defaults to
            ``Path.cwd() / ".s3cache"``.
        use_cache: If True (default), skip downloading files that already exist
            locally. If False, always re-download matching files.
        clear_on_exit: If True, delete the *local cached directory tree* for this
            prefix when exiting a context manager block.
        allowlist: Optional allowlist of glob patterns (string or list of strings).
        blocklist: Optional blocklist of glob patterns (string or list of strings).
        s3_client: Optional pre-configured boto3 S3 client. If None, a default
            client is created lazily on first use.
        show_progress: If True (default), show nested tqdm bars while downloading.
    """

    def __init__(
        self,
        uri: str,
        *,
        cache_dir: str | os.PathLike | None = None,
        use_cache: bool = True,
        clear_on_exit: bool = False,
        allowlist: str | list[str] | None = None,
        blocklist: str | list[str] | None = None,
        s3_client=None,
        show_progress: bool = True,
    ):
        loc = parse_s3_uri(uri)

        self.uri = uri
        self.bucket = loc.bucket
        self.prefix = loc.key.rstrip("/")  # may be ""

        self.cache_dir = (
            Path(cache_dir) if cache_dir is not None else (Path.cwd() / ".s3cache")
        )
        self.local_dir = s3_prefix_to_local_dir(
            cache_dir=self.cache_dir, bucket=self.bucket, prefix=self.prefix
        )

        self.use_cache = use_cache
        self.clear_on_exit = clear_on_exit
        self.show_progress = show_progress

        self.allowlist = as_patterns(allowlist)
        self.blocklist = as_patterns(blocklist)

        self._s3_client = s3_client

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    def iter_objects(self) -> list[dict]:
        return list_s3_objects(
            s3=self.s3_client,
            bucket=self.bucket,
            prefix=self.prefix,
            allowlist=self.allowlist,
            blocklist=self.blocklist,
        )

    def download(self) -> Path:
        ensure_gitignore(self.cache_dir)

        objects = self.iter_objects()
        listing_prefix = _listing_prefix(self.prefix)

        files_bar = _files_progress_bar(
            enabled=self.show_progress,
            bucket=self.bucket,
            prefix=self.prefix,
            total=len(objects),
        )

        try:
            for obj in objects:
                key = obj["Key"]
                size_bytes = int(obj.get("Size", 0)) or None

                destination = _destination_for_key(
                    local_dir=self.local_dir,
                    key=key,
                    listing_prefix=listing_prefix,
                )

                fetch_or_download(
                    s3=self.s3_client,
                    bucket=self.bucket,
                    key=key,
                    dst=destination,
                    use_cache=self.use_cache,
                    show_progress=self.show_progress,
                    total_bytes=size_bytes,
                )

                if files_bar is not None:
                    files_bar.update(1)
        finally:
            if files_bar is not None:
                files_bar.close()

        return self.local_dir

    @property
    def path(self) -> Path:
        return self.download()

    def clear(self, *, missing_ok: bool = True) -> None:
        if not self.local_dir.exists():
            if missing_ok:
                return
            raise FileNotFoundError(str(self.local_dir))
        shutil.rmtree(self.local_dir, ignore_errors=missing_ok)

    def __enter__(self) -> Path:
        return self.download()

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.clear_on_exit:
            self.clear(missing_ok=True)
        return False
