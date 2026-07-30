from __future__ import annotations

import os
from pathlib import Path

import boto3

from leads_atlas.s3.s3utils import ensure_gitignore, fetch_or_download, parse_s3_uri


class S3File:
    """Materializes an S3 object (s3://bucket/key) to a local file.

    The local file is stored under a cache directory that mirrors the bucket/key
    layout:

        <cache_dir>/<bucket>/<key>

    By default, ``cache_dir`` is ``.s3cache`` under the current working directory.
    When the cache directory is created, a ``.gitignore`` is also created at the
    cache root to prevent cached content from being tracked by git.

    Args:
        uri: S3 URI of the form ``"s3://<bucket>/<key>"``.
        cache_dir: Local directory used to store cached copies. Defaults to
            ``Path.cwd() / ".s3cache"``.
        use_cache: If True (default), reuse the cached file if it exists. If
            False, always download from S3 and overwrite any existing cached file.
        clear_on_exit: If True, delete the local cached file when exiting a
            context manager block. This only applies when using ``with``.
        s3_client: Optional pre-configured boto3 S3 client. If None, a default
            client is created lazily on first use.
        show_progress: If True (default), show a tqdm progress bar when downloading.
    """

    def __init__(
        self,
        uri: str,
        *,
        cache_dir: str | os.PathLike | None = None,
        use_cache: bool = True,
        clear_on_exit: bool = False,
        s3_client=None,
        show_progress: bool = True,
    ):
        loc = parse_s3_uri(uri)
        if not loc.key or loc.key.endswith("/"):
            raise ValueError(f"S3 uri must point to an object, not a prefix: {uri}")

        self.uri = uri
        self.bucket = loc.bucket
        self.key = loc.key

        self.cache_dir = (
            Path(cache_dir) if cache_dir is not None else (Path.cwd() / ".s3cache")
        )
        self.local_path = self.cache_dir / self.bucket / Path(self.key)

        self.use_cache = use_cache
        self.clear_on_exit = clear_on_exit
        self.show_progress = show_progress
        self._s3_client = s3_client

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    def exists(self) -> bool:
        return self.local_path.is_file()

    def download(self) -> Path:
        ensure_gitignore(self.cache_dir)
        return fetch_or_download(
            s3=self.s3_client,
            bucket=self.bucket,
            key=self.key,
            dst=self.local_path,
            use_cache=self.use_cache,
            show_progress=self.show_progress,
        )

    @property
    def path(self) -> Path:
        return self.download()

    def clear(self, *, missing_ok: bool = True) -> None:
        try:
            self.local_path.unlink()
        except FileNotFoundError:
            if not missing_ok:
                raise

    def __enter__(self) -> Path:
        return self.download()

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self.clear_on_exit:
            self.clear(missing_ok=True)
        return False
