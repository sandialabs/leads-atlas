from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("leads_atlas")
except PackageNotFoundError:
    __version__ = "unknown"
