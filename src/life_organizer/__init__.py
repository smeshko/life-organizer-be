"""Life Organizer Backend - budget capture and query API for the Life Organizer iOS app."""

from importlib.metadata import PackageNotFoundError, version

__version__: str
try:
    __version__ = version("life-organizer")
except PackageNotFoundError:
    __version__ = "unknown"
