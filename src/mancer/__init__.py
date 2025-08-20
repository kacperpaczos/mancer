import logging

from .domain.model.version_info import VersionInfo

# Eksportujemy klasę i funkcję do łatwego dostępu
__version__ = VersionInfo.get_mancer_version().version

# Zapobiega ostrzeżeniom o braku handlerów po stronie bibliotek
logging.getLogger(__name__).addHandler(logging.NullHandler())
