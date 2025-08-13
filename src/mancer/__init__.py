from .domain.model.version_info import VersionInfo
import logging

# Eksportujemy klasę i funkcję do łatwego dostępu
__version__ = VersionInfo.get_mancer_version().version

# Zapobiega ostrzeżeniom o braku handlerów po stronie bibliotek
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Importuj moduły dla dostępności w testach
from . import application
from . import infrastructure
from . import domain
