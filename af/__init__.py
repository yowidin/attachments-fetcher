from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("attachments-fetcher")
except PackageNotFoundError:
    __version__ = "unknown"
