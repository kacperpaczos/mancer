from .domain.model.version_info import VersionInfo

# Eksportujemy klasę i funkcję do łatwego dostępu
__version__ = VersionInfo.get_mancer_version().version

# Importuj moduły dla dostępności w testach
from . import application
from . import infrastructure
from . import domain
